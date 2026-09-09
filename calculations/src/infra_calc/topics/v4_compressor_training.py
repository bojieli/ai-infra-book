"""Ratio128 complete-prefill compressor, unrounded differentiable reference."""

import math
from . import v4_attention_projections as ops
from infra_calc.sources import model_config, provenance
from infra_calc.units import positive_int


def reference(x, wkv, wgate, ape, gamma, angles, upstream, ratio=128, epsilon=1e-6):
    """One batch, complete blocks; non-overlap only. Angles supplied per block."""
    if ratio == 4 or len(x) % ratio or len(x) < ratio:
        raise ValueError("Reference is non-overlap, complete blocks only")
    d = len(wkv)
    hidden = len(x[0])
    blocks = len(x) // ratio
    kv = [ops.mv(wkv, row) for row in x]
    scores = [ops.mv(wgate, row) for row in x]
    dkv = [[0.0] * d for _ in x]
    dscores = [[0.0] * d for _ in x]
    dape = [[0.0] * d for _ in range(ratio)]
    dgamma = [0.0] * d
    output = []
    for block in range(blocks):
        ids = list(range(block * ratio, (block + 1) * ratio))
        probabilities = []
        pooled = []
        for j in range(d):
            logits = [scores[i][j] + ape[k][j] for k, i in enumerate(ids)]
            maximum = max(logits)
            weights = [math.exp(a - maximum) for a in logits]
            den = sum(weights)
            p = [a / den for a in weights]
            probabilities.append(p)
            pooled.append(sum(p[k] * kv[i][j] for k, i in enumerate(ids)))
        normalized, state = ops.rms(pooled, gamma, epsilon)
        output.append(ops.rotate(normalized, angles[block]))
        dpool, dg = ops.rms_vjp(
            state, ops.rotate(upstream[block], angles[block], True), gamma
        )
        dgamma = [a + b for a, b in zip(dgamma, dg)]
        for j in range(d):
            p = probabilities[j]
            dp = [dpool[j] * kv[i][j] for i in ids]
            dot = sum(a * b for a, b in zip(p, dp))
            for k, i in enumerate(ids):
                dkv[i][j] = p[k] * dpool[j]
                dscores[i][j] = p[k] * (dp[k] - dot)
                dape[k][j] += dscores[i][j]
    dwkv = [[0.0] * hidden for _ in range(d)]
    dwgate = [[0.0] * hidden for _ in range(d)]
    dx = []
    for i, row in enumerate(x):
        dxk, dwk = ops.mv_vjp(wkv, row, dkv[i])
        dxg, dwg = ops.mv_vjp(wgate, row, dscores[i])
        dx.append([a + b for a, b in zip(dxk, dxg)])
        for j in range(d):
            for k in range(hidden):
                dwkv[j][k] += dwk[j][k]
                dwgate[j][k] += dwg[j][k]
    return dict(
        output=output, dx=dx, dwkv=dwkv, dwgate=dwgate, dape=dape, dgamma=dgamma
    )


