#!/usr/bin/env python3
"""实验 2-4：V4-Flash 的压缩历史与稀疏访问。

按 43 层配置（2 window + 21 CSA + 20 HCA）分别给出：
  - 完整 prefill 与命中前缀后续算的 FLOPs、权重读取；
  - 每步 decode 的窗口／压缩历史读取、索引扫描与状态写入；
  - 8K／128K／1M 历史 × batch=1／64 的状态扫描；
  - 压缩块完成时的更新峰值单列。

本实验不重算：所有数字由本书统一计算项目的 CLI 现场生成
（`calculations/calc.py state|v4-forward|v4-prefix-continuation`），
产物写入本目录 results/。只依赖 Python 3 标准库。
"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
CALC = os.path.join(ROOT, 'calculations', 'calc.py')
RESULTS = os.path.join(HERE, 'results')

MiB = 2 ** 20
GiB = 2 ** 30
TFLOP = 10 ** 12

STATE_CASES = [(8192, 1), (131072, 1), (1048576, 1), (8192, 64), (131072, 64), (1048576, 64)]
FORWARD_CASES = [
    ('完整 prefill 8192', ['--batch', '1', '--tokens', '8192', '--history', '0']),
    ('decode batch=1，历史 8192', ['--batch', '1', '--tokens', '1', '--history', '8192']),
    ('decode batch=64，历史 8192', ['--batch', '64', '--tokens', '1', '--history', '8192']),
    ('decode batch=1，历史 131072', ['--batch', '1', '--tokens', '1', '--history', '131072']),
]


def run(args, out):
    path = os.path.join(RESULTS, out)
    cmd = [sys.executable, CALC] + args + ['--format', 'json', '--output', path]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        sys.exit('调用失败：%s\n%s' % (' '.join(cmd), proc.stderr[-800:]))
    return json.load(open(path))


def main() -> int:
    os.makedirs(RESULTS, exist_ok=True)
    if not os.path.exists(CALC):
        sys.exit('缺少 %s：本实验复用本书统一计算项目的 CLI。' % CALC)

    states = []
    for length, batch in STATE_CASES:
        name = 'state-n%d-b%d.json' % (length, batch)
        d = run(['state', '--model', 'deepseek-v4-flash', '--length', str(length),
                 '--batch', str(batch)], name)
        c = d['components']
        states.append(dict(length=length, batch=batch, file=name,
                           layer_counts=d.get('layer_counts'),
                           window_history_bytes=c['window_history_bytes'],
                           compressed_history_bytes=c['compressed_history_bytes'],
                           index_history_bytes=c['index_history_bytes'],
                           main_compressor_buffer_bytes=c['main_compressor_buffer_bytes'],
                           index_compressor_buffer_bytes=c['index_compressor_buffer_bytes'],
                           selected_payload_bytes=c['main_selected_payload_bytes'],
                           index_scan_payload_bytes=c['index_scan_payload_bytes'],
                           next_token_window_write_bytes=c['next_token_window_write_bytes'],
                           next_token_completed_entry_write_bytes=c['next_token_completed_entry_write_bytes'],
                           resident_bytes=d['summary']['resident_bytes']))

    forwards = []
    for label, args in FORWARD_CASES:
        name = 'forward-%s.json' % label.replace(' ', '').replace('，', '-').replace('=', '')
        d = run(['v4-forward', '--model', 'deepseek-v4-flash'] + args, name)
        s = d['summary']
        forwards.append(dict(label=label, file=name, scenario=d['scenario'],
                             matrix_flops_effective=s['matrix_flops_effective_attention'],
                             matrix_flops_with_tiles=s['matrix_flops_with_reference_sparse_and_expert_tiles'],
                             scalar_flops=s['accounted_scalar_flops'],
                             uniform_bf16_parameter_bytes=s['uniform_bf16_parameter_bytes'],
                             hash_routing_table_int32_bytes=s['hash_routing_table_int32_bytes'],
                             state_resident_after_bytes=s['state_resident_after_bytes'],
                             base_checkpoint_payload_bytes=s['base_checkpoint_payload_bytes'],
                             coverage=d.get('coverage')))

    prefix = run(['v4-prefix-continuation'], 'prefix-continuation.json')

    result = dict(schema_version=1, experiment='2-4', title='V4-Flash 的压缩历史与稀疏访问',
                  source_note='由 calculations/calc.py 现场生成，本实验不另行实现公式。',
                  layer_counts=states[0]['layer_counts'],
                  states=states, forwards=forwards,
                  prefix_continuation_summary=prefix.get('summary'),
                  python_version=sys.version)
    json.dump(result, open(os.path.join(RESULTS, 'v4-flash.json'), 'w'), indent=2, ensure_ascii=False)

    lc = states[0]['layer_counts']
    lines = ['# 实验 2-4 结果：V4-Flash 的压缩历史与稀疏访问', '',
             '层构成：window %d + CSA %d + HCA %d = %d 层。' % (
                 lc['window'], lc['CSA'], lc['HCA'], sum(lc.values())), '',
             '## 状态扫描（历史长度 × batch）', '',
             '| 历史 | batch | 窗口 | 压缩历史 | 索引历史 | 压缩缓冲 | 常驻合计 | 每步选中载荷 | 索引扫描 |',
             '| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |']
    for r in states:
        lines.append('| %d | %d | %.2f MiB | %.2f MiB | %.2f MiB | %.2f MiB | %.3f GiB | %.2f MiB | %.2f MiB |' % (
            r['length'], r['batch'], r['window_history_bytes'] / MiB,
            r['compressed_history_bytes'] / MiB, r['index_history_bytes'] / MiB,
            (r['main_compressor_buffer_bytes'] + r['index_compressor_buffer_bytes']) / MiB,
            r['resident_bytes'] / GiB, r['selected_payload_bytes'] / MiB,
            r['index_scan_payload_bytes'] / MiB))
    lines += ['', '## 每步写入与压缩块完成时的更新', '',
              '| 历史 | batch | 窗口写入 | 压缩块完成时写入 |', '| ---: | ---: | ---: | ---: |']
    for r in states:
        lines.append('| %d | %d | %d B | %d B |' % (
            r['length'], r['batch'], r['next_token_window_write_bytes'],
            r['next_token_completed_entry_write_bytes']))
    lines += ['', '## 前向工作与权重', '',
              '| 场景 | 有效注意力 TFLOPs | 含参考稀疏/专家 tile | 标量 GFLOPs | 统一 BF16 权重 | 哈希表 int32 |',
              '| --- | ---: | ---: | ---: | ---: | ---: |']
    for r in forwards:
        lines.append('| %s | %.3f | %.3f | %.1f | %.1f GiB | %.2f MiB |' % (
            r['label'], r['matrix_flops_effective'] / TFLOP,
            r['matrix_flops_with_tiles'] / TFLOP, r['scalar_flops'] / 1e9,
            r['uniform_bf16_parameter_bytes'] / GiB,
            r['hash_routing_table_int32_bytes'] / MiB))
    lines.append('')
    open(os.path.join(RESULTS, 'v4-flash.md'), 'w').write('\n'.join(lines))
    print('\n'.join(lines))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
