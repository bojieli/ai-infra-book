"""Measured target/background completion under cache-first and queue-first rules."""
import hashlib
import json
from statistics import median
from ..paths import PROJECT
from ..models import forward
from ..schema import Scenario


def read_records():
    lock=json.loads((PROJECT/'configs/router-pressure.lock.json').read_text());raw={};sources=[]
    for entry in lock['files']:
        data=(PROJECT/entry['file']).read_bytes()
        if hashlib.sha256(data).hexdigest()!=entry['sha256']:raise ValueError('Pressure raw SHA mismatch')
        raw[entry['file'].split('sources/router-pressure/',1)[1]]=data.decode()
        sources.append(dict(file=entry['file'],url='../../'+entry['origin'],sha256=entry['sha256']))
    return raw,sources


def calculate():
    raw,sources=read_records();execution=json.loads(raw['results/execution.json'])
    for name,sha in execution['source_hashes'].items():
        if hashlib.sha256(raw[name].encode()).hexdigest()!=sha:raise ValueError('Execution identity mismatch')
    commands=execution['commands']
    if len(commands)!=2:raise ValueError('Expected two worker commands')
    for command in commands:
        if not command[command.index('--model-path')+1].endswith('b968826d9c46dd6066d109eabc6255188de91218') or command[command.index('--max-running-requests')+1]!='1' or command[command.index('--dtype')+1]!='bfloat16':
            raise ValueError('Unexpected model or running capacity')
    raw_rows=[json.loads(line) for line in raw['results/raw.jsonl'].splitlines()]
    inputs=json.loads(raw['results/inputs.json']);n=len(inputs['target_ids'])
    if len(raw_rows)!=6:raise ValueError('Expected six pressure conditions')
    cold=forward('qwen3-8b',Scenario(tokens=n,output_head='last'))
    rows=[];seen=set();reference=None
    for row in raw_rows:
        identity=(row['trial'],row['policy'])
        if identity in seen or row['policy'] not in ('cache_first','queue_first'):raise ValueError('Duplicate/unknown condition')
        seen.add(identity)
        target,warm,busy=(row[key] for key in ('target','warm','background'))
        for request in (target,warm,busy):
            if request['start_s']>request['end_s']:raise ValueError('Negative request duration')
        if not warm['end_s']<=busy['start_s']<target['start_s']<busy['end_s']:
            raise ValueError('Target was not sent during a live background request')
        warm_meta=warm['response']['meta_info']
        if warm_meta['prompt_tokens']!=n or warm_meta['completion_tokens']!=1:raise ValueError('Warm request mismatch')
        meta=target['response']['meta_info'];hit=meta['cached_tokens']
        if meta['prompt_tokens']!=n or meta['completion_tokens']!=1 or meta['num_retractions']!=0 or busy['response']['meta_info']['completion_tokens']!=128:
            raise ValueError('Unexpected measured workload')
        output=target['response']['output_ids']
        if output!=warm['response']['output_ids'] or len(output)!=1 or (reference is not None and output!=reference):
            raise ValueError('Target/warm output mismatch')
        reference=output
        load=row['decision_load']
        if load['31191'][0]['num_reqs']<1 or load['31192'][0]['num_reqs']!=0:
            raise ValueError('Decision load does not establish busy/cold choice')
        if not row['samples']:raise ValueError('Missing load samples')
        peak=max(sample['loads']['31191'][0]['num_waiting_reqs'] for sample in row['samples'])
        if row['policy']=='cache_first':
            if row['selected_port']!=31191 or hit!=n-1 or peak<1:raise ValueError('Cache-first observation mismatch')
        elif row['selected_port']!=31192 or hit!=0:raise ValueError('Queue-first observation mismatch')
        logical=forward('qwen3-8b',Scenario(tokens=n-hit,history=hit,output_head='last'))
        times=[sample['time_s'] for sample in row['samples']]
        if times!=sorted(times):raise ValueError('Sample clock is not ordered')
        rows.append(dict(trial=row['trial'],policy=row['policy'],selected_port=row['selected_port'],
                         cached_tokens=hit,prompt_tokens=n,target_seconds=target['end_s']-target['start_s'],
                         background_seconds=busy['end_s']-busy['start_s'],
                         pair_completion_seconds=max(target['end_s'],busy['end_s'])-busy['start_s'],
                         background_remaining_at_target_dispatch_seconds=busy['end_s']-target['start_s'],
                         sampled_waiting_peak=peak,sample_count=len(times),
                         max_sample_gap_seconds=max((b-a for a,b in zip(times,times[1:])),default=0),
                         target_logical_matrix_flops=logical['summary']['matrix_flops'],
                         target_saved_matrix_flops=cold['summary']['matrix_flops']-logical['summary']['matrix_flops']))
    trials=sorted({row['trial'] for row in rows})
    if len(trials)!=3 or len(seen)!=2*len(trials):raise ValueError('Incomplete paired trials')
    pairs=[]
    for trial in trials:
        a=next(row for row in rows if row['trial']==trial and row['policy']=='cache_first')
        b=next(row for row in rows if row['trial']==trial and row['policy']=='queue_first')
        pairs.append(dict(trial=trial,target_seconds_saved_by_queue_first=a['target_seconds']-b['target_seconds'],
                          pair_completion_seconds_added_by_queue_first=b['pair_completion_seconds']-a['pair_completion_seconds'],
                          background_seconds_added_by_queue_first=b['background_seconds']-a['background_seconds']))
    summary=dict(conditions=6,actual_generation_calls=18,target_prompt_tokens=n,
                 target_saved_seconds_paired_median=median(r['target_seconds_saved_by_queue_first'] for r in pairs),
                 pair_added_seconds_paired_median=median(r['pair_completion_seconds_added_by_queue_first'] for r in pairs))
    for policy in ('cache_first','queue_first'):
        selected=[row for row in rows if row['policy']==policy]
        for metric in ('target_seconds','background_seconds','pair_completion_seconds'):
            summary[policy+'_'+metric+'_median']=median(row[metric] for row in selected)
    return dict(schema_version=1,calculation='router-pressure',scenario=dict(experiment='9-9 queue-pressure'),
                sources=sources+cold['sources'],summary=summary,pressure_requests=rows,pressure_pairs=pairs,
                assumptions=[
                    '实验9-9补测两个Qwen8 BF16 worker共享RTX PRO，每实例max_running_requests=1，客户端cache_first/queue_first各3轮；不是原生Router策略实现。读取封存原件，不重跑服务。',
                    '每条件清缓存、预热、后台128输出及目标1输出，共18调用。目标从各自提交算完成；两任务从后台提交算最后完成，不能用目标局部收益替代整组收益。',
                    '核对实际决策负载、目标在后台活跃期间发出、命中3135/3136或0、输出与预热相同。单token输出与原失败Agent输入不证明任务质量。',
                    '队列峰值为离散/get_load采样，不是排队持续时间；background_remaining是事后计算，不是路由时的完成时间预测。实际采样最大间隔另列，不假定严格10ms。',
                    '配对差值先逐trial计算再取中位，另列每组中位，不混用中位数之差。只有3轮、共享GPU和观测开销，不推广跨机、线上p95或任意后台长度。',
                    '目标矩阵按官方逻辑前向复算，后台及完整服务性能不由此推断；实际部分prefill图仍启用，未称全程eager。事件恢复与预测路由仍待验证。',
                ])
