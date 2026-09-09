"""Full fixed-selection MoE mathematical VJP, one Flash MoE layer."""

from . import v4_attention_projections as ops
from . import v4_training_primitives as primitive
from ..models.qwen3_moe import routing_counts
from ..sources import model_config, provenance
from ..units import positive_int


def expert_vjp(x, weights, upstream, route=None, limit=10.0):
    rawg = ops.mv(weights["w1"], x)
    rawu = ops.mv(weights["w3"], x)
    if any(v == limit for v in rawg) or any(abs(v) == limit for v in rawu):
        raise ValueError("Clipping kink points are excluded from this smooth fixture")
    g = [min(v, limit) for v in rawg]
    u = [max(-limit, min(v, limit)) for v in rawu]
    s = [primitive.sigmoid(v) for v in g]
    a = [v * w for v, w in zip(g, s)]
    product = [v * w for v, w in zip(a, u)]
    down = product if route is None else [route * v for v in product]
    out = ops.mv(weights["w2"], down)
    dz, dw2 = ops.mv_vjp(weights["w2"], down, upstream)
    droute = None if route is None else sum(v * w for v, w in zip(dz, product))
    dp = dz if route is None else [route * v for v in dz]
    da = [v * w for v, w in zip(dp, u)]
    du = [v * w for v, w in zip(dp, a)]
    dg = [v * (sig + act * (1 - sig)) for v, sig, act in zip(da, s, a)]
    dg = [v if original < limit else 0.0 for v, original in zip(dg, rawg)]
    du = [v if abs(original) < limit else 0.0 for v, original in zip(du, rawu)]
    dxg, dw1 = ops.mv_vjp(weights["w1"], x, dg)
    dxu, dw3 = ops.mv_vjp(weights["w3"], x, du)
    return dict(
        output=out,
        dx=[v + w for v, w in zip(dxg, dxu)],
        dweights=dict(w1=dw1, w2=dw2, w3=dw3),
        droute=droute,
    )


def reference(
    x, router_weight, experts, shared, indices, upstream, route_scale=1.5, limit=10.0
):
    """One token, unique fixed selected IDs; inactive expert gradients explicitly zero."""
    if any(
        isinstance(i, bool) or not isinstance(i, int) or i < 0 or i >= len(experts)
        for i in indices
    ):
        raise ValueError("Selected expert IDs must be valid nonnegative integers")
    logits = ops.mv(router_weight, x)
    route, _ = primitive.router_vjp(logits, indices, [0.0] * len(indices), route_scale)
    output = [0.0] * len(x)
    dx = [0.0] * len(x)
    grads = []
    for expert in experts:
        grads.append(
            {
                name: [[0.0] * len(row) for row in matrix]
                for name, matrix in expert.items()
            }
        )
    route_grad = []
    for i, weight in zip(indices, route):
        result = expert_vjp(x, experts[i], upstream, weight, limit)
        output = [a + b for a, b in zip(output, result["output"])]
        dx = [a + b for a, b in zip(dx, result["dx"])]
        grads[i] = result["dweights"]
        route_grad.append(result["droute"])
    common = expert_vjp(x, shared, upstream, limit=limit)
    output = [a + b for a, b in zip(output, common["output"])]
    dx = [a + b for a, b in zip(dx, common["dx"])]
    _, dlogits = primitive.router_vjp(logits, indices, route_grad, route_scale)
    dxgate, dgate = ops.mv_vjp(router_weight, x, dlogits)
    dx = [a + b for a, b in zip(dx, dxgate)]
    return dict(
        output=output,
        dx=dx,
        drouter_weight=dgate,
        drouter_logits=dlogits,
        dexperts=grads,
        dshared=common["dweights"],
        selected_route_weights=route,
        selected_route_weight_gradients=route_grad,
    )


