"""First three reduce-scatter rounds on a 16-node bidirectional physical ring."""
from collections import Counter
import hashlib
import json
from ..paths import PROJECT
from ..sources import model_config,provenance
from ..models import qwen3
from ..units import positive_int
from ..traffic import account


def shortest_path(sender,receiver,nodes=16):
    clockwise=(receiver-sender)%nodes
    anticlockwise=(sender-receiver)%nodes
    if not clockwise or clockwise==anticlockwise:
        raise ValueError('This example requires a unique nonempty shortest path')
    direction=1 if clockwise<anticlockwise else -1
    path=[];current=sender
    for _ in range(min(clockwise,anticlockwise)):
        following=(current+direction)%nodes
        path.append((current,following));current=following
    return path


def calculate(model='qwen3-8b',tokens=1024,rounds=3,bandwidth_bytes_per_second=50*10**9):
    for name,value in [('tokens',tokens),('rounds',rounds),('bandwidth_bytes_per_second',bandwidth_bytes_per_second)]:positive_int(value,name)
    if rounds>3:raise ValueError('Only the first three rounds of the 16-node example are supported')
    c=model_config(model);qwen3.validate(c)
    if tokens>c['max_position_embeddings']:raise ValueError('Tokens exceed pinned context')
    lock=json.loads((PROJECT/'configs/collective-paths.lock.json').read_text())
    if hashlib.sha256((PROJECT/lock['file']).read_bytes()).hexdigest()!=lock['sha256']:
        raise ValueError('Official Swing source hash mismatch')
    source={key:lock[key] for key in ('file','url','sha256')}
    payload=2*tokens*c['hidden_size']
    patterns=[]
    for name in ('recursive','swing'):
        schedules=[];paths={};details=[]
        for step in range(rounds):
            message=payload//2**(step+1)
            if message%2:raise ValueError('Round payload must contain whole BF16 values')
            offset=sum((-2)**i for i in range(step+1))
            edges=[];routes=[];counts=Counter()
            for rank in range(16):
                peer=rank^(1<<step) if name=='recursive' else (rank+(offset if rank%2==0 else -offset))%16
                route=shortest_path(rank,peer)
                resources=[f'{a}->{b}' for a,b in route]
                paths[(rank,peer)]=resources
                counts.update(resources)
                edges.append(dict(sender=rank,receiver=peer,bytes=message))
                routes.append(dict(sender=rank,receiver=peer,path=[list(edge) for edge in route],hops=len(route)))
            schedules.append(dict(phase='reduce_scatter_prefix',edges=edges))
            details.append(dict(round=step,message_bytes=message,routes=routes,
                                directed_link_messages=dict(sorted(counts.items())),
                                peak_link_messages=max(counts.values()),peak_link_bytes=max(counts.values())*message,
                                injected_bytes=16*message,physical_link_bytes=sum(counts.values())*message,
                                hops_per_message=sorted({r['hops'] for r in routes})))
        rates={f'{a}->{(a+d)%16}':bandwidth_bytes_per_second for a in range(16) for d in (-1,1)}
        physical=account(schedules,paths,rates)
        for row,phase in zip(details,physical['rounds']):
            row['directed_link_bytes']=phase['resource_bytes']
            row['serialization_lower_seconds']=phase['resource_lower_seconds']
        patterns.append(dict(pattern=name,rounds=details,physical_account=physical,
                             total_physical_link_bytes=sum(r['physical_link_bytes'] for r in details),
                             injected_bytes=physical['logical_send_bytes'],
                             sequential_round_lower_seconds=physical['sum_round_resource_lower_seconds']))
    return dict(schema_version=1,calculation='qwen-collective-physical-paths',model=model,
                scenario=dict(tokens=tokens,rounds=rounds,participants=16,bandwidth_bytes_per_second=bandwidth_bytes_per_second),
                sources=provenance(model)+[source],collective_path_patterns=patterns,
                summary=dict(payload_bytes_per_rank=payload,
                             enumerated_messages=sum(len(row['routes']) for p in patterns for row in p['rounds']),
                             recursive_physical_link_bytes=patterns[0]['total_physical_link_bytes'],
                             swing_physical_link_bytes=patterns[1]['total_physical_link_bytes'],
                             recursive_prefix_lower_seconds=patterns[0]['sequential_round_lower_seconds'],
                             swing_prefix_lower_seconds=patterns[1]['sequential_round_lower_seconds'],
                             full_all_reduce_seconds=None,measured_network_seconds=None),
                assumptions=[
                    '官方Qwen BF16[tokens,H]输入，默认8MiB；固定16物理节点双向环，仅枚举reduce-scatter前三轮4/2/1MiB消息，不是Qwen推荐部署，也不是完整all-reduce。',
                    '递归对端r XOR 2^s；Swing按官方论文式2，rho=sum((-2)^i)，偶数r加rho、奇数r减rho再模16。只采用已核对的前三轮路径，不复现完整块归约／重排或非二次幂算法正确性。',
                    '消息沿唯一最短路径，正反方向是独立有向资源，每经过一条链路计一次发送字节，不再加接收副本。平均跳数与最忙链路消息数分别枚举。',
                    '每条有向链路50GB/s是教学有效带宽；单轮下界为最大链路bytes/B，轮间屏障下界相加。未计启动、逐跳延迟、路由／端口共享、归约、包级阻塞和后续轮次。',
                    'physical_account同时保存全程聚合资源下界与逐轮下界，不能以聚合平均代替有屏障调度；前三轮下界比值不代表完整集合通信或训练加速比。',
                ])