def calculate(batch=1, tokens=256):
    positive_int(batch, "batch")
    positive_int(tokens, "tokens")
    cfg = model_config("deepseek-v4-flash", reference=True)
    ratio = 128
    if tokens < ratio or tokens % ratio:
        raise ValueError(
            "Ratio128 complete-prefill contract requires a positive multiple of 128 tokens"
        )
    r = batch * tokens
    c = batch * (tokens // ratio)
    h = cfg["dim"]
    d = cfg["head_dim"]
    rd = cfg["rope_head_dim"]
    matrices = [
        dict(
            name=name,
            input_shape=[r, h],
            weight_shape=[d, h],
            forward_flops=2 * r * h * d,
            backward_dx_flops=2 * r * h * d,
            backward_dw_flops=2 * r * h * d,
        )
        for name in ["wkv", "wgate"]
    ]
    saved = dict(
        x_fp32=4 * r * h,
        projected_kv_fp32=4 * r * d,
        channelwise_probabilities_fp32=4 * r * d,
        norm_normalized_before_gamma_fp32=4 * c * d,
        norm_inverse_rms_fp32=4 * c,
    )
    return dict(
        schema_version=1,
        calculation="v4-ratio128-compressor-training-reference",
        model="deepseek-v4-flash",
        scenario=dict(batch=batch, tokens=tokens),
        sources=provenance("deepseek-v4-flash"),
        dimensions=dict(
            rows=r,
            hidden=h,
            head_dim=d,
            ratio=ratio,
            blocks_per_batch=tokens // ratio,
            total_blocks=c,
            rope_dim=rd,
        ),
        execution=dict(
            start_pos=0,
            complete_blocks=True,
            overlap=False,
            rotate=False,
            rope_positions=list(range(0, tokens, ratio)),
            scope="one main-attention HCA compressor, not indexer compressor or all layers",
        ),
        matrices=matrices,
        scalar=dict(
            forward_ape_softmax_pool_flops=6 * r * d - 2 * c * d,
            backward_pool_softmax_flops=6 * r * d - c * d,
            backward_ape_reduce_flops=ratio * d * (c - 1),
            forward_norm_flops=c * (4 * d + 1),
            backward_norm_flops=7 * c * d + d * (c - 1),
            forward_rope_flops=3 * c * rd,
            backward_rope_flops=3 * c * rd,
            backward_x_branch_join_flops=r * h,
        ),
        special_ops=dict(
            forward_exp_calls=r * d,
            forward_max_comparisons=c * d * (ratio - 1),
            forward_rsqrt_calls=c,
            backward_special_calls=0,
        ),
        saved_forward_boundary=dict(
            buffers=saved,
            total_bytes=sum(saved.values()),
            shared_frequency_constants_fp32_bytes=4 * (tokens // ratio) * rd,
            exclusions=[
                "projected score/APE-shifted logits not needed after saving probabilities",
                "output and incoming gradients",
                "weight/parameter-gradient ownership",
                "quantization/cast intermediates, backward temporary values and allocator workspace",
            ],
            scope="FP32 saved reference subset, not actual peak",
        ),
        source_state_boundary=dict(
            state_byte_scope="active batch slices, not registered max_batch_size allocation",
            kv_state_fp32_bytes=4 * batch * ratio * d,
            score_state_fp32_bytes=4 * batch * ratio * d,
            compressed_cache_semantic_bf16_bytes=2 * c * d,
            ratio128_full_prefill_does_not_write_state_buffers=True,
            online_gradient_contract=None,
            notes=[
                "complete prefill returns compressed outputs but does not seed ratio128 rolling states; the next ratio128 block overwrites every slot before pooling",
                "source online expects one token per positive start_pos call; new block is emitted only at (start_pos+1)%128==0",
                "tail remainder buffers and restored-state gradients are excluded and rejected by this calculate input contract",
            ],
        ),
        lifecycle=[
            dict(event="project_all_tokens", retains=["x", "projected kv"]),
            dict(
                event="ape_and_channelwise_softmax",
                retains=["probabilities"],
                releases=["score logits"],
            ),
            dict(
                event="pool_norm_rope",
                retains=["norm xhat/r"],
                transfers=["compressed output to attention"],
            ),
            dict(event="reverse_rope_and_norm", creates=["dpool", "dgamma"]),
            dict(event="pool_and_softmax_vjp", creates=["dkv", "dscore", "dape"]),
            dict(event="projection_vjps", creates=["dxkv", "dxgate", "dwkv", "dwgate"]),
            dict(event="join_input_gradients", creates=["dx"]),
        ],
        totals=dict(
            forward_matrix_flops=4 * r * h * d,
            backward_matrix_flops=8 * r * h * d,
            forward_scalar_flops=6 * r * d - 2 * c * d + c * (4 * d + 1) + 3 * c * rd,
            backward_scalar_flops=6 * r * d
            - c * d
            + ratio * d * (c - 1)
            + 7 * c * d
            + d * (c - 1)
            + 3 * c * rd
            + r * h,
        ),
        coverage=dict(
            ratio128_complete_prefill_vjp=True,
            ratio4_overlap_vjp=False,
            online_restored_state_vjp=False,
            cast_surrogate_gradient=None,
            source_quantized_value_equivalence=False,
            complete_v4_training=False,
            actual_peak_bytes=None,
        ),
        assumptions=[
            "Per-feature softmax spans the ratio token axis, not the channel axis. Every output feature has its own probabilities and APE.",
            "Two compressor linears are FP32 in fixed source. Subsequent pooled-value cast, RMS output cast, in-place RoPE and non-rope FP8 simulation are removed in this real-math reference; no STE is inferred.",
            "Scalar sums use n-1 reductions; numerical helpers may initialize accumulated parameter gradients from zero. Matrix dW includes full token-row reduction, not an extra scalar reduction.",
            "Source ratio4 has doubled projections and previous/current half-channel overlap; this is explicitly not computed by substituting ratio=4 into these formulas.",
            "Core attention, other attention projections, indexer/compressor branch objectives and request-level gradient routing are outside this one compressor.",
        ],
    )


def markdown(result):
    lines = [
        "# V4 ratio128 Compressor 训练参考",
        "",
        "仅完整分块 prefill、无 overlap、非 indexer rotate 支路。每feature沿token轴softmax，包含两投影/APE/池化/RMS/RoPE反向。",
        "",
        "尾块、在线恢复状态、ratio4重叠及量化cast梯度未实现。保存子集不是实际峰值。",
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
