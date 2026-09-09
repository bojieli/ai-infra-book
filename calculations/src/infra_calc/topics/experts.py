"""Architecture-specific FFN matrix ledger, independent of full attention graphs.

This accounts for routed, shared, dense, router and latent projection matrices.
Nonlinear routing, activation and normalization arithmetic are returned in a
separate ledger. Reference dispatch operands are a third ledger; real memory traffic remains unknown.
Matrix byte counts use an explicit uniform teaching format.
"""
from ..models.qwen3_moe import routing_counts
from ..sources import model_config, provenance
from ..units import positive_int
from . import expert_arithmetic, expert_dispatch, v4_expert_format


def geometry(model: str) -> dict:
    config = model_config(model)
    if config['model_type'] == 'qwen3_moe':
        if config.get('mlp_only_layers') or config.get('decoder_sparse_step', 1) != 1:
            raise ValueError('Unsupported Qwen MoE layer pattern')
        layers = list(range(config['num_hidden_layers']))
        return dict(hidden=config['hidden_size'], expert_hidden=config['hidden_size'],
                    intermediate=config['moe_intermediate_size'], experts=config['num_experts'],
                    top_k=config['num_experts_per_tok'], shared=0, moe_layers=layers, dense_layers=[],
                    dense_intermediate=0, hash_layers=[], latent=False, latent_norm=False,
                    router_bias_layers=[], router_compute_input='activation dtype', router_accumulator='unspecified',
                    activation=config['hidden_act'], selection='softmax_topk', vocab=config['vocab_size'])
    if model in ('deepseek-v4-flash', 'deepseek-v4-pro'):
        config = model_config(model, reference=True)
        layers = list(range(config['n_layers']))
        hashes = list(range(config['n_hash_layers']))
        return dict(hidden=config['dim'], expert_hidden=config['dim'],
                    intermediate=config['moe_inter_dim'], experts=config['n_routed_experts'],
                    top_k=config['n_activated_experts'], shared=config['n_shared_experts'],
                    moe_layers=layers, dense_layers=[], dense_intermediate=0, hash_layers=hashes,
                    latent=False, latent_norm=False, router_bias_layers=layers[len(hashes):],
                    router_compute_input='FP32', router_accumulator='FP32', activation='clipped_swiglu',
                    selection=config['score_func'] + '_hash_or_bias_topk', vocab=config['vocab_size'])
    if model == 'kimi-k3':
        config = config['text_config']
        layers = list(range(config['num_hidden_layers']))
        moe = [i for i in layers if i >= config['first_k_dense_replace'] and i % config['moe_layer_freq'] == 0]
        return dict(hidden=config['hidden_size'], expert_hidden=config['routed_expert_hidden_size'],
                    intermediate=config['moe_intermediate_size'], experts=config['num_experts'],
                    top_k=config['num_experts_per_token'], shared=config['num_shared_experts'],
                    moe_layers=moe, dense_layers=[i for i in layers if i not in moe],
                    dense_intermediate=config['intermediate_size'], hash_layers=[], latent=True,
                    latent_norm=config['latent_moe_use_norm'], router_bias_layers=moe,
                    router_compute_input='FP32', router_accumulator='FP32', activation=config['hidden_act'],
                    selection=config['moe_router_activation_func'] + '_bias_topk', vocab=config['vocab_size'])
    raise ValueError(f'Expert matrix adapter not implemented for {model}')


