"""Conditional service demand for a declared RL cohort and resource mapping.

Pool occupancies add when stages share resources. The pipeline bound does not
assert that policy-version dependencies permit that overlap.
"""
from ..units import positive_int, positive_number, ceil_div
from . import rl_cycle


def teaching_supply() -> dict:
    return dict(matrix={
        'rollout_prefill': dict(pool='actor', flops_per_second=200e12),
        'rollout_decode': dict(pool='actor', flops_per_second=20e12),
        'reference_scoring': dict(pool='reference', flops_per_second=200e12),
        'teacher_scoring': dict(pool='teacher', flops_per_second=200e12),
        'policy_update': dict(pool='learner', flops_per_second=200e12)},
        verifier=dict(pool='verifier', seconds_per_candidate=0.05, workers=8),
        synchronization=dict(pool='weight_link', bytes_per_second=50e9))


def calculate(cycle: dict | None = None, supply: dict | None = None,
              pool_speedups: dict | None = None) -> dict:
    workload = rl_cycle.calculate(**(cycle or {}))
    supplied = teaching_supply() if supply is None else supply
    if set(supplied) != {'matrix', 'verifier', 'synchronization'}:
        raise ValueError('Supply requires matrix, verifier and synchronization records')
    names = {r['name'] for r in workload['rl_stages']}
    if set(supplied['matrix']) != names:
        raise ValueError('Supply must name every matrix stage exactly once')
    speedups = pool_speedups or {}
    rows = []
    pools = {}

    def add(stage, pool, seconds, serial_seconds=None):
        if not isinstance(pool, str) or not pool:
            raise ValueError('Pool must be a nonempty string')
        factor = positive_number(speedups.get(pool, 1), 'pool speedup')
        rows.append(dict(stage=stage, pool=pool, speedup=factor,
                         service_seconds=seconds / factor,
                         isolated_batch_seconds=(seconds if serial_seconds is None else serial_seconds) / factor))
        pools[pool] = pools.get(pool, 0) + seconds / factor

    for stage in workload['rl_stages']:
        record = supplied['matrix'][stage['name']]
        rate = positive_number(record['flops_per_second'], 'effective matrix FLOPs/s')
        add(stage['name'], record['pool'], stage['matrix_flops'] / rate)
    v = supplied['verifier']
    workers = positive_int(v['workers'], 'verifier workers')
    per_candidate = positive_number(v['seconds_per_candidate'], 'verifier seconds/candidate')
    candidates = workload['summary']['generated_samples']
    # Throughput demand versus finite-batch wave rounding must stay distinct.
    add('verification', v['pool'], candidates * per_candidate / workers,
        ceil_div(candidates, workers) * per_candidate)
    sync = supplied['synchronization']
    bandwidth = positive_number(sync['bytes_per_second'], 'sync bandwidth bytes/s')
    add('weight_sync', sync['pool'], workload['summary']['independent_unicast_weight_sync_bytes'] / bandwidth)
    if set(speedups) - pools.keys():
        raise ValueError('Speedup names an unused pool')
    bottleneck = max(pools.values())
    serial = sum(r['isolated_batch_seconds'] for r in rows)
    accepted = workload['summary']['accepted_samples']
    return dict(schema_version=1, calculation='rl-conditional-resource-supply', model=workload['model'],
                scenario=dict(cycle=workload['scenario'], supply=supplied, pool_speedups=speedups,
                              supply_kind='teaching_assumption' if supply is None else 'user_supplied_unverified'),
                sources=workload['sources'], service_stages=rows, pool_service_seconds=pools,
                summary=dict(generated_samples=candidates, accepted_samples=accepted,
                             serial_component_batch_seconds=serial,
                             ideal_pipeline_interval_lower_seconds=bottleneck,
                             limiting_pools=[name for name, value in pools.items() if value == bottleneck],
                             conditional_serial_accepted_samples_per_second=accepted / serial,
                             ideal_pipeline_accepted_samples_per_second_upper=accepted / bottleneck,
                             actual_cycle_seconds=None),
                assumptions=workload['assumptions'] + [
                    '本表为显式供给情景：默认矩阵速率、验证服务时间及链路带宽均为教学输入，不是官方 GPU 峰值或实测。输入速率必须与本账有效矩阵 FLOPs 口径相同；不能把含 padding 的硬件执行量或稀疏宣传值直接作为分母。',
                    '矩阵阶段时间为工作量除该阶段占用整个 pool 时的聚合有效速率，不再额外乘除 GPU 数。相同 pool 的阶段占用相加；不同 pool 仅在理想无限缓冲、多批流水条件下可重叠。',
                    '验证对全部候选执行，workers 个同速独立服务槽。孤立批次按 ceil(候选/workers) 轮计；稳态服务需求按总候选服务量/workers 计。尾轮空槽不能误当持续资源需求。',
                    'serial_component_batch_seconds 是所列组件依次执行的条件模型；max(pool 累积需求) 是多批流水间隔下界。同步 on-policy 下一批依赖新权重时不能直接使用流水吞吐上界，且真实损失／优化器／排队等缺项未补齐。',
                    'pool_speedups 是假设整个 pool 的服务能力按比例提升，包括同池全部阶段；不保证加倍设备就达到加倍服务率，也不改变样本质量、接受数或工作量。验证池倍率解释为每个 worker 服务变快，不改变有限批次轮数。',
                ])
