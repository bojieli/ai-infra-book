"""Functional mHC wrapper VJP with an explicitly supplied inner-function VJP."""

import importlib.util
import math
from pathlib import Path

from infra_calc.sources import model_config, provenance
from infra_calc.units import positive_int

PRIMITIVE = (
    Path(__file__).resolve().parents[2]
    / "v4-training-reference/src/infra_calc/topics/v4_training_primitives.py"
)
spec = importlib.util.spec_from_file_location("frozen_v4_primitives", PRIMITIVE)
primitive = importlib.util.module_from_spec(spec)
spec.loader.exec_module(primitive)


def forward(
    x, weight, scale, base, inner, iterations=20, epsilon=1e-6, norm_epsilon=1e-6
):
    """One row. `inner(y)` is the mathematical sublayer, not a claimed V4 kernel."""
    c, h = len(x), len(x[0])
    flat = [v for row in x for v in row]
    r = 1 / math.sqrt(sum(v * v for v in flat) / len(flat) + norm_epsilon)
    linear = [sum(a * b for a, b in zip(row, flat)) for row in weight]
    mixes = [v * r for v in linear]
    split = primitive.sinkhorn_vjp(
        mixes,
        scale,
        base,
        [0.0] * c,
        [0.0] * c,
        [[0.0] * c for _ in range(c)],
        c,
        iterations,
        epsilon,
    )
    pre, post, comb = split["pre"], split["post"], split["comb"]
    y = [sum(pre[i] * x[i][k] for i in range(c)) for k in range(h)]
    z = inner(y)
    out = [
        [post[j] * z[k] + sum(comb[i][j] * x[i][k] for i in range(c)) for k in range(h)]
        for j in range(c)
    ]
    return dict(
        output=out,
        x=x,
        flat=flat,
        r=r,
        linear=linear,
        mixes=mixes,
        pre=pre,
        post=post,
        comb=comb,
        y=y,
        z=z,
    )


def vjp(
    x,
    weight,
    scale,
    base,
    inner,
    inner_vjp,
    upstream,
    iterations=20,
    epsilon=1e-6,
    norm_epsilon=1e-6,
):
    """Compose both mHC endpoints through a caller-provided inner VJP."""
    state = forward(x, weight, scale, base, inner, iterations, epsilon, norm_epsilon)
    c, h = len(x), len(x[0])
    z, comb, post = state["z"], state["comb"], state["post"]
    dz = [sum(upstream[j][k] * post[j] for j in range(c)) for k in range(h)]
    dpost = [sum(upstream[j][k] * z[k] for k in range(h)) for j in range(c)]
    dcomb = [
        [sum(upstream[j][k] * x[i][k] for k in range(h)) for j in range(c)]
        for i in range(c)
    ]
    dx_residual = [
        [sum(upstream[j][k] * comb[i][j] for j in range(c)) for k in range(h)]
        for i in range(c)
    ]
    dy = inner_vjp(state["y"], dz)
    dpre = [sum(dy[k] * x[i][k] for k in range(h)) for i in range(c)]
    dx_pre = [[state["pre"][i] * dy[k] for k in range(h)] for i in range(c)]
    split = primitive.sinkhorn_vjp(
        state["mixes"], scale, base, dpre, dpost, dcomb, c, iterations, epsilon
    )
    dm = split["dmixes"]
    da = [g * state["r"] for g in dm]
    dr = sum(g * a for g, a in zip(dm, state["linear"]))
    dweight = [[g * v for v in state["flat"]] for g in da]
    dx_linear = [
        sum(da[j] * weight[j][i] for j in range(len(weight))) for i in range(c * h)
    ]
    # r=(mean(x²)+eps)^(-1/2); derivative coefficient is -dr*r³/N.
    coefficient = -(dr * state["r"] * state["r"] * state["r"]) / (c * h)
    dx_norm = [coefficient * v for v in state["flat"]]
    dx = [
        [
            dx_residual[i][k] + dx_pre[i][k] + dx_linear[i * h + k] + dx_norm[i * h + k]
            for k in range(h)
        ]
        for i in range(c)
    ]
    return dict(
        output=state["output"],
        dx=dx,
        dweight=dweight,
        dscale=split["dscale"],
        dbase=split["dbase"],
        inner_output_gradient=dz,
        inner_input_gradient=dy,
        x_gradient_branches=dict(
            residual=dx_residual, pre=dx_pre, linear=dx_linear, rms=dx_norm
        ),
    )


