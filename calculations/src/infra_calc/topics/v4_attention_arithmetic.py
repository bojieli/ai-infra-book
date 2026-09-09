"""V4 normalization, rotary, compressor pooling and index scoring arithmetic.

Hadamard uses a mathematical butterfly count; quantization follows the pinned
V4 simulation expressions. Sparse attention online softmax is a separate ledger.
"""
from collections import Counter
from . import transforms


def calculate(c: dict, batch: int, tokens: int, history: int) -> dict:
    m, end = batch * tokens, history + tokens
    h, d, rd, heads = (c[k] for k in ('dim', 'head_dim', 'rope_head_dim', 'n_heads'))
    layers = list(range(c['n_layers']))
    ratios = c['compress_ratios'][:c['n_layers']]
    ops = []

    def add(name, ids, shape, scalar=0, special=None, note=''):
        ops.append(dict(name=name, layer_ids=ids, shape=shape, scalar_flops_per_layer=scalar,
                        scalar_flops=scalar * len(ids),
                        special_ops={key: value * len(ids) for key, value in (special or {}).items()}, notes=note))

    def norm(name, ids, rows, width, learned=True):
        add(name, ids, [rows, width], scalar=rows * ((4 if learned else 3) * width + 1),
            special={'rsqrt': rows}, note='Square, n-1 sum, mean division, epsilon, normalization multiply, and learned scale if present.')

    def rotary(name, ids, rows):
        add(name, ids, [rows, rd], scalar=3 * rows * rd,
            note='Complex multiply: four multiplies and two add/subtract per pair; excludes frequency-table construction and casts.')

    norm('q_lowrank_norm', layers, m, c['q_lora_rank'])
    norm('q_head_norm', layers, m * heads, d, learned=False)
    norm('window_kv_norm', layers, m, d)
    rotary('query_rope', layers, m * heads)
    rotary('window_kv_rope', layers, m)
    rotary('output_inverse_rope', layers, m * heads)
    add('window_kv_quantization', layers, [m, d - rd],
        special={'fp8_simulated_elements': m * (d - rd)}, note='QAT simulation returns activation dtype, not FP8-resident cache; arithmetic is expanded below.')
    for ratio in sorted(set(ratios) - {0}):
        ids = [i for i, r in enumerate(ratios) if r == ratio]
        coff = 2 if ratio == 4 else 1
        completed = batch * (end // ratio - history // ratio)
        widths = [('main', d)] + ([('index', c['index_head_dim'])] if ratio == 4 else [])
        for branch, width in widths:
            prefix = f'compress_r{ratio}_{branch}'
            # Prefill saves the last full overlapping block, adding APE there
            # as well as in the full-block pooling input. Decode adds once.
            saved = batch * ratio * coff * width if history == 0 and ratio == 4 and tokens >= ratio else 0
            add(prefix + '_ape', ids, [m, coff * width], scalar=m * coff * width + saved,
                note='Includes duplicate APE addition when prefill saves the last full overlap block for subsequent decode.')
            window = coff * ratio
            softmax_rows = completed * width
            add(prefix + '_pool_softmax', ids, [completed, window, width],
                scalar=softmax_rows * (3 * window - 1),
                special={'exp': softmax_rows * window, 'compare_max': softmax_rows * (window - 1)},
                note='Softmax across the pooled token axis, independently for every channel. First overlap block includes padded slots.')
            add(prefix + '_weighted_pool', ids, [completed, window, width], scalar=softmax_rows * (2 * window - 1))
            norm(prefix + '_norm', ids, completed, width)
            rotary(prefix + '_rope', ids, completed)
            if branch == 'index':
                add(prefix + '_rotate_quantize', ids, [completed, width],
                    special={'hadamard_rows': completed, 'hadamard_elements': completed * width,
                             'fp4_simulated_elements': completed * width},
                    note='Hadamard butterfly and FP4 simulation arithmetic are expanded below; no inferred CUDA instruction or traffic count.')
            else:
                add(prefix + '_quantize', ids, [completed, width - rd], special={'fp8_simulated_elements': completed * (width - rd)})
    indexed = [i for i, ratio in enumerate(ratios) if ratio == 4]
    ih, idim, columns = c['index_n_heads'], c['index_head_dim'], end // 4
    rotary('index_query_rope', indexed, m * ih)
    add('index_query_rotate_quantize', indexed, [m, ih, idim],
        special={'hadamard_rows': m * ih, 'hadamard_elements': m * ih * idim, 'fp4_simulated_elements': m * ih * idim})
    add('index_head_weight_scale', indexed, [m, ih], scalar=m * ih)
    add('index_relu_weight_reduce', indexed, [m, ih, columns], scalar=m * columns * (2 * ih - 1),
        special={'relu_compare': m * ih * columns}, note='Reference scores all rectangular columns before prefill masking.')
    if history == 0:
        add('index_causal_mask_add', indexed, [m, columns], scalar=m * columns)
    add('index_topk', indexed, [m, columns], special={'topk_rows': m, 'topk_candidates': m * columns},
        note='Selection primitive; no assumed comparison algorithm.')
    for op in ops:
        special = op['special_ops']
        if 'hadamard_rows' in special:
            work = transforms.hadamard(special.pop('hadamard_rows'), c['index_head_dim'])
            special.pop('hadamard_elements')
            op['scalar_flops'] += work['scalar_flops']
            op['notes'] += ' ' + work['notes']
        for precision, group_size in [('FP4', 32), ('FP8', 64)]:
            key = precision.lower() + '_simulated_elements'
            if key in special:
                work = transforms.simulated_quantization(special.pop(key), group_size, precision)
                op['scalar_flops'] += work['scalar_flops']
                for name, value in work['special_ops'].items():
                    special[name] = special.get(name, 0) + value
                op['notes'] += ' ' + work['notes']
        if op['layer_ids']:
            op['scalar_flops_per_layer'] = op['scalar_flops'] // len(op['layer_ids'])
    total = Counter()
    for op in ops:
        total.update(op['special_ops'])
    return dict(non_matrix_operations=ops,
                non_matrix_summary=dict(scalar_flops=sum(op['scalar_flops'] for op in ops), special_ops=dict(total)),
                non_matrix_scope='Attention normalization/rotary, compressor pooling and index scoring only. Sparse-attention online softmax is in sparse_kernel_summary, not this subtotal. Includes mathematical Hadamard butterfly/scale and quantize-dequantize arithmetic; excludes compiler-specific shuffle/sign instructions, frequency table construction, data movement and external sublayer norms. Special functions are not Tensor FLOPs.')
