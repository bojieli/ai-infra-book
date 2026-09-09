"""V4 attention matrix work, preserving grouped projections and index masking.

Reference supports initial prefill or single-token incremental decode. The
indexer computes rectangular scores before its prefill causal mask; attention
effective pairs are reported separately. No claim of complete kernel traffic.
"""
from ..sources import model_config, provenance
from ..units import positive_int
from . import v4_attention_arithmetic, v4_sparse_kernel


def capped_floor_sum(n: int, ratio: int, cap: int) -> int:
    """Sum min(floor(t/ratio), cap), t=1..n, without a token loop."""
    cutoff = min(n, cap * ratio - 1)
    q = cutoff // ratio
    return q * (cutoff + 1) - ratio * q * (q + 1) // 2 + max(0, n - cutoff) * cap


def calculate(model: str, batch: int = 1, tokens: int = 8192, history: int = 0) -> dict:
    if model not in ('deepseek-v4-flash', 'deepseek-v4-pro'):
        raise ValueError('V4 attention requires Flash or Pro')
    for key, value in [('batch', batch), ('tokens', tokens), ('history', history)]:
        positive_int(value, key, allow_zero=key == 'history')
    if history and tokens != 1:
        raise ValueError('Pinned V4 incremental path supports one token; chunked prefix continuation needs a separate execution path')
    c = model_config(model, reference=True)
    h, d, heads, qrank, groups, orank = (c[k] for k in ('dim', 'head_dim', 'n_heads', 'q_lora_rank', 'o_groups', 'o_lora_rank'))
    if heads % groups:
        raise ValueError('Query heads must divide into output groups')
    m, end = batch * tokens, history + tokens
    all_layers = list(range(c['n_layers']))
    ratios = c['compress_ratios'][:c['n_layers']]
    matrices = []

    def add(name, rows, inputs, outputs, layers, copies=1):
        matrices.append(dict(name=name, layer_ids=layers, rows_summed_per_layer=rows,
                             input_width=inputs, output_width=outputs, weight_storage_each=[outputs, inputs],
                             stored_copies_per_layer=copies, visited_copies_per_layer=copies,
                             parameters=len(layers) * copies * inputs * outputs,
                             matrix_flops=2 * len(layers) * rows * inputs * outputs,
                             uniform_weight_payload_bytes=2 * len(layers) * copies * inputs * outputs))

    add('wq_a', m, h, qrank, all_layers)
    add('wq_b', m, qrank, heads * d, all_layers)
    add('wkv_shared', m, h, d, all_layers)
    add('wo_a_grouped', m * groups, heads * d // groups, orank, all_layers, groups)
    add('wo_b', m, groups * orank, h, all_layers)
    layer_work = []
    for ratio in sorted(set(ratios)):
        ids = [i for i, r in enumerate(ratios) if r == ratio]
        if ratio:
            width = (2 if ratio == 4 else 1) * d
            add(f'compress_r{ratio}_wkv', m, h, width, ids)
            add(f'compress_r{ratio}_wgate', m, h, width, ids)
        if ratio == 4:
            ih, idim = c['index_n_heads'], c['index_head_dim']
            add('index_wq_b', m, qrank, ih * idim, ids)
            add('index_weights_proj', m, h, ih, ids)
            add('index_compress_wkv', m, h, 2 * idim, ids)
            add('index_compress_wgate', m, h, 2 * idim, ids)
        window_pairs = capped_floor_sum(end, 1, c['window_size']) - capped_floor_sum(history, 1, c['window_size'])
        compressed_pairs = 0
        if ratio:
            cap = c['index_topk'] if ratio == 4 else end // ratio + 1
            compressed_pairs = capped_floor_sum(end, ratio, cap) - capped_floor_sum(history, ratio, cap)
        selected_pairs = batch * (window_pairs + compressed_pairs)
        rectangular_index_pairs = batch * tokens * (end // ratio) if ratio == 4 else 0
        valid_index_pairs = batch * (capped_floor_sum(end, 4, end // 4 + 1) - capped_floor_sum(history, 4, end // 4 + 1)) if ratio == 4 else 0
        layer_work.append(dict(layer_ids=ids, compress_ratio=ratio,
                               selected_attention_pairs_per_layer=selected_pairs,
                               qk_and_pv_matrix_flops=4 * len(ids) * heads * d * selected_pairs,
                               actual_index_rectangular_matrix_flops=2 * len(ids) * c['index_n_heads'] * c['index_head_dim'] * rectangular_index_pairs,
                               causal_index_matrix_flops=2 * len(ids) * c['index_n_heads'] * c['index_head_dim'] * valid_index_pairs,
                               completed_compressed_rows_per_request=(end // ratio - history // ratio) if ratio else 0))
    projection = sum(row['matrix_flops'] for row in matrices)
    attention = sum(row['qk_and_pv_matrix_flops'] for row in layer_work)
    index = sum(row['actual_index_rectangular_matrix_flops'] for row in layer_work)
    arithmetic = v4_attention_arithmetic.calculate(c, batch, tokens, history)
    kernel = v4_sparse_kernel.calculate(c, batch, tokens, history, layer_work)
    return dict(**arithmetic, **kernel,
                schema_version=1, calculation='v4-attention-matrices', model=model,
                scenario=dict(batch=batch, tokens=tokens, history=history), sources=provenance(model),
                matrices=matrices, attention_layer_groups=layer_work,
                summary=dict(projection_matrix_flops=projection, effective_qk_pv_matrix_flops=attention,
                             reference_index_matrix_flops=index,
                             matrix_flops=projection + attention + index,
                             reference_with_sparse_tiles_matrix_flops=projection + index + kernel['sparse_kernel_summary']['matrix_flops'],
                             accounted_scalar_flops=arithmetic['non_matrix_summary']['scalar_flops'] + kernel['sparse_kernel_summary']['online_softmax_scalar_flops'],
                             matrix_parameters=sum(row['parameters'] for row in matrices),
                             causal_index_matrix_flops=sum(row['causal_index_matrix_flops'] for row in layer_work)),
                assumptions=[
                    'Initial prefill or one-token incremental decode, single-device logical model. No MTP, expert or mHC work in this subledger.',
                    'wo_a consists of independent per-group matrices. Its flattened checkpoint storage is not a dense mixing across all query heads.',
                    'Both compressor projections execute on every new token, including decode steps that do not complete a compressed record.',
                    'Indexer computes all end_pos//4 columns before masking in prefill. Causal index work is a counterfactual lower work count, not the reference GEMM.',
                    'QK/PV count valid selected entries only. Padding, sparse-kernel tile work and attention sink softmax are separate in sparse_kernel_summary. Pooling, norms and RoPE are in non_matrix_operations; Hadamard butterfly and simulation quantization arithmetic are expanded there; bitwise rounding and format casts remain separate primitives.',
                    'Matrix parameters exclude norm scales, attention sinks and compressor APE. Uniform two-byte matrix payload is a teaching comparison, not actual FP8/FP4/FP32 checkpoint storage or HBM.',
                ])
