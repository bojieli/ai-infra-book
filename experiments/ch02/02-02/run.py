#!/usr/bin/env python3
"""实验 2-2：Qwen3-8B 的逐层计算。

四个场景各自复算：8192-token prefill、已有 8192 历史的 batch=1／64 decode、
命中 6144-token 前缀后补 2048 token。每个场景分别给出：
  - 逐算子的尺寸、矩阵 FLOPs、权重读取与激活读写；
  - 容量（常驻权重＋KV）、读取（权重＋历史）与新增写入三项各自的合计。

数值取自本书统一计算项目已复算的结果（官方 Qwen3-8B config、固定 revision、
逐算子逻辑账，并已通过其官方权重索引与守恒检查），本实验不重算。

只依赖 Python 3 标准库。
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
CALC = os.path.join(ROOT, 'calculations', 'results')
RESULTS = os.path.join(HERE, 'results')

SCENARIOS = [
    ('8192-token prefill', 'qwen3-8b-prefill-8192.json'),
    ('decode batch=1，历史 8192', 'qwen3-8b-decode-b1-s8192.json'),
    ('decode batch=64，历史 8192', 'qwen3-8b-decode-b64-s8192.json'),
    ('命中 6144 前缀，补 2048 token', 'qwen3-8b-prefix-6144-plus-2048.json'),
]

GROUP = {
    'embedding': '嵌入', 'rope_table': 'RoPE 表',
    'input_layernorm': '归一化', 'post_attention_layernorm': '归一化', 'final_norm': '归一化',
    'q_proj': 'QKV 投影', 'k_proj': 'QKV 投影', 'v_proj': 'QKV 投影',
    'q_norm': 'QK Norm', 'k_norm': 'QK Norm',
    'apply_rope': 'RoPE 应用', 'kv_append': 'KV 写入',
    'qk': '注意力', 'score_scale_mask_softmax': '注意力', 'pv': '注意力',
    'o_proj': '输出投影',
    'attention_residual': '残差', 'ffn_residual': '残差',
    'gate_proj': 'SwiGLU', 'up_proj': 'SwiGLU', 'silu_mul': 'SwiGLU', 'down_proj': 'SwiGLU',
    'lm_head': '输出头',
}

GiB = 2 ** 30
TFLOP = 10 ** 12


def load(name):
    path = os.path.join(CALC, name)
    if not os.path.exists(path):
        sys.exit('缺少输入：%s\n请先在仓库根目录运行 python3 calculations/calc.py reproduce' % path)
    return json.load(open(path))


def group_rows(ops):
    """把 23 个算子按功能归组，每组给出总 FLOPs 与总访问字节（已乘层数）。"""
    acc = {}
    for op in ops:
        key = GROUP.get(op['name'], op['name'])
        row = acc.setdefault(key, dict(group=key, operators=[], matrix_flops=0,
                                       weight_read_bytes=0, activation_read_bytes=0,
                                       activation_write_bytes=0))
        r = op['repeats']
        row['operators'].append('%s×%d' % (op['name'], r))
        row['matrix_flops'] += op['matrix_flops'] * r
        row['weight_read_bytes'] += op['weight_read_bytes'] * r
        row['activation_read_bytes'] += op['activation_read_bytes'] * r
        row['activation_write_bytes'] += op['activation_write_bytes'] * r
    return sorted(acc.values(), key=lambda r: -r['matrix_flops'])


def main() -> int:
    os.makedirs(RESULTS, exist_ok=True)
    scenarios = []
    dims = None
    for label, name in SCENARIOS:
        src = load(name)
        dims = dims or src['dimensions']
        s = src['summary']
        scenarios.append(dict(
            label=label, source=name, scenario=src['scenario'],
            groups=group_rows(src['operators']),
            capacity=dict(
                weight_resident_bytes=s['weight_resident_bytes'],
                kv_resident_after_bytes=s['kv_resident_after_bytes'],
                minimum_required_weight_and_kv_bytes=s['minimum_required_weight_and_kv_bytes']),
            reading=dict(
                weight_read_once_per_operator_bytes=s['weight_read_once_per_operator_bytes'],
                kv_existing_history_unique_payload_bytes=s['kv_existing_history_unique_payload_bytes'],
                kv_attention_unique_payload_bytes=s['kv_attention_unique_payload_bytes'],
                activation_operand_read_bytes=s['activation_operand_read_bytes']),
            writing=dict(
                kv_new_write_bytes=s['kv_new_write_bytes'],
                activation_operand_write_bytes=s['activation_operand_write_bytes']),
            work=dict(matrix_flops=s['matrix_flops'],
                      backbone_projection_ffn_flops=s['backbone_projection_ffn_flops'],
                      causal_attention_matrix_flops=s['causal_attention_matrix_flops'],
                      scalar_flops=s['scalar_flops']),
            parameters=s['parameters'],
        ))

    result = dict(schema_version=1, experiment='2-2', title='Qwen3-8B 的逐层计算',
                  dimensions=dims,
                  source_note='数值取自 calculations/results/ 的已复算逐算子账（官方 config、固定 revision）；本实验不重算。',
                  scenarios=scenarios,
                  reading_rule='容量、读取与新增写入必须各自复算，不能合成一项“显存需求”。',
                  python_version=sys.version)
    json.dump(result, open(os.path.join(RESULTS, 'qwen3-8b.json'), 'w'), indent=2, ensure_ascii=False)

    lines = ['# 实验 2-2 结果：Qwen3-8B 的逐层计算', '',
             'Qwen3-8B 官方配置：%d 层、hidden %d、intermediate %d、%d 个 Q 头／%d 个 KV 头、head_dim %d、词表 %d。' % (
                 dims['num_hidden_layers'], dims['hidden_size'], dims['intermediate_size'],
                 dims['num_attention_heads'], dims['num_key_value_heads'], dims['head_dim'],
                 dims['vocab_size']), '',
             '## 四个场景的三项账', '',
             '| 场景 | 矩阵 TFLOPs | 常驻权重 | 结束时 KV | 权重读取 | 历史读取 | 新写 KV |',
             '| --- | ---: | ---: | ---: | ---: | ---: | ---: |']
    for s in scenarios:
        lines.append('| %s | %.4f | %.3f GiB | %.4f GiB | %.3f GiB | %.4f GiB | %.5f GiB |' % (
            s['label'], s['work']['matrix_flops'] / TFLOP,
            s['capacity']['weight_resident_bytes'] / GiB,
            s['capacity']['kv_resident_after_bytes'] / GiB,
            s['reading']['weight_read_once_per_operator_bytes'] / GiB,
            s['reading']['kv_attention_unique_payload_bytes'] / GiB,
            s['writing']['kv_new_write_bytes'] / GiB))
    for s in scenarios:
        lines += ['', '## %s：按功能分组' % s['label'], '',
                  '| 功能组 | 矩阵 TFLOPs | 权重读取 | 激活读 | 激活写 |',
                  '| --- | ---: | ---: | ---: | ---: |']
        for g in s['groups']:
            lines.append('| %s | %.5f | %.3f GiB | %.3f GiB | %.3f GiB |' % (
                g['group'], g['matrix_flops'] / TFLOP, g['weight_read_bytes'] / GiB,
                g['activation_read_bytes'] / GiB, g['activation_write_bytes'] / GiB))
    lines.append('')
    open(os.path.join(RESULTS, 'qwen3-8b.md'), 'w').write('\n'.join(lines))
    print('\n'.join(lines[:22]))
    print('...\n完整逐组表写入 results/qwen3-8b.md')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
