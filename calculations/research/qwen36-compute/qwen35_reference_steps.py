"""Explicit selected PyTorch fallback tensor operations, separate from HBM."""


def supplement(batch, tokens, history, counts, record_past=False, *, text_config=None, gate_weight_bytes=None):
    B, T, S = batch, tokens, history
    M = B * T
    if text_config is None:
        from ..sources import model_config
        text_config = model_config("qwen3.5-397b-a17b")["text_config"]
    gate_weight_bytes = gate_weight_bytes or {"A_log": 4, "dt_bias": 2}
    t = text_config
    H = t["hidden_size"]
    heads = t["linear_num_value_heads"]
    k, v = t["linear_key_head_dim"], t["linear_value_head_dim"]
    channels = 2 * t["linear_num_key_heads"] * k + heads * v
    kernel = t["linear_conv_kernel_dim"]
    layers = t["num_hidden_layers"]
    linear_layers = t["layer_types"].count("linear_attention")
    full_layers = t["layer_types"].count("full_attention")
    Q, KV, D = t["num_attention_heads"], t["num_key_value_heads"], t["head_dim"]
    rotary = int(D * t["rope_parameters"]["partial_rotary_factor"])
    half = rotary // 2
    sections = t["rope_parameters"]["mrope_section"]
    copied = sum(len(range(axis, min(sections[axis] * 3, half), 3)) for axis in (1, 2))
    C = 64
    steps = []

    def add(
        name,
        repeats=1,
        scalar=0,
        matrix=0,
        special=None,
        read=0,
        write=0,
        integer=0,
        notes="",
    ):
        steps.append(
            dict(
                name=name,
                repeats=repeats,
                scalar_flops=scalar,
                matrix_flops=matrix,
                special_ops=special or {},
                tensor_input_bytes=read,
                tensor_output_bytes=write,
                integer_operations=integer,
                notes=notes,
            )
        )

    # Source executes the convolution before slicing away surplus positions.
    conv_update = S > 0 and T == 1 and not record_past
    L = (kernel + T if S else max(kernel, T)) if not record_past else (None if S else T)
    if L is not None:
        outputs = L - kernel + 1 if conv_update else L + kernel - 1
        kept = T if conv_update else L
        valid = sum(min(kernel, S + i + 1) for i in range(T))
        extra = outputs * kernel - valid
        add(
            "conv.additional_padded_and_discarded_products",
            linear_layers,
            matrix=2 * B * channels * extra,
            read=2 * B * channels * L,
            write=2 * B * channels * outputs,
            notes="Dense convolution multiply-accumulate slots including zero-padding and outputs discarded by slices; FMA=2, not backend instruction count.",
        )
        add(
            "conv.extra_silu_before_final_crop",
            linear_layers,
            scalar=B * channels * (kept - T),
            special={"sigmoid": B * channels * (kept - T)},
            read=2 * B * channels * kept,
            write=2 * B * channels * kept,
        )
        add(
            "conv.cache_concat_or_initial_pad",
            linear_layers,
            read=2 * B * channels * (L if S else T),
            write=2 * B * channels * L,
            notes="Concat/pad interface; initial T>=4 has no copy in update_conv_state, so corrected below.",
        )
        if not S and (T >= kernel or record_past):
            steps[-1]["tensor_input_bytes"] = steps[-1]["tensor_output_bytes"] = 0
        if not record_past:
            add(
                "conv.cache_copy_last4",
                linear_layers,
                read=2 * B * channels * kernel,
                write=2 * B * channels * kernel,
            )
        else:
            add(
                "conv.record_past_assign_alias",
                linear_layers,
                notes="Initial recorded cache aliases full input; no last4 copy, retained length is T.",
            )
        if not S:
            add("conv.cache_initial_zero", linear_layers, write=2 * B * channels * kernel)
    else:
        outputs = kept = None
    recurrent = S > 0 and T == 1
    if not recurrent:
        chunks = (T + C - 1) // C
        G = B * heads * chunks
        P = chunks * C
        raw = M * heads
        padded = B * heads * P
        # These supplement the existing Q/K norm and state/matrix operations.
        add(
            "chunk.fp32_input_casts",
            linear_layers,
            read=2 * raw * (2 * k + v + 1) + 4 * raw,
            write=4 * raw * (2 * k + v + 2),
            notes="q/k/v/beta cast outputs; g is already FP32, transpose/contiguous alias behavior not equated to memory traffic.",
        )
        add(
            "chunk.pad_q_k_v_beta_g",
            linear_layers,
            read=4 * raw * (2 * k + v + 2),
            write=4 * padded * (2 * k + v + 2),
            notes="F.pad tensor interface even at zero padding; storage aliasing/backend copies not asserted.",
        )
        add(
            "chunk.beta_K_V",
            linear_layers * G,
            scalar=C * (k + v),
            read=4 * C * (k + v + 1),
            write=4 * C * (k + v),
        )
        add(
            "chunk.cumsum",
            linear_layers * G,
            scalar=C - 1,
            read=4 * C,
            write=4 * C,
            notes="Mathematical inclusive prefix-sum additions; parallel scan implementation may differ.",
        )
        add(
            "chunk.triu_mask_construction",
            linear_layers,
            integer=C * C,
            write=C * C,
            notes="One CxC mask per layer invocation, reused across all heads/chunks.",
        )
        add(
            "chunk.pairwise_decay_difference_mask_exp",
            linear_layers * G,
            scalar=C * C,
            special={"exp": C * C},
            read=8 * C + C * C,
            write=12 * C * C,
            notes="Broadcast diff, masked-fill and exp each write CxC; exp(-inf) slots included.",
        )
        add(
            "chunk.ut_and_intra_decay_multiply",
            linear_layers * G,
            scalar=2 * C * C,
            read=16 * C * C,
            write=8 * C * C,
        )
        add(
            "chunk.exp_cum_for_decayed_Kbeta",
            linear_layers * G,
            scalar=C * k,
            special={"exp": C},
            read=4 * C * (k + 1),
            write=4 * C * (k + 1),
        )
        add(
            "chunk.exp_cum_for_Q",
            linear_layers * G,
            scalar=C * k,
            special={"exp": C},
            read=4 * C * (k + 1),
            write=4 * C * (k + 1),
        )
        add(
            "chunk.last_minus_cum_exp_for_K",
            linear_layers * G,
            scalar=C + C * k,
            special={"exp": C},
            read=4 * (C * k + C + 1),
            write=4 * (C * k + 2 * C),
        )
        add("chunk.exp_final_decay", linear_layers * G, special={"exp": 1}, read=4, write=4)
        add(
            "chunk.unit_triangular_solver_interfaces",
            linear_layers * G,
            read=4 * (2 * C * C + C * (k + v)),
            write=4 * C * (k + v),
            notes="Two linalg.solve_triangular calls. Mathematical solve arithmetic already in main operator ledger; solver workspace/algorithm not specified.",
        )
        add("chunk.scan_vnew_subtract", linear_layers * G, read=8 * C * v, write=4 * C * v)
        add("chunk.scan_output_add", linear_layers * G, read=8 * C * v, write=4 * C * v)
        add(
            "chunk.scan_state_decay_add",
            linear_layers * G,
            scalar=k * v,
            read=12 * k * v + 4,
            write=8 * k * v,
            notes="Main ledger counted decay multiply; this adds omitted state-update addition and interfaces for both statements.",
        )
        if not S:
            add("chunk.initial_state_zeros", linear_layers, write=4 * B * heads * k * v)
        add(
            "chunk.output_zeros_and_indexed_writes",
            linear_layers,
            write=8 * B * heads * P * v,
            notes="zeros_like(new_values) plus per-chunk assignment; matrix/add outputs separately own their interfaces.",
        )
        add(
            "chunk.crop_and_output_cast",
            linear_layers,
            read=4 * M * heads * v,
            write=2 * M * heads * v,
        )
    else:
        add(
            "recurrent.fp32_casts",
            linear_layers,
            read=2 * M * heads * (2 * k + v + 1) + 4 * M * heads,
            write=4 * M * heads * (2 * k + v + 2),
        )
        add(
            "recurrent.decay_exp_interface", linear_layers, read=4 * B * heads, write=4 * B * heads
        )
        add(
            "recurrent.decay_state_interface",
            linear_layers,
            read=4 * B * heads * (k * v + 1),
            write=4 * B * heads * k * v,
        )
        add(
            "recurrent.K_state_products_and_reduce",
            linear_layers,
            read=4 * B * heads * (k * v + k),
            write=4 * B * heads * (k * v + v),
            notes="Eager product tensor then reduction; FMA convention in primary arithmetic ledger.",
        )
        add(
            "recurrent.delta_subtract_beta_multiply",
            linear_layers,
            read=4 * B * heads * (4 * v + 1),
            write=8 * B * heads * v,
        )
        add(
            "recurrent.outer_product_and_state_add",
            linear_layers,
            read=4 * B * heads * (k + v + 2 * k * v),
            write=8 * B * heads * k * v,
        )
        add(
            "recurrent.Q_state_products_and_reduce",
            linear_layers,
            read=4 * B * heads * (k * v + k),
            write=4 * B * heads * (k * v + v),
        )
        add(
            "recurrent.output_zero_assignment_cast",
            linear_layers,
            read=4 * M * heads * v,
            write=10 * M * heads * v,
        )
    add(
        "linear.cache_update_recurrent_copy",
        linear_layers,
        read=4 * B * heads * k * v,
        write=4 * B * heads * k * v,
    )
    if not S:
        add("linear.cache_recurrent_initial_zero", linear_layers, write=4 * B * heads * k * v)
    # Rotary invocation shared across all layers; source expands three axes
    # even for plain text. Config inverse-frequency buffer initialization is separate.
    axes = 3
    add(
        "rope.position_arange_and_history_add",
        integer=T,
        write=8 * T,
        notes="Pure text default position_ids; views expanded to4 axes, three used by rotary.",
    )
    add("rope.position_ids_fp32_cast", read=8 * axes * M, write=4 * axes * M)
    add(
        "rope.frequency_outer_product",
        matrix=2 * axes * M * half,
        read=4 * (axes * B * half + axes * M),
        write=4 * axes * M * half,
    )
    add(
        "rope.sin_cos_and_scaling",
        scalar=2 * axes * M * half,
        special={"sin": axes * M * half, "cos": axes * M * half},
        read=8 * axes * M * half,
        write=16 * axes * M * half,
        notes="Source multiplies both sin and cos by attention_scaling=1.",
    )
    add(
        "rope.recompose_and_duplicate",
        read=8 * M * (copied + rotary),
        write=8 * M * (copied + rotary),
        notes="Two axis slices per sin/cos:11+10 values; concat duplicates32 frequencies to64." if (sections, half) == ([11, 11, 10], 32) else f"Two axis slices per sin/cos copy {copied} values; concat duplicates {half} frequencies to {rotary}.",
    )
    add("rope.cast_BF16", read=8 * M * rotary, write=4 * M * rotary)
    add(
        "rope.rotate_half_negation",
        full_layers,
        scalar=M * (Q + KV) * half,
        read=2 * M * (Q + KV) * half,
        write=2 * M * (Q + KV) * half,
    )
    add(
        "rope.concat_rotated_and_passthrough",
        full_layers,
        read=2 * M * (Q + KV) * D,
        write=2 * M * (Q + KV) * D,
    )
    # Select the eager reference explicitly: full rectangular QK/PV, then mask.
    rect = B * T * (S + T)
    valid = B * (T * S + T * (T + 1) // 2)
    delta = rect - valid
    add("full.eager_masked_matrix_slots", full_layers, matrix=4 * Q * D * delta)
    add(
        "full.eager_additional_softmax_and_mask",
        full_layers,
        scalar=4 * Q * delta + Q * rect,
        special={"exp": Q * delta, "max_comparisons": Q * delta},
        notes="Additional rectangular softmax positions plus attention-mask addition to every score slot.",
    )
    add(
        "full.kv_cache_concat",
        full_layers,
        read=2 * 2 * B * (S + T) * KV * D if S else 0,
        write=2 * 2 * B * (S + T) * KV * D if S else 0,
        notes="Dynamic cache concatenates old/new K and V; empty initial cache can alias incoming tensors.",
    )
    add(
        "full.repeat_kv_logical_materialization",
        full_layers,
        read=2 * 2 * B * (S + T) * KV * D,
        write=2 * 2 * B * (S + T) * Q * D,
        notes="repeat_kv expand/reshape logical output shape; physical alias/fusion not asserted.",
    )
    add(
        "full.QK_interfaces",
        full_layers,
        read=2 * (M * Q * D + B * (S + T) * Q * D),
        write=2 * Q * rect,
    )
    add(
        "full.scale_mask_softmax_cast_interfaces",
        full_layers,
        read=2 * Q * rect * 3 + 4 * Q * rect,
        write=2 * Q * rect * 3 + 4 * Q * rect,
        notes="Scale, mask add, FP32 softmax result, BF16 cast outputs; softmax internal reduction buffers are backend-dependent.",
    )
    add(
        "full.PV_interfaces",
        full_layers,
        read=2 * (Q * rect + B * (S + T) * Q * D),
        write=2 * M * Q * D,
    )
    add("full.transpose_contiguous", full_layers, read=2 * M * Q * D, write=2 * M * Q * D)
    # Fixed eager mask constructor, plain text with DynamicCache and no external
    # padding mask: non-vmap causal comparison, expand, then bool-to-BF16 where.
    add(
        "mask.arange_offsets",
        integer=T + (S + T),
        write=8 * (B + 1 + 2 * T + 2 * (S + T)),
        notes="batch/head/query/key aranges; query/key offset additions create their output vectors.",
    )
    add(
        "mask.causal_compare_before_batch_expand",
        integer=T * (S + T),
        read=8 * (T + S + T),
        write=T * (S + T),
        notes="q>=kv produces one broadcast plane; expand across B is a view.",
    )
    add(
        "mask.bool_to_BF16_where",
        integer=rect,
        read=rect,
        write=2 * rect,
        notes="eager_mask torch.where; boolean expanded interface, output [B,1,T,S+T]. Recurrent attention_mask=None returns None without per-element work.",
    )
    # Router backend topk remains a primitive with declared input/output shape;
    # no guessed comparison count for the algorithm selected by torch.
    E = t["num_experts"]
    top = t["num_experts_per_tok"]
    A = M * top
    hit = sum(n > 0 for n in counts)
    add(
        "router.logits_cast_softmax",
        layers,
        read=6 * M * E,
        write=8 * M * E,
        notes="FP32 softmax primitive boundaries, excluding unspecified reduction workspace.",
    )
    add(
        "router.topk_primitive_interfaces",
        layers,
        read=4 * M * E,
        write=M * top * (4 + 8),
        notes="Exact data types/shapes, implementation comparison schedule unspecified.",
    )
    add(
        "router.probability_cast_and_selected_renorm",
        layers,
        read=12 * M * top + 4 * M,
        write=6 * M * top + 4 * M,
        notes="Selected top-k sum, division and BF16 cast interfaces; arithmetic counted in main router operator.",
    )
    add(
        "router.one_hot_initialize_scatter",
        layers,
        integer=A,
        read=8 * A,
        write=8 * A * E + 8 * A,
        notes="int64 one_hot logical zero initialization plus one selected entry per assignment.",
    )
    add(
        "router.expert_hit_reduce_compare_nonzero",
        layers,
        integer=E * (A - 1) + E,
        read=8 * A * E + 8 * E + E,
        write=8 * E + E + 8 * hit,
        notes="Integer reduction, >0 and nonzero output; primitive scan scheduling unspecified.",
    )
    add(
        "router.where_per_active_expert",
        layers,
        integer=hit * top * M,
        read=8 * hit * top * M,
        write=16 * A,
    )
    add("router.input_gather", layers, read=8 * A + 2 * A * H, write=2 * A * H)
    add("router.probability_gather", layers, read=16 * A + 2 * A, write=2 * A)
    add("router.destination_zero_fill", layers, write=2 * M * H)
    add(
        "router.index_add_destination_interfaces",
        layers,
        read=8 * A + 4 * A * H,
        write=2 * A * H,
        notes="Logical source + destination per assignment, no deduplication/HBM inference.",
    )

    # Norm/gate statement interfaces. Arithmetic/special primitive counts already
    # live in main operators, so these entries deliberately add no FLOPs twice.
    def norm_interfaces(name, rows, width, repeats, offset=True, gated=False):
        N = rows * width
        add(name + ".input_fp32_cast", repeats, read=2 * N, write=4 * N)
        add(
            name + ".square_mean_epsilon_rsqrt",
            repeats,
            read=8 * N + 8 * rows,
            write=4 * N + 12 * rows,
            notes="Square, mean, epsilon add, rsqrt statement outputs; reduction kernel workspace unspecified.",
        )
        add(name + ".normalize_multiply", repeats, read=4 * (N + rows), write=4 * N)
        if offset:
            add(
                name + ".weight_cast_plus_one", repeats, read=6 * width, write=8 * width
            )
            add(
                name + ".weight_multiply_output_cast",
                repeats,
                read=8 * N + 4 * width,
                write=6 * N,
            )
        else:
            add(
                name + ".normalized_cast_weight_multiply",
                repeats,
                read=6 * N + 2 * width,
                write=4 * N,
            )
        if gated:
            add(name + ".z_cast_silu", repeats, read=6 * N, write=8 * N)
            add(name + ".gate_multiply_final_cast", repeats, read=10 * N, write=6 * N)

    norm_interfaces("norm.layer_input_and_post", M, H, 2 * layers)
    norm_interfaces("norm.full_Q", M * Q, D, full_layers)
    norm_interfaces("norm.full_K", M * KV, D, full_layers)
    norm_interfaces("norm.final", M, H, 1)
    norm_interfaces("norm.linear_gated", M * heads, v, linear_layers, offset=False, gated=True)
    if gate_weight_bytes["A_log"] != 4:
        add("linear.A_fp32_cast", linear_layers,
            read=gate_weight_bytes["A_log"] * heads, write=4 * heads,
            notes="A_log.float() converts BF16 checkpoint parameter to FP32 before exp.")
    add(
        "linear.A_exp_negation",
        linear_layers,
        scalar=heads,
        read=8 * heads,
        write=8 * heads,
        notes="FP32 exp(A_log), then unary negation; exponent primitive counted in primary operator.",
    )
    add(
        "linear.a_dt_softplus_decay_multiply",
        linear_layers,
        read=14 * M * heads + (4 + gate_weight_bytes["dt_bias"]) * heads,
        write=16 * M * heads,
        notes="a.float plus dt_bias, softplus, multiply by negative exp A.",
    )
    add("linear.b_sigmoid", linear_layers, read=2 * M * heads, write=2 * M * heads)
    add(
        "linear.qk_norm_internal",
        linear_layers,
        read=2 * (12 * M * heads * k + 12 * M * heads),
        write=2 * (8 * M * heads * k + 12 * M * heads),
        notes="Two L2 norms: square/reduce/epsilon/rsqrt/multiply. Query scaling interfaces follow separately.",
    )
    add(
        "linear.query_scale_interface",
        linear_layers,
        read=4 * M * heads * k,
        write=4 * M * heads * k,
    )
    add("moe.routed_silu_and_up_multiply", layers, read=6 * A * t["moe_intermediate_size"], write=4 * A * t["moe_intermediate_size"])
    add("moe.routed_probability_multiply", layers, read=2 * A * (H + 1), write=2 * A * H)
    add("moe.shared_silu_and_up_multiply", layers, read=6 * M * t["shared_expert_intermediate_size"], write=4 * M * t["shared_expert_intermediate_size"])
    add(
        "moe.shared_gate_sigmoid_multiply_combine",
        layers,
        read=2 * M + 2 * M * (H + 1) + 4 * M * H,
        write=2 * M + 4 * M * H,
    )
    add(
        "full.output_gate_sigmoid_multiply",
        full_layers,
        read=6 * M * Q * D,
        write=4 * M * Q * D,
    )
    return dict(
        steps=steps,
        conv=dict(
            input_positions=L,
            conv_output_positions_before_slice=outputs,
            silu_positions_before_final_crop=kept,
            source_path="update" if conv_update else "padded_fn",
            record_past_shape_known=L is not None,
        ),
        scalar_additions=sum(x["scalar_flops"] * x["repeats"] for x in steps),
        matrix_additions=sum(x["matrix_flops"] * x["repeats"] for x in steps),
        tensor_interface_read_bytes=sum(
            x["tensor_input_bytes"] * x["repeats"] for x in steps
        ),
        tensor_interface_write_bytes=sum(
            x["tensor_output_bytes"] * x["repeats"] for x in steps
        ),
        scope="Additional source-operation interfaces; not an exhaustive whole-model interface sum or measured HBM. Matmul FMA=2 and reductions mathematical counts; torch primitive backend algorithms remain unspecified.",
        startup=dict(
            rope_inv_freq_elements=half,
            scalar_divisions=2 * half,
            special_ops={"power": half},
            note="Model construction only; not repeated each forward.",
        ),
    )
