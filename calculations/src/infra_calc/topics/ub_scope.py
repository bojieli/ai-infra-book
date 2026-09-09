"""Eight-card capacity and declared communication path across one/two servers.

Modern model exercise, not a reconstruction of the historical UB workload.
"""
from fractions import Fraction
import hashlib
import json
from ..paths import PROJECT
from ..sources import provenance
from ..units import positive_int
from .pd_pool import exact_rate
from . import dense_placement,dense_communication


def historical_evidence():
    rows=json.loads((PROJECT/'configs/ub-scope.lock.json').read_text())
    for r in rows:
        b=(PROJECT/r['file']).read_bytes()
        if len(b)!=r['bytes'] or hashlib.sha256(b).hexdigest()!=r['sha256']:
            raise ValueError('UB historical source changed')
    return rows


def calculate(model='qwen3-32b',history=8192,batch=1,decode_steps=32,
              capacity_bytes=24_000_000_000,workspace_bytes=2*2**30,
              local_bytes_per_second=50_000_000_000,local_startup_ns=2000,
              remote_bytes_per_second=25_000_000_000,remote_startup_ns=5000):
    scenario=locals().copy()
    for k in ('history','workspace_bytes','local_startup_ns','remote_startup_ns'):
        positive_int(scenario[k],k,allow_zero=True)
    for k in ('batch','decode_steps','capacity_bytes'):positive_int(scenario[k],k)
    local_bw=exact_rate(local_bytes_per_second,'local_bytes_per_second')
    remote_bw=exact_rate(remote_bytes_per_second,'remote_bytes_per_second')
    local_alpha=Fraction(local_startup_ns,10**9);remote_alpha=Fraction(remote_startup_ns,10**9)
    candidates=[]
    for name,tp,pp in [('single_server_tp8',8,1),('two_servers_tp4_pp2',4,2)]:
        # Cache grows over the sequence; final forward is the capacity maximum.
        placement=dense_placement.calculate(model=model,tp=tp,pp=pp,batch_per_replica=batch,
            history=history+decode_steps-1,tokens=1,capacity_bytes=capacity_bytes,workspace_bytes=workspace_bytes)
        path=dense_communication.calculate(model=model,tp=tp,pp=pp,batch_per_replica=batch,tokens=1)
        cards=[]
        for card in placement['placement_cards']:
            cards.append(dict(card,server=card['stage'] if pp>1 else 0,physical_card=card['stage']*tp+card['tp_rank']))
        operations=[];local_time=Fraction(0);remote_payload=0;remote_calls=0
        for op in path['communication_operations']:
            remote=op['name'] in ('pipeline_hidden_transfer','selected_token_to_first_stage')
            # PP rank links share a single server egress in this exercise.
            size=op['network_send_bytes_per_replica'] if remote else op['critical_resource_bytes']
            rounds=1 if remote else op['rounds']
            time=rounds*(remote_alpha if remote else local_alpha)+Fraction(size)/(remote_bw if remote else local_bw)
            if remote:
                remote_payload+=size;remote_calls+=1
            else:local_time+=time
            operations.append(dict(name=op['name'],stage=op['stage'],layer=op['layer'],
                interface='shared_interserver_egress' if remote else 'independent_local_collective_edges',
                occurrences_per_forward=1,forward_evaluations=decode_steps,
                startup_rounds_per_forward=rounds,startup_rounds_all_forwards=rounds*decode_steps,
                network_send_bytes_per_forward=op['network_send_bytes_per_replica'],
                network_send_bytes_all_forwards=op['network_send_bytes_per_replica']*decode_steps,
                charged_resource_bytes_per_forward=size,
                modeled_seconds_per_forward_exact=str(time),modeled_seconds_all_forwards_exact=str(time*decode_steps)))
        remote_time=remote_calls*remote_alpha+Fraction(remote_payload)/remote_bw
        total=local_time+remote_time
        candidates.append(dict(name=name,servers=pp,cards_per_server=tp,placement_cards=cards,
            placement_summary=placement['summary'],handoff_operations=operations,
            summary=dict(final_cache_positions=history+decode_steps,
                all_cards_fit=placement['summary']['all_cards_fit_declared_budget'],
                maximum_card_resident_bytes=placement['summary']['maximum_card_resident_bytes'],
                local_communication_seconds_per_forward_exact=str(local_time),
                interserver_payload_bytes_per_forward=remote_payload,
                interserver_startup_calls_per_forward=remote_calls,
                serial_communication_seconds_per_forward_exact=str(total),
                serial_communication_seconds_all_forwards_exact=str(total*decode_steps),
                predicted_iteration_seconds=None)))
    one,two=(x['summary'] for x in candidates)
    single=Fraction(one['serial_communication_seconds_per_forward_exact'])
    dual=Fraction(two['serial_communication_seconds_per_forward_exact'])
    cross_local=Fraction(two['local_communication_seconds_per_forward_exact'])
    payload=two['interserver_payload_bytes_per_forward'];calls=two['interserver_startup_calls_per_forward']
    available=single-cross_local-calls*remote_alpha
    maximum_alpha=(single-cross_local-Fraction(payload)/remote_bw)/calls
    preferred='tie' if single==dual else ('single_server_tp8' if single<dual else 'two_servers_tp4_pp2')
    return dict(schema_version=1,calculation='ub-scope',model=model,scenario=scenario,
        sources=provenance(model),historical_sources=historical_evidence(),scope_candidates=candidates,
        scope_crossover=dict(comparison='declared serial communication only; assumes both capacity-feasible',
            remote_bandwidth_threshold_bytes_per_second_exact=str(Fraction(payload)/available) if available>0 else None,
            bandwidth_threshold_relation='two-server path is lower strictly above threshold' if available>0 else 'no finite remote bandwidth wins at supplied startup',
            remote_startup_threshold_seconds_exact=str(maximum_alpha) if maximum_alpha>=0 else None,
            startup_threshold_relation='two-server path is lower strictly below threshold' if maximum_alpha>=0 else 'no nonnegative remote startup wins at supplied bandwidth',
            communication_only_preference=preferred,
            both_capacity_feasible=one['all_cards_fit'] and two['all_cards_fit']),
        assumptions=[
            '同一固定官方当代Qwen3 Dense模型、相同8卡与请求量，单机TP8对双机TP4×PP2；现代模型仅是教学载荷，不代表UB研究开始时已知的需求或历史硬件配置。',
            '作者回忆只支持研究早于2020年GPT-3转折、其后获得更大认可和投入的时间线；当年实际模型、接口有效带宽/启动与价格未知，本结果不据此替历史团队作定量结论。',
            '逐卡复用dense-placement的BF16权重、真实GQA KV头归属及显式workspace；容量按最后一步history+decode_steps，未声称覆盖全部activation/allocator峰值。DP=1，8张卡均有独立容量检查。',
            '逐次复用dense-communication完整声明图：词表embedding规约、每层attention/FFN规约、PP hidden、末位logits收集、所选token返回及首阶段广播。decode_steps是执行次数，预填充不混入此账。',
            '每服务器内部TP环边独立；跨机只有一个声明共享出口，4份复制hidden按4倍载荷串行占用出口，随后token反馈另一次启动；不把4个rank发送当4条独立NIC带宽。',
            '每个通信图按依赖顺序累加，仅是通信路径预算。计算、采样、排队、重叠、pipeline气泡与SLO未计，communication_only_preference不是模型总时延/吞吐最优决定；容量不合格时不据比较选择该方案。',
            '启动按每collective轮/PP服务启动定义，带宽是显式单向有效服务条件，不引用宣传峰值；翻转阈值仅在此固定消息图、共享出口和服务假设下成立。',
        ])