def calculate(batch=1, tokens=128, layer_id=3, routing="balanced", counts=None):
    positive_int(batch, "batch")
    positive_int(tokens, "tokens")
    positive_int(layer_id, "layer_id", allow_zero=True)
    c = model_config("deepseek-v4-flash", reference=True)
    if layer_id >= c["n_layers"]:
        raise ValueError("layer_id exceeds fixed Flash layers")
    r = batch * tokens
    h = c["dim"]
    f = c["moe_inter_dim"]
    e = c["n_routed_experts"]
    k = c["n_activated_experts"]
    a = r * k
    hashed = layer_id < c["n_hash_layers"]
    hist = routing_counts(r, e, k, routing, counts)
    visited = sum(n > 0 for n in hist)
    expert_rows = []
    for i, n in enumerate(hist):
        expert_rows.append(
            dict(
                expert=i,
                assigned_rows=n,
                w1_input=[n, h],
                w1_weight=[f, h],
                w3_input=[n, h],
                w3_weight=[f, h],
                w2_input=[n, f],
                w2_weight=[h, f],
                forward_matrix_flops=6 * n * h * f,
                backward_matrix_flops=12 * n * h * f,
            )
        )
    router = dict(
        forward_matrix_flops=2 * r * h * e,
        backward_matrix_flops=4 * r * h * e,
        forward_scalar_flops=r * (3 * k - 1) + (0 if hashed else r * e),
        backward_scalar_flops=r * (5 * k - 1 + 3 * e),
        forward_softplus_calls=r * e,
        forward_sqrt_calls=r * e,
        backward_sigmoid_calls=r * e,
        selection="fixed hash-table branch" if hashed else "fixed bias-topk branch",
        selection_bias_continuous_main_loss_gradient=(
            "not present"
            if hashed
            else "zero inside fixed-selection region; bias update and auxiliary losses excluded"
        ),
    )
    scalar = dict(
        expert_forward_silu_and_product_flops=2 * (a + r) * f,
        routed_forward_weight_product_flops=a * f,
        forward_output_accumulation_flops=(a + r) * h,
        expert_backward_swiglu_flops=6 * (a + r) * f,
        routed_weight_backward_flops=a * (3 * f - 1),
        backward_input_branches_and_scatter_flops=(2 * a + 3 * r) * h,
    )
    parameters = dict(
        router_weight=e * h,
        routed_expert_weights=e * 3 * h * f,
        shared_expert_weights=3 * h * f,
        selection_bias=0 if hashed else e,
        nontrainable_hash_table_int32_elements=c["vocab_size"] * k if hashed else 0,
        visited_expert_gradient_parameters=visited * 3 * h * f,
        unvisited_expert_main_loss_gradient="zero for this fixed-selection microbatch, not absent parameters or an optimizer-update assertion",
    )
    saved = dict(
        x_shared_fp32=4 * r * h,
        selected_ids_source_dtype_bytes=(4 if hashed else 8) * a,
        dispatch_token_slot_int64=16 * a,
        router_logits_fp32=4 * r * e,
        router_sqrtsoftplus_scores_fp32=4 * r * e,
        selected_normalized_probabilities_fp32=4 * a,
        selected_scaled_weights_fp32=4 * a,
        selected_denominator_fp32=4 * r,
        expert_a_sigmoid_u_fp32=4 * 3 * (a + r) * f,
        expert_unweighted_swiglu_product_fp32=4 * (a + r) * f,
        routed_weighted_down_input_fp32=4 * a * f,
        clipping_masks_bool=2 * (a + r) * f,
    )
    return dict(
        schema_version=1,
        calculation="v4-fixed-selection-moe-training",
        model="deepseek-v4-flash",
        scenario=dict(
            batch=batch,
            tokens=tokens,
            layer_id=layer_id,
            routing=routing,
            counts=counts,
        ),
        sources=provenance("deepseek-v4-flash"),
        config_geometry=dict(
            hidden=h,
            intermediate=f,
            experts=e,
            top_k=k,
            shared_experts=c["n_shared_experts"],
            score_func=c["score_func"],
            route_scale=c["route_scale"],
            clip_limit=c["swiglu_limit"],
        ),
        routing_histogram=hist,
        routing_scope=dict(
            assignments=a,
            visited_experts=visited,
            scope="conditional distinct-ID histogram, not observed production routing or verified checkpoint tid2eid",
            construction=(
                "token i selects (i*K+j)%E"
                if counts is None and routing == "balanced"
                else (
                    "all tokens select first K experts"
                    if counts is None
                    else "caller histogram, checked sum/row-cap; no token-ID assignment inferred"
                )
            ),
        ),
        router=router,
        routed_experts=expert_rows,
        shared=dict(
            rows=r,
            forward_matrix_flops=6 * r * h * f,
            backward_matrix_flops=12 * r * h * f,
            weight_shapes=dict(w1=[f, h], w3=[f, h], w2=[h, f]),
        ),
        scalar=scalar,
        nonflop_operations=dict(
            forward_expert_sigmoid_calls=(a + r) * f,
            forward_clamp_comparisons=3 * (a + r) * f,
            backward_clamp_mask_selects=2 * (a + r) * f,
            topk_selection_rows=0 if hashed else r,
            hash_lookup_entries=a if hashed else 0,
            selected_score_gather_entries=a,
            bincount_assignment_entries=a,
            source_where_candidate_tests=visited * r * k,
        ),
        selected_id_dtype="int32 hash lookup" if hashed else "int64 torch.topk",
        parameters=parameters,
        saved_forward_boundary=dict(
            buffers=saved,
            total_bytes=sum(saved.values()),
            scope="one MoE-layer FP32 mathematical save strategy; gathered expert X is an indexed view of shared X, no extra persistent copies",
            reuse=[
                "shared unweighted product is already its down-projection input",
                "routed unweighted product retained for route-weight VJP, distinct from weighted down input",
                "router primitive scalar/weight VJP formulas included exactly once, not an added 43-layer primitive result",
            ],
        ),
        data_ops=dict(
            forward_output_zero_bytes=4 * r * h,
            backward_input_gradient_zero_bytes=4 * r * h,
            scope="declared zeros only; not full traffic/gradient allocation",
        ),
        lifecycle=[
            dict(
                event="router",
                retains=[
                    "X",
                    "logits",
                    "sqrtsoftplus scores",
                    "selected p/weight/denominator",
                    "indices",
                ],
            ),
            dict(
                event="expert_forward",
                retains=[
                    "a/s/u",
                    "clipping masks",
                    "unweighted product",
                    "routed weighted down input",
                ],
            ),
            dict(
                event="sum_outputs",
                scope="no extra learned combining weight beyond F-wide route weight",
            ),
            dict(
                event="expert_backward",
                creates=[
                    "expert parameter/input gradients",
                    "selected route-weight adjoints",
                ],
            ),
            dict(event="router_vjp", creates=["dlogits", "router dW/dX"]),
            dict(event="join_dx", creates=["combined X gradient"]),
        ],
        totals=dict(
            forward_matrix_flops=2 * r * h * e + 6 * (a + r) * h * f,
            backward_matrix_flops=4 * r * h * e + 12 * (a + r) * h * f,
            forward_scalar_flops=router["forward_scalar_flops"]
            + sum(v for key, v in scalar.items() if "forward_" in key),
            backward_scalar_flops=router["backward_scalar_flops"]
            + sum(v for key, v in scalar.items() if "backward_" in key),
        ),
        quantization_contract=dict(
            official_report="Expert QAT FP32 master -> MXFP4 -> FP8 forward; backward with the same FP8 weights, STE to FP32 master disclosed in report section5.2.1",
            reference="unrounded full precision mathematical graph; does not simulate quantization, cast or claim identical gradients to disclosed QAT",
            unresolved=[
                "exact quantizer clip/scale derivatives and implementation",
                "kernel-specific gradient precision",
                "complete optimizer and auxiliary balancing/indexer/MTP objectives",
            ],
        ),
        coverage=dict(
            full_fixed_selection_moe_main_loss_vjp=True,
            router_score_gradient_included=True,
            shared_and_routed_experts=True,
            selection_boundary_derivative=False,
            qat_numerical_equivalence=False,
            complete_v4_training=False,
            actual_peak_bytes=None,
        ),
        assumptions=[
            "One actual-geometry Flash MoE layer. World size1 removes all_reduce; distributed communication and per-rank expert placement are outside this contract.",
            "Fixed unique selections are a smooth local branch; hash layers still compute router scores and normalized weights. Topk/hash/bias update objectives are not silently differentiated or declared untrainable.",
            "Source clips gate above +limit only and up to [-limit,+limit]. Saved masks select backward gradients; exact kink points are excluded from numerical fixtures.",
            "Source route weight multiplies F-wide activation before w2. This position is preserved; no extra H-wide route multiplication or duplicate route VJP is counted.",
            "Matrix each dX/dW is derived from its own shape, not inference FLOPs times3. Unvisited expert matrix work is zero while stored parameters remain present.",
            "Save strategy retains both unweighted product for route derivative and weighted down input for w2 dW, preventing hidden recomputation. FP32 values/boolean masks are mathematical reference storage, not actual allocator peak.",
        ],
    )


def markdown(result):
    lines = [
        "# V4-Flash 固定选择 MoE 训练参考",
        "",
        "一个真实配置MoE层的shared/routed专家、router分数归一化与输入联合VJP；histogram为声明条件，不是实测。",
        "",
        "离散选择边界、辅助目标、量化逐值等价和完整训练峰值不在此账。",
        "",
        "| 字段 | 值 |",
        "|---|---|",
    ]

    def visit(value, path):
        if isinstance(value, dict) and value:
            for k, v in value.items():
                visit(v, f"{path}.{k}" if path else k)
        elif isinstance(value, list) and value:
            for i, v in enumerate(value):
                visit(v, f"{path}[{i}]")
        else:
            text = "unknown (null)" if value is None else str(value)
            lines.append(
                f'| {path} | {text.replace(chr(10),"<br>").replace("|","&#124;")} |'
            )

    visit(result, "")
    return "\n".join(lines) + "\n"
