"""Explicit smooth router and finite Sinkhorn VJPs; no full V4 training claim."""

import math

from infra_calc.sources import model_config, provenance
from infra_calc.units import positive_int


def sigmoid(x):
    return 1 / (1 + math.exp(-x)) if x >= 0 else math.exp(x) / (1 + math.exp(x))


def router_vjp(logits, indices, upstream, route_scale=1.5):
    if len(indices) != len(upstream) or len(set(indices)) != len(indices):
        raise ValueError(
            "This fixture requires unique selected expert IDs and matching upstream"
        )
    scores = [math.sqrt(max(x, 0) + math.log1p(math.exp(-abs(x)))) for x in logits]
    selected = [scores[i] for i in indices]
    denominator = sum(selected)
    probabilities = [s / denominator for s in selected]
    weighted_upstream = [route_scale * g for g in upstream]
    dot = sum(g * p for g, p in zip(weighted_upstream, probabilities))
    dscore = [0.0] * len(scores)
    for i, g in zip(indices, weighted_upstream):
        dscore[i] = (g - dot) / denominator
    dz = [g * sigmoid(z) / (2 * s) for g, z, s in zip(dscore, logits, scores)]
    return [route_scale * p for p in probabilities], dz


def _normalize(matrix, axis, epsilon):
    size = len(matrix)
    denominators = (
        [sum(matrix[i][j] for i in range(size)) + epsilon for j in range(size)]
        if axis == 0
        else [sum(row) + epsilon for row in matrix]
    )
    out = [
        [matrix[i][j] / denominators[j if axis == 0 else i] for j in range(size)]
        for i in range(size)
    ]
    return out, denominators


def _normalize_vjp(output, denominators, gradient, axis):
    size = len(output)
    dots = (
        [sum(gradient[i][j] * output[i][j] for i in range(size)) for j in range(size)]
        if axis == 0
        else [sum(g * y for g, y in zip(gradient[i], output[i])) for i in range(size)]
    )
    return [
        [
            (gradient[i][j] - dots[j if axis == 0 else i])
            / denominators[j if axis == 0 else i]
            for j in range(size)
        ]
        for i in range(size)
    ]


def sinkhorn_vjp(
    mixes,
    scales,
    base,
    pre_grad,
    post_grad,
    comb_grad,
    hc=4,
    iterations=20,
    epsilon=1e-6,
):
    """Manual reverse of exact ordered kernel math with hoisted denominators."""
    width = hc * (hc + 2)
    if len(mixes) != width or len(base) != width or len(scales) != 3:
        raise ValueError("mHC split dimensions differ")
    positive_int(iterations, "iterations")
    pre_s = [sigmoid(scales[0] * mixes[i] + base[i]) for i in range(hc)]
    post_s = [sigmoid(scales[1] * mixes[hc + i] + base[hc + i]) for i in range(hc)]
    logits = [
        [
            scales[2] * mixes[2 * hc + i * hc + j] + base[2 * hc + i * hc + j]
            for j in range(hc)
        ]
        for i in range(hc)
    ]
    probability = []
    for row in logits:
        exponent = [math.exp(x - max(row)) for x in row]
        denominator = sum(exponent)
        probability.append([x / denominator for x in exponent])
    matrix = [[x + epsilon for x in row] for row in probability]
    stages = []
    for axis in [0] + [axis for _ in range(iterations - 1) for axis in (1, 0)]:
        matrix, denominators = _normalize(matrix, axis, epsilon)
        stages.append((axis, matrix, denominators))
    grad = [row[:] for row in comb_grad]
    for axis, output, denominators in reversed(stages):
        grad = _normalize_vjp(output, denominators, grad, axis)
    for i in range(hc):
        dot = sum(g * p for g, p in zip(grad[i], probability[i]))
        grad[i] = [p * (g - dot) for g, p in zip(grad[i], probability[i])]
    du = [g * s * (1 - s) for g, s in zip(pre_grad, pre_s)]
    du += [2 * g * s * (1 - s) for g, s in zip(post_grad, post_s)]
    du += [v for row in grad for v in row]
    group = lambda i: 0 if i < hc else 1 if i < 2 * hc else 2
    dmix = [g * scales[group(i)] for i, g in enumerate(du)]
    dscale = [
        sum(g * mixes[i] for i, g in enumerate(du) if group(i) == part)
        for part in range(3)
    ]
    return dict(
        pre=[s + epsilon for s in pre_s],
        post=[2 * s for s in post_s],
        comb=matrix,
        dmixes=dmix,
        dbase=du,
        dscale=dscale,
        normalization_stages=len(stages),
    )


