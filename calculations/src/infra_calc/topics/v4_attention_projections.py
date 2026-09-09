"""One V4 attention periphery, unrounded reference; core work is excluded."""

import math
from infra_calc.sources import model_config, provenance
from infra_calc.units import positive_int


def mv(weight, x):
    return [sum(a * b for a, b in zip(row, x)) for row in weight]


def mv_vjp(weight, x, gradient):
    dx = [
        sum(gradient[j] * weight[j][i] for j in range(len(weight)))
        for i in range(len(x))
    ]
    dw = [[g * v for v in x] for g in gradient]
    return dx, dw


def rms(x, gamma=None, epsilon=1e-6):
    r = 1 / math.sqrt(sum(v * v for v in x) / len(x) + epsilon)
    normalized = [v * r for v in x]
    return [
        v * (gamma[i] if gamma is not None else 1) for i, v in enumerate(normalized)
    ], (normalized, r)


def rms_vjp(state, gradient, gamma=None):
    normalized, r = state
    g = [v * (gamma[i] if gamma is not None else 1) for i, v in enumerate(gradient)]
    mean = sum(a * b for a, b in zip(g, normalized)) / len(g)
    dx = [r * (v - y * mean) for v, y in zip(g, normalized)]
    return dx, (
        [a * b for a, b in zip(gradient, normalized)] if gamma is not None else None
    )


def rotate(x, angles, inverse=False):
    result = x[:]
    start = len(x) - 2 * len(angles)
    for j, angle in enumerate(angles):
        c, s = math.cos(angle), math.sin(angle) * (-1 if inverse else 1)
        i = start + 2 * j
        a, b = x[i : i + 2]
        result[i], result[i + 1] = a * c - b * s, a * s + b * c
    return result


def reference(
    x,
    weights,
    q_gamma,
    kv_gamma,
    heads,
    groups,
    angles,
    core,
    core_vjp,
    upstream,
    epsilon=1e-6,
):
    """One row; differentiable core callback is explicit, its work is not ledgered."""
    qa = mv(weights["wq_a"], x)
    qr, qstate = rms(qa, q_gamma, epsilon)
    qb = mv(weights["wq_b"], qr)
    d = len(qb) // heads
    qstates = []
    q = []
    for head in range(heads):
        unit, state = rms(qb[head * d : (head + 1) * d], epsilon=epsilon)
        qstates.append(state)
        q.append(rotate(unit, angles))
    kva = mv(weights["wkv"], x)
    kvunit, kvstate = rms(kva, kv_gamma, epsilon)
    kv = rotate(kvunit, angles)
    o = core(q, kv)
    derot = [rotate(row, angles, True) for row in o]
    flat = [v for row in derot for v in row]
    group_width = len(flat) // groups
    grouped = [
        mv(weights["wo_a"][g], flat[g * group_width : (g + 1) * group_width])
        for g in range(groups)
    ]
    output_input = [v for row in grouped for v in row]
    output = mv(weights["wo_b"], output_input)
    dmid, dwob = mv_vjp(weights["wo_b"], output_input, upstream)
    rank = len(grouped[0])
    dflat = []
    dwoa = []
    for g in range(groups):
        values, dweight = mv_vjp(
            weights["wo_a"][g],
            flat[g * group_width : (g + 1) * group_width],
            dmid[g * rank : (g + 1) * rank],
        )
        dflat.extend(values)
        dwoa.append(dweight)
    do = [rotate(dflat[h * d : (h + 1) * d], angles) for h in range(heads)]
    dq, dkv = core_vjp(q, kv, do)
    dqb = []
    for h in range(heads):
        values, _ = rms_vjp(qstates[h], rotate(dq[h], angles, True))
        dqb.extend(values)
    dqr, dwqb = mv_vjp(weights["wq_b"], qr, dqb)
    dqa, dqgamma = rms_vjp(qstate, dqr, q_gamma)
    dxq, dwqa = mv_vjp(weights["wq_a"], x, dqa)
    dkva, dkvgamma = rms_vjp(kvstate, rotate(dkv, angles, True), kv_gamma)
    dxkv, dwkv = mv_vjp(weights["wkv"], x, dkva)
    return dict(
        output=output,
        dx=[a + b for a, b in zip(dxq, dxkv)],
        dweights=dict(wq_a=dwqa, wq_b=dwqb, wkv=dwkv, wo_a=dwoa, wo_b=dwob),
        dq_gamma=dqgamma,
        dkv_gamma=dkvgamma,
        core_output_gradient=do,
    )


