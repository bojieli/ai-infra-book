"""V4 mHC from the pinned model and TileLang Sinkhorn reference.

Logical arithmetic follows source expressions. Reductions use n-1 additions;
epsilon inside a per-cell division is counted per cell, without compiler CSE.
"""
from collections import Counter

from ..sources import model_config, provenance
from ..units import positive_int


def sinkhorn_work(copies: int, iterations: int) -> dict:
    positive_int(copies, 'copies')
    positive_int(iterations, 'iterations')
    c = copies
    # pre/post affine + epsilon or output factor; comb affine.
    affine = 6 * c + 2 * c * c
    # Initial row softmax: subtract max, reduce sum, divide, add epsilon.
    initial = 4 * c * c - c
    # First column normalization, then I-1 row/column pairs.
    normalization = c * (c - 1) + 2 * c * c
    return dict(scalar_flops=affine + initial + (2 * iterations - 1) * normalization,
                special_ops={'sigmoid': 2 * c, 'exp': c * c, 'compare_max': c * (c - 1)},
                normalization_passes=2 * iterations - 1)


def calculate(model: str, batch: int = 1, tokens: int = 8192, activation_bytes: int = 2) -> dict:
    if model not in ('deepseek-v4-flash', 'deepseek-v4-pro'):
        raise ValueError('mHC adapter currently supports V4 Flash/Pro')
    for key, value in [('batch', batch), ('tokens', tokens), ('activation_bytes', activation_bytes)]:
        positive_int(value, key)
    config = model_config(model, reference=True)
    m, h, c, layers = batch * tokens, config['dim'], config['hc_mult'], config['n_layers']
    iterations = config.get('hc_sinkhorn_iters', 20)  # pinned ModelArgs default
    d, j, branches = c * h, (c + 2) * c, 2 * layers
    sink = sinkhorn_work(c, iterations)
    operations = []

    def add(name, repeats, shapes, matrix=0, scalar=0, special=None, note=''):
        operations.append(dict(name=name, repeats=repeats, shapes=shapes,
                               matrix_flops=matrix * repeats, scalar_flops=scalar * repeats,
                               special_ops={key: value * repeats for key, value in (special or {}).items()}, notes=note))

    add('pre_rms_statistic', branches, {'input': [m, d]}, scalar=m * (2 * d + 1), special={'rsqrt': m},
        note='FP32 square, sum, mean division and epsilon. No learned RMS scale in hc_pre.')
    add('pre_mix_projection', branches, {'A': [m, d], 'W_math': [d, j], 'Y': [m, j]}, matrix=2 * m * d * j,
        note='FP32 source operands; accumulator and achievable matrix-unit peak require a separate backend match.')
    add('pre_mix_normalize', branches, {'mixes': [m, j]}, scalar=m * j)
    add('split_sinkhorn', branches, {'pre': [m, c], 'post': [m, c], 'comb': [m, c, c]},
        scalar=m * sink['scalar_flops'], special={key: m * value for key, value in sink['special_ops'].items()},
        note=f"Initial row softmax, one column normalization, then {iterations - 1} row/column pairs. Per-cell epsilon expressions are not hoisted.")
    add('pre_weighted_reduce', branches, {'input': [m, c, h], 'output': [m, h]}, scalar=m * (2 * c - 1) * h,
        note='c multiplies and c-1 sum additions per output channel; output casts to activation dtype.')
    add('post_residual_mix', branches, {'residual': [m, c, h], 'comb': [m, c, c], 'output': [m, c, h]},
        scalar=m * (2 * c * c + c) * h,
        note='Literal broadcast/reduce: c²H residual multiplies, c(c-1)H reductions, cH post multiplies and cH final adds.')
    # The reference head reduces all new token rows, even though logits use -1.
    add('head_rms_statistic', 1, {'input': [m, d]}, scalar=m * (2 * d + 1), special={'rsqrt': m})
    add('head_mix_projection', 1, {'A': [m, d], 'W_math': [d, c], 'Y': [m, c]}, matrix=2 * m * d * c)
    add('head_mix_and_gate', 1, {'pre': [m, c]}, scalar=4 * m * c, special={'sigmoid': m * c},
        note='Multiply RMS statistic, scale, add base, sigmoid, add epsilon.')
    add('head_weighted_reduce', 1, {'input': [m, c, h], 'output': [m, h]}, scalar=m * (2 * c - 1) * h)
    parameters = branches * (j * d + j + 3) + c * d + c + 1
    special = Counter()
    for row in operations:
        special.update(row['special_ops'])
    return dict(schema_version=1, calculation='v4-hyper-connections', model=model,
                scenario=dict(batch=batch, tokens=tokens, activation_bytes=activation_bytes),
                sources=provenance(model), residual_operations=operations,
                summary=dict(hc_mult=c, hidden_size=h, sublayer_occurrences=branches,
                             sinkhorn_iterations=iterations, sinkhorn_normalizations_per_sublayer=sink['normalization_passes'],
                             hc_parameters=parameters, hc_fp32_parameter_bytes=parameters * 4,
                             matrix_flops=sum(row['matrix_flops'] for row in operations),
                             scalar_flops=sum(row['scalar_flops'] for row in operations), special_ops=dict(special),
                             residual_activation_tensor_bytes=m * c * h * activation_bytes,
                             one_sublayer_post_comb_fp32_bytes=m * (c + c * c) * 4,
                             embedding_repeat_output_bytes=m * c * h * activation_bytes),
                assumptions=[
                    'Each decoder layer has separate attention and FFN mHC; the final hc_head is counted once over all new token rows, matching reference before last-position logits.',
                    'Only mHC: excludes attention/FFN, external sublayer RMSNorm, final model RMSNorm, vocabulary projection, MTP and communication.',
                    'Matrix projection uses FMA=2; broadcast multiply/reductions follow source as scalar arithmetic. Special functions are primitives, not Tensor FLOPs.',
                    'Sinkhorn uses FP32 and keeps its c×c fragment local across iterations; multiplying iteration count by an HBM tensor round trip would be incorrect.',
                    'Reported tensor sizes are separate live objects, not summed workspace peaks or measured HBM. Embedding repeat materializes the c copies in the reference.',
                    'No compilation-specific common-subexpression elimination: repeated denominator epsilon additions are counted per output cell. These counts are logical source work, not GPU instructions.',
                ])
