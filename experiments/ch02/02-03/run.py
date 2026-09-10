#!/usr/bin/env python3
"""实验 2-3：GQA 与 K3 MLA 的容量和访问。

用 Qwen3-8B（GQA）与 Kimi K3（MLA）的实际配置，分别给出：
  1. 常驻历史、一个 decode 步的历史读取与新增写入；
  2. 一段完整生成（8192 prompt + 1024 步）累加后的读取、写入与最终容量；
  3. MHA／GQA／MQA 的同序列对照，以及 K3 两种 MLA 执行路径的矩阵尺寸与额外中间量。

每头／每层对照与整模型对照分开列。数值取自本书统一计算项目已复算的结果，
本实验不重算。只依赖 Python 3 标准库。
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
CALC = os.path.join(ROOT, 'calculations', 'results')
RESULTS = os.path.join(HERE, 'results')

GiB = 2 ** 30
MiB = 2 ** 20
TFLOP = 10 ** 12


def load(name):
    path = os.path.join(CALC, name + '.json')
    if not os.path.exists(path):
        sys.exit('缺少输入：%s\n请先在仓库根目录运行 python3 calculations/calc.py reproduce' % path)
    return json.load(open(path))


def main() -> int:
    os.makedirs(RESULTS, exist_ok=True)
    qwen_seq = load('cache-sequence-qwen3-8b-b1')
    qwen_seq64 = load('cache-sequence-qwen3-8b-b64')
    k3_seq = load('cache-sequence-kimi-k3-b1')
    q_state = load('state-qwen3-8b-n8192-b1-native')
    k3_compact = load('state-kimi-k3-n8192-b1-compact')
    k3_expanded = load('state-kimi-k3-n8192-b1-expanded')
    mla_compact = load('k3-mla-compact-b64-t1-s8192')
    mla_expanded = load('k3-mla-expanded-b64-t1-s8192')

    # 单步：常驻、历史读取、新增写入
    step = [
        dict(model='Qwen3-8B（GQA，8 KV 头）',
             resident_bytes=q_state['summary']['resident_bytes'],
             history_read_bytes=q_state['summary']['selected_history_payload_bytes'],
             append_bytes=q_state['summary']['next_token_append_bytes'],
             bytes_per_token=q_state['summary']['kv_bytes_per_token_per_request']),
        dict(model='Kimi K3（MLA compact 路径）',
             resident_bytes=k3_compact['summary']['resident_bytes'],
             history_read_bytes=k3_compact['summary']['selected_history_payload_bytes'],
             append_bytes=k3_compact['summary'].get('next_token_append_bytes'),
             bytes_per_token=k3_compact['summary'].get('kv_bytes_per_token_per_request')),
        dict(model='Kimi K3（MLA expanded 路径，HF 实际保存）',
             resident_bytes=k3_expanded['summary']['resident_bytes'],
             history_read_bytes=k3_expanded['summary']['selected_history_payload_bytes'],
             append_bytes=k3_expanded['summary'].get('next_token_append_bytes'),
             bytes_per_token=k3_expanded['summary'].get('kv_bytes_per_token_per_request')),
    ]

    # 整段生成累加（8192 prompt + 1024 步）
    def seq_rows(src, label):
        rows = []
        for v in src['cache_variants']:
            rows.append(dict(
                group=label, variant=v['name'], reference=v['reference'],
                kv_heads=v.get('kv_heads'),
                history_bytes_per_token=v['history_bytes_per_token'],
                final_persistent_state_bytes=v['final_persistent_state_bytes'],
                decode_history_read_bytes=v['decode_prior_history_read_payload_bytes'],
                decode_append_write_bytes=v['decode_append_write_bytes'],
                decode_attention_flops=v['decode_attention_matrix_flops'],
                uncached_recompute_attention_flops=v['uncached_recompute_attention_matrix_flops'],
                prefix_checkpoint_payload_bytes=v['prefix_checkpoint_payload_bytes']))
        return rows

    sequence = (seq_rows(qwen_seq, 'Qwen3-8B batch=1') +
                seq_rows(qwen_seq64, 'Qwen3-8B batch=64') +
                seq_rows(k3_seq, 'Kimi K3 batch=1'))

    # MLA 两条执行路径的矩阵与中间量
    def mla_row(src, label):
        s = src['summary']
        return dict(path=label,
                    matrix_parameters=s['matrix_parameters'],
                    projection_matrix_flops=s['projection_matrix_flops'],
                    attention_matrix_flops=s['valid_attention_matrix_flops'],
                    matrix_flops=s['matrix_flops'],
                    kv_resident_after_bytes=s['kv_resident_after_bytes'],
                    kv_new_write_bytes=s['kv_new_write_bytes'],
                    history_unique_payload_bytes=s['history_unique_payload_bytes'],
                    score_fp32_per_layer_bytes=s['rectangular_score_fp32_tensor_per_layer_bytes'])

    mla = [mla_row(mla_compact, 'compact（权重吸收，教学执行路径）'),
           mla_row(mla_expanded, 'expanded（显式展开，HF 代码实际保存）')]

    result = dict(schema_version=1, experiment='2-3', title='GQA 与 K3 MLA 的容量和访问',
                  source_note='数值取自 calculations/results/ 的已复算结果；本实验不重算。',
                  step_scenario=dict(history_tokens=8192, batch=1),
                  step=step,
                  generation_scenario=qwen_seq['scenario'],
                  sequence=sequence,
                  mla_paths=mla,
                  python_version=sys.version)
    json.dump(result, open(os.path.join(RESULTS, 'gqa-mla.json'), 'w'), indent=2, ensure_ascii=False)

    lines = ['# 实验 2-3 结果：GQA 与 K3 MLA 的容量和访问', '',
             '## 一个 decode 步（历史 8192、batch=1）', '',
             '| 模型／路径 | 每 token 状态 | 常驻历史 | 历史读取 | 新增写入 |',
             '| --- | ---: | ---: | ---: | ---: |']
    for r in step:
        bpt = '%d B' % r['bytes_per_token'] if r['bytes_per_token'] else '—'
        ap = '%d B' % r['append_bytes'] if r['append_bytes'] else '—'
        lines.append('| %s | %s | %.3f MiB | %.3f MiB | %s |' % (
            r['model'], bpt, r['resident_bytes'] / MiB, r['history_read_bytes'] / MiB, ap))
    lines += ['', '## 一段完整生成（prompt %d、%d 步、命中前缀 %d）' % (
        qwen_seq['scenario']['prompt'], qwen_seq['scenario']['steps'], qwen_seq['scenario']['prefix_hit']), '',
        '| 组 | 变体 | KV 头 | 每 token | 最终常驻 | 整段历史读取 | 整段写入 |',
        '| --- | --- | ---: | ---: | ---: | ---: | ---: |']
    for r in sequence:
        lines.append('| %s | %s%s | %s | %s | %.3f GiB | %.1f GiB | %.3f GiB |' % (
            r['group'], r['variant'], '（基准）' if r['reference'] else '',
            r['kv_heads'] if r['kv_heads'] else '—',
            '%d B' % r['history_bytes_per_token'],
            r['final_persistent_state_bytes'] / GiB,
            r['decode_history_read_bytes'] / GiB,
            r['decode_append_write_bytes'] / GiB))
    lines += ['', '## K3 两条 MLA 执行路径（batch=64、历史 8192、单步）', '',
              '| 路径 | 矩阵参数 | 投影 TFLOPs | 注意力 TFLOPs | 历史载荷 | 新增写入 | 每层 FP32 分数张量 |',
              '| --- | ---: | ---: | ---: | ---: | ---: | ---: |']
    for r in mla:
        lines.append('| %s | %.3f B | %.4f | %.4f | %.2f GiB | %.2f MiB | %.1f MiB |' % (
            r['path'], r['matrix_parameters'] / 1e9,
            r['projection_matrix_flops'] / TFLOP, r['attention_matrix_flops'] / TFLOP,
            r['history_unique_payload_bytes'] / GiB, r['kv_new_write_bytes'] / MiB,
            r['score_fp32_per_layer_bytes'] / MiB))
    lines.append('')
    open(os.path.join(RESULTS, 'gqa-mla.md'), 'w').write('\n'.join(lines))
    print('\n'.join(lines))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
