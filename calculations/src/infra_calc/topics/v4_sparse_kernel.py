"""Pinned V4 sparse-attention kernel: 64 gathered slots per GEMM tile.

Invalid indices mask loads and scores, but do not remove the dense tile GEMMs.
Payload counts assume one logical read per source gather, not measured HBM.
"""


def calculate(config: dict, batch: int, tokens: int, history: int, groups: list[dict]) -> dict:
    heads, d, block = config['n_heads'], config['head_dim'], 64
    if heads < 16:
        raise ValueError('This adapter expects V4 heads without wrapper head padding')
    m, end = batch * tokens, history + tokens
    window_slots = config['window_size'] if history else min(tokens, config['window_size'])
    result = []
    for group in groups:
        ratio = group['compress_ratio']
        extra = min(config['index_topk'], end // ratio) if ratio == 4 else end // ratio if ratio else 0
        slots = window_slots + extra
        tiles = (slots + block - 1) // block
        layers = len(group['layer_ids'])
        valid = group['selected_attention_pairs_per_layer']
        result.append(dict(layer_ids=group['layer_ids'], compress_ratio=ratio,
                           allocated_index_slots_per_query=slots, tiles_per_query=tiles,
                           padded_slots_per_query=tiles * block,
                           matrix_flops=layers * 4 * m * heads * d * tiles * block,
                           effective_matrix_flops=group['qk_and_pv_matrix_flops'],
                           online_softmax_scalar_flops=layers * m * heads * (tiles * (3 * block + 2 + d) + d + 2),
                           exp_ops=layers * m * heads * (tiles * (block + 1) + 1),
                           max_comparisons=layers * m * heads * tiles * block,
                           gathered_kv_bytes=layers * valid * d * 2,
                           query_read_bytes=layers * m * heads * d * 2,
                           output_write_bytes=layers * m * heads * d * 2,
                           index_read_bytes=layers * m * slots * 4,
                           sink_read_bytes=layers * m * heads * 4))
    keys = ['matrix_flops', 'effective_matrix_flops', 'online_softmax_scalar_flops', 'exp_ops',
            'max_comparisons', 'gathered_kv_bytes', 'query_read_bytes', 'output_write_bytes', 'index_read_bytes', 'sink_read_bytes']
    summary = {key: sum(row[key] for row in result) for key in keys}
    summary['source_declared_shared_bytes_per_cta'] = 4 * heads * d + 2 * block * d + 2 * heads * block
    summary['source_declared_fragment_bytes_per_cta'] = 4 * (heads * block + heads * d + 5 * heads + block)
    return dict(sparse_kernel_groups=result, sparse_kernel_summary=summary,
                sparse_kernel_scope=[
                    'BF16 Q/KV/probability GEMMs, FP32 score/output accumulators. Two GEMMs execute each padded 64-slot tile even when indices are -1.',
                    'Per head and tile: score scale/subtract/reduce, running-max rescale, denominator update, and D output rescale multiplies; final learned sink exponential and D divisions included.',
                    'Index array width is fixed across queries in prefill; valid historical entries grow per query. Invalid slots do not load KV, but GEMM and online-softmax tile work remain.',
                    'Gathered KV read once per valid index and reused by QK/PV within a tile. No extra K/V factor of two: the shared representation serves both.',
                    'Q, output, indices and sinks use logical per-CTA operands; cache reuse, transactions, spills and allocator traffic are not inferred.',
                    'Shared/fragment sizes sum explicit source declarations only. Compiler pipeline buffering, alignment, register mapping and feasibility must be checked on the target; this is not a measured launch footprint.',
                ])
