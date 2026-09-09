"""One S/P/G/B logical request contract for the four chapter-2 model branches."""
from collections import Counter

from infra_calc.models import qwen3
from infra_calc.schema import Scenario
from infra_calc.sources import model_config
from infra_calc.units import positive_int
from infra_calc.topics import k3_forward, state, v4_forward, v4_prefix_continuation

MODELS = ('qwen3-8b', 'deepseek-v4-flash', 'deepseek-v4-pro', 'kimi-k3')


def base_row(result):
    """Normalize totals only; retain the complete source ledger alongside them."""
    s = result['summary']
    return dict(matrix_flops=s.get('matrix_flops', s.get('matrix_flops_effective_attention')),
                accounted_scalar_flops=s.get('scalar_flops', s.get('accounted_scalar_flops')),
                special_ops=s.get('special_ops', s.get('accounted_special_ops', {})))


def add_rows(rows):
    total = Counter()
    special = Counter()
    interfaces = Counter()
    for row in rows:
        total.update(matrix_flops=row['matrix_flops'], accounted_scalar_flops=row['accounted_scalar_flops'])
        special.update(row['special_ops'])
        interfaces.update(row.get('known_interfaces', {}))
    return dict(total, special_ops=dict(special), known_interfaces=dict(interfaces))


def qwen_interfaces(result):
    s = result['summary']
    return {k: s[k] for k in ('weight_read_once_per_operator_bytes', 'activation_operand_read_bytes',
                             'activation_operand_write_bytes', 'kv_existing_history_unique_payload_bytes',
                             'kv_new_write_bytes')}


def k3_interfaces(result):
    a = result['components']['mla']['summary']
    e = result['components']['experts']['summary']
    return dict(mla_old_history_unique_payload_bytes=a['history_unique_payload_bytes'],
                mla_append_bytes=a['kv_new_write_bytes'],
                expert_uniform_matrix_weight_payload_bytes=e['uniform_matrix_weight_payload_bytes'],
                embedding_lookup_payload_bytes=result['summary']['embedding_lookup_payload_bytes'])


def linear_decode(model, batch, history, steps, mla_path, routing):
    """Affine full-history decode work; checkpoint-heavy K3 ledger runs once."""
    if model == 'qwen3-8b':
        config = model_config(model)
        first = qwen3.calculate(model, Scenario(batch=batch, tokens=1, history=history))
        last = qwen3.calculate(model, Scenario(batch=batch, tokens=1, history=history - 1))
        start = base_row(first)
        end = base_row(last)
        matrix_slope = start['matrix_flops'] - end['matrix_flops']
        scalar_slope = start['accounted_scalar_flops'] - end['accounted_scalar_flops']
        special_slope = {k: start['special_ops'].get(k, 0) - end['special_ops'].get(k, 0)
                         for k in set(start['special_ops']) | set(end['special_ops'])}
        io_first, io_last = qwen_interfaces(first), qwen_interfaces(last)
        io_slope = {k: io_first[k] - io_last[k] for k in io_first}
        state_first = first['summary']['kv_resident_after_bytes']
        state_slope = batch * first['summary']['kv_bytes_per_token_per_request']
    else:
        config = model_config(model)['text_config']
        first = k3_forward.calculate(batch=batch, tokens=1, history=history, mla_path=mla_path, routing=routing)
        start = base_row(first)
        shapes = first['components']['mla']['attention_shapes']
        layers = len(config['linear_attn_config']['full_attn_layers'])
        cells_slope = batch * layers * config['num_attention_heads']
        matrix_slope = 2 * cells_slope * (shapes['query'][-1] + shapes['value_logical'][-1])
        scalar_slope = 4 * cells_slope
        special_slope = dict(exp=cells_slope, compare_max=cells_slope)
        io_first = k3_interfaces(first)
        state_slope = first['components']['mla']['summary']['kv_new_write_bytes']
        io_slope = {k: state_slope if k == 'mla_old_history_unique_payload_bytes' else 0 for k in io_first}
        recurrent = first['components']['state']['summary']['recurrent_read_once_write_once_bytes']
        io_first['kda_recurrent_read_once_write_once_bytes'] = recurrent
        io_slope['kda_recurrent_read_once_write_once_bytes'] = 0
        state_first = first['summary']['state_resident_after_bytes']
    rows = []
    for step in range(steps):
        special = {k: start['special_ops'].get(k, 0) + step * special_slope.get(k, 0)
                   for k in set(start['special_ops']) | set(special_slope)}
        rows.append(dict(step=step, input_position=history + step,
                         matrix_flops=start['matrix_flops'] + step * matrix_slope,
                         accounted_scalar_flops=start['accounted_scalar_flops'] + step * scalar_slope,
                         special_ops=special,
                         known_interfaces={k: v + step * io_slope[k] for k, v in io_first.items()},
                         state_resident_after_bytes=state_first + step * state_slope))
    return dict(schedule='single-token decode', calls=steps, rows=rows, totals=add_rows(rows),
                first_call_ledger=first,
                affine_proof=dict(matrix_per_history_position=matrix_slope,
                                  scalar_per_history_position=scalar_slope,
                                  state_per_appended_position=state_slope,
                                  special_per_history_position=special_slope),
                final_state_resident_bytes=rows[-1]['state_resident_after_bytes'])