def calculate(batch=1, tokens=128):
    positive_int(batch, "batch")
    positive_int(tokens, "tokens")
    cfg = model_config("deepseek-v4-flash", reference=True)
    r = batch * tokens
    h = cfg["dim"]
    heads = cfg["n_heads"]
    d = cfg["head_dim"]
    q = cfg["q_lora_rank"]
    g = cfg["o_groups"]
    o = cfg["o_lora_rank"]
    rd = cfg["rope_head_dim"]
    if heads * d % g:
        raise ValueError("Grouped output projection dimension must divide exactly")
    matrices = []
    for name, input_width, output_width, groups in [
        ("wq_a", h, q, 1),
        ("wq_b", q, heads * d, 1),
        ("wkv", h, d, 1),
        ("wo_a", heads * d // g, o, g),
        ("wo_b", g * o, h, 1),
    ]:
        matrices.append(
            dict(
                name=name,
                input_shape=[r, groups, input_width],
                weight_shape=[groups, output_width, input_width],
                output_shape=[r, groups, output_width],
                forward_flops=2 * r * groups * input_width * output_width,
                backward_dx_flops=2 * r * groups * input_width * output_width,
                backward_dw_flops=2 * r * groups * input_width * output_width,
            )
        )
    norms = dict(
        weighted_q_rank=dict(
            forward_scalar_flops=r * (4 * q + 1),
            backward_scalar_flops=7 * r * q + q * (r - 1),
            rsqrt_calls=r,
        ),
        weighted_kv=dict(
            forward_scalar_flops=r * (4 * d + 1),
            backward_scalar_flops=7 * r * d + d * (r - 1),
            rsqrt_calls=r,
        ),
        unweighted_q_heads=dict(
            forward_scalar_flops=r * heads * (3 * d + 1),
            backward_scalar_flops=5 * r * heads * d,
            rsqrt_calls=r * heads,
        ),
    )
    rope = 3 * r * rd * (2 * heads + 1)
    saved = dict(
        x_shared_q_kv_fp32=4 * r * h,
        q_rank_normalized_before_gamma_fp32=4 * r * q,
        q_rank_inverse_rms_fp32=4 * r,
        q_rank_output_for_wqb_fp32=4 * r * q,
        q_head_normalized_before_rope_fp32=4 * r * heads * d,
        q_head_inverse_rms_fp32=4 * r * heads,
        kv_normalized_before_gamma_fp32=4 * r * d,
        kv_inverse_rms_fp32=4 * r,
        derotated_core_output_for_woa_fp32=4 * r * heads * d,
        grouped_output_for_wob_fp32=4 * r * g * o,
    )
    return dict(
        schema_version=1,
        calculation="v4-attention-periphery-training-reference",
        model="deepseek-v4-flash",
        scenario=dict(batch=batch, tokens=tokens),
        sources=provenance("deepseek-v4-flash"),
        dimensions=dict(
            rows=r,
            hidden=h,
            heads=heads,
            head_dim=d,
            q_rank=q,
            groups=g,
            o_rank=o,
            rope_dim=rd,
        ),
        matrices=matrices,
        norms=norms,
        rope=dict(
            forward_scalar_flops=rope,
            backward_scalar_flops=rope,
            frequency_table_setup_included=False,
            reference_pair_order="adjacent real/imag pairs, only final rope_dim coordinates",
            source_forward_directions=dict(
                q="forward", kv="forward", output="conjugate"
            ),
            backward="transpose rotation; frequencies are fixed constants",
        ),
        gradient_join=dict(
            x_q_and_kv_additions=r * h, qr_indexer_branch_included=False
        ),
        totals=dict(
            forward_matrix_flops=sum(a["forward_flops"] for a in matrices),
            backward_matrix_flops=sum(
                a["backward_dx_flops"] + a["backward_dw_flops"] for a in matrices
            ),
            forward_scalar_flops=sum(a["forward_scalar_flops"] for a in norms.values())
            + rope,
            backward_scalar_flops=sum(
                a["backward_scalar_flops"] for a in norms.values()
            )
            + rope
            + r * h,
            forward_rsqrt_calls=sum(a["rsqrt_calls"] for a in norms.values()),
        ),
        saved_forward_boundary=dict(
            buffers=saved,
            total_bytes=sum(saved.values()),
            fixed_frequency_constants_fp32_bytes=4 * tokens * rd,
            exclusions=[
                "core Q/KV/probability state already belongs to core ledger",
                "weight and parameter-gradient owners",
                "core output original and core upstream temporaries",
                "frequency construction, cast buffers, backward temporary gradients, allocator workspace",
            ],
            scope="one periphery saved subset; no independent K/V copies",
        ),
        lifecycle=[
            dict(
                event="input_projections",
                retains=[
                    "shared x",
                    "q-rank normalized values/r and weighted output",
                    "head normalized values/r",
                    "KV normalized values/r",
                ],
            ),
            dict(
                event="q_kv_rope",
                transfers=["Q and KV to caller core"],
                note="those core-owned tensors excluded here",
            ),
            dict(event="core_forward", scope="external work/state excluded"),
            dict(
                event="output_inverse_rope_and_projections",
                retains=["derotated core output", "grouped output"],
            ),
            dict(
                event="output_backward",
                creates=["dO supplied to core_vjp"],
                releases=["derotated core output", "grouped output"],
            ),
            dict(event="core_vjp", scope="external work/state excluded"),
            dict(
                event="input_backward",
                creates=["dXq", "dXkv", "projection and norm parameter gradients"],
                releases=["input projections saved subset"],
            ),
            dict(event="join_dx", creates=["dX"]),
        ],
        coverage=dict(
            five_projection_vjps=True,
            weighted_and_head_rms_vjps=True,
            rope_vjps=True,
            core_work_included=False,
            indexer_qr_gradient_included=False,
            compressor_input_gradient_included=False,
            quantized_kernel_equivalence=False,
            complete_v4_training=False,
            cast_surrogate_gradient=None,
            actual_peak_bytes=None,
        ),
        assumptions=[
            "One source-shaped attention periphery, not all layers. The no-compressor/no-indexer path is realized by source ratio=0 layers; source-shaped projections repeat elsewhere but extra branch gradients are not covered.",
            "Unrounded real math with FP32 saved-state contract, FP64 numerical validation. Source FP8 projection quantizers, BF16 wo_a, norm output casts and RoPE in-place casts are not assigned invented STE rules.",
            "Matrix work is derived separately for forward, dX and dW. Norm reductions across rows and X branch addition are separate scalar work.",
            "RoPE fixed complex frequencies use six real FLOPs per pair. No sin/cos/table setup is multiplied into forward/backward; source constants are caller-supplied.",
            "Saved values are FP32 mathematical references, not a claimed low-precision training schedule or runtime peak. No core work or core saved buffer is counted again.",
        ],
    )


def markdown(result):
    lines = [
        "# V4 attention 外围投影训练参考",
        "",
        "包含五组投影、两种加权 RMSNorm、逐 head RMS 与正/逆 RoPE。排除 core、indexer 和 compressor 工作。",
        "",
        "固定源低精度转换未复现；保存项为去舍入参考子集，不是实际训练峰值。",
        "",
        "| 字段 | 值 |",
        "|---|---|",
    ]

    def visit(value, path):
        if isinstance(value, dict) and value:
            for key, child in value.items():
                visit(child, f"{path}.{key}" if path else key)
        elif isinstance(value, list) and value:
            for i, child in enumerate(value):
                visit(child, f"{path}[{i}]")
        else:
            text = "unknown (null)" if value is None else str(value)
            lines.append(
                f'| {path} | {text.replace(chr(10),"<br>").replace("|","&#124;")} |'
            )

    visit(result, "")
    return "\n".join(lines) + "\n"
