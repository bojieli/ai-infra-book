#!/usr/bin/env python3
"""实验 7-10：网络优化的模型级收益。

通信快了，训练或推理到底快多少？把**公开集合通信曲线**（实验 7-3 已解析的
16／32 rank AllReduce 记录）代入本章的训练与跨服务器推理候选，比较：
  分层通信、重叠、慢链路与故障退化四种条件下的训练步时与推理延迟。

集合通信曲线来自 ../07-03/rows.csv（公开记录的实测点，已通过 294 项校验）；
模型工作量由 calculations/calc.py forward 现场生成。本实验不重算这两者。
"""
import csv
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
CALC = os.path.join(ROOT, 'calculations', 'calc.py')
CURVE = os.path.join(HERE, '..', '07-03', 'rows.csv')
RESULTS = os.path.join(HERE, 'results')
MiB = 2 ** 20
PEAK = 989.4e12
BANDWIDTH = 3.35e12
LAYERS = 36
HIDDEN = 4096


def load_curve():
    if not os.path.exists(CURVE):
        sys.exit('缺少公开集合通信记录：%s（见实验 7-3）' % CURVE)
    rows = []
    for r in csv.DictReader(open(CURVE)):
        if r['row_correct'] != 'True' or r['mode'] != 'in_place':
            continue
        rows.append(dict(run=r['run'], nranks=int(r['nranks']),
                         size_bytes=int(r['size_bytes']),
                         time_us=float(r['time_us']),
                         busbw=float(r['busbw_GB_s'])))
    return rows


def lookup(curve, run, size_bytes):
    """在公开曲线上取最接近（不小于）该消息大小的实测点；越界时按最大点的带宽外推并标注。"""
    pts = sorted([r for r in curve if r['run'] == run], key=lambda r: r['size_bytes'])
    if not pts:
        return None, 'no_points'
    for p in pts:
        if p['size_bytes'] >= size_bytes:
            return p, 'measured_point'
    biggest = pts[-1]
    if biggest['busbw'] <= 0:
        return biggest, 'extrapolated_no_bandwidth'
    scaled = dict(biggest)
    scaled['time_us'] = biggest['time_us'] * size_bytes / biggest['size_bytes']
    scaled['size_bytes'] = size_bytes
    return scaled, 'extrapolated_from_largest'


def work(tokens, batch, history):
    path = os.path.join(RESULTS, 'work-t%d-b%d-h%d.json' % (tokens, batch, history))
    proc = subprocess.run([sys.executable, CALC, 'forward', '--model', 'qwen3-8b',
                           '--batch', str(batch), '--tokens', str(tokens),
                           '--history', str(history),
                           '--format', 'json', '--output', path],
                          capture_output=True, text=True)
    if proc.returncode != 0:
        sys.exit('调用失败：\n' + proc.stderr[-600:])
    s = json.load(open(path))['summary']
    return s['matrix_flops'], (s['weight_read_once_per_operator_bytes'] +
                               s['kv_attention_unique_payload_bytes'] + s['kv_new_write_bytes'])


def main() -> int:
    os.makedirs(RESULTS, exist_ok=True)
    curve = load_curve()

    scenarios = [
        ('训练步（8192-token 前反向，梯度 all-reduce 一次）', 'train', 8192, 1, 0),
        ('跨服务器推理 prefill 8192（每层 all-reduce）', 'prefill', 8192, 1, 0),
        ('跨服务器推理 decode b64 h8192（每层 all-reduce）', 'decode', 1, 64, 8192),
    ]
    conditions = [
        ('基线（直接用公开曲线）', 1.0, False, 1.0),
        ('分层通信（跨机消息减半）', 0.5, False, 1.0),
        ('与计算重叠（80% 可重叠）', 1.0, True, 1.0),
        ('慢链路（通信时间 ×3）', 1.0, False, 3.0),
        ('故障退化（一条链路失效，通信 ×2）', 1.0, False, 2.0),
    ]

    rows = []
    for label, kind, tokens, batch, history in scenarios:
        flops, traffic = work(tokens, batch, history)
        if kind == 'train':
            flops *= 3          # 前向＋反向按 1:2 计
            message = 8_190_735_360 * 2      # 梯度 all-reduce 载荷（BF16 参数量）
            calls = 1
        else:
            message = batch * tokens * HIDDEN * 2
            calls = LAYERS
        compute = flops / PEAK
        memory = traffic / BANDWIDTH
        for run in ('hgx2', 'hgx4'):
            point, basis = lookup(curve, run, message)
            for cond, msg_scale, overlap, slow in conditions:
                p2, b2 = lookup(curve, run, int(message * msg_scale))
                comm = calls * (p2['time_us'] / 1e6) * slow
                if overlap:
                    exposed = comm * 0.2
                    total = max(compute, memory) + exposed
                else:
                    exposed = comm
                    total = max(compute, memory) + comm
                rows.append(dict(scenario=label, run=run, ranks=point['nranks'],
                                 condition=cond, message_bytes=int(message * msg_scale),
                                 curve_basis=b2, calls=calls,
                                 communication_seconds=comm, exposed_seconds=exposed,
                                 compute_seconds=compute, memory_seconds=memory,
                                 total_seconds=total))

    result = dict(schema_version=1, experiment='7-10', title='网络优化的模型级收益',
                  curve_source='experiments/ch07/07-03/rows.csv（公开 NCCL AllReduce 记录）',
                  curve_points=len(curve), scenarios=[s[0] for s in scenarios],
                  conditions=[c[0] for c in conditions], rows=rows,
                  source_note='集合通信时间取自公开记录的实测点；模型工作量由 calc.py 现场生成。',
                  python_version=sys.version)
    json.dump(result, open(os.path.join(RESULTS, 'model-level.json'), 'w'),
              indent=2, ensure_ascii=False)

    lines = ['# 实验 7-10 结果：网络优化的模型级收益', '',
             '集合通信时间取自实验 7-3 已解析的公开 NCCL AllReduce 记录（%d 个可用实测点）。' % len(curve), '',
             '| 场景 | 记录 | rank | 条件 | 曲线依据 | 通信 | 暴露通信 | 计算/访存 | 合计 |',
             '| --- | --- | ---: | --- | --- | ---: | ---: | ---: | ---: |']
    for r in rows:
        lines.append('| %s | %s | %d | %s | %s | %.2f ms | %.2f ms | %.2f ms | **%.2f ms** |' % (
            r['scenario'], r['run'], r['ranks'], r['condition'], r['curve_basis'],
            r['communication_seconds'] * 1e3, r['exposed_seconds'] * 1e3,
            max(r['compute_seconds'], r['memory_seconds']) * 1e3,
            r['total_seconds'] * 1e3))
    lines.append('')
    open(os.path.join(RESULTS, 'model-level.md'), 'w').write('\n'.join(lines))
    print('\n'.join(lines[:24]))
    print('...\n完整表见 results/model-level.md')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
