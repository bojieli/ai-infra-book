"""Fresh ratio4 prefill with differentiable returned writes, including tail state."""

import math
from . import v4_attention_projections as ops
from infra_calc.sources import model_config, provenance
from infra_calc.units import positive_int


def reference(
    x,
    wkv,
    wgate,
    ape,
    gamma,
    angles,
    upstream,
    state_kv_upstream=None,
    state_score_upstream=None,
    epsilon=1e-6,
):
    """One batch. State adjoints supplied only for writes from this fresh prefill."""
    ratio = 4
    d = len(gamma)
    hidden = len(x[0])
    blocks = len(x) // 4
    tail = len(x) % 4
    kv = [ops.mv(wkv, row) for row in x]
    score = [
        [v + ape[i % 4][j] for j, v in enumerate(ops.mv(wgate, row))]
        for i, row in enumerate(x)
    ]
    state_kv = [[0.0] * (2 * d) for _ in range(8)]
    state_score = [[float("-inf")] * (2 * d) for _ in range(8)]
    writes = []
    if blocks:
        writes += [(i, (blocks - 1) * 4 + i) for i in range(4)]
    writes += [(4 + i, blocks * 4 + i) for i in range(tail)]
    for slot, token in writes:
        state_kv[slot] = kv[token][:]
        state_score[slot] = score[token][:]
    dkv = [[0.0] * (2 * d) for _ in x]
    ds = [[0.0] * (2 * d) for _ in x]
    dgamma = [0.0] * d
    output = []
    for block in range(blocks):
        mapping = (
            [(None, j) for j in range(4)]
            if block == 0
            else [((block - 1) * 4 + j, 0) for j in range(4)]
        )
        mapping += [(block * 4 + j, d) for j in range(4)]
        probabilities = []
        values = []
        pooled = []
        for j in range(d):
            logits = [
                float("-inf") if token is None else score[token][offset + j]
                for token, offset in mapping
            ]
            vals = [
                0.0 if token is None else kv[token][offset + j]
                for token, offset in mapping
            ]
            maximum = max(logits)
            exps = [math.exp(a - maximum) for a in logits]
            total = sum(exps)
            p = [v / total for v in exps]
            probabilities.append(p)
            values.append(vals)
            pooled.append(sum(a * b for a, b in zip(p, vals)))
        normalized, saved = ops.rms(pooled, gamma, epsilon)
        output.append(ops.rotate(normalized, angles[block]))
        du, dg = ops.rms_vjp(
            saved, ops.rotate(upstream[block], angles[block], True), gamma
        )
        dgamma = [a + b for a, b in zip(dgamma, dg)]
        for j in range(d):
            p = probabilities[j]
            dp = [du[j] * v for v in values[j]]
            dot = sum(a * b for a, b in zip(p, dp))
            for slot, (token, offset) in enumerate(mapping):
                if token is not None:
                    dkv[token][offset + j] += p[slot] * du[j]
                    ds[token][offset + j] += p[slot] * (dp[slot] - dot)
    state_kv_upstream = (
        state_kv_upstream
        if state_kv_upstream is not None
        else [[0.0] * (2 * d) for _ in range(8)]
    )
    state_score_upstream = (
        state_score_upstream
        if state_score_upstream is not None
        else [[0.0] * (2 * d) for _ in range(8)]
    )
    for slot, token in writes:
        for j in range(2 * d):
            dkv[token][j] += state_kv_upstream[slot][j]
            ds[token][j] += state_score_upstream[slot][j]
    dape = [[0.0] * (2 * d) for _ in range(4)]
    dwkv = [[0.0] * hidden for _ in range(2 * d)]
    dwgate = [[0.0] * hidden for _ in range(2 * d)]
    dx = []
    for i, row in enumerate(x):
        dxk, dwk = ops.mv_vjp(wkv, row, dkv[i])
        dxg, dwg = ops.mv_vjp(wgate, row, ds[i])
        dx.append([a + b for a, b in zip(dxk, dxg)])
        for j in range(2 * d):
            dape[i % 4][j] += ds[i][j]
            for k in range(hidden):
                dwkv[j][k] += dwk[j][k]
                dwgate[j][k] += dwg[j][k]
    return dict(
        output=output,
        state_kv=state_kv,
        state_score=state_score,
        writes=writes,
        dx=dx,
        dwkv=dwkv,
        dwgate=dwgate,
        dape=dape,
        dgamma=dgamma,
    )