def calculate(model: str, batch: int = 64, tokens: int = 1, routing: str = 'balanced',
              counts: list[int] | None = None, element_bytes: int = 2) -> dict:
    for key, value in [('batch', batch), ('tokens', tokens), ('element_bytes', element_bytes)]:
        positive_int(value, key)
    g = geometry(model)
    m, h, r, f = batch * tokens, g['hidden'], g['expert_hidden'], g['intermediate']
    hist = routing_counts(m, g['experts'], g['top_k'], routing, counts)
    union, assignments, layers = sum(n > 0 for n in hist), sum(hist), g['moe_layers']
    matrices = []

    def add(name, category, nrows, inputs, outputs, layer_ids, stored_copies=1, visited_copies=1):
        """Grouped rows sum to nrows; weight storage and visited copies differ."""
        matrices.append(dict(name=name, category=category, layer_ids=layer_ids,
                             rows_summed_per_layer=nrows, input_width=inputs, output_width=outputs,
                             weight_storage_each=[outputs, inputs], stored_copies_per_layer=stored_copies,
                             visited_copies_per_layer=visited_copies,
                             parameters=len(layer_ids) * stored_copies * inputs * outputs,
                             matrix_flops=2 * len(layer_ids) * nrows * inputs * outputs,
                             uniform_weight_payload_bytes=len(layer_ids) * visited_copies * inputs * outputs * element_bytes,
                             uniform_activation_read_bytes=len(layer_ids) * nrows * inputs * element_bytes,
                             uniform_activation_write_bytes=len(layer_ids) * nrows * outputs * element_bytes))

    add('router', 'router', m, h, g['experts'], layers)
    if g['latent']:
        add('routed_expert_down_proj', 'latent', m, h, r, layers)
    for name, inputs, outputs in [('gate', r, f), ('up', r, f), ('down', f, r)]:
        add('routed_' + name, 'routed', assignments, inputs, outputs, layers, g['experts'], union)
    if g['latent']:
        add('routed_expert_up_proj', 'latent', m, r, h, layers)
    if g['shared']:
        # K3 concatenates shared intermediate channels; it stays in full H,
        # unlike the routed experts which operate in latent R.
        shared_width = g['shared'] * f
        for name, inputs, outputs in [('gate', h, shared_width), ('up', h, shared_width), ('down', shared_width, h)]:
            add('shared_' + name, 'shared', m, inputs, outputs, layers)
    if g['dense_layers']:
        dense_width = g['dense_intermediate']
        for name, inputs, outputs in [('gate', h, dense_width), ('up', h, dense_width), ('down', dense_width, h)]:
            add('dense_' + name, 'dense', m, inputs, outputs, g['dense_layers'])
    summary = dict(ffn_matrix_parameters=sum(row['parameters'] for row in matrices),
                   ffn_matrix_flops=sum(row['matrix_flops'] for row in matrices),
                   uniform_matrix_resident_bytes=sum(row['parameters'] for row in matrices) * element_bytes,
                   uniform_matrix_weight_payload_bytes=sum(row['uniform_weight_payload_bytes'] for row in matrices),
                   assignments_per_moe_layer=assignments, expert_union_per_moe_layer=union,
                   hash_lookup_resident_int32_bytes=len(g['hash_layers']) * g['vocab'] * g['top_k'] * 4,
                   hash_lookup_selected_int32_bytes=len(g['hash_layers']) * m * g['top_k'] * 4,
                   router_bias_elements=len(g['router_bias_layers']) * g['experts'],
                   latent_norm_scale_elements=len(layers) * r if g['latent_norm'] else 0)
    for category in ('routed', 'shared', 'dense', 'latent', 'router'):
        summary[category + '_matrix_flops'] = sum(row['matrix_flops'] for row in matrices if row['category'] == category)
    return dict(**expert_arithmetic.calculate(model, g, m),
                **v4_expert_format.calculate(model, g, hist),
                **expert_dispatch.calculate(model, g, m, hist, element_bytes),
                schema_version=1, calculation='expert-matrix-ledger', model=model,
                scenario=dict(batch=batch, tokens=tokens, routing='explicit_histogram' if counts is not None else routing,
                              element_bytes=element_bytes, tokens_per_expert=hist),
                sources=provenance(model), geometry=g, matrices=matrices, summary=summary,
                expert_matrices=[dict(expert=e, tokens=n,
                                      gate_and_up_each=dict(A=[n, r], W_math=[r, f], Y=[n, f]),
                                      down=dict(A=[n, f], W_math=[f, r], Y=[n, r])) for e, n in enumerate(hist)],
                assumptions=[
                    '矩阵字段只计 FFN GEMM；V4/K3 的激活、归一化、路由及合并算术由 non_matrix_operations 另列。参考 dispatch 载荷由 dispatch_operations 单列；排除注意力、mHC/AttnRes、MTP、视觉与通信。',
                    '统一 element_bytes 是教学格式；不代表 V4 FP4/FP8 或 K3 MXFP4 的实际存储、计算精度、scale/metadata 或 HBM 流量。',
                    'V4/K3 router 参考实现以 FP32 输入和权重计算；uniform 字节字段仅表示统一格式的对照载荷，不可直接映射 router Roofline。',
                    '每个 MoE 层使用同一声明直方图，无 padding/token drop；每个访问专家的权重按本层读一次。不是实际路由或质量结论。',
                    'V4 前三个 hash 层仍计算全部 router logits；tid2eid 的 int32 容量和选中条目读取单列，不计作浮点参数。未下载实际映射权重，因此直方图仅是条件输入。',
                    'K3 router 和 shared 分支保持原始 hidden_size；只有 routed 分支经过降维、专家、归一化及升维。dense 首层单列。',
                    'matrix_parameters 不含 router bias 和 latent norm scale；它们另列元素数，未与不同格式的字节混加。',
                ])
