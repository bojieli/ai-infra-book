"""Kimi K3 MLA: reference expanded cache vs algebraic compact absorption.

Compact absorption is a declared alternative, not the pinned HF cache path.
Output gating prevents silently merging the value and output projections.
"""
from ..schema import Scenario
from ..sources import model_config, provenance


def calculate(batch: int = 1, tokens: int = 8192, history: int = 0, path: str = 'expanded') -> dict:
    scenario = Scenario(batch=batch, tokens=tokens, history=history)
    if path not in ('expanded', 'compact'):
        raise ValueError('MLA path must be expanded or compact')
    c = model_config('kimi-k3')['text_config']
    ids = [i - 1 for i in c['linear_attn_config']['full_attn_layers']]
    if not c['mla_use_nope'] or c['num_attention_heads'] != c['num_key_value_heads']:
        raise ValueError('Adapter requires K3 NoPE MLA and equal query/KV head counts')
    h, heads, rank, qr, dn, extra, dv = (c[k] for k in ('hidden_size', 'num_attention_heads', 'kv_lora_rank', 'q_lora_rank', 'qk_nope_head_dim', 'qk_rope_head_dim', 'v_head_dim'))
    layers, m, n, width = len(ids), scenario.rows, history + tokens, dn + extra
    matrices = []

    def add(name, rows, inputs, outputs, copies=1, layout=None):
        matrices.append(dict(name=name, layer_ids=ids, rows_summed_per_layer=rows,
                             input_width=inputs, output_width=outputs, weight_storage_each=layout or [outputs, inputs],
                             stored_copies_per_layer=copies, visited_copies_per_layer=copies,
                             parameters=layers * copies * inputs * outputs,
                             matrix_flops=2 * layers * rows * inputs * outputs,
                             uniform_weight_payload_bytes=2 * layers * copies * inputs * outputs))

    add('q_a_proj', m, h, qr)
    add('q_b_proj', m, qr, heads * width)
    add('kv_a_proj_with_mqa', m, h, rank + extra)
    if path == 'expanded':
        add('kv_b_proj', m, rank, heads * (dn + dv))
        qk_dim, pv_dim = width, dv
        cache_per_token = heads * (width + dv) * 2
    else:
        add('query_absorb_Wk', m * heads, dn, rank, heads, [dn, rank])
        add('latent_output_Wv', m * heads, rank, dv, heads, [dv, rank])
        qk_dim, pv_dim = rank + extra, rank
        cache_per_token = (rank + extra) * 2
    if c['mla_use_output_gate']:
        add('g_proj', m, h, heads * dv)
    add('o_proj', m, heads * dv, h)
    pairs, rectangle = scenario.pairs, scenario.rectangular_pairs
    attention_flops = 2 * layers * heads * pairs * (qk_dim + pv_dim)
    summary = dict(matrix_parameters=sum(row['parameters'] for row in matrices),
                   norm_scale_parameters=layers * (qr + rank),
                   projection_matrix_flops=sum(row['matrix_flops'] for row in matrices),
                   valid_attention_matrix_flops=attention_flops,
                   rectangular_attention_matrix_flops=2 * layers * heads * rectangle * (qk_dim + pv_dim),
                   matrix_flops=sum(row['matrix_flops'] for row in matrices) + attention_flops,
                   kv_resident_after_bytes=layers * batch * n * cache_per_token,
                   kv_new_write_bytes=layers * batch * tokens * cache_per_token,
                   history_unique_payload_bytes=layers * batch * history * cache_per_token,
                   qk_norm_scalar_flops=layers * m * (4 * qr + 1 + 4 * rank + 1),
                   norm_rsqrt_ops=2 * layers * m,
                   output_gate_scalar_flops=layers * m * heads * dv if c['mla_use_output_gate'] else 0,
                   output_gate_sigmoid_ops=layers * m * heads * dv if c['mla_use_output_gate'] else 0,
                   rectangular_score_fp32_tensor_per_layer_bytes=batch * heads * tokens * n * 4)
    return dict(schema_version=1, calculation='kimi-k3-mla', model='kimi-k3',
                scenario=dict(batch=batch, tokens=tokens, history=history, path=path), sources=provenance('kimi-k3'),
                matrices=matrices, summary=summary,
                attention_shapes=dict(query=[batch, heads, tokens, qk_dim],
                                      key_logical=[batch, heads, n, qk_dim],
                                      scores=[batch, heads, tokens, n],
                                      value_logical=[batch, heads, n, pv_dim],
                                      attention_output=[batch, heads, tokens, pv_dim],
                                      gate_input_and_output=[m, heads * dv]),
                assumptions=[
                    '24 MLA layers, using official 1-based full_attn_layers converted to actual zero-based layer IDs. KDA, FFN, AttnRes, vision and MTP excluded.',
                    'Expanded is the pinned HF implementation: kv_b expands K/V before cache update, shared extra key branch is concatenated across heads. Compact is an algebraic alternative storing normalized latent KV plus the extra branch.',
                    'Despite the qk_rope_head_dim field name, mla_use_nope is true and this forward applies NO RoPE. The extra 64 dimensions remain present in Q/K and compact cache.',
                    'Compact computes Q_pass @ Wk before QK, then probability-weighted latent @ Wv. Wk/Wv are views of the same kv_b weights, not new parameter copies.',
                    'Output gate is sigmoid(g_proj(x)) times the restored head-value output, before o_proj. Do not absorb Wv into o_proj across this nonlinear gate.',
                    'BF16 two-byte teaching weights/cache. Valid causal attention work and rectangular eager work are separate; selected backend padding/softmax and true mixed quantization need separate accounting.',
                    'The expanded flash_attention_2 path pads V to Q width before attention and slices the output afterward; the reported valid PV count is unpadded logical work, not that backend tile work.',
                    'History payload is each cache record once, not a measured HBM total. Score tensor size is a separate object, not a summed peak workspace.',
                ])