def calculate(batch=1, tokens=9):
    positive_int(batch, "batch")
    positive_int(tokens, "tokens")
    cfg = model_config("deepseek-v4-flash", reference=True)
    h = cfg["dim"]
    d = cfg["head_dim"]
    rd = cfg["rope_head_dim"]
    blocks = tokens // 4
    tail = tokens % 4
    r = batch * tokens
    c = batch * blocks
    valid_per_batch = 4 * max(0, 2 * blocks - 1)
    written = (4 if blocks else 0) + tail
    matrices = [
        dict(
            name=name,
            input_shape=[r, h],
            weight_shape=[2 * d, h],
            forward_flops=4 * r * h * d,
            backward_dx_flops=4 * r * h * d,
            backward_dw_flops=4 * r * h * d,
        )
        for name in ["wkv", "wgate"]
    ]
    norm_backward = 7 * c * d + d * max(c - 1, 0)
    scalar = dict(
        forward_shared_ape_flops=2 * r * d,
        forward_full_eight_slot_softmax_pool_flops=38 * c * d,
        backward_full_eight_slot_pool_softmax_flops=47 * c * d,
        backward_compressed_gradient_scatter_add_flops=2 * batch * valid_per_batch * d,
        backward_returned_state_scatter_add_flops=4 * batch * written * d,
        backward_ape_reduce_flops=2 * d * (r - min(tokens, 4)),
        forward_norm_flops=c * (4 * d + 1),
        backward_norm_flops=norm_backward,
        forward_rope_flops=3 * c * rd,
        backward_rope_flops=3 * c * rd,
        backward_x_join_flops=r * h,
    )
    saved = dict(
        x_fp32=4 * r * h,
        projected_kv_fp32=8 * r * d,
        full_eight_slot_probabilities_fp32=4 * 8 * c * d,
        norm_normalized_before_gamma_fp32=4 * c * d,
        norm_inverse_rms_fp32=4 * c,
    )
    writes = ([(i, (blocks - 1) * 4 + i) for i in range(4)] if blocks else []) + [
        (4 + i, blocks * 4 + i) for i in range(tail)
    ]
    return dict(
        schema_version=1,
        calculation="v4-ratio4-overlap-prefill-training-reference",
        model="deepseek-v4-flash",
        scenario=dict(batch=batch, tokens=tokens),
        sources=provenance("deepseek-v4-flash"),
        dimensions=dict(
            batch=batch,
            tokens=tokens,
            hidden=h,
            head_dim=d,
            ratio=4,
            blocks=blocks,
            tail=tail,
            total_blocks=c,
            projection_width=2 * d,
        ),
        execution=dict(
            start_pos=0,
            fresh_state=True,
            rotate=False,
            rope_positions=list(range(0, 4 * blocks, 4)),
            returned_state_writes=[
                dict(slot=s, token=t, channels=2 * d) for s, t in writes
            ],
            returned_state_adjoint="explicit caller gradient for every written KV/score channel; future computation itself is not inferred",
            unused_state="fresh KV zero and score -inf constants, with no trainable initial-state gradient",
        ),
        matrices=matrices,
        scalar=scalar,
        special_ops=dict(exp_calls=8 * c * d, max_comparisons=7 * c * d, rsqrt_calls=c),
        declared_source_difference=dict(
            shared_ape_common_expression=True,
            source_extra_forward_ape_additions_for_last_complete_state=(
                8 * batch * d if blocks else 0
            ),
            explanation="Source separately adds APE for last complete block state and all compressed blocks; reference computes score+APE once and shares it. Its state and compressed-output adjoints are joined before APE reduction.",
        ),
        data_ops=dict(
            projected_kv_and_score_gradient_zero_bytes=16 * r * d,
            ape_gradient_zero_bytes=4 * 4 * 2 * d,
            source_state_materialization_kv_write_bytes=8 * batch * written * d,
            source_state_materialization_score_write_bytes=8 * batch * written * d,
            scope="explicit reference gradient initialization and source write interfaces, not complete memory traffic",
        ),
        saved_forward_boundary=dict(
            buffers=saved,
            total_bytes=sum(saved.values()),
            frequency_constants_fp32_bytes=4 * blocks * rd,
            source_active_state_buffers_bytes=2 * 4 * batch * 8 * 2 * d,
            returned_written_state_values_bytes=2 * 4 * batch * written * 2 * d,
            scope="saved subset only; state output materialization is a separate interface and not automatically added to saved tensors",
            aliases=[
                "last complete/tail state writes refer to existing projected KV and shared biased score values in this functional graph",
                "first block absent previous half is constant padding, not trainable tokens",
            ],
        ),
        lifecycle=[
            dict(
                event="project_and_bias",
                retains=["X", "KV"],
                creates=["shared biased score"],
            ),
            dict(
                event="overlap_pool",
                reads=["previous block first D, current block last D"],
                retains=["8-slot probabilities", "RMS xhat/r"],
            ),
            dict(
                event="return_state",
                transfers=["last complete block both halves", "tail both halves"],
                scope="caller owns outputs and supplies their adjoints",
            ),
            dict(
                event="output_backward",
                creates=["projection KV/score gradients from compressed outputs"],
            ),
            dict(
                event="join_state_adjoints",
                creates=["combined projection gradients"],
                note="state KV and score gradients added even for tail tokens with no compressed output",
            ),
            dict(
                event="parameter_vjps",
                creates=["Wkv/Wgate/APE/gamma gradients", "joined X gradient"],
            ),
        ],
        totals=dict(
            forward_matrix_flops=8 * r * h * d,
            backward_matrix_flops=16 * r * h * d,
            forward_scalar_flops=sum(
                v for k, v in scalar.items() if k.startswith("forward_")
            ),
            backward_scalar_flops=sum(
                v for k, v in scalar.items() if k.startswith("backward_")
            ),
        ),
        coverage=dict(
            ratio4_fresh_prefill_with_tail_vjp=True,
            returned_written_state_vjp=True,
            arbitrary_restored_state_vjp=False,
            positive_start_pos_online_schedule=False,
            cast_surrogate_gradient=None,
            source_quantized_value_equivalence=False,
            complete_v4_training=False,
            actual_peak_bytes=None,
        ),
        assumptions=[
            "Full eight-slot reference computes padding softmax/pool arithmetic, but discards adjoints of first-block constant padding. It does not optimize those slots away.",
            "Two projected halves have distinct roles. A token first half contributes to the next block; its second half to its own block. Returned writes preserve both halves of last complete block and tail.",
            "Reference aliases score+APE as a common expression. Source duplicate APE addition is reported separately; this is not literal source instruction replay.",
            "RMS and RoPE use unrounded real math. FP32 linears do not justify inventing gradients for later BF16/FP8 cast and quantization.",
            "Core attention, ratio128, indexer rotate/Hadamard/FP4 branch, future online execution and restored history are excluded.",
        ],
    )


def markdown(result):
    lines = [
        "# V4 ratio4 overlap prefill 训练参考",
        "",
        "首块padding、前块前半/当前后半通道、最后完整块和尾块返回状态梯度均显式处理。",
        "",
        "只fresh start_pos=0；未推导任意恢复状态、未来online调度或量化cast梯度。",
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
