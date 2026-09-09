"""Enumerate integer PD pool assignments in one common request unit.

Effective stage rates are supplied for the stated workload; they are not inferred
from advertised Tensor FLOPS. Results are steady-state resource bounds, not SLOs.
"""
from fractions import Fraction
from itertools import product
from math import prod
from ..units import positive_int
from . import state


def exact_rate(value, name, allow_zero=False):
    if isinstance(value, bool) or not isinstance(value, (int, str)):
        raise ValueError(f'{name} must be an integer or exact decimal/fraction string')
    try:
        result = Fraction(value)
    except (ValueError, ZeroDivisionError) as exc:
        raise ValueError(f'Invalid {name}') from exc
    if result < 0 or (result == 0 and not allow_zero):
        raise ValueError(f'{name} must be positive')
    return result


def calculate(model='qwen3-8b', prompt_tokens=8192, output_tokens=129,
              cached_prefix_tokens=0, workers=None, network_bytes_per_second=25*10**9,
              arrival_requests_per_second='4'):
    for name, value in [('prompt_tokens',prompt_tokens),('output_tokens',output_tokens),
                        ('cached_prefix_tokens',cached_prefix_tokens)]:
        positive_int(value,name,allow_zero=name=='cached_prefix_tokens')
    if cached_prefix_tokens >= prompt_tokens:
        raise ValueError('At least one uncached prefill token is required')
    network = exact_rate(network_bytes_per_second,'network_bytes_per_second')
    arrival = exact_rate(arrival_requests_per_second,'arrival_requests_per_second',True)
    workers = ([dict(name='prefill-oriented',count=4,prefill_tokens_per_second=16384,
                     decode_tokens_per_second=64),
                dict(name='decode-oriented',count=4,prefill_tokens_per_second=4096,
                     decode_tokens_per_second=256)] if workers is None else workers)
    if not isinstance(workers,list) or not workers:
        raise ValueError('Supply nonempty worker types')
    names=set(); types=[]
    new_tokens=prompt_tokens-cached_prefix_tokens
    decode_calls=output_tokens-1
    for worker in workers:
        if not isinstance(worker,dict) or set(worker) != {'name','count','prefill_tokens_per_second','decode_tokens_per_second'}:
            raise ValueError('Each worker requires name, count and both stage token rates')
        name=worker['name']
        if not isinstance(name,str) or not name or name in names:
            raise ValueError('Worker names must be distinct nonempty strings')
        names.add(name);positive_int(worker['count'],'count')
        p=exact_rate(worker['prefill_tokens_per_second'],'prefill_tokens_per_second')
        d=exact_rate(worker['decode_tokens_per_second'],'decode_tokens_per_second')
        prefill_seconds=Fraction(new_tokens)/p
        decode_seconds=Fraction(decode_calls)/d
        types.append(dict(name=name,count=worker['count'],p=p/new_tokens,
                          d=d/decode_calls if decode_calls else None,
                          prefill_seconds=prefill_seconds,decode_seconds=decode_seconds,
                          colocated=1/(prefill_seconds+decode_seconds)))
    if prod(t['count']+1 for t in types)>100000:
        raise ValueError('Enumeration limited to 100000 assignments')
    # A cold decode destination needs the full prompt state, including P cache hits.
    state_result=state.calculate(model,prompt_tokens)
    snapshot=state_result['summary']['resident_bytes']
    transferred=snapshot if decode_calls else 0
    network_capacity=network/transferred if transferred else None
    colocated=sum((t['count']*t['colocated'] for t in types),Fraction(0))
    rows=[]
    for assignment in product(*(range(t['count']+1) for t in types)):
        p=sum((n*t['p'] for n,t in zip(assignment,types)),Fraction(0))
        d=sum(((t['count']-n)*t['d'] for n,t in zip(assignment,types)),Fraction(0)) if decode_calls else None
        capacities={'prefill':p}
        if decode_calls:
            capacities.update(decode=d,network=network_capacity)
        bound=min(capacities.values())
        rows.append(dict(prefill_workers=dict(zip([t['name'] for t in types],assignment)),
                         decode_workers={t['name']:t['count']-n for t,n in zip(types,assignment)},
                         prefill_requests_per_second_exact=str(p),
                         decode_requests_per_second_exact=str(d) if d is not None else None,
                         bound_requests_per_second_exact=str(bound),
                         bottlenecks=[key for key,value in capacities.items() if value==bound],
                         strictly_below_all_capacity_bounds=arrival<bound,
                         network_demand_at_bound_exact_bytes_per_second=str(bound*transferred)))
    best=max(rows,key=lambda row:Fraction(row['bound_requests_per_second_exact']))
    best_rate=Fraction(best['bound_requests_per_second_exact'])
    return dict(schema_version=1,calculation='pd-pool',sources=state_result['sources'],
                scenario=dict(model=model,prompt_tokens=prompt_tokens,output_tokens=output_tokens,
                              cached_prefix_tokens=cached_prefix_tokens,workers=workers,
                              network_bytes_per_second=network_bytes_per_second,
                              arrival_requests_per_second=arrival_requests_per_second),
                summary=dict(new_prefill_tokens_per_request=new_tokens,decode_calls_per_request=decode_calls,
                             full_prompt_state_bytes=snapshot,pd_transfer_bytes_per_request=transferred,
                             network_capacity_requests_per_second_exact=str(network_capacity) if network_capacity is not None else None,
                             assignments=len(rows),best_prefill_workers=best['prefill_workers'],
                             best_decode_workers=best['decode_workers'],
                             best_pd_bound_requests_per_second_exact=str(best_rate),
                             colocated_bound_requests_per_second_exact=str(colocated),
                             pd_to_colocated_bound_ratio_exact=str(best_rate/colocated),
                             best_bottlenecks=best['bottlenecks'],
                             arrival_strictly_below_best_pd_bound=arrival<best_rate,
                             arrival_strictly_below_colocated_bound=arrival<colocated),
                pool_assignments=rows,
                pool_worker_rates=[dict(name=t['name'],count=t['count'],
                                        prefill_service_seconds_exact=str(t['prefill_seconds']),
                                        decode_service_seconds_exact=str(t['decode_seconds']),
                                        colocated_requests_per_second_exact=str(t['colocated'])) for t in types],
                assumptions=[
                    '两个教学worker类型不是A100/H20规格或实测；每个worker代表已能容纳该完整模型与所需KV的独立服务副本，可为一组设备。模型放置、并行组、实际内存可行性须另外验收。',
                    '输入阶段token/s必须对应相同模型、精度、上下文、batch和质量条件下的有效服务能力。prefill按新处理token数，decode按调用次数；prefill最后logits产生首输出，所以G输出需要G-1次decode。',
                    '每个worker固定分配P或D，池内允许理想流量分配；独立资源容量取min，异构副本的请求/s先相加。共置每副本先加两个阶段的资源秒再取倒数，假定阶段共享资源且无额外混跑惩罚。',
                    '这是给定服务能力的稳态上界。没有请求排队、时变负载、启动同步、流水填充、transfer窗口限制、SLO、能耗或费用，不能把低于上界视为稳定性或尾延迟保证。',
                    'P已命中前缀仅减少其新token工作；假设D冷缓存，仍交接完整prompt状态。跨长度复用相同token/s只是一项教学敏感性假设，实际需重新校准。',
                    'KV使用state模块的默认BF16与模型状态约定，不含格式转换、分片复制、路由元数据或双端temporary。网络给共享有效单向payload带宽上界，收发不重复相加。',
                    '仅一个输出时不需要D调用或KV交接，最优把全部worker给P；多输出时要求两个池都有正能力。到达率恰等容量不标为严格低于，余量也不代替SLO证据。',
                    '枚举内最大值只对当前整数候选与假设成立；同值选输入顺序中的首项，不是唯一配比或真实系统最优。',
                ])