def calculate(batch=1, tokens=128):
    positive_int(batch, "batch")
    positive_int(tokens, "tokens")
    c = model_config("deepseek-v4-flash", reference=True)
    rows, layers = batch * tokens, c["n_layers"]
    experts, topk, hidden, ffn = (
        c["n_routed_experts"],
        c["n_activated_experts"],
        c["dim"],
        c["moe_inter_dim"],
    )
    hc, iterations = c["hc_mult"], c["hc_sinkhorn_iters"]
    width, normalizations = hc * (hc + 2), 2 * iterations - 1
    occurrence_rows = 2 * layers * rows
    router = dict(
        rows_per_layer=rows,
        hash_layers=c["n_hash_layers"],
        score_selected_layers=layers - c["n_hash_layers"],
        forward_score_matrix_flops=2 * layers * rows * hidden * experts,
        backward_score_matrix_flops=4 * layers * rows * hidden * experts,
        forward_scalar_flops=layers * rows * (3 * topk - 1)
        + (layers - c["n_hash_layers"]) * rows * experts,
        backward_scalar_flops=layers * rows * (5 * topk - 1 + 3 * experts),
        forward_special_ops=dict(
            softplus=layers * rows * experts, sqrt=layers * rows * experts
        ),
        backward_special_ops=dict(sigmoid=layers * rows * experts),
        integer_actions=dict(
            hash_lookup_entries=c["n_hash_layers"] * rows * topk,
            score_topk_rows=(layers - c["n_hash_layers"]) * rows,
            selected_score_gathers=layers * rows * topk,
        ),
        selected_expert_weight_backward_scalar_flops=layers
        * rows
        * topk
        * (3 * ffn - 1),
        bias_main_task_continuous_gradient="zero on fixed-selection regions; external update/auxiliary losses not zeroed globally",
    )
    # Base gradient reduction spans rows independently in each of 86 sublayers.
    split = dict(
        hc=hc,
        iterations=iterations,
        epsilon=c.get("hc_eps", 1e-6),
        sublayer_occurrences=2 * layers,
        normalizations_per_occurrence=normalizations,
        forward_scalar_flops=occurrence_rows
        * (5 * hc + (6 + 2 * normalizations) * hc * hc),
        backward_scalar_flops=(
            occurrence_rows
            * (7 * hc + (normalizations + 1) * (4 * hc * hc - hc) + width)
            + 2 * layers * (2 * rows * width - 3 + width * (rows - 1))
        ),
        forward_special_ops=dict(
            sigmoid=occurrence_rows * 2 * hc,
            exp=occurrence_rows * hc * hc,
            max_compare=occurrence_rows * hc * (hc - 1),
        ),
        declared_saved_forward_bytes=4
        * occurrence_rows
        * (2 * hc + hc * hc + normalizations * (hc * hc + hc)),
        saved_scope="pre/post sigmoid values, initial softmax probabilities, each normalized output and denominator; excludes mixes/base/scales and external mHC graph",
    )
    return dict(
        schema_version=1,
        calculation="v4-training-smooth-primitives",
        model="deepseek-v4-flash",
        scenario=dict(batch=batch, tokens=tokens),
        sources=provenance("deepseek-v4-flash"),
        router=router,
        sinkhorn_split=split,
        coverage=dict(
            router_logits_and_selected_weights_vjp=True,
            finite_sinkhorn_split_vjp=True,
            full_mhc_x_weight_vjp=False,
            full_attention_compressor_backward=False,
            complete_training_backward_flops=None,
            complete_optimizer_flops=None,
            complete_activation_peak_bytes=None,
        ),
        assumptions=[
            "Fixed unique selections define a smooth local router branch. Hash selection retains router scores and their gradients. Selection margins/ties and actual token IDs are not inferred.",
            "Router backward evaluates sqrtsoftplus derivative on all E logits then dense score-matrix gradients. Inactive expert scalar gradients are zero; no sparse GEMM optimization is assumed.",
            "Selected expert route weight multiplies F-wide SwiGLU activation before down projection; its scalar VJP is counted separately, not a complete Expert backward.",
            "Split Sinkhorn uses exact finite source order, epsilon and 39 normalizations. Denominators are hoisted per vector and saved; this is mathematical arithmetic, not literal TileLang instructions.",
            "Manual numerical helpers validate values/gradients, not Python instruction counts. Saved subset excludes the surrounding hc_pre/hc_post graph, their matrix inputs and gradients; not full mHC or model peak.",
            "Official report discloses QAT STE and majority Muon. These primitive counts neither substitute an AdamW-only V4 optimizer nor claim fully implemented QAT backward.",
        ],
    )
