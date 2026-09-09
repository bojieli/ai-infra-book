"""K3 KDA projections, causal depthwise conv and recurrent mathematical work.

Prefill reference chooses chunk KDA; this recurrent ledger is a mathematical
baseline, not the chunk kernel's execution work. Dependency revision is explicit.
"""
from ..schema import Scenario
from ..sources import model_config, provenance


def calculate(batch: int = 1, tokens: int = 1, history: int = 8192) -> dict:
    s = Scenario(batch=batch, tokens=tokens, history=history)
    c = model_config('kimi-k3')['text_config']
    linear = c['linear_attn_config']
    ids = [i - 1 for i in linear['kda_layers']]
    h, d, heads, window = c['hidden_size'], linear['head_dim'], linear['num_heads'], linear['short_conv_kernel_size']
    m, j, layers = s.rows, d * heads, len(ids)
    matrices = []

    def add(name, inputs, outputs):
        matrices.append(dict(name=name, layer_ids=ids, rows_summed_per_layer=m,
                             input_width=inputs, output_width=outputs, weight_storage_each=[outputs, inputs],
                             stored_copies_per_layer=1, visited_copies_per_layer=1,
                             parameters=layers * inputs * outputs, matrix_flops=2 * layers * m * inputs * outputs,
                             uniform_weight_payload_bytes=2 * layers * inputs * outputs))
    for name in ('q_proj', 'k_proj', 'v_proj'):
        add(name, h, j)
    add('f_a_proj', h, d)
    add('f_b_proj', d, j)
    add('b_proj', h, heads)
    if linear['use_full_rank_gate']:
        add('g_proj', h, j)
    else:
        add('g_a_proj', h, d)
        add('g_b_proj', d, j)
    add('o_proj', j, h)
    if linear.get('gate_lower_bound') is None:
        raise ValueError('KDA ledger currently requires the configured bounded gate')
    operations = []

    def op(name, shape, scalar, special=None, note=''):
        operations.append(dict(name=name, layer_ids=ids, shape=shape, scalar_flops_per_layer=scalar,
                               scalar_flops=layers * scalar,
                               special_ops={k: layers * v for k, v in (special or {}).items()}, notes=note))
    op('qkv_causal_depthwise_conv', [3, batch, tokens, j, window], 3 * m * j * (2 * window - 1),
       {'silu': 3 * m * j}, 'Bias-free width-4 convolution; full taps including zero padding, n-1 additions. SiLU is a primitive.')
    op('qk_l2norm', [2, m, heads, d], 6 * m * j, {'sqrt': 2 * m * heads},
       'Per vector: D squares, D-1 sum, epsilon and D divisions; no mean and no learned scale.')
    op('bounded_decay_gate', [m, heads, d], 3 * m * j,
       {'exp_A': m * heads, 'sigmoid': m * j, 'exp_decay': m * j},
       'Bias add, exp(A)*g, lower_bound*sigmoid; then exponentiate log gate for state decay. Per-token logical count, without loop hoisting.')
    op('beta_sigmoid', [m, heads], 0, {'sigmoid': m * heads})
    op('recurrent_state_update_and_query', [m, heads, d, d], m * heads * (7 * d * d + d),
       note='Decay S; predict k^T S; subtract from v; multiply beta; outer-product add; query scaled q^T S. Dot reductions use D-1 additions.')
    op('output_rmsnorm_sigmoid_gate', [m, heads, d], m * heads * (5 * d + 1),
       {'rsqrt': m * heads, 'sigmoid': m * j},
       'RMSNorm learned scale shared across heads, then multiply sigmoid(g); no bias.')
    state_bytes = layers * batch * heads * d * d * 4
    return dict(schema_version=1, calculation='kimi-k3-kda-recurrent-ledger', model='kimi-k3',
                scenario=dict(batch=batch, tokens=tokens, history=history,
                              reference_dispatch='fused_recurrent with cache' if tokens == 1 else 'chunk; recurrent work below is a baseline'),
                sources=provenance('kimi-k3'), matrices=matrices, non_matrix_operations=operations,
                non_matrix_scope='Logical recurrent baseline. Chunk prefill, CUDA/Triton tiling, casts and state/conv movement require separate execution ledgers.',
                summary=dict(projection_matrix_flops=sum(row['matrix_flops'] for row in matrices),
                             projection_parameters=sum(row['parameters'] for row in matrices),
                             convolution_parameters=layers * 3 * j * window,
                             output_norm_parameters=layers * d,
                             decay_parameters=layers * (heads + j),
                             recurrent_and_other_scalar_flops=sum(row['scalar_flops'] for row in operations),
                             recurrent_state_fp32_bytes=state_bytes,
                             recurrent_state_one_read_plus_write_bytes=2 * state_bytes,
                             convolution_cache_bf16_bytes=layers * batch * 3 * j * window * 2,
                             qkv_projected_tensor_each_bytes=m * j * 2),
                assumptions=[
                    '69 KDA layers, 96 heads of dimension 128. This excludes MLA, experts, AttnRes, embedding/head and external sublayer normalization.',
                    'Matrix shapes come from pinned K3. ShortConvolution bias=False and [B, channels, kernel_size] state shape follow selected FLA official source.',
                    'Selected FLA revision is algorithm evidence, not a proven K3 release dependency. Both pinned KDA wrappers explicitly translate deprecated transpose_state_layout to state_v_first; this keyword alias is verified, but full runtime/checkpoint compatibility, including A_log shapes, is not established.',
                    'Recurrent mathematical state update uses FP32 K×V state. One read/write is a declared call-boundary payload, not per-token HBM; prefill cannot multiply this by T and claim actual traffic.',
                    'T>1 in fixed K3 dispatches to chunk KDA. The recurrent arithmetic reported here is an equivalent mathematical baseline, not chunk-kernel FLOPs or measured runtime.',
                    'No padding tokens, no packed sequence boundaries, uniform two-byte projected/conv-cache tensors; true mixed quantization formats remain separate.',
                ])
