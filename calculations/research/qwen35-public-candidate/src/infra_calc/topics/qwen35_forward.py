"""Pinned Qwen3.5 base-text operator ledger; no runtime-performance claim."""

import json
import math
from collections import Counter
from infra_calc.schema import Scenario, Operator, linear
from .qwen35_reference_steps import supplement
from ..paths import PROJECT
from ..sources import provenance, read_source, model_config

EVIDENCE = PROJECT / "research/f02-qwen35-inputs"
MODEL = "qwen3.5-397b-a17b"
MASK_SOURCE = "sources/qwen3.5-397b-a17b/masking_utils.py"


def evidence():
    rows = provenance(MODEL)
    if MASK_SOURCE not in {r["file"] for r in rows}:
        raise ValueError("Missing pinned Qwen3.5 mask implementation source")
    for row in rows:
        read_source(row["file"])
    return rows


def expected_shapes(t):
    H = t["hidden_size"]
    V = t["vocab_size"]
    E = t["num_experts"]
    F = t["moe_intermediate_size"]
    S = t["shared_expert_intermediate_size"]
    expected = {}

    def add(n, shape):
        expected[n] = shape

    add("model.language_model.embed_tokens.weight", [V, H])
    add("model.language_model.norm.weight", [H])
    add("lm_head.weight", [V, H])
    for i, kind in enumerate(t["layer_types"]):
        p = f"model.language_model.layers.{i}."
        for n in ["input_layernorm", "post_attention_layernorm"]:
            add(p + n + ".weight", [H])
        add(p + "mlp.gate.weight", [E, H])
        add(p + "mlp.experts.gate_up_proj", [E, 2 * F, H])
        add(p + "mlp.experts.down_proj", [E, H, F])
        for n, sh in [
            ("gate_proj", [S, H]),
            ("up_proj", [S, H]),
            ("down_proj", [H, S]),
        ]:
            add(p + "mlp.shared_expert." + n + ".weight", sh)
        add(p + "mlp.shared_expert_gate.weight", [1, H])
        if kind == "linear_attention":
            K = t["linear_num_key_heads"] * t["linear_key_head_dim"]
            W = t["linear_num_value_heads"] * t["linear_value_head_dim"]
            heads = t["linear_num_value_heads"]
            for n, sh in [
                ("in_proj_qkv.weight", [2 * K + W, H]),
                ("in_proj_z.weight", [W, H]),
                ("in_proj_b.weight", [heads, H]),
                ("in_proj_a.weight", [heads, H]),
                ("out_proj.weight", [H, W]),
                ("conv1d.weight", [2 * K + W, 1, t["linear_conv_kernel_dim"]]),
                ("A_log", [heads]),
                ("dt_bias", [heads]),
                ("norm.weight", [t["linear_value_head_dim"]]),
            ]:
                add(p + "linear_attn." + n, sh)
        else:
            D = t["head_dim"]
            Q = t["num_attention_heads"]
            KV = t["num_key_value_heads"]
            for n, sh in [
                ("q_proj.weight", [2 * Q * D, H]),
                ("k_proj.weight", [KV * D, H]),
                ("v_proj.weight", [KV * D, H]),
                ("o_proj.weight", [H, Q * D]),
                ("q_norm.weight", [D]),
                ("k_norm.weight", [D]),
            ]:
                add(p + "self_attn." + n, sh)
    return expected


