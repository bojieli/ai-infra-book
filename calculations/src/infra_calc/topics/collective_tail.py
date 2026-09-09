"""Explicit rank readiness and weighted finite task completion traces."""
from fractions import Fraction
from ..sources import model_config, provenance
from ..units import positive_int


def weighted_quantile(rows, field, percent):
    """Nearest-rank quantile of integer-count observations, without expansion."""
    count = sum(row['count'] for row in rows)
    target = (percent * count + 99) // 100
    cumulative = 0
    for row in sorted(rows, key=lambda row: Fraction(row[field])):
        cumulative += row['count']
        if cumulative >= target:
            return Fraction(row[field])
    raise ValueError('Empty observations')


def calculate(model='qwen3-8b', tokens=1024, observations=None,
              exchange_speedup=2, post_compute_ns=0):
    positive_int(tokens, 'tokens')
    positive_int(exchange_speedup, 'exchange_speedup')
    positive_int(post_compute_ns, 'post_compute_ns', allow_zero=True)
    if observations is None:
        observations = [dict(name='book-ready-skew', count=1,
                             ready_ns=[0, 0, 0, 2000000], exchange_ns=400000,
                             recovery_ns=0)]
    if not isinstance(observations, list) or not observations:
        raise ValueError('Nonempty observations required')
    config = model_config(model)
    rows = []
    rank_count = None
    for observation in observations:
        ready = observation['ready_ns']
        if not isinstance(ready, list) or not ready:
            raise ValueError('At least one rank required')
        if rank_count is None:
            rank_count = len(ready)
        if len(ready) != rank_count:
            raise ValueError('All observations must have the same rank count')
        for value in ready:
            positive_int(value, 'ready_ns', allow_zero=True)
        for field in ('count', 'exchange_ns', 'recovery_ns'):
            positive_int(observation[field], field, allow_zero=field != 'count')
        last_ready = max(ready)
        exchange = observation['exchange_ns']
        recovery = observation['recovery_ns']
        baseline = last_ready + exchange + recovery + post_compute_ns
        faster = last_ready + Fraction(exchange, exchange_speedup) + recovery + post_compute_ns
        # Equalize every rank to the earliest observed ready time, not time zero.
        aligned = min(ready) + exchange + recovery + post_compute_ns
        rows.append(dict(name=observation.get('name', 'observation'), count=observation['count'],
                         ready_ns=ready, rank_wait_ns=[last_ready-t for t in ready],
                         exchange_ns=exchange, recovery_ns=recovery,
                         baseline_exact_ns=str(baseline), faster_exchange_exact_ns=str(faster),
                         aligned_ready_exact_ns=str(aligned),
                         no_recovery_exact_ns=str(baseline-recovery)))
    count = sum(row['count'] for row in rows)
    policies = []
    for field in ('baseline_exact_ns', 'faster_exchange_exact_ns',
                  'aligned_ready_exact_ns', 'no_recovery_exact_ns'):
        mean = sum(Fraction(row[field])*row['count'] for row in rows)/count
        policies.append(dict(policy=field.removesuffix('_exact_ns'), mean_exact_ns=str(mean),
                             p50_exact_ns=str(weighted_quantile(rows,field,50)),
                             p99_exact_ns=str(weighted_quantile(rows,field,99)),
                             max_exact_ns=str(max(Fraction(row[field]) for row in rows))))
    return dict(schema_version=1, calculation='collective-tail',
                scenario=dict(model=model,tokens=tokens,observations=observations,
                              exchange_speedup=exchange_speedup,post_compute_ns=post_compute_ns),
                sources=provenance(model), collective_observations=rows, completion_policies=policies,
                summary=dict(payload_bytes_per_rank=2*tokens*config['hidden_size'],
                             ranks=rank_count, observation_count=count,
                             baseline_mean_exact_ns=policies[0]['mean_exact_ns'],
                             faster_exchange_mean_exact_ns=policies[1]['mean_exact_ns'],
                             aligned_ready_mean_exact_ns=policies[2]['mean_exact_ns'],
                             baseline_p99_exact_ns=policies[0]['p99_exact_ns'],
                             faster_exchange_p99_exact_ns=policies[1]['p99_exact_ns'],
                             baseline_max_exact_ns=policies[0]['max_exact_ns']),
                assumptions=[
                    '官方hidden_size确定每rank BF16 [tokens,H]载荷；就绪、交换、恢复与后续计算时间为显式教学记录，不由payload或峰值带宽推断。',
                    '屏障教学模型：全部rank就绪后交换，随后串行恢复和后续计算。不能提前分块推进；真实集合通信需逐rank时间线校准。rank_wait之和是rank时间，不能加到墙钟时间。',
                    '四策略逐条配对：仅缩短交换、将就绪对齐到该条最早时刻、消除显式恢复，以及原始。它们是条件式反事实，不保证部署可实现。恢复不会随交换加速自动缩短。',
                    'count为有限记录的整数重复次数；p50/p99取排序后ceil(p*N)项，不插值。保留同一条记录中就绪、交换和恢复的联合关系，不相加边际分位数、不假设独立、不拟合故障概率。',
                    '观察分位数不等于总体SLO或统计置信结论；未模拟多次集合通信、故障重试、检查点回滚或完整训练作业。',
                ])
