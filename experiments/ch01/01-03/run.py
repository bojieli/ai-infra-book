#!/usr/bin/env python3
"""实验 1-3：什么改动能缩短生成时间。

沿第 1 章的教学模型（名义 70B，逐 token 生成）分别做四种改动：翻倍算力、
翻倍带宽、降低存储位宽、增加 batch。每种改动都按同一顺序回答三个问题：

  1. 容量：权重＋声明的状态与工作区能否驻留？放不下就不必比时间。
  2. 计算下界：矩阵工作 ÷ 计算峰值。
  3. 读取下界：这一步必须读写的字节 ÷ 显存带宽。

取两项下界的最大值作为该步的资源时间下界（假设两者可以重叠），并记录
当前由哪一项主导、以及这次改动没有计入哪些新增成本。

只依赖 Python 3 标准库。
"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(HERE, 'results')

GB = 10 ** 9

# 官方资源卡（H100 SXM 标称值；BF16 输入／FP32 累加／dense 张量峰值）
PEAK_FLOPS = 989.4e12
BANDWIDTH = 3.35e12
CAPACITY = 80 * GB

PARAMETERS = 70_000_000_000


def budget(label, weight_bits=8, batch=1, compute_multiplier=1.0, bandwidth_multiplier=1.0,
           kv_history_bytes=0, kv_append_bytes=0, workspace_bytes=0, note=''):
    """一步 decode 的容量检查与两项资源下界。"""
    compute = PEAK_FLOPS * compute_multiplier
    bandwidth = BANDWIDTH * bandwidth_multiplier
    weights = (PARAMETERS * weight_bits + 7) // 8
    per_request = kv_history_bytes + kv_append_bytes
    traffic = weights + batch * per_request          # 权重整批共读一次
    resident = traffic + workspace_bytes
    flops = 2 * PARAMETERS * batch                    # 每参数两次浮点运算
    fits = resident <= CAPACITY
    compute_seconds = flops / compute
    memory_seconds = traffic / bandwidth
    lower_bound = max(compute_seconds, memory_seconds)
    return dict(
        label=label, note=note,
        weight_bits=weight_bits, batch=batch,
        compute_multiplier=compute_multiplier, bandwidth_multiplier=bandwidth_multiplier,
        weight_bytes=weights, declared_traffic_bytes=traffic, resident_bytes=resident,
        capacity_bytes=CAPACITY, fits_capacity=fits,
        matrix_flops=flops,
        arithmetic_intensity=flops / traffic,
        compute_seconds=compute_seconds, memory_seconds=memory_seconds,
        resource_lower_bound_seconds=lower_bound if fits else None,
        dominant='compute' if compute_seconds >= memory_seconds else 'memory',
        tokens_per_second=(batch / lower_bound) if fits else None,
    )


def crossover_batch(weight_bits=8, per_request_bytes=0):
    """计算与读取相等的 batch：shared/bw = B*2N/compute + B*kv/bw。"""
    weights = (PARAMETERS * weight_bits + 7) // 8
    denominator = 2 * PARAMETERS * BANDWIDTH / PEAK_FLOPS - per_request_bytes
    if denominator <= 0:
        return None
    return max(1, math.ceil(weights / denominator))


def main() -> int:
    os.makedirs(RESULTS, exist_ok=True)
    base = budget('基线：8 bit 权重，batch=1', note='正文 1.3.2 的初算')
    rows = [
        base,
        budget('翻倍算力', compute_multiplier=2.0, note='只缩短已经很小的计算项'),
        budget('翻倍带宽', bandwidth_multiplier=2.0, note='改变当前主导的读取项'),
        budget('位宽 8→4 bit', weight_bits=4, note='权重字节减半；量化质量与反量化开销未计'),
        budget('位宽 8→16 bit', weight_bits=16, note='容量先不成立，无需比较时间'),
        budget('batch=8', batch=8),
        budget('batch=64', batch=64),
        budget('batch=148', batch=148, note='计算与读取的交叉点'),
        budget('batch=256', batch=256),
        budget('batch=64 且每请求 128 MB KV', batch=64, kv_history_bytes=128_000_000,
               kv_append_bytes=0, note='把历史状态计入后容量与流量都改变'),
    ]
    result = dict(
        schema_version=1, experiment='1-3', title='什么改动能缩短生成时间',
        resource_card=dict(device='H100 SXM（标称）', peak_flops=PEAK_FLOPS,
                           peak_basis='BF16 输入／FP32 累加／dense 张量峰值 989.4 TFLOPs/s',
                           bandwidth_bytes_per_second=BANDWIDTH, capacity_bytes=CAPACITY),
        model=dict(parameters=PARAMETERS, matrix_flops_per_token='2×N×batch',
                   weight_read_per_step='整批共享一次'),
        scans=rows,
        crossover_batch_no_kv=crossover_batch(8, 0),
        crossover_batch_with_128mb_kv=crossover_batch(8, 128_000_000),
        uncounted_costs=[
            '历史状态（KV）的读取随 batch 与长度线性增长，基线里被设为 0。',
            '非矩阵操作（归一化、Softmax、激活、RoPE、采样）不在 2N 里。',
            'kernel 启动、调度与主机提交的串行等待没有计入。',
            '低位宽存储需要反量化，可能增加计算和片上缓冲；质量变化必须单独评测。',
            '更大 batch 需要更多工作区与 KV 容量，可能先撞到容量而不是时间。',
            '批内请求要等齐，单请求等待时间会变长，与全机吞吐不是同一件事。',
        ],
        python_version=sys.version,
    )
    with open(os.path.join(RESULTS, 'sensitivity.json'), 'w') as fh:
        json.dump(result, fh, indent=2, ensure_ascii=False)
        fh.write('\n')

    lines = ['# 实验 1-3 结果：改动与生成时间', '',
             '| 改动 | 驻留 | 容量 | 计算下界 | 读取下界 | 资源下界 | 主导 | 吞吐 |',
             '| --- | ---: | :---: | ---: | ---: | ---: | --- | ---: |']
    for row in rows:
        lb = '—' if row['resource_lower_bound_seconds'] is None else '%.3f ms' % (row['resource_lower_bound_seconds'] * 1e3)
        tp = '—' if row['tokens_per_second'] is None else '%.0f tok/s' % row['tokens_per_second']
        lines.append('| {label} | {res:.1f} GB | {fit} | {c:.3f} ms | {m:.3f} ms | {lb} | {dom} | {tp} |'.format(
            label=row['label'], res=row['resident_bytes'] / GB, fit='通过' if row['fits_capacity'] else '不通过',
            c=row['compute_seconds'] * 1e3, m=row['memory_seconds'] * 1e3, lb=lb,
            dom='读取' if row['dominant'] == 'memory' else '计算', tp=tp))
    lines += ['', '计算与读取相等的 batch：无 KV 时 **%d**；每请求 128 MB KV 时 **%s**。' % (
        result['crossover_batch_no_kv'],
        result['crossover_batch_with_128mb_kv'] if result['crossover_batch_with_128mb_kv'] else '不存在（读取永远主导）'), '',
        '## 尚未计入的成本', ''] + ['- ' + item for item in result['uncounted_costs']] + ['']
    with open(os.path.join(RESULTS, 'sensitivity.md'), 'w') as fh:
        fh.write('\n'.join(lines))
    print('\n'.join(lines))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
