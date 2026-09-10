#!/usr/bin/env python3
"""实验 3-1：Prefill 与 Decode 的资源变化。

同一个模型、同样的**总 token 数**，只改变阶段组成：
  时段 A（输入较多）：每请求 prompt 4096 ＋ 输出 128；
  时段 B（生成较多）：每请求 prompt 512  ＋ 输出 3712；
两者每请求总计都是 4224 token。再各扫 batch=1／8／32。

分别汇总：prefill 工作、decode 整段工作、权重读取、历史读取、KV 峰值。

本实验不重算：由 `calculations/calc.py forward|generate` 现场生成
（复用第 2 章已有的长度／batch／前缀命中需求表口径）。只依赖标准库。
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
TFLOP = 10 ** 12

MODEL = 'qwen3-8b'
PERIODS = [('A 输入较多', 4096, 128), ('B 生成较多', 512, 3712)]
BATCHES = [1, 8, 32]
PREFIX_HIT = 3072   # 时段 A 的前缀命中变体


def run(args, out):
    path = os.path.join(RESULTS, out)
    proc = subprocess.run([sys.executable, CALC] + args + ['--format', 'json', '--output', path],
                          capture_output=True, text=True)
    if proc.returncode != 0:
        sys.exit('调用失败：%s\n%s' % (' '.join(args), proc.stderr[-900:]))
    return json.load(open(path))


def period_row(label, prompt, steps, batch, prefix=0):
    tag = '%s-b%d-p%d-g%d-h%d' % (label[0], batch, prompt, steps, prefix)
    pre = run(['forward', '--model', MODEL, '--batch', str(batch),
               '--tokens', str(prompt - prefix), '--history', str(prefix)],
              'prefill-%s.json' % tag)
    gen = run(['generate', '--model', MODEL, '--batch', str(batch),
               '--history', str(prompt), '--steps', str(steps)],
              'decode-%s.json' % tag)
    ps, gs = pre['summary'], gen['summary']
    return dict(period=label, prompt=prompt, prefix_hit=prefix, output=steps, batch=batch,
                total_tokens_per_request=prompt + steps,
                prefill_matrix_flops=ps['matrix_flops'],
                prefill_weight_read_bytes=ps['weight_read_once_per_operator_bytes'],
                prefill_kv_write_bytes=ps['kv_new_write_bytes'],
                decode_matrix_flops=gs['matrix_flops'],
                decode_weight_read_bytes=gs['weight_read_once_per_step_bytes'],
                decode_history_read_bytes=gs['kv_existing_history_read_bytes'],
                decode_kv_write_bytes=gs['kv_new_write_bytes'],
                kv_final_resident_bytes=gs['kv_final_resident_bytes'])


def main() -> int:
    os.makedirs(RESULTS, exist_ok=True)
    rows = []
    for label, prompt, steps in PERIODS:
        for batch in BATCHES:
            rows.append(period_row(label, prompt, steps, batch))
    rows.append(period_row('A 输入较多（命中 3072 前缀）', 4096, 128, 8, PREFIX_HIT))

    result = dict(schema_version=1, experiment='3-1', title='Prefill 与 Decode 的资源变化',
                  model=MODEL, periods=PERIODS, batches=BATCHES,
                  source_note='由 calculations/calc.py forward|generate 现场生成。',
                  rows=rows, python_version=sys.version)
    json.dump(result, open(os.path.join(RESULTS, 'stages.json'), 'w'), indent=2, ensure_ascii=False)

    lines = ['# 实验 3-1 结果：Prefill 与 Decode 的资源变化', '',
             '模型 %s；两个时段每请求总 token 数都是 4,224。' % MODEL, '',
             '| 时段 | batch | prompt | 输出 | prefill TFLOPs | decode TFLOPs | prefill 权重读取 | decode 权重读取 | decode 历史读取 | 结束 KV |',
             '| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |']
    for r in rows:
        lines.append('| %s | %d | %d | %d | %.3f | %.3f | %.2f GiB | %.1f GiB | %.1f GiB | %.3f GiB |' % (
            r['period'], r['batch'], r['prompt'], r['output'],
            r['prefill_matrix_flops'] / TFLOP, r['decode_matrix_flops'] / TFLOP,
            r['prefill_weight_read_bytes'] / GiB, r['decode_weight_read_bytes'] / GiB,
            r['decode_history_read_bytes'] / GiB, r['kv_final_resident_bytes'] / GiB))
    lines.append('')
    open(os.path.join(RESULTS, 'stages.md'), 'w').write('\n'.join(lines))
    print('\n'.join(lines))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