def sequential_v4(model, batch, history, tokens, routing, max_length):
    result = v4_prefix_continuation.calculate(model=model, prefix_tokens=history, new_tokens=tokens,
                                            batch=batch, routing=routing,
                                            allocated_max_seq_len=max_length, allocated_max_batch_size=batch)
    rows = [dict(step=s['step'], input_position=s['input_position'],
                 matrix_flops=s['matrix_flops_effective_attention'],
                 accounted_scalar_flops=s['accounted_scalar_flops'], special_ops=s['accounted_special_ops'],
                 known_interfaces=s['known_interfaces'], state_resident_after_bytes=s['state_resident_after_bytes'],
                 completed_ratios=s['completed_ratios']) for s in result['steps']]
    return dict(schedule='sequential known-token continuation', calls=tokens, rows=rows,
                totals=add_rows(rows), source_ledger=result,
                final_state_resident_bytes=result['summary']['final_state_resident_bytes'])


def calculate(prefix_tokens=0, new_tokens=128, output_tokens=4, batch=1,
              k3_mla_path='expanded', routing='balanced'):
    positive_int(prefix_tokens, 'restored prefix length', allow_zero=True)
    for key, value in (('new input length', new_tokens), ('output tokens', output_tokens), ('batch', batch)):
        positive_int(value, key)
    if k3_mla_path not in ('expanded', 'compact'):
        raise ValueError('K3 MLA path must be expanded or compact')
    history = prefix_tokens + new_tokens
    decode_calls = output_tokens - 1
    final_length = history + decode_calls
    # The common four-model comparison cannot exceed its shortest supported context.
    if final_length > model_config('qwen3-8b')['max_position_embeddings']:
        raise ValueError('Common request exceeds the fixed Qwen3-8B context contract')
    comparisons = []
    for model in MODELS:
        if model.startswith('deepseek-v4') and prefix_tokens:
            prefill = sequential_v4(model, batch, prefix_tokens, new_tokens, routing, final_length)
            reference = prefill['source_ledger']['static_base_forward']
        else:
            if model == 'qwen3-8b':
                reference = qwen3.calculate(model, Scenario(batch=batch, tokens=new_tokens, history=prefix_tokens))
                interfaces = qwen_interfaces(reference)
                state_after = reference['summary']['kv_resident_after_bytes']
            elif model == 'kimi-k3':
                reference = k3_forward.calculate(batch=batch, tokens=new_tokens, history=prefix_tokens,
                                                 mla_path=k3_mla_path, routing=routing)
                interfaces = k3_interfaces(reference)
                state_after = reference['summary']['state_resident_after_bytes']
            else:
                reference = v4_forward.calculate(model, batch=batch, tokens=new_tokens, history=0, routing=routing)
                interfaces = dict(embedding_lookup_payload_bytes=reference['summary']['embedding_lookup_payload_bytes'])
                interfaces.update({k: v for k, v in reference['components']['attention']['sparse_kernel_summary'].items()
                                   if k in ('gathered_kv_bytes', 'query_read_bytes', 'output_write_bytes', 'index_read_bytes', 'sink_read_bytes')})
                state_after = reference['summary']['state_resident_after_bytes']
                interfaces.update(
                    attention_uniform_bf16_matrix_weight_payload_bytes=2 * reference['components']['attention']['summary']['matrix_parameters'],
                    expert_uniform_bf16_matrix_weight_payload_bytes=reference['components']['experts']['summary']['uniform_matrix_weight_payload_bytes'],
                    routed_expert_actual_packed_and_scale_payload_bytes=reference['components']['experts']['routed_expert_format']['summary']['visited_weight_and_scale_payload_bytes'],
                    hc_fp32_parameter_payload_bytes=reference['components']['hyper_connections']['summary']['hc_fp32_parameter_bytes'],
                )
            row = dict(base_row(reference), known_interfaces=interfaces)
            prefill = dict(schedule='new-input full logical forward', calls=1, totals=add_rows([row]),
                           source_ledger=reference, final_state_resident_bytes=state_after)
        if decode_calls:
            decode = (sequential_v4(model, batch, history, decode_calls, routing, final_length)
                      if model.startswith('deepseek-v4') else
                      linear_decode(model, batch, history, decode_calls, k3_mla_path, routing))
            decode['schedule'] = 'single-token autoregressive forward budget; token identities supplied externally'
        else:
            decode = dict(schedule='no additional forward; first output uses input-stage logits', calls=0,
                          rows=[], totals=dict(matrix_flops=0, accounted_scalar_flops=0, special_ops={}, known_interfaces={}),
                          final_state_resident_bytes=prefill['final_state_resident_bytes'])
        total = add_rows([prefill['totals'], decode['totals']])
        restored = state.calculate(model, prefix_tokens, batch, mla_path=k3_mla_path)['summary']['resident_bytes'] if prefix_tokens else 0
        weights = reference['summary']
        uniform_weights = weights.get('weight_resident_bytes', weights.get('uniform_bf16_parameter_bytes'))
        allocation = None
        if model.startswith('deepseek-v4'):
            c = model_config(model, reference=True)
            cache = state.v4_state(c, final_length, batch, 2)['summary']['resident_bytes']
            cache += c['n_layers'] * max(0, c['window_size'] - final_length) * batch * c['head_dim'] * 2
            allocation = dict(max_seq_len=final_length, max_batch_size=batch,
                              bf16_cache_and_fp32_compressor_bytes=cache,
                              scope='Declared source allocation for both phases; overrides ModelArgs defaults, excludes frequency tables/weights/transients')
        comparisons.append(dict(model=model, sources=reference['sources'], prefill=prefill, decode=decode,
                                source_cache_allocation=allocation,
                                summary=dict(total, final_state_resident_bytes=decode['final_state_resident_bytes'],
                                             restored_prefix_state_bytes=restored,
                                             state_growth_over_restored_prefix_bytes=decode['final_state_resident_bytes'] - restored,
                                             uniform_bf16_weight_comparison_bytes=uniform_weights,
                                             full_forward_calls=prefill['calls'] + decode_calls,
                                             complete_hbm_traffic_bytes=None, complete_runtime_peak_bytes=None, complete_scalar_flops=None,
                                             predicted_latency_seconds=None, quality_equivalence=None),
                                source_coverage=reference.get('coverage', dict(logical_operators=True)),
                                source_assumptions=reference['assumptions']))
    return dict(schema_version=1, calculation='request-model-comparison',
                scenario=dict(prefix_tokens=prefix_tokens, new_tokens=new_tokens, output_tokens=output_tokens,
                              batch=batch, k3_mla_path=k3_mla_path, routing=routing),
                contract=dict(S=prefix_tokens, P=new_tokens, G=output_tokens, B=batch,
                              decode_forward_calls=decode_calls, final_retained_positions=final_length,
                              first_output_from_input_stage=True), comparisons=comparisons,
                assumptions=[
                    'Same integer request geometry is a controlled comparison, not equal tokenization, quality or semantic task evidence. Four original chapter-2 model identities are retained.',
                    'P and G are positive. The first output is obtained from input-stage last logits; only G-1 further token forwards append state. Last returned output token has not itself been fed back; retained length is S+P+G-1.',
                    'Sampling, EOS early termination, tools, tokenizer and chosen token IDs are not modeled. Outputs are a declared fixed length, not predicted behavior.',
                    'S>0 requires exact compatible restored prefix state in each model. Restoration/lookup/network work is unknown; common prefix length does not imply identical or interchangeable state.',
                    'V4 nonzero-prefix input runs P sequential reference forwards, including discarded intermediate heads; other branches use their declared multi-token input graph. Do not compare these as the same parallel prefill schedule.',
                    'K3 uses fixed config/source logical dimensions despite unresolved A_log checkpoint mismatch. Expanded is fixed HF cache representation; compact is an algebraic alternative. Chunk initial state and convolution cache must be restored for prefix reuse.',
                    'Qwen/K3 decode history contribution is affine; KDA recurrence does not grow with history. V4 enumerates every position and compression/tile boundary. Checkpoint parsing occurs a constant number of times per model, never per decode step.',
                    'Routing is a balanced/concentrated fixed synthetic histogram at each call size; prefill and decode expert reuse differ. Actual token-dependent router work needs recorded histograms.',
                    'Interface columns have different completeness and formats across models. BF16 comparison weights are not actual checkpoint/runtime storage; partial logical interface sums are not HBM or a fair measured latency denominator.',
                    'No hardware winner is inferred. Roofline requires separately matched precision/unit/dense-or-sparse peaks and justified interface-to-resource mapping; quality and full runtime unknowns remain explicit.',
                ])


