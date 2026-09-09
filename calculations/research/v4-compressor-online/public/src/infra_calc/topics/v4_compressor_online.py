"""Functional positive-start compressor timeline and explicit initial-state VJP."""

import math
from . import v4_attention_projections as ops
from infra_calc.sources import model_config, provenance
from infra_calc.units import positive_int


def reference(
    initial_kv,
    initial_score,
    x,
    start_pos,
    ratio,
    wkv,
    wgate,
    ape,
    gamma,
    angles,
    upstream,
    final_kv_upstream=None,
    final_score_upstream=None,
    epsilon=1e-6,
):
    if ratio not in (4, 128) or start_pos <= 0:
        raise ValueError("Actual ratio4/128 and positive start_pos required")
    d = len(gamma)
    width = d * (2 if ratio == 4 else 1)
    slots = ratio * (2 if ratio == 4 else 1)
    hidden = len(x[0])
    kv = [row[:] for row in initial_kv]
    score = [row[:] for row in initial_score]
    if (
        len(kv) != slots
        or len(score) != slots
        or any(len(row) != width for row in kv + score)
    ):
        raise ValueError("Initial state shape differs from fixed source ratio")
    tape = []
    outputs = []
    emit = 0
    for step, row in enumerate(x):
        pos = start_pos + step
        slot = (ratio if ratio == 4 else 0) + pos % ratio
        values = ops.mv(wkv, row)
        biased = [v + ape[pos % ratio][j] for j, v in enumerate(ops.mv(wgate, row))]
        kv[slot] = values
        score[slot] = biased
        record = dict(slot=slot, pos=pos, emit=False)
        if (pos + 1) % ratio == 0:
            mapping = (
                [(i, 0) for i in range(ratio)] + [(ratio + i, d) for i in range(ratio)]
                if ratio == 4
                else [(i, 0) for i in range(ratio)]
            )
            saved_values = []
            probabilities = []
            pooled = []
            for j in range(d):
                logits = [score[i][offset + j] for i, offset in mapping]
                maximum = max(logits)
                if not math.isfinite(maximum):
                    raise ValueError("Emitted channel must have a finite score")
                weights = [math.exp(v - maximum) for v in logits]
                den = sum(weights)
                p = [v / den for v in weights]
                vals = [kv[i][offset + j] for i, offset in mapping]
                probabilities.append(p)
                saved_values.append(vals)
                pooled.append(sum(a * b for a, b in zip(p, vals)))
            normalized, norm = ops.rms(pooled, gamma, epsilon)
            outputs.append(ops.rotate(normalized, angles[emit]))
            record.update(
                emit=True,
                index=emit,
                mapping=mapping,
                values=saved_values,
                probabilities=probabilities,
                norm=norm,
            )
            emit += 1
            if ratio == 4:
                kv[:ratio] = [row[:] for row in kv[ratio:]]
                score[:ratio] = [row[:] for row in score[ratio:]]
        tape.append(record)
    gkv = (
        [row[:] for row in final_kv_upstream]
        if final_kv_upstream is not None
        else [[0.0] * width for _ in range(slots)]
    )
    gs = (
        [row[:] for row in final_score_upstream]
        if final_score_upstream is not None
        else [[0.0] * width for _ in range(slots)]
    )
    # -inf entries denote fixed mask constants, not differentiable finite-valued leaves.
    for i in range(slots):
        for j in range(width):
            if score[i][j] == float("-inf"):
                gs[i][j] = 0.0
    dgamma = [0.0] * d
    dape = [[0.0] * width for _ in range(ratio)]
    dwkv = [[0.0] * hidden for _ in range(width)]
    dwgate = [[0.0] * hidden for _ in range(width)]
    dx = [None] * len(x)
    for step in reversed(range(len(x))):
        rec = tape[step]
        if rec["emit"]:
            if ratio == 4:
                # Reverse prev <- current: both post-copy aliases accumulate to current.
                for i in range(ratio):
                    for j in range(width):
                        gkv[ratio + i][j] += gkv[i][j]
                        gs[ratio + i][j] += gs[i][j]
                gkv[:ratio] = [[0.0] * width for _ in range(ratio)]
                gs[:ratio] = [[0.0] * width for _ in range(ratio)]
            idx = rec["index"]
            du, dg = ops.rms_vjp(
                rec["norm"], ops.rotate(upstream[idx], angles[idx], True), gamma
            )
            dgamma = [a + b for a, b in zip(dgamma, dg)]
            for j in range(d):
                p = rec["probabilities"][j]
                dp = [du[j] * v for v in rec["values"][j]]
                dot = sum(a * b for a, b in zip(p, dp))
                for k, (slot, offset) in enumerate(rec["mapping"]):
                    gkv[slot][offset + j] += p[k] * du[j]
                    gs[slot][offset + j] += p[k] * (dp[k] - dot)
        slot = rec["slot"]
        dk, ds = gkv[slot], gs[slot]
        # Overwritten previous slot value has no derivative through this write.
        gkv[slot] = [0.0] * width
        gs[slot] = [0.0] * width
        dxk, dwk = ops.mv_vjp(wkv, x[step], dk)
        dxg, dwg = ops.mv_vjp(wgate, x[step], ds)
        dx[step] = [a + b for a, b in zip(dxk, dxg)]
        for j in range(width):
            dape[rec["pos"] % ratio][j] += ds[j]
            for k in range(hidden):
                dwkv[j][k] += dwk[j][k]
                dwgate[j][k] += dwg[j][k]
    for i in range(slots):
        for j in range(width):
            if initial_score[i][j] == float("-inf"):
                gs[i][j] = 0.0
    return dict(
        output=outputs,
        final_kv=kv,
        final_score=score,
        dx=dx,
        dwkv=dwkv,
        dwgate=dwgate,
        dape=dape,
        dgamma=dgamma,
        dinitial_kv=gkv,
        dinitial_score=gs,
    )


