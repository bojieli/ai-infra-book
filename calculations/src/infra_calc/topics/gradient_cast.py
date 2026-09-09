"""One full gate-gradient transfer: casting placement and live buffer capacity."""
from fractions import Fraction

from ..models import qwen3, qwen3_moe
from ..sources import model_config, provenance
from ..units import positive_int
from .pipeline_schedule import peak_intervals


def calculate(model='qwen3-8b', link_bytes_per_second=32*10**9,
              cpu_cast_bytes_per_second=100*10**9, gpu_cast_bytes_per_second=1500*10**9,
              copy_startup_ns=0, cpu_cast_startup_ns=0, gpu_cast_startup_ns=0,
              extra_gpu_budget_bytes=256*1024**2, host_budget_bytes=512*1024**2):
    inputs = dict(model=model, link_bytes_per_second=link_bytes_per_second,
                  cpu_cast_bytes_per_second=cpu_cast_bytes_per_second,
                  gpu_cast_bytes_per_second=gpu_cast_bytes_per_second,
                  copy_startup_ns=copy_startup_ns, cpu_cast_startup_ns=cpu_cast_startup_ns,
                  gpu_cast_startup_ns=gpu_cast_startup_ns,
                  extra_gpu_budget_bytes=extra_gpu_budget_bytes, host_budget_bytes=host_budget_bytes)
    for name, value in inputs.items():
        if name != 'model':
            positive_int(value, name, allow_zero=not name.endswith('per_second'))
    config = model_config(model)
    adapter = qwen3_moe if config['model_type'] == 'qwen3_moe' else qwen3
    adapter.validate(config)
    hidden = config['hidden_size']
    ffn = config['moe_intermediate_size'] if config['model_type'] == 'qwen3_moe' else config['intermediate_size']
    n = hidden * ffn
    bf16, fp32, cast_access = 2*n, 4*n, 6*n
    cpu_cast = Fraction(cast_access, cpu_cast_bytes_per_second) + Fraction(cpu_cast_startup_ns, 10**9)
    gpu_cast = Fraction(cast_access, gpu_cast_bytes_per_second) + Fraction(gpu_cast_startup_ns, 10**9)
    small_copy = Fraction(bf16, link_bytes_per_second) + Fraction(copy_startup_ns, 10**9)
    large_copy = Fraction(fp32, link_bytes_per_second) + Fraction(copy_startup_ns, 10**9)
    paths = []
    for location in ('cpu', 'gpu'):
        if location == 'cpu':
            finish = small_copy + cpu_cast
            operations = [('d2h_bf16', Fraction(0), small_copy, bf16),
                          ('cast_on_cpu', small_copy, finish, cast_access)]
            buffers = [('gpu', 'common_bf16_gradient', Fraction(0), small_copy, bf16, True),
                       ('host', 'bf16_staging', Fraction(0), finish, bf16, False),
                       ('host', 'fp32_output', small_copy, finish, fp32, False)]
        else:
            finish = gpu_cast + large_copy
            operations = [('cast_on_gpu', Fraction(0), gpu_cast, cast_access),
                          ('d2h_fp32', gpu_cast, finish, fp32)]
            buffers = [('gpu', 'common_bf16_gradient', Fraction(0), gpu_cast, bf16, True),
                       ('gpu', 'fp32_staging', Fraction(0), finish, fp32, False),
                       ('host', 'fp32_output', gpu_cast, finish, fp32, False)]
        peaks = {tier: peak_intervals([(start, end, size) for t, _, start, end, size, _ in buffers if t == tier])
                 for tier in ('gpu', 'host')}
        extra_gpu = peak_intervals([(start, end, size) for tier, _, start, end, size, common in buffers if tier == 'gpu' and not common])
        fits = extra_gpu <= extra_gpu_budget_bytes and peaks['host'] <= host_budget_bytes
        paths.append(dict(cast_location=location, ready_seconds=float(finish), ready_exact_seconds=str(finish),
                          link_payload_bytes=bf16 if location == 'cpu' else fp32,
                          cast_read_write_bytes=cast_access, gpu_peak_including_common_bytes=peaks['gpu'],
                          extra_gpu_peak_bytes=extra_gpu, host_peak_bytes=peaks['host'],
                          specified_buffers_fit=fits,
                          operations=[dict(name=name, start_exact_seconds=str(start), end_exact_seconds=str(end), logical_bytes=size)
                                      for name, start, end, size in operations],
                          buffers=[dict(tier=tier, name=name, start_exact_seconds=str(start), end_exact_seconds=str(end), bytes=size, common_input=common)
                                   for tier, name, start, end, size, common in buffers]))
    cast_saving = cpu_cast - gpu_cast
    threshold = Fraction(fp32-bf16, 1) / cast_saving if cast_saving > 0 else None
    best_time = min(Fraction(p['ready_exact_seconds']) for p in paths)
    feasible = [p for p in paths if p['specified_buffers_fit']]
    feasible_time = min((Fraction(p['ready_exact_seconds']) for p in feasible), default=None)
    return dict(schema_version=1, calculation='gradient-cast', model=model, scenario=inputs,
                sources=provenance(model), gradient_cast_paths=paths,
                summary=dict(gate_shape=[ffn, hidden], gradient_elements=n, bf16_bytes=bf16, fp32_bytes=fp32,
                             cast_logical_read_write_bytes=cast_access,
                             cpu_cast_exact_seconds=str(cpu_cast), gpu_cast_exact_seconds=str(gpu_cast),
                             equal_time_link_bytes_per_second_exact=str(threshold) if threshold is not None else None,
                             fastest_without_capacity=[p['cast_location'] for p in paths if Fraction(p['ready_exact_seconds']) == best_time],
                             fastest_fitting_buffers=[p['cast_location'] for p in feasible if Fraction(p['ready_exact_seconds']) == feasible_time]),
                assumptions=[
                    '官方Qwen一层gate梯度，MoE为一个专家而非全层专家集合。GPU已有BF16梯度，终点为CPU可消费FP32；主权重、Adam更新、参数回传和其它层不在这段路径内。',
                    '转换逻辑访问每元素读2写4，共6Nbytes；带宽为针对该操作总读写的有效吞吐输入，不是硬件峰值或实测。链路是有效单向D2H。BF16到FP32不改变有限值表示，未模拟数值内核。',
                    '同一完整张量内cast/copy顺序执行、不分块、不重叠；相同copy启动两路各付一次，cast启动可不同。CPU转换比GPU转换慢时才有正交点，GPU路径严格更快需要链路超过交点；交点相等保留两者。',
                    '双方主机缓冲均已锁页、预分配。只报告声明区间内的活跃载荷，缓冲池预留和allocator另计。源梯度为共有输入，GPU净额外预算不重复扣除它。输入在最后读取结束释放，FP32输出在就绪终点交给CPU消费者；消费者之后的生命周期另算。',
                    'CPU路径host输入保留到cast读完，输出从cast开始写入，两者重叠；GPU路径FP32暂存保留到D2H读完。时间为半开区间，全部使用精确有理数。容量通过仅表示这组缓冲可容纳，不证明整个训练步可执行或加速。',
                ])