def markdown(result):
    import json

    def value(x):
        if x is None:
            return 'unknown'
        if isinstance(x, (dict, list)):
            x = json.dumps(x, ensure_ascii=False, sort_keys=True)
        return str(x).replace('|', '\\|')

    def table(headers, rows):
        return ['| ' + ' | '.join(headers) + ' |', '| ' + ' | '.join('---' for _ in headers) + ' |',
                *('| ' + ' | '.join(value(x) for x in row) + ' |' for row in rows)]

    lines = ['# 同请求四模型逻辑预算', '', '## S/P/G/B 契约', '']
    lines += table(['字段', '值'], result['contract'].items())
    lines += ['', '## 并排汇总', '', '矩阵与scalar单位分别为FLOPs；权重与状态为bytes。BF16权重是统一比较格式，不是实际运行时存储。', '']
    lines += table(['模型', '输入阶段调用', 'decode调用', '输入矩阵', 'decode矩阵', '全段矩阵', '已计scalar', '末状态', 'BF16权重比较'],
                   [[x['model'], x['prefill']['calls'], x['decode']['calls'], x['prefill']['totals']['matrix_flops'],
                     x['decode']['totals']['matrix_flops'], x['summary']['matrix_flops'], x['summary']['accounted_scalar_flops'],
                     x['summary']['final_state_resident_bytes'], x['summary']['uniform_bf16_weight_comparison_bytes']]
                    for x in result['comparisons']])
    for model in result['comparisons']:
        lines += ['', '## ' + model['model'], '']
        lines += table(['summary字段', '值'], model['summary'].items())
        if model['source_cache_allocation']:
            lines += ['']
            lines += table(['源分配字段', '值'], model['source_cache_allocation'].items())
        for phase_name in ('prefill', 'decode'):
            phase = model[phase_name]
            lines += ['', '### ' + phase_name, '', phase['schedule'], '']
            lines += table(['阶段合计', '值'], phase['totals'].items())
            if phase.get('rows'):
                lines += ['']
                lines += table(['step', '输入位置', '矩阵FLOPs', 'scalarFLOPs', '末状态bytes', '完成ratio', 'special次数', '已知接口bytes'],
                               [[r['step'], r['input_position'], r['matrix_flops'], r['accounted_scalar_flops'],
                                 r['state_resident_after_bytes'], r.get('completed_ratios', []), r['special_ops'], r['known_interfaces']]
                                for r in phase['rows']])
        lines += ['', '### 原路径覆盖与限制', '']
        lines += table(['coverage字段', '值'], model['source_coverage'].items())
        lines += ['', *('- ' + x for x in model['source_assumptions']), '', '### 固定来源', '']
        lines += table(['序号', '记录'], enumerate(model['sources']))
    lines += ['', '## 共同前提与未完成范围', '', *('- ' + x for x in result['assumptions'])]
    return '\n'.join(lines) + '\n'
