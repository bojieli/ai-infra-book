"""Non-matrix FFN arithmetic from the pinned V4 and K3 reference code.

Special functions are named primitives, never equivalent Tensor Core FLOPs.
Counts are logical operations, not kernel instructions or memory transactions.
"""
from collections import Counter

from ..sources import model_config


def calculate(model: str, geometry: dict, rows: int) -> dict:
    g, m = geometry, rows
    h, r, f, e, k = (g[key] for key in ('hidden', 'expert_hidden', 'intermediate', 'experts', 'top_k'))
    layers, dense = g['moe_layers'], g['dense_layers']
    operations = []

    def add(name, layer_ids, shape, scalar=0, special=None, note=''):
        operations.append(dict(name=name, layer_ids=layer_ids, shape=shape,
                               scalar_flops_per_layer=scalar,
                               scalar_flops=scalar * len(layer_ids),
                               special_ops={key: value * len(layer_ids) for key, value in (special or {}).items()},
                               notes=note))

    if model.startswith('deepseek-v4-'):
        config = model_config(model, reference=True)
        if config['score_func'] != 'sqrtsoftplus':
            raise ValueError('Non-matrix V4 adapter currently requires sqrtsoftplus scores')
        add('router_score', layers, [m, e], special={'softplus': m * e, 'sqrt': m * e},
            note='FP32 softplus includes its backend-dependent threshold branch as one primitive.')
        add('router_selection_bias', g['router_bias_layers'], [m, e], scalar=m * e)
        add('router_topk', g['router_bias_layers'], [m, e], special={'topk_rows': m, 'topk_candidates': m * e},
            note='Only non-hash layers select top-k; candidate count is not a comparison count.')
        add('router_hash_lookup', g['hash_layers'], [m, k], special={'integer_lookup_entries': m * k})
        add('router_normalize_scale', layers, [m, k], scalar=m * (3 * k - 1),
            note='k-1 sum additions, k divisions and k scale multiplies, including unit scales.')
        for branch, n in [('routed', m * k * f), ('shared', m * g['shared'] * f)]:
            special = {'silu': n}
            if config['swiglu_limit'] > 0:
                special['clamp_bound_comparisons'] = 3 * n
            add(branch + '_activation', layers, [n], scalar=n, special=special,
                note='FP32 SiLU(gate) times up; gate upper clamp and up lower/upper clamps are separate comparisons.')
        add('routed_probability_multiply', layers, [m * k, f], scalar=m * k * f,
            note='Reference weights the intermediate activation BEFORE down projection, in F rather than H dimensions.')
        add('routed_combine', layers, [m, h], scalar=m * k * h,
            note='Reference adds each expert output into a zero-initialized FP32 accumulator; includes first add into zero.')
    elif model == 'kimi-k3':
        config = model_config(model)['text_config']
        if config['hidden_act'] != 'situ' or config['moe_router_activation_func'] != 'sigmoid':
            raise ValueError('K3 non-matrix adapter requires Situ and sigmoid routing')
        if config.get('num_expert_group', 1) != 1:
            raise ValueError('Grouped K3 routing requires its group selection ledger')
        add('router_score', layers, [m, e], special={'sigmoid': m * e})
        add('router_selection_bias', layers, [m, e], scalar=m * e)
        add('router_topk', layers, [m, e], special={'topk_rows': m, 'topk_candidates': m * e})
        scalar = m * k
        if k > 1 and config['moe_renormalize']:
            scalar += m * 2 * k  # k-1 reduction + epsilon + k divisions
        add('router_normalize_scale', layers, [m, k], scalar=scalar,
            note='Renormalization includes the 1e-20 denominator addition; scale multiplication follows.')
        branches = [('routed', m * k * f, layers), ('shared', m * g['shared'] * f, layers),
                    ('dense', m * g['dense_intermediate'], dense)]
        for branch, n, ids in branches:
            extra_up = config.get('activation_situ_linear_beta') is not None
            add(branch + '_activation', ids, [n], scalar=n * (6 if extra_up else 4),
                special={'tanh': n * (2 if extra_up else 1), 'sigmoid': n},
                note='FP32 beta*tanh(gate/beta)*sigmoid(gate)*up; configured up transform adds divide, tanh and multiply.')
        add('routed_probability_multiply', layers, [m * k, r], scalar=m * k * r,
            note='Reference weights the latent expert OUTPUT after down projection, then reduces across top-k.')
        add('routed_combine', layers, [m, r], scalar=m * (k - 1) * r,
            note='Logical sum of k weighted outputs uses k-1 additions; backend reduction scheduling is unspecified.')
        if g['latent_norm']:
            add('latent_rmsnorm', layers, [m, r], scalar=m * (4 * r + 1), special={'rsqrt': m},
                note='Square, sum, mean division, epsilon, normalized output and learned scale; FP32 reduction, final scale after dtype cast.')
    else:
        return {}  # Qwen has a complete non-matrix ledger in its forward adapter.
    add('shared_output_add', layers, [m, h], scalar=m * h)
    special_total = Counter()
    for operation in operations:
        special_total.update(operation['special_ops'])
    return dict(non_matrix_operations=operations,
                non_matrix_summary=dict(scalar_flops=sum(op['scalar_flops'] for op in operations),
                                        special_ops=dict(special_total)),
                non_matrix_scope='FFN floating-point arithmetic only. Special functions are opaque primitives; dispatch/indexing, casts, allocation and memory traffic remain separate. No full-model latency claim.')
