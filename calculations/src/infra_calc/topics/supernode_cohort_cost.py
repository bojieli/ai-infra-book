"""Experiment6-10: same burst, eight cards, capacity/service/failure/SLO/cost.

Official model geometry is reused; all service times, prices and failure
parameters below are explicit teaching inputs, not device measurements.
"""
from fractions import Fraction
from functools import lru_cache
from pathlib import Path
import json
from . import dense_placement, reconfiguration
from ..models import qwen3
from ..schema import Scenario
from ..units import positive_int


@lru_cache(maxsize=None)
def workload(model,prompt,outputs):
    stages=[('prefill',qwen3.calculate(model,Scenario(batch=1,tokens=prompt,output_head='last'))['summary']['matrix_flops'])]
    for step in range(outputs-1):
        result=qwen3.calculate(model,Scenario(batch=1,tokens=1,history=prompt+step))
        stages.append((f'decode{step}',result['summary']['matrix_flops']))
    return stages


@lru_cache(maxsize=None)
def placement(model,tp,prompt,outputs):
    return dense_placement.calculate(model=model,tp=tp,pp=1,dp=8//tp,batch_per_replica=1,
        history=prompt+outputs-2,tokens=1,capacity_bytes=24_000_000_000,workspace_bytes=2*2**30)


def schedule(requests,replicas,durations,stage_work,fault_at_ms,recovery_ms):
    """Static round-robin queues, one request per replica, restart whole attempt.

Completed requests win ties with failure. If a nonfinal stage ends exactly at
failure, that stage completed but the uncommitted whole request still restarts.
No request re-routing, batching, streaming commitment or spare hardware.
"""
    output=[];all_attempts=[];fault_used=False
    for replica in range(replicas):
        now=0;failure_consumed=replica!=0 or fault_at_ms is None
        for request in range(replica,requests,replicas):
            attempt_number=0
            while True:
                if not failure_consumed and now>=fault_at_ms:
                    now=max(now,fault_at_ms+recovery_ms);failure_consumed=True;fault_used=True
                start=now;complete=[];partial=None;aborted=False
                for index,((name,flops),duration) in enumerate(zip(stage_work,durations)):
                    end=now+duration
                    final=index==len(durations)-1
                    hit=not failure_consumed and (now<=fault_at_ms<end or (fault_at_ms==end and not final))
                    if hit:
                        spent=fault_at_ms-now
                        if spent==duration:
                            complete.append(dict(name=name,matrix_flops=flops))
                        else:
                            partial=dict(name=name,elapsed_ms=spent,matrix_flops=None)
                        now=fault_at_ms;aborted=True;failure_consumed=True;fault_used=True
                        break
                    now=end;complete.append(dict(name=name,matrix_flops=flops))
                row=dict(request=request,replica=replica,attempt=attempt_number,start_ms=start,end_ms=now,
                    aborted=aborted,completed_stages=complete,partial_stage=partial,
                    completed_stage_matrix_flops=sum(s['matrix_flops'] for s in complete))
                all_attempts.append(row)
                if aborted:
                    now=fault_at_ms+recovery_ms;attempt_number+=1
                else:
                    output.append(dict(request=request,replica=replica,arrival_ms=0,completion_ms=now,
                                       latency_ms=now,attempts=attempt_number+1));break
    return dict(requests=sorted(output,key=lambda row:row['request']),attempts=all_attempts,
        horizon_ms=max(row['completion_ms'] for row in output),fault_used=fault_used,
        abandoned_completed_stage_matrix_flops=sum(r['completed_stage_matrix_flops'] for r in all_attempts if r['aborted']),
        abandoned_partial_stage_work_unknown=any(r['partial_stage'] is not None for r in all_attempts))


