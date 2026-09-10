#!/usr/bin/env python3
"""实验 2-9：请求条件下的模型选择（资源侧完整对照）。

固定同一请求输入（命中前缀 6144，新输入 2048，输出 256，batch=1），
完整比较四个模型的 prefill、decode 每步与整段工作、常驻权重／状态、读取与更新：
  Qwen3-8B、DeepSeek-V4-Flash、DeepSeek-V4-Pro、Kimi K3。

质量条件不在资源表里：同消息检索质量记录见 paired-retrieval/，多键变体见 multikey/。
本实验不重算：由 `calculations/calc.py request-model-comparison` 现场生成。
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

REQUEST = dict(prefix_tokens=6144, new_tokens=2048, output_tokens=256, batch=1,
               k3_mla_path='compact', routing='balanced')


def main() -> int:
    os.makedirs(RESULTS, exist_ok=True)
    ipath = os.path.join(RESULTS, 'request.json')
    json.dump(REQUEST, open(ipath, 'w'), indent=1)
    out = os.path.join(RESULTS, 'comparison.json')
    proc = subprocess.run([sys.executable, CALC, 'request-model-comparison',
                           '--inputs', ipath, '--format', 'json', '--output', out],
                          capture_output=True, text=True)
    if proc.returncode != 0:
        sys.exit('调用失败：\n' + proc.stderr[-900:])
    doc = json.load(open(out))

    READ_KEYS = {
        'qwen3-8b': ['kv_existing_history_unique_payload_bytes'],
        'deepseek-v4-flash': ['gathered_kv_bytes', 'index_read_bytes', 'sink_read_bytes'],
        'deepseek-v4-pro': ['gathered_kv_bytes', 'index_read_bytes', 'sink_read_bytes'],
        'kimi-k3': ['mla_old_history_unique_payload_bytes', 'kda_recurrent_read_once_write_once_bytes'],
    }
    WRITE_KEYS = {
        'qwen3-8b': ['kv_new_write_bytes'],
        'deepseek-v4-flash': ['window_slot_write_bytes', 'completed_cache_entry_write_bytes',
                              'compressor_fp32_slot_write_bytes'],
        'deepseek-v4-pro': ['window_slot_write_bytes', 'completed_cache_entry_write_bytes',
                            'compressor_fp32_slot_write_bytes'],
        'kimi-k3': ['mla_append_bytes'],
    }
    WEIGHT_KEYS = {
        'qwen3-8b': ['weight_read_once_per_operator_bytes'],
        'deepseek-v4-flash': ['attention_uniform_bf16_matrix_weight_payload_bytes',
                              'expert_uniform_bf16_matrix_weight_payload_bytes',
                              'vocabulary_head_uniform_bf16_weight_payload_bytes'],
        'deepseek-v4-pro': ['attention_uniform_bf16_matrix_weight_payload_bytes',
                            'expert_uniform_bf16_matrix_weight_payload_bytes',
                            'vocabulary_head_uniform_bf16_weight_payload_bytes'],
        'kimi-k3': ['expert_uniform_matrix_weight_payload_bytes'],
    }

    def pick(interfaces, keys):
        return sum(interfaces.get(k, 0) for k in keys)

    rows = []
    for c in doc['comparisons']:
        model = c['model']
        pre = c['prefill']['totals']
        pk = pre['known_interfaces']
        dec = c['decode']
        dec_rows = dec['rows']
        first = dec_rows[0]
        rows.append(dict(
            model=model,
            prefill_matrix_flops=pre['matrix_flops'],
            prefill_weight_read_bytes=pick(pk, WEIGHT_KEYS[model]),
            prefill_history_read_bytes=pick(pk, READ_KEYS[model]),
            prefill_state_write_bytes=pick(pk, WRITE_KEYS[model]),
            decode_calls=dec['calls'],
            decode_first_step_flops=first['matrix_flops'],
            decode_first_step_history_bytes=pick(first['known_interfaces'], READ_KEYS[model]),
            decode_total_flops=sum(r['matrix_flops'] for r in dec_rows),
            decode_total_history_bytes=sum(pick(r['known_interfaces'], READ_KEYS[model]) for r in dec_rows),
            decode_total_write_bytes=sum(pick(r['known_interfaces'], WRITE_KEYS[model]) for r in dec_rows),
            state_resident_after_bytes=dec_rows[-1].get('state_resident_after_bytes'),
            read_keys=READ_KEYS[model], write_keys=WRITE_KEYS[model], weight_keys=WEIGHT_KEYS[model],
            prefill_interface_items=pk,
            last_decode_interface_items=dec_rows[-1]['known_interfaces'],
            coverage=c.get('source_coverage')))

    result = dict(schema_version=1, experiment='2-9', title='请求条件下的模型选择',
                  request=REQUEST, contract=doc['contract'],
                  source_note='由 calculations/calc.py request-model-comparison 现场生成。',
                  rows=rows,
                  quality_conditions=[
                      '同一批消息上的检索是否都答对（paired-retrieval：8/8 对 8/8，不能据此排序）。',
                      '长距离多键检索是否保持（multikey 题目已固定，需要更大上下文）。',
                      '压缩／稀疏路径在目标任务分布上的质量损失是否可接受。',
                      '输出长度与推理预算是否相同——不同 reasoning 长度会改变整段成本。',
                  ],
                  python_version=sys.version)
    json.dump(result, open(os.path.join(RESULTS, 'model-choice.json'), 'w'), indent=2, ensure_ascii=False)

    lines = ['# 实验 2-9 结果：请求条件下的模型选择（资源侧）', '',
             '同一请求：命中前缀 %d、新输入 %d、输出 %d、batch=%d。' % (
                 REQUEST['prefix_tokens'], REQUEST['new_tokens'],
                 REQUEST['output_tokens'], REQUEST['batch']), '',
             '| 模型 | prefill TFLOPs | prefill 权重载荷* | 首步 decode TFLOPs | 首步历史读取 | 整段 decode TFLOPs | 整段历史读取 | 结束时状态 |',
             '| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |']
    for r in rows:
        lines.append('| %s | %.3f | %.2f GiB | %.5f | %.3f GiB | %.4f | %.1f GiB | %.3f GiB |' % (
            r['model'], r['prefill_matrix_flops'] / TFLOP,
            r['prefill_weight_read_bytes'] / GiB,
            r['decode_first_step_flops'] / TFLOP,
            r['decode_first_step_history_bytes'] / GiB,
            r['decode_total_flops'] / TFLOP,
            r['decode_total_history_bytes'] / GiB,
            (r['state_resident_after_bytes'] or 0) / GiB))
    lines += ['', '\\* 权重载荷按各模型自己的口径累计：Dense 模型是“每算子读一次”，MoE 模型是“逐层批内专家并集”，'
              '因此 MoE 的 prefill 载荷远大于其驻留权重，两者不可直接比较。逐项名称见 JSON 的 `weight_keys`。', '',
              '## 使模型选择成立的质量条件', ''] + ['- ' + q for q in result['quality_conditions']] + ['']
    open(os.path.join(RESULTS, 'model-choice.md'), 'w').write('\n'.join(lines))
    print('\n'.join(lines))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