def calculate(
    batch=1,
    tokens=8192,
    history=0,
    output_head="all",
    routing_counts=None,
    chunk_size=64,
    record_past=False,
):
    if type(record_past) != bool:
        raise ValueError("record_past must be boolean")
    s = Scenario(batch=batch, tokens=tokens, history=history, output_head=output_head)
    if chunk_size != 64:
        raise ValueError(
            "Pinned default reference chunk size is 64; alternative kernel choices require separate contract"
        )
    sources = evidence()
    c = model_config(MODEL)
    t = c["text_config"]
    if history + tokens > t["max_position_embeddings"]:
        raise ValueError("Context exceeds fixed config")
    if (
        t["layer_types"]
        != [
            "linear_attention",
            "linear_attention",
            "linear_attention",
            "full_attention",
        ]
        * 15
    ):
        raise ValueError("Unsupported layer ordering")
    shapes = expected_shapes(t)
    # Inventory is derived data: match every selected shape and dtype against raw locked headers.
    actual = {}
    index = json.loads(
        read_source("research/f02-qwen35-inputs/model/model.safetensors.index.json")
    )
    for shard in set(index["weight_map"].values()):
        for name, row in json.loads(
            read_source(f"research/f02-qwen35-inputs/headers/{shard}.json")
        ).items():
            if name in shapes:
                actual[name] = row
    if set(actual) != set(shapes) or any(
        actual[n]["shape"] != sh for n, sh in shapes.items()
    ):
        raise ValueError("Base-text shape mismatch")
    weights = [
        dict(
            name=n,
            shape=sh,
            parameters=math.prod(sh),
            storage_dtype=actual[n]["dtype"],
            checkpoint_bytes=math.prod(sh) * {"BF16": 2, "F32": 4}[actual[n]["dtype"]],
        )
        for n, sh in shapes.items()
    ]
    H = t["hidden_size"]
    M = s.rows
    E = t["num_experts"]
    F = t["moe_intermediate_size"]
    D = t["head_dim"]
    Q = t["num_attention_heads"]
    KV = t["num_key_value_heads"]
    VH = t["linear_num_value_heads"]
    KD = t["linear_key_head_dim"]
    VD = t["linear_value_head_dim"]
    K = t["linear_num_key_heads"] * KD
    W = VH * VD
    C = chunk_size
    if routing_counts is None:
        total = M * t["num_experts_per_tok"]
        counts = [total // E + (i < total % E) for i in range(E)]
    else:
        counts = list(routing_counts)
        if (
            len(counts) != E
            or any(type(n) != int or n < 0 or n > M for n in counts)
            or sum(counts) != M * t["num_experts_per_tok"]
        ):
            raise ValueError(
                "Histogram must assign distinct top-k experts per token in aggregate: 512 counts, each 0..M, sum10M"
            )
    ops = []

    def add(
        name,
        cat,
        repeats=1,
        flops=0,
        scalar=0,
        special=None,
        read=0,
        write=0,
        weight=0,
        shape=None,
        note="",
    ):
        ops.append(
            Operator(
                name,
                cat,
                shape or {},
                repeats,
                flops,
                scalar,
                special or {},
                weight,
                read,
                write,
                note,
            ).record()
        )

    def gemm(name, m, k, n, repeats=1, dtype=2):
        sc = Scenario(batch=1, tokens=1, weight_bytes=dtype, activation_bytes=dtype)
        if name.startswith("linear.chunk."):
            add(
                name,
                "state_matrix",
                repeats,
                flops=2 * m * k * n,
                read=dtype * (m * k + k * n),
                write=dtype * m * n,
                shape={"left": [m, k], "right": [k, n], "output": [m, n]},
                note="Both operands are activations/state, not persistent model weights; source padded dimensions included.",
            )
        else:
            ops.append(linear(name, m, k, n, sc, repeats=repeats).record())

    def norm(name, rows, width, repeats, offset=True):
        # square + reduction + mean + epsilon + scale x + weight multiply;
        # offset RMSNorm also forms 1+w once per invocation, not per row.
        add(
            name,
            "normalization",
            repeats,
            scalar=rows * (4 * width + 1) + (width if offset else 0),
            special={"rsqrt": rows},
            read=2 * rows * width,
            write=2 * rows * width,
            weight=2 * width,
            shape={"rows": rows, "width": width},
            note="FP32 internal arithmetic; interfaces are BF16 input/output, not internal conversion traffic.",
        )

    add(
        "embedding",
        "gather",
        read=8 * M,
        write=2 * M * H,
        weight=2 * M * H,
        shape={"ids": [batch, tokens], "output": [M, H]},
    )
    norm("input_and_post_attention_norm", M, H, 120)
    add(
        "two_residuals_per_layer",
        "elementwise",
        120,
        scalar=M * H,
        read=4 * M * H,
        write=2 * M * H,
    )
    # 15 full-attention layers: Q projection includes a second, equally wide gate.
    for name, n in [("q_and_gate", 2 * Q * D), ("key", KV * D), ("value", KV * D)]:
        gemm("full." + name, M, H, n, 15)
    gemm("full.output", M, Q * D, H, 15)
    norm("full.q_norm", M * Q, D, 15)
    norm("full.k_norm", M * KV, D, 15)
    rotary = int(D * t["rope_parameters"]["partial_rotary_factor"])
    add(
        "full.apply_partial_rope",
        "rotary",
        15,
        scalar=3 * M * (Q + KV) * rotary,
        read=2 * M * (Q + KV) * rotary,
        write=2 * M * (Q + KV) * rotary,
        note="Rotation multiplication/addition only; shared position-id and sin/cos construction are listed in the reference supplement.",
    )
    for name in ["QK", "PV"]:
        add(
            "full." + name,
            "attention_matrix",
            15,
            flops=2 * Q * D * s.pairs,
            shape={
                "valid_pairs": s.pairs,
                "rectangular_pairs": s.rectangular_pairs,
                "heads": Q,
                "head_dim": D,
            },
            note="Valid causal arithmetic; eager full rectangle work is separately reported, not inferred GPU execution.",
        )
    add(
        "full.softmax",
        "softmax",
        15,
        scalar=4 * Q * s.pairs - Q * M,
        special={"exp": Q * s.pairs, "max_comparisons": Q * (s.pairs - M)},
        note="Scale/subtract/reduce/divide over valid pairs; softmax FP32, full score materialization not assumed.",
    )
    add(
        "full.output_gate",
        "elementwise",
        15,
        scalar=M * Q * D,
        special={"sigmoid": M * Q * D},
        read=4 * M * Q * D,
        write=2 * M * Q * D,
    )
    # Linear-attention projections and exact source-path loop dimensions.
    for name, n in [("qkv", 2 * K + W), ("z", W), ("a", VH), ("b", VH)]:
        gemm("linear." + name, M, H, n, 45)
    gemm("linear.output", M, W, H, 45)
    use_recurrent = history > 0 and tokens == 1
    # Conv source fallback uses padding K-1 on both sides and slices afterward;
    # count valid causal multiplies separately from all conv1d output positions.
    width = 2 * K + W
    kernel = t["linear_conv_kernel_dim"]
    valid_taps = sum(min(kernel, history + i + 1) for i in range(tokens))
    add(
        "linear.causal_conv_valid",
        "depthwise_conv",
        45,
        flops=2 * batch * width * valid_taps,
        weight=2 * width * kernel,
        shape={
            "channels": width,
            "kernel": kernel,
            "valid_taps_per_channel_request": valid_taps,
        },
        note="Only mathematically valid nonpadding tap products. Padded fallback conv1d and cached history recomputation are not this valid subtotal.",
    )
    add(
        "linear.conv_silu",
        "activation",
        45,
        scalar=M * width,
        special={"sigmoid": M * width},
        read=2 * M * width,
        write=2 * M * width,
    )
    add(
        "linear.decay_and_beta",
        "gate",
        45,
        scalar=2 * M * VH,
        special={"exp": VH, "softplus": M * VH, "sigmoid": M * VH},
        weight=8 * VH,
        note="A_log and dt_bias FP32. exp(A_log) once per invocation; unary negative and cast interfaces are listed in the reference supplement.",
    )
    # Q/K are projected at16 heads then repeated4x before norm/core.
    add(
        "linear.repeat_qk",
        "copy",
        45,
        read=4 * M * K,
        write=4 * M * VH * KD,
        shape={"repeat_factor": VH // t["linear_num_key_heads"]},
        note="Logical expanded Q/K interfaces; a kernel can avoid materialization.",
    )
    add(
        "linear.qk_l2norm_and_query_scale",
        "normalization",
        45,
        scalar=2 * M * VH * (3 * KD) + M * VH * KD,
        special={"rsqrt": 2 * M * VH},
        note="Squares,reduction,epsilon,normalization plus query scaling; FP32 core. Reduction convention counts KD-1 additions.",
    )
    norm("linear.gated_output_norm", M * VH, VD, 45, offset=False)
    add(
        "linear.norm_z_gate",
        "activation",
        45,
        scalar=2 * M * W,
        special={"sigmoid": M * W},
        note="SiLU(z) then multiplication with normalized values.",
    )
    state_elements = batch * VH * KD * VD
    if use_recurrent:
        add(
            "linear.recurrent.state_read_K",
            "state_matrix",
            45,
            flops=2 * batch * VH * KD * VD,
            shape={"loop_tokens": 1, "state": [batch, VH, KD, VD]},
        )
        add(
            "linear.recurrent.outer_update",
            "state_matrix",
            45,
            flops=2 * batch * VH * KD * VD,
        )
        add(
            "linear.recurrent.state_read_Q",
            "state_matrix",
            45,
            flops=2 * batch * VH * KD * VD,
        )
        add(
            "linear.recurrent.decay_delta",
            "elementwise",
            45,
            scalar=state_elements + 2 * batch * VH * VD,
            special={"exp": batch * VH},
            read=4 * state_elements,
            write=4 * state_elements,
            note="One logical persistent-state read/write; intermediate state passes not counted as measured memory.",
        )
        core_path = dict(
            kind="reference_recurrent",
            token_iterations=1,
            chunk_iterations=0,
            padded_tokens=tokens,
        )
    else:
        chunks = (tokens + C - 1) // C
        groups = batch * VH * chunks
        for name, k, n in [("Kbeta_Kt", KD, C), ("Q_Kt", KD, C)]:
            gemm("linear.chunk." + name, C, k, n, 45 * groups, 4)
        # Two unit-lower-triangular solves: C(C-1)/2 FMA per RHS.
        add(
            "linear.chunk.two_triangular_solves",
            "triangular_solve",
            45 * groups,
            scalar=C * (C - 1) * (KD + VD),
            shape={"order": C, "rhs_columns": [VD, KD]},
            note="Unit diagonal forward-substitution multiply/subtract arithmetic; not GEMM FLOPs or actual torch solver kernel counts.",
        )
        for name, m, k, n in [
            ("Kcum_S", C, KD, VD),
            ("Q_S", C, KD, VD),
            ("intra_Vnew", C, C, VD),
            ("Kt_Vnew", KD, C, VD),
        ]:
            gemm("linear.chunk." + name, m, k, n, 45 * groups, 4)
        add(
            "linear.chunk.decay_and_combine",
            "elementwise",
            45 * groups,
            scalar=2 * C * VD + KD * VD,
            shape={"chunks_per_request": chunks},
            note="v_new subtract, intra/inter add and state decay; beta/decay preparation arithmetic is listed in the reference supplement.",
        )
        core_path = dict(
            kind="reference_chunk_nonexport",
            chunk_size=C,
            chunk_iterations=chunks,
            token_iterations=tokens,
            padded_tokens=chunks * C,
            triangular_solves_per_chunk=2,
        )
    # MoE preserves concrete expert M, all60 layers use same declared histogram.
    gemm("moe.router", M, H, E, 60)
    add(
        "moe.router_softmax_topk",
        "router",
        60,
        scalar=M * (3 * E - 1 + 2 * t["num_experts_per_tok"] - 1),
        special={"exp": M * E, "topk_selections": M, "max_comparisons": M * (E - 1)},
        note="Topk algorithm comparison count unknown; FP32 probabilities and top10 renormalization.",
    )
    for expert, n in enumerate(counts):
        if n:
            gemm(f"moe.expert{expert}.gate_up", n, H, 2 * F, 60)
            gemm(f"moe.expert{expert}.down", n, F, H, 60)
    assignments = sum(counts)
    add(
        "moe.routed_swiglu",
        "activation",
        60,
        scalar=2 * assignments * F,
        special={"sigmoid": assignments * F},
    )
    add(
        "moe.routed_weight_and_index_add",
        "routing",
        60,
        scalar=2 * assignments * H,
        read=2 * assignments * H,
        write=2 * assignments * H,
        note="Probability multiply and addition into zero-initialized destination; gather/metadata/scatter physical traffic not complete.",
    )
    for name, k, n in [
        ("gate_up", H, 2 * t["shared_expert_intermediate_size"]),
        ("down", t["shared_expert_intermediate_size"], H),
        ("gate", H, 1),
    ]:
        gemm("moe.shared." + name, M, k, n, 60)
    add(
        "moe.shared_swiglu_gate_combine",
        "activation",
        60,
        scalar=2 * M * t["shared_expert_intermediate_size"] + 2 * M * H,
        special={"sigmoid": M * t["shared_expert_intermediate_size"] + M},
    )
    norm("final_norm", M, H, 1)
    if s.head_rows:
        gemm("lm_head", s.head_rows, H, t["vocab_size"])
    detail = supplement(batch, tokens, history, counts, record_past)
    for step in detail["steps"]:
        # Tensor-statement interfaces have their own ledger; they can overlap
        # operator-boundary interfaces, so never add the two traffic sums.
        if step["matrix_flops"] or step["scalar_flops"] or step["special_ops"]:
            add(
                "reference." + step["name"],
                "reference_supplement",
                step["repeats"],
                flops=step["matrix_flops"],
                scalar=step["scalar_flops"],
                special=step["special_ops"],
                note=step["notes"],
            )
    totals = {
        key: sum(row[key] * row["repeats"] for row in ops)
        for key in [
            "matrix_flops",
            "scalar_flops",
            "weight_read_bytes",
            "activation_read_bytes",
            "activation_write_bytes",
        ]
    }
    special = Counter()
    for op in ops:
        for k, n in op["special_ops"].items():
            special[k] += n * op["repeats"]
    return dict(
        schema_version=1,
        calculation="qwen35-base-text-ledger",
        model=MODEL,
        scenario=dict(
            batch=batch,
            tokens=tokens,
            history=history,
            output_head=output_head,
            routing_counts=routing_counts,
            chunk_size=chunk_size,
            record_past=record_past,
        ),
        sources=sources,
        weights=weights,
        operators=ops,
        reference_execution_steps=detail,
        summary=dict(
            **totals,
            special_ops=dict(special),
            base_text_parameters=sum(w["parameters"] for w in weights),
            base_checkpoint_bytes=sum(w["checkpoint_bytes"] for w in weights),
            full_forward_exact=False,
            reference_integer_operations=sum(
                x["integer_operations"] * x["repeats"] for x in detail["steps"]
            ),
            reference_arithmetic_scope="Selected nonexport chunk or recurrent fallback; eager rectangular attention; dense conv slots; FMA=2 and named special primitives. Not backend instruction count.",
            attention_execution="eager_rectangular_reference",
            tensor_interface_scope="Operator boundary subtotal; source statement supplement separately returned, never add overlapping sums",
        ),
        execution=dict(
            linear_path=core_path,
            conv_path=(
                "causal_conv1d_update"
                if use_recurrent and not record_past
                else "update_conv_state_then_causal_conv1d_fn"
            ),
            record_past=record_past,
            layer_dag=[
                dict(
                    layer=i,
                    kind=kind,
                    stages=[
                        "input_norm",
                        "attention_or_delta",
                        "residual",
                        "post_norm",
                        "router_and_routed_parallel_shared",
                        "residual",
                    ],
                )
                for i, kind in enumerate(t["layer_types"])
            ],
            expert_histogram=counts,
        ),
        state=dict(
            full_kv_before_bytes=15 * batch * history * 2 * KV * D * 2,
            full_kv_after_bytes=15 * batch * (history + tokens) * 2 * KV * D * 2,
            full_kv_append_bytes=15 * M * 2 * KV * D * 2,
            linear_recurrent_fp32_bytes=45 * state_elements * 4,
            linear_conv_slot_elements=45 * batch * width * kernel,
            linear_conv_dtype="input activation dtype; declared BF16 path",
            linear_conv_slot_bytes=45 * batch * width * kernel * 2,
            record_past_extra_allocation_bytes=None if record_past and history else 0,
            record_past_retained_conv_bytes=(
                45 * batch * width * tokens * 2
                if record_past and history == 0
                else None if record_past else 45 * batch * width * kernel * 2
            ),
        ),
        auxiliary_metrics=dict(
            full_attention_rectangular_matrix_flops=15
            * 4
            * Q
            * D
            * s.rectangular_pairs,
            full_attention_valid_matrix_flops=15 * 4 * Q * D * s.pairs,
        ),
        gaps=[
            "Whole-model exact runtime work is not claimed: torch triangular solver, softmax/topk/where/reduction algorithms and hub kernel replacements have backend-dependent instruction counts.",
            "record_past=True with pre-existing recorded convolution history has unknown retained length; source conv work and extra log allocation remain unknown for that case. Default record_past=False prefill/decode conv padded slots and cached recomputation are enumerated.",
            "Reference chunk nonexport preparation and scan arithmetic, shared text RoPE construction, eager rectangular attention, conv source slots, router one_hot/where/gather have explicit supplemental records. Export inverse-construction path is not selected.",
            "Plain-text eager causal-mask construction is counted from additionally pinned masking_utils: no external padding/custom packed mask is accepted by this interface; those different inputs require separate scope.",
            "Operator boundary bytes and supplementary statement interfaces overlap and cannot be summed into a single complete traffic result; norm/gate casts now have statement records, but view aliasing, primitive internal workspace and allocator lifetimes are not actual traffic or peak memory. No HBM or memory peak claimed.",
            "Vision/MTP excluded; output_head all is source default, last/none explicit narrower scopes; no payload numerical inference execution.",
        ],
        assumptions=[
            "All base-text weights enumerated including shared experts, gates, FP32 A_log/dt_bias and embedding/head; checkpoint bytes are not runtime allocated memory.",
            "Linear-state provenance is caller supplied via history; identical input histories/positions/cache dtype required. No engine execution or payload numerical validation.",
            "Every operator interface is logical per-call payload; repeated sums are not peak allocation or HBM. Scalar and special operations must not be folded into Tensor Core FLOPs.",
        ],
    )


def markdown(result):
    """Dedicated rendering: selected reference work and interface scopes stay visible."""
    summary = result["summary"]
    steps = result["reference_execution_steps"]
    path = result["execution"]
    lines = [
        "# Qwen3.5 基础文本参考执行账",
        "",
        "BF16 纯文本、eager attention、非 export DeltaNet fallback；FMA=2。算术和张量接口不是实测 HBM、运行时间或完整显存峰值。",
        "",
        "## 场景",
        "",
        "```json",
        json.dumps(result["scenario"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## 汇总",
        "",
        "| 项 | 值 |",
        "| --- | ---: |",
    ]
    for key in [
        "base_text_parameters",
        "base_checkpoint_bytes",
        "matrix_flops",
        "scalar_flops",
        "reference_integer_operations",
        "full_forward_exact",
    ]:
        lines.append(f"| {key} | {summary[key]} |")
    lines.extend(
        [
            "",
            "特殊数学 primitive：`"
            + json.dumps(summary["special_ops"], ensure_ascii=False, sort_keys=True)
            + "`。",
            "",
            "## 执行路径与状态",
            "",
            "```json",
            json.dumps(
                dict(
                    linear=path["linear_path"],
                    conv=steps["conv"],
                    state=result["state"],
                ),
                ensure_ascii=False,
                indent=2,
            ),
            "```",
            "",
            "## 按类别累计工作",
            "",
            "| 类别 | matrix FLOPs | scalar FLOPs |",
            "| --- | ---: | ---: |",
        ]
    )
    grouped = {}
    for row in result["operators"]:
        pair = grouped.setdefault(row["category"], [0, 0])
        pair[0] += row["matrix_flops"] * row["repeats"]
        pair[1] += row["scalar_flops"] * row["repeats"]
    for name, pair in sorted(grouped.items()):
        lines.append(f"| {name} | {pair[0]} | {pair[1]} |")
    lines.extend(
        [
            "",
            "## 补充源码语句接口",
            "",
            "**此表与算子边界 bytes 存在重叠，禁止将两者相加成 HBM 或全模型流量。** 完整权重、算子形状和逐项重复次数保留在 JSON。",
            "",
            "| 语句 | 次数 | 每次输入 bytes | 每次输出 bytes |",
            "| --- | ---: | ---: | ---: |",
        ]
    )
    for row in steps["steps"]:
        lines.append(
            f"| {row['name']} | {row['repeats']} | {row['tensor_input_bytes']} | {row['tensor_output_bytes']} |"
        )
    lines.extend(["", "## 未证明的范围", ""])
    lines.extend("- " + note for note in result["gaps"] + result["assumptions"])
    lines.extend(["", "## 固定原件", ""])
    lines.extend(
        f"- [{row['file']}]({row['url']})；revision `{row['revision']}`；SHA `{row['sha256']}`。"
        for row in result["sources"]
        if "/headers/" not in row["file"] and "/prefixes/" not in row["file"]
    )
    return "\n".join(lines) + "\n"