def calculate(model='qwen3-8b',requests=4,prompt=256,outputs=8,deadline_ms=250,
              fault_at_ms=None,recovery_ms=100,recovery_fee='0',minimum_valid_fraction='3/4'):
    scenario=locals().copy()
    if model not in ('qwen3-8b','qwen3-32b'):
        raise ValueError('This finite scenario supports two pinned dense models')
    for key in ('requests','prompt','outputs','deadline_ms','recovery_ms'):
        positive_int(scenario[key],key,allow_zero=key=='recovery_ms')
    if fault_at_ms is not None:positive_int(fault_at_ms,'fault_at_ms',allow_zero=True)
    fee=reconfiguration.number(recovery_fee,'recovery_fee')
    minimum=reconfiguration.number(minimum_valid_fraction,'minimum_valid_fraction',positive=True)
    if minimum>1:raise ValueError('Minimum valid fraction exceeds1')
    required=(requests*minimum.numerator+minimum.denominator-1)//minimum.denominator
    work=workload(model,prompt,outputs)
    factor=1 if model=='qwen3-8b' else 2
    candidates=[]
    for tp,prefill_ms,decode_ms in ((8,20,6),(4,30,10),(2,48,16)):
        replicas=8//tp;placed=placement(model,tp,prompt,outputs)
        cards=[{key:c[key] for key in ('replica','tp_rank','weight_bytes','kv_bytes','workspace_bytes','resident_bytes','fits_declared_budget')} for c in placed['placement_cards']]
        capacity=placed['summary']['all_cards_fit_declared_budget']
        durations=[factor*prefill_ms]+[factor*decode_ms]*(outputs-1)
        row=dict(id=f'tp{tp}-replicas{replicas}',tp=tp,replicas=replicas,total_cards=8,
                 per_card_capacity_bytes=24_000_000_000,placement_cards=cards,
                 capacity_fits=capacity,declared_stage_durations_ms=durations,
                 schedule=None,cost=None,valid_requests=None,slo_eligible=False)
        if capacity:
            trace=schedule(requests,replicas,durations,work,fault_at_ms,recovery_ms)
            valid=sum(r['latency_ms']<=deadline_ms for r in trace['requests'])
            # Whole reservation includes idle, failed, recovery and restarted
            # compute time. Do not charge those card-ms again in other terms.
            terms={name:[] for name in reconfiguration.COST_TERMS}
            terms['steady_service']=[dict(quantity=8*trace['horizon_ms'],rate='1/1000')]
            terms['recovery_and_replay']=[dict(quantity=int(trace['fault_used']),rate=str(fee))]
            cost=reconfiguration.deployment_cost(dict(currency='declared_credit',terms=terms,
                slo_valid_completed_requests=valid))
            row.update(schedule=trace,cost=cost,valid_requests=valid,slo_eligible=valid>=required)
        candidates.append(row)
    eligible=[r for r in candidates if r['slo_eligible']]
    minimum_cost=min((Fraction(r['cost']['cost_per_slo_valid_request_exact']) for r in eligible),default=None)
    winners=[r['id'] for r in eligible if Fraction(r['cost']['cost_per_slo_valid_request_exact'])==minimum_cost]
    return dict(calculation='supernode-cohort-cost',scenario=scenario,
        sources=placement(model,8,prompt,outputs)['sources'],stages=[dict(name=n,matrix_flops=f) for n,f in work],
        candidates=candidates,selection=dict(required_valid_requests=required,eligible=[r['id'] for r in eligible],
            minimum_cost_per_valid_request_exact=None if minimum_cost is None else str(minimum_cost),winners=winners),
        assumptions=[
            '同一批requests在t=0到达，相同模型/P/G，静态轮转到服务副本，每副本一次服务一个请求；并发是到达cohort大小，不是tensor batch。全部8卡及全部副本始终预留至cohort完成。',
            'TP8单副本、TP4两副本、TP2四副本均总8卡。每卡24GB与2GiBworkspace为教学预算；真实BF16权重/KV/头归属来自公共适配器，队列不保留已算KV，活跃batch=1。必要容量通过不是运行峰值证明。',
            'prefill产生首输出，之后G−1次decode；最终KV是P+G−1。阶段矩阵工作来自真实模型，声明服务毫秒并非用FLOPs/峰值推算。32B服务倍率2是独立教学假设，不是实测比例。',
            '故障仅影响包含物理卡0的整个服务副本；其他副本按原队列继续。正在运行的请求全量重启，不迁移、不保留KV，也不复用已算token；已完整完成请求不重启，完成与故障同刻时先提交完成。',
            '服务成功只指声明计算cohort完成；无模型输出质量实验。SLO是原始arrival至完整响应的deadline，最低有效比例由输入声明，不把TTFT或流式部分输出混入分母。',
            '恢复停机长度是输入，期间受影响副本无服务。已完成但放弃的阶段FLOPs分列，故障打断阶段的工作未知，绝不按耗时比例推FLOPs。源权重可恢复性、checkpoint加载/重放细节未模拟。',
            '费用按8卡×cohort结束毫秒×1/1000声明credit，含闲置、失败、恢复和重做卡时；recovery_fee仅额外外部服务费，不再收同一GPU时段。其他费用在本教学边界显式设零，非真实TCO或现价。',
            '仅在必要容量及最低SLO有效比例都满足时，按包含所有失败/超时工作的总费用除有效请求数比较，保留持平和无可行候选。图/扫描的选择都以这些假设为条件。'])


def markdown(result):
    lines=['# 超节点规模：同请求集合、故障、SLO与费用', '', '```json',json.dumps(result['scenario'],ensure_ascii=False,indent=2),'```','',
           '| 部署 | 容量通过 | SLO有效数 | 完成ms | 全部声明费用 | 每有效请求费用 | 可选 |','|---|---|---:|---:|---:|---:|---|']
    for c in result['candidates']:
        schedule=c['schedule'] or {};cost=c['cost'] or {}
        lines.append(f"| {c['id']} | {c['capacity_fits']} | {c['valid_requests']} | {schedule.get('horizon_ms')} | {cost.get('full_declared_cost_exact')} | {cost.get('cost_per_slo_valid_request_exact')} | {c['slo_eligible']} |")
    lines += ['', '选择：`'+json.dumps(result['selection'],ensure_ascii=False)+'`','',
              '| 部署 | 请求 | 副本 | 完成ms | 尝试次数 |','|---|---:|---:|---:|---:|']
    for c in result['candidates']:
        for r in (c['schedule'] or {}).get('requests',[]):
            lines.append(f"| {c['id']} | {r['request']} | {r['replica']} | {r['completion_ms']} | {r['attempts']} |")
    lines += ['', *result['assumptions'],'','```json',json.dumps(result,ensure_ascii=False,indent=2),'```','']
    return '\n'.join(lines)