def calculate(batch=1, tokens=128):
    positive_int(batch, "batch")
    positive_int(tokens, "tokens")
    cfg = model_config("deepseek-v4-flash", reference=True)
    rows = batch * tokens
    c = cfg["hc_mult"]
    h = cfg["dim"]
    n = c * h
    v = c * (c + 2)
    occurrences = 2 * cfg["n_layers"]
    all_rows = rows * occurrences
    split = primitive.calculate(batch, tokens)["sinkhorn_split"]
    matrices = [
        dict(
            name="mix_linear",
            phase="forward",
            formula="2*R*V*N",
            flops=occurrences * 2 * rows * v * n,
        ),
        dict(
            name="mix_linear_dx_dw",
            phase="backward",
            formula="4*R*V*N",
            flops=occurrences * 4 * rows * v * n,
        ),
        dict(
            name="pre_reduction",
            phase="forward",
            formula="2*R*c*H",
            flops=all_rows * 2 * c * h,
        ),
        dict(
            name="post_residual_mix",
            phase="forward",
            formula="2*R*c*c*H",
            flops=all_rows * 2 * c * c * h,
        ),
        dict(
            name="pre_dpre_and_post_dz_dpost",
            phase="backward",
            formula="6*R*c*H",
            flops=all_rows * 6 * c * h,
        ),
        dict(
            name="post_dcomb_dxresidual",
            phase="backward",
            formula="4*R*c*c*H",
            flops=all_rows * 4 * c * c * h,
        ),
    ]
    # Matmul convention 2mnk includes contractions; do not add their reductions again.
    outer_forward = all_rows * (4 * n + v + 1)
    outer_backward = all_rows * (5 * n + 3 * v + 3)
    # For one sublayer, stores are identities. X and residual are the same buffer.
    saved = {
        "x_fp32_residual_alias": 4 * rows * n,
        "inverse_rms": 4 * rows,
        "linear_before_rms": 4 * rows * v,
        "mixes_for_scale_gradient": 4 * rows * v,
        "pre_weights": 4 * rows * c,
        "post_weights": 4 * rows * c,
        "inner_output_fp32_reference": 4 * rows * h,
        "sinkhorn_saved_subset_including_final_comb": split[
            "declared_saved_forward_bytes"
        ]
        // occurrences,
    }
    return dict(
        schema_version=1,
        calculation="v4-hc-training-wrapper",
        model="deepseek-v4-flash",
        scenario=dict(batch=batch, tokens=tokens),
        sources=provenance("deepseek-v4-flash"),
        dimensions=dict(
            rows=rows,
            hc=c,
            hidden=h,
            flat=n,
            mix_width=v,
            sublayer_occurrences=occurrences,
        ),
        matrices=matrices,
        outer_forward_scalar_flops=outer_forward,
        outer_backward_scalar_flops=outer_backward,
        outer_forward_special_ops=dict(rsqrt=all_rows),
        outer_backward_special_ops={},
        reused_split=split,
        totals=dict(
            forward_matrix_flops=sum(
                a["flops"] for a in matrices if a["phase"] == "forward"
            ),
            backward_matrix_flops=sum(
                a["flops"] for a in matrices if a["phase"] == "backward"
            ),
            forward_scalar_flops=outer_forward + split["forward_scalar_flops"],
            backward_scalar_flops=outer_backward + split["backward_scalar_flops"],
        ),
        saved_forward_boundary=dict(
            per_sublayer_buffers=saved,
            per_sublayer_bytes=sum(saved.values()),
            all_sublayers_no_recompute_saved_subset_bytes=occurrences
            * sum(saved.values()),
            exclusions=[
                "inner function saved tensors, its y input requirement and backward temporaries",
                "weights and parameter gradients",
                "dtype conversion buffers",
                "backward temporary tensors and allocator/workspace",
            ],
            aliases=[
                "residual aliases x, not another allocation",
                "final comb is the final normalized output already in split subset",
            ],
        ),
        lifecycle=[
            dict(
                event="hc_pre",
                creates=[
                    "x_fp32_residual_alias",
                    "inverse_rms",
                    "linear_before_rms",
                    "mixes_for_scale_gradient",
                    "pre_weights",
                    "post_weights",
                    "sinkhorn_saved_subset_including_final_comb",
                ],
                retains="all declared saved identities",
            ),
            dict(
                event="inner_forward",
                creates=["inner_output_fp32_reference"],
                retains="outer saved tensors plus unknown inner graph",
            ),
            dict(
                event="hc_post_forward",
                creates=["output transient"],
                retains="declared saved boundary; output transient belongs to next stage",
            ),
            dict(
                event="hc_post_backward",
                creates=["dz", "dpost", "dcomb", "dx_residual"],
                releases=["inner_output_fp32_reference", "post_weights"],
            ),
            dict(
                event="inner_backward",
                creates=["dy"],
                releases=["dz"],
                scope="caller supplies inner VJP; its work is excluded",
            ),
            dict(
                event="hc_pre_backward",
                creates=["dpre", "dx_pre"],
                releases=["pre_weights"],
            ),
            dict(
                event="split_backward",
                creates=["dmixes", "dbase", "dscale"],
                releases=[
                    "mixes_for_scale_gradient",
                    "sinkhorn_saved_subset_including_final_comb",
                ],
            ),
            dict(
                event="mix_and_rms_backward",
                creates=["dx_linear", "dx_rms", "dweight"],
                releases=["linear_before_rms", "inverse_rms"],
            ),
            dict(
                event="join_dx",
                creates=["dx"],
                releases=[
                    "x_fp32_residual_alias",
                    "dx_residual",
                    "dx_pre",
                    "dx_linear",
                    "dx_rms",
                ],
            ),
        ],
        coverage=dict(
            complete_hc_wrapper_vjp=True,
            inner_vjp_supplied_by_caller=True,
            complete_v4_training=False,
            full_runtime_peak_bytes=None,
        ),
        assumptions=[
            "Functional FP32 real-arithmetic training reference, tested with FP64. Source casts and BF16 rounding have no derivative asserted here.",
            "Matrix contractions use 2mnk; scalar reductions outside matrices use n-1 additions. Unary negation is a sign operation, excluded from FLOPs.",
            "Frozen Sinkhorn split is included once; its mix/base/scale adjoints are not recounted in outer ledger.",
            "No router or inner RMSNorm/attention/MoE work is included. 86 independent wrappers, no head wrapper.",
            "Saved identities define a forward retention subset and event dependencies, not an allocator peak. References retain X once.",
        ],
    )
