#!/usr/bin/env python3
"""实验 4-1：注意力计算与单元配比。

两层：
  A. 单 SM 内的资源配比：同一 Qwen3-8B head_dim=128 的注意力 tile，
     分别只提高矩阵能力、只提高指数（向量／特殊函数）能力，看限制资源怎样转移。
  B. 整设备映射：把同一注意力工作放到 NVIDIA、昇腾与 Apple 的官方规格上，
     固定访存条件后算**完成时间**（不是峰值总和），再增大上下文重做。

本实验不重算：由 `calculations/calc.py fa4-resource-balance|forward|roofline` 现场生成。
"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
CALC = os.path.join(ROOT, 'calculations', 'calc.py')
RESULTS = os.path.join(HERE, 'results')
GiB = 2 ** 30

DEVICES = [
    ('a100-80gb-sxm', 'BF16', 'FP32', 'tensor', 'dense'),
    ('h100-sxm', 'BF16', 'FP32', 'tensor', 'dense'),
    ('b200-sxm', 'BF16', 'FP32', 'tensor', 'dense'),
    ('ascend-950pr-max-spec', 'BF16', 'unspecified', 'cube', 'unspecified'),
    ('ascend-950dt-max-spec', 'BF16', 'unspecified', 'cube', 'unspecified'),
    ('m2-max-38gpu-96gb', None, None, None, None),
    ('rtx-pro6000-blackwell-ws', 'BF16', 'FP32', 'tensor', 'dense'),
]

# 官方未公布矩阵峰值的设备，只按已记录的显存带宽给访存下界
BANDWIDTH_ONLY = {
    'm2-max-38gpu-96gb': (400e9, '官方未公布该 SoC 的 GPU 矩阵峰值。'),
    'ascend-950pr-max-spec': (1600e9, '官方 cube 峰值的累加精度为 unspecified，统一计算项目拒绝用于精度特定的 Roofline。'),
    'ascend-950dt-max-spec': (4000e9, '官方 cube 峰值的累加精度为 unspecified，统一计算项目拒绝用于精度特定的 Roofline。'),
}
CONTEXTS = [8192, 32768]


def run(args, out):
    path = os.path.join(RESULTS, out)
    proc = subprocess.run([sys.executable, CALC] + args + ['--format', 'json', '--output', path],
                          capture_output=True, text=True)
    if proc.returncode != 0:
        return None, proc.stderr.strip().splitlines()[-1] if proc.stderr else 'failed'
    return json.load(open(path)), None


def main() -> int:
    os.makedirs(RESULTS, exist_ok=True)
    balance, err = run(['fa4-resource-balance'], 'fa4-balance.json')
    if balance is None:
        sys.exit('fa4-resource-balance 调用失败：' + err)

    work = []
    for tokens in CONTEXTS:
        doc, err = run(['forward', '--model', 'qwen3-8b', '--batch', '1',
                        '--tokens', str(tokens), '--history', '0'],
                       'forward-t%d.json' % tokens)
        if doc is None:
            sys.exit('forward 调用失败：' + err)
        s = doc['summary']
        work.append(dict(tokens=tokens,
                         attention_flops=s['causal_attention_matrix_flops'],
                         kv_write_bytes=s['kv_new_write_bytes'],
                         score_io_bytes=s['materialized_scores_probabilities_io_all_layers_bytes'],
                         exp_ops=s['special_ops'].get('exp', 0)))

    device_rows = []
    for w in work:
        # 固定访存条件：注意力唯一必需载荷＝写入 KV ＋ 读回 KV 一次
        traffic = w['kv_write_bytes'] * 2
        for dev, prec, acc, unit, sparsity in DEVICES:
            if dev in BANDWIDTH_ONLY:
                device_rows.append(dict(
                    tokens=w['tokens'], device=dev, compute_unavailable=True,
                    summary=dict(compute_service_seconds=None,
                                 memory_service_seconds=traffic / BANDWIDTH_ONLY[dev][0],
                                 resource_time_lower_bound_seconds=None),
                    note=BANDWIDTH_ONLY[dev][1] + ' 只给已记录带宽下的访存下界。'))
                continue
            args = ['roofline', '--device', dev, '--flops', str(w['attention_flops']),
                    '--traffic-bytes', str(traffic), '--precision', prec,
                    '--accumulator', acc, '--unit', unit, '--sparsity', sparsity]
            doc, err = run(args, 'roofline-%s-t%d.json' % (dev, w['tokens']))
            if doc is None:
                device_rows.append(dict(tokens=w['tokens'], device=dev, error=err))
                continue
            device_rows.append(dict(tokens=w['tokens'], device=dev,
                                    summary=doc.get('summary'), peak=doc.get('selected_peak')))

    result = dict(schema_version=1, experiment='4-1', title='注意力计算与单元配比',
                  source_note='由 calculations/calc.py 现场生成；不重算公式。',
                  single_sm_balance=balance, attention_work=work, device_rows=device_rows,
                  python_version=sys.version)
    json.dump(result, open(os.path.join(RESULTS, 'attention-units.json'), 'w'),
              indent=2, ensure_ascii=False)

    lines = ['# 实验 4-1 结果：注意力计算与单元配比', '',
             '## A. 单 SM 内的三项资源（Qwen3-8B head_dim=128）', '',
             '| tile | 矩阵周期 | SMEM 周期 | 指数周期 | 下界 | 限制资源 |',
             '| --- | ---: | ---: | ---: | ---: | --- |']
    def frac(f):
        return f['numerator'] / f['denominator']
    for sc in balance['scenarios']:
        c = sc['cycles']
        lines.append('| %s | %.0f | %.0f | %.0f | %.0f | %s |' % (
            sc['id'], frac(c['matrix']), frac(c['smem']), frac(c['exp']),
            frac(sc['accounted_steady_state_bound_cycles']),
            '、'.join(sc['tied_limiting_resources'])))
    lines += ['', '## B. 同一注意力工作在各设备上的完成时间', '',
              '| 上下文 | 设备 | 峰值口径 | 计算下界 | 访存下界 | Roofline 下界 | 主导 |',
              '| ---: | --- | --- | ---: | ---: | ---: | --- |']
    for r in device_rows:
        if 'error' in r:
            lines.append('| %d | %s | 官方峰值未记录 | — | — | — | — |' % (r['tokens'], r['device']))
            continue
        s = r['summary']
        if r.get('compute_unavailable'):
            lines.append('| %d | %s | 见备注 | — | %.3f ms | — | 只能给访存下界 |' % (
                r['tokens'], r['device'], s['memory_service_seconds'] * 1e3))
            continue
        peak = r.get('peak') or {}
        basis = '%s/%s %s %.0f T' % (peak.get('input_precision', '—'),
                                     peak.get('accumulator_precision', '—'),
                                     peak.get('execution_unit', '—'),
                                     peak.get('tera_ops_per_second', 0))
        dom = '计算' if s['compute_service_seconds'] >= s['memory_service_seconds'] else '访存'
        lines.append('| %d | %s | %s | %.3f ms | %.3f ms | %.3f ms | %s |' % (
            r['tokens'], r['device'], basis,
            s['compute_service_seconds'] * 1e3, s['memory_service_seconds'] * 1e3,
            s['resource_time_lower_bound_seconds'] * 1e3, dom))
    lines += ['', '## 注意力工作量本身', '',
              '| 上下文 | 因果注意力 TFLOPs | 新写 KV | 分数张量读写 | exp 次数 |',
              '| ---: | ---: | ---: | ---: | ---: |']
    for w in work:
        lines.append('| %d | %.3f | %.3f GiB | %.1f GiB | %.3g |' % (
            w['tokens'], w['attention_flops'] / 1e12, w['kv_write_bytes'] / GiB,
            w['score_io_bytes'] / GiB, w['exp_ops']))
    lines.append('')
    open(os.path.join(RESULTS, 'attention-units.md'), 'w').write('\n'.join(lines))
    print('\n'.join(lines))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