def calculate(
    batch=1, start_pos=3, tokens=6, ratio=4, initial_state_mode="external_history"
):
    for name, value in [("batch", batch), ("start_pos", start_pos), ("tokens", tokens)]:
        positive_int(value, name)
    positive_int(ratio, "ratio")
    if ratio not in (4, 128):
        raise ValueError("ratio must be 4 or 128")
    if initial_state_mode not in ("leaf", "external_history"):
        raise ValueError("Unknown initial state gradient ownership")
    cfg = model_config("deepseek-v4-flash", reference=True)
    h = cfg["dim"]
    d = cfg["head_dim"]
    rd = cfg["rope_head_dim"]
    coff = 2 if ratio == 4 else 1
    width = coff * d
    slots = coff * ratio
    positions = [
        p for p in range(start_pos, start_pos + tokens) if (p + 1) % ratio == 0
    ]
    e = batch * len(positions)
    r = batch * tokens
    versions = [f"initial:{i}" for i in range(slots)]
    events = []
    for step, pos in enumerate(range(start_pos, start_pos + tokens)):
        slot = (ratio if ratio == 4 else 0) + pos % ratio
        old = versions[slot]
        versions[slot] = f"token:{step}"
        event = dict(
            step=step,
            start_pos=pos,
            write_slot=slot,
            overwritten_version=old,
            new_version=versions[slot],
            emit=(pos + 1) % ratio == 0,
        )
        if event["emit"]:
            event["pool_dependencies"] = (
                [dict(version=versions[i], channels=[0, d]) for i in range(ratio)]
                + [
                    dict(version=versions[ratio + i], channels=[d, 2 * d])
                    for i in range(ratio)
                ]
                if ratio == 4
                else [dict(version=v, channels=[0, d]) for v in versions]
            )
            event["rope_position"] = pos + 1 - ratio
            if ratio == 4:
                event["copy_current_to_previous"] = True
                versions[:ratio] = versions[ratio:]
        events.append(event)
    scalar = dict(
        forward_ape_flops=r * width,
        forward_pool_softmax_flops=(5 * slots - 2) * e * d,
        backward_pool_softmax_flops=(6 * slots - 1) * e * d,
        backward_pool_gradient_scatter_flops=2 * slots * e * d,
        backward_state_copy_gradient_join_flops=(
            2 * ratio * width * e if ratio == 4 else 0
        ),
        backward_ape_reduce_flops=width * (r - min(tokens, ratio)),
        forward_norm_flops=e * (4 * d + 1),
        backward_norm_flops=7 * e * d + d * max(e - 1, 0),
        forward_rope_flops=3 * e * rd,
        backward_rope_flops=3 * e * rd,
        backward_input_join_flops=r * h,
    )
    saved = dict(
        new_token_inputs_fp32=4 * r * h,
        per_emit_gathered_kv_fp32=4 * e * slots * d,
        per_emit_probabilities_fp32=4 * e * slots * d,
        per_emit_norm_xhat_fp32=4 * e * d,
        per_emit_norm_inverse_rms_fp32=4 * e,
    )
    return dict(
        schema_version=1,
        calculation="v4-compressor-online-timegraph-training",
        model="deepseek-v4-flash",
        scenario=dict(
            batch=batch,
            start_pos=start_pos,
            tokens=tokens,
            ratio=ratio,
            initial_state_mode=initial_state_mode,
        ),
        sources=provenance("deepseek-v4-flash"),
        dimensions=dict(
            hidden=h,
            head_dim=d,
            projection_width=width,
            state_slots=slots,
            emits_per_batch=len(positions),
            new_token_rows=r,
        ),
        timeline=events,
        final_state_versions=versions,
        initial_state_contract=dict(
            mode=initial_state_mode,
            gradient="return VJP for initial KV and finite initial scores; -inf mask scores are constants",
            chain_rule="leaf: report gradients for independent initial state; external_history: caller must feed these gradients through its history producer and add shared-parameter gradients",
            validity="caller supplies source-shaped states with at least one finite score per emitted feature; arbitrary finite state values permitted",
            detachment_assumed=False,
        ),
        matrices=[
            dict(
                name=name,
                weight_shape=[width, h],
                forward_flops=2 * r * h * width,
                backward_dx_flops=2 * r * h * width,
                backward_dw_flops=2 * r * h * width,
            )
            for name in ("wkv", "wgate")
        ],
        scalar=scalar,
        special_ops=dict(
            exp_calls=e * slots * d, max_comparisons=e * d * (slots - 1), rsqrt_calls=e
        ),
        state_operations=dict(
            forward_new_kv_and_score_write_bytes=2 * 4 * r * width,
            forward_copy_previous_kv_and_score_read_bytes=(
                2 * 4 * ratio * width * e if ratio == 4 else 0
            ),
            forward_copy_previous_kv_and_score_write_bytes=(
                2 * 4 * ratio * width * e if ratio == 4 else 0
            ),
            backward_overwritten_gradient_slot_zero_bytes=2 * 4 * r * width,
            backward_copy_previous_gradient_zero_bytes=(
                2 * 4 * ratio * width * e if ratio == 4 else 0
            ),
            scope="selected explicit copies/clears, not total memory traffic",
        ),
        saved_forward_boundary=dict(
            buffers=saved,
            total_bytes=sum(saved.values()),
            initial_state_interface_fp32_bytes=2 * 4 * batch * slots * width,
            final_state_interface_fp32_bytes=2 * 4 * batch * slots * width,
            frequency_constants_fp32_bytes=4 * len(positions) * rd,
            scope="saved values use a per-emit gathered-KV snapshot strategy; initial/final interfaces are separate ownership, not automatically extra saved copies; not peak",
        ),
        totals=dict(
            forward_matrix_flops=4 * r * h * width,
            backward_matrix_flops=8 * r * h * width,
            forward_scalar_flops=sum(
                v for k, v in scalar.items() if k.startswith("forward_")
            ),
            backward_scalar_flops=sum(
                v for k, v in scalar.items() if k.startswith("backward_")
            ),
        ),
        coverage=dict(
            positive_start_pos_one_token_sequence=True,
            joint_initial_state_and_parameter_vjp=True,
            history_producer_vjp_included=False,
            parallel_chunk_supported=False,
            cast_surrogate_gradient=None,
            source_quantized_value_equivalence=False,
            complete_v4_training=False,
            actual_peak_bytes=None,
        ),
        assumptions=[
            "Each positive-start source call processes exactly one token. This is a sequential time graph, never an unsupported parallel chunk.",
            "Ratio4 reverses prev<-current copies by joining both post-copy state adjoints into current before pooling adjoints, then kills overwritten old-slot paths. Ratio128 retains slots until each is overwritten.",
            "Pooled output adjoints and final-state adjoints are independent inputs and both contribute to shared weights/APE/gamma. No truncation or detach is silently inserted.",
            "Finite initial score entries are mathematical leaves; -inf mask constants have zero adjoint. Arbitrary runtime state validity is not inferred solely from start_pos.",
            "FP32 projection source does not specify gradients for downstream dtype casts/FP8 simulation. All VJPs are unrounded real-math references; no STE is inferred.",
            "Counts use full source-shaped pool slots, separate parameter reductions and explicit gradient joins. Actual allocator, complete traffic and history producer work are excluded.",
        ],
    )


def markdown(result):
    lines = [
        "# V4 Compressor 在线可微时间图",
        "",
        "正start_pos逐token执行；返回初态、最终状态、新输入及共享参数的联合VJP。初态叶子与外部history连接显式区分。",
        "",
        "不把在线时间图称为并行chunk，也不推定cast梯度或完整训练峰值。",
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
