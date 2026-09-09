"""Tensor-identity GEMM input saves over the existing conditional PP4 schedule."""

from . import training_pipeline_schedule as pipeline
from . import training_nonmatrix
from ..sources import model_config, provenance


def calculate(
    microbatches=8,
    microbatch_size=1,
    tokens=128,
    policy="1f1b",
    activation_policy="save_nonlinear",
    gemm_policy="save_inputs",
    service_options=None,
):
    if gemm_policy not in ("save_inputs", "recompute_products"):
        raise ValueError("Unknown GEMM input preservation strategy")
    service_options = {} if service_options is None else dict(service_options)
    allowed = {
        "forward_seconds",
        "backward_seconds",
        "activation_transfer_seconds",
        "gradient_transfer_seconds",
        "link_mode",
        "optimizer_seconds",
        "setup_seconds",
    }
    if set(service_options) - allowed:
        raise ValueError("service_options may only override explicit time/link inputs")
    source = training_nonmatrix.calculate(
        batch=microbatch_size, tokens=tokens, activation_policy=activation_policy
    )
    cfg = model_config("qwen3-8b")
    r = microbatch_size * tokens
    h = cfg["hidden_size"]
    q = cfg["num_attention_heads"]
    k = cfg["num_key_value_heads"]
    d = cfg["head_dim"]
    f = cfg["intermediate_size"]
    layers = cfg["num_hidden_layers"]
    existing = {(obj["layer"], obj["name"]): obj for obj in source["saved_objects"]}
    objects = []
    requirements = []
    recomputations = []

    def create(name, layer, shape, producer, last_consumer, derived=None):
        stage = 3 if layer is None else layer // 9
        identity = f'gemm:{layer if layer is not None else "head"}:{name}'
        elements = 1
        for n in shape:
            elements *= n
        recompute = derived is not None and gemm_policy == "recompute_products"
        obj = dict(
            id=identity,
            name=name,
            layer=layer,
            stage=stage,
            shape=shape,
            dtype="fp32_reference",
            elements=elements,
            bytes=4 * elements,
            producer=producer,
            last_consumer=last_consumer,
            strategy="recompute" if recompute else "save",
            derived_from=derived,
        )
        objects.append(obj)
        if recompute:
            recomputations.append(
                dict(
                    object=identity,
                    stage=stage,
                    scalar_flops=elements,
                    special_calls=0,
                    workspace_bytes=4 * elements,
                    before_event=last_consumer.replace(
                        "backward_end", "backward_begin"
                    ),
                    release_event=last_consumer,
                    formula="elementwise product of two available operands",
                )
            )
        return identity

    def require(name, layer, operands):
        requirements.append(
            dict(
                matrix=name,
                layer=layer,
                stage=3 if layer is None else layer // 9,
                saved_operand_ids=operands,
                weight_for_dx="resident parameter, excluded from activation budget",
                upstream_gradient="backward temporary, excluded from saved-forward subset",
            )
        )

    for layer in range(layers):
        z = existing[layer, "input_norm_z_r"]["id"]
        postz = existing[layer, "post_norm_z_r"]["id"]
        swiglu = existing[
            layer,
            "swiglu_g_u" if activation_policy == "recompute_silu" else "swiglu_a_s_u",
        ]["id"]
        inp = create(
            "input_norm_weighted",
            layer,
            [r, h],
            "input_rmsnorm.forward",
            "qkv_projection.backward_end",
            dict(saved=z, component="z", other="input_norm.gamma resident parameter"),
        )
        qr = create(
            "q_after_norm_rope",
            layer,
            [microbatch_size, q, tokens, d],
            "q_norm_rope.forward",
            "qk.backward_end",
        )
        kr = create(
            "k_after_norm_rope_unique",
            layer,
            [microbatch_size, k, tokens, d],
            "k_norm_rope.forward",
            "qk.backward_end",
        )
        vv = create(
            "v_unique",
            layer,
            [microbatch_size, k, tokens, d],
            "v_proj.forward",
            "pv.backward_end",
        )
        context = create(
            "attention_context", layer, [r, q * d], "pv.forward", "o_proj.backward_end"
        )
        mlp = create(
            "post_norm_weighted",
            layer,
            [r, h],
            "post_rmsnorm.forward",
            "gate_up_projection.backward_end",
            dict(
                saved=postz, component="z", other="post_norm.gamma resident parameter"
            ),
        )
        down = create(
            "swiglu_product",
            layer,
            [r, f],
            "a_times_u.forward",
            "down_proj.backward_end",
            dict(
                saved=swiglu,
                component=(
                    "a and u"
                    if activation_policy == "save_nonlinear"
                    else "a from existing recompute_silu and saved u"
                ),
                other="no new sigmoid when existing policy already recomputes it",
            ),
        )
        for name in ("q_proj", "k_proj", "v_proj"):
            require(name, layer, [inp])
        require("qk", layer, [qr, kr])
        require("pv", layer, [existing[layer, "attention_probabilities"]["id"], vv])
        require("o_proj", layer, [context])
        for name in ("gate_proj", "up_proj"):
            require(name, layer, [mlp])
        require("down_proj", layer, [down])
    head = create(
        "final_norm_weighted",
        None,
        [r, h],
        "final_rmsnorm.forward",
        "lm_head.backward_end",
        dict(
            saved=existing[None, "final_norm_z_r"]["id"],
            component="z",
            other="final_norm.gamma resident parameter",
        ),
    )
    require("lm_head", None, [head])
    saved_per_stage = [
        sum(
            o["bytes"]
            for o in objects
            if o["stage"] == stage and o["strategy"] == "save"
        )
        for stage in range(4)
    ]
    baseline = pipeline.calculate(
        microbatches=microbatches,
        microbatch_size=microbatch_size,
        tokens=tokens,
        policy=policy,
        activation_policy=activation_policy,
        **service_options,
    )
    scheduled = pipeline.calculate(
        microbatches=microbatches,
        microbatch_size=microbatch_size,
        tokens=tokens,
        policy=policy,
        activation_policy=activation_policy,
        additional_saved_bytes=saved_per_stage,
        **service_options,
    )
    intervals = [dict(i) for i in scheduled["activation_intervals"]]
    workspace = [
        max(
            [node["workspace_bytes"] for node in recomputations if node["stage"] == s]
            + [0]
        )
        for s in range(4)
    ]
    for event in scheduled["events"]:
        if event["kind"] == "B" and workspace[event["stage"]]:
            intervals.append(
                dict(
                    id=f'gemm-product-workspace:{event["stage"]}:{event["microbatch"]}',
                    stage=event["stage"],
                    start=event["start"],
                    end=event["end"],
                    bytes=workspace[event["stage"]],
                    kind="gemm_product_recompute_workspace",
                )
            )
    peaks = pipeline._peaks(intervals)
    # Tensor-specific reservations share stage F/B envelopes; semantic releases remain above.
    envelopes = []
    event_map = {e["id"]: e for e in scheduled["events"]}
    for obj in objects:
        if obj["strategy"] != "save":
            continue
        for mb in range(microbatches):
            envelopes.append(
                dict(
                    id=f'{obj["id"]}:mb{mb}',
                    tensor_id=obj["id"],
                    stage=obj["stage"],
                    microbatch=mb,
                    start=event_map[f'F:{obj["stage"]}:{mb}']["start"],
                    end=event_map[f'B:{obj["stage"]}:{mb}']["end"],
                    bytes=obj["bytes"],
                )
            )
    extra = sum(node["scalar_flops"] for node in recomputations)
    return dict(
        schema_version=1,
        calculation="qwen8-pipeline-gemm-saved-identities",
        scenario=dict(
            microbatches=microbatches,
            microbatch_size=microbatch_size,
            tokens=tokens,
            policy=policy,
            activation_policy=activation_policy,
            gemm_policy=gemm_policy,
            service_options=service_options,
        ),
        sources=provenance("qwen3-8b"),
        semantic_layer_order=dict(
            forward=[
                "input_norm",
                "qkv_projection",
                "qk_norm_rope",
                "qk_softmax",
                "pv",
                "o_proj",
                "residual",
                "post_norm",
                "gate_up_projection",
                "swiglu",
                "down_proj",
                "residual",
            ],
            backward=[
                "down_proj",
                "swiglu",
                "gate_up_projection",
                "post_norm",
                "residual",
                "o_proj",
                "pv",
                "softmax",
                "qk",
                "qk_norm_rope",
                "qkv_projection",
                "input_norm",
            ],
            head_backward=["loss", "lm_head", "final_norm", "layer35_backward"],
            rule="Each product reconstruction precedes its backward GEMM consumers and releases after their final use; no layer-backward overlap is assumed",
        ),
        tensor_objects=objects,
        matrix_vjp_requirements=requirements,
        reused_nonlinear_saved_objects=source["saved_objects"],
        recomputation_nodes=recomputations,
        gqa_contract=dict(
            q_heads=q,
            kv_heads=k,
            head_dim=d,
            group_size=q // k,
            probability_identity="existing per-layer triangular attention_probabilities",
            kv_expansion="logical grouped access, no separately saved repeat_kv tensor",
            backward_head_reduction="already in public nonmatrix, not counted again",
        ),
        work=dict(
            original_pipeline_work=baseline["work"],
            extra_per_microbatch_scalar_flops=extra,
            extra_all_microbatches_scalar_flops=microbatches * extra,
            extra_matrix_flops=0,
            extra_special_calls=0,
            combined_all_microbatches_backward_scalar_flops=baseline["work"][
                "all_microbatches_backward_scalar_flops"
            ]
            + microbatches * extra,
        ),
        reservation=dict(
            added_persistent_bytes_per_microbatch_stage=saved_per_stage,
            additional_product_workspace_bytes_per_stage=workspace,
            individual_tensor_envelopes=envelopes,
            combined_intervals=intervals,
            combined_timelines=peaks,
            combined_peak_declared_bytes=[
                p["peak_declared_reserved_bytes"] for p in peaks
            ],
            baseline_peak_declared_bytes=baseline["summary"][
                "reserved_activation_scope_peak_bytes"
            ],
            scope="forward-start/backward-end conservative stage reservations; tensor semantic producer/last-consumer are separate, no invented within-stage timestamps",
        ),
        schedule=dict(
            events=scheduled["events"],
            stage_orders=scheduled["stage_orders"],
            summary=dict(
                scheduled["summary"],
                reserved_activation_scope_peak_bytes=[
                    p["peak_declared_reserved_bytes"] for p in peaks
                ],
            ),
            time_interpretation="Caller F/B services must include selected extra recomputation; no new measured runtime inferred",
        ),
        coverage=dict(
            all_public_qwen_dense_matrix_input_identities=True,
            probabilities_and_gqa_deduplicated=True,
            complete_training_activation_peak_bytes=None,
            actual_allocator_peak_bytes=None,
            source_dtype_runtime_equivalence=False,
        ),
        assumptions=[
            "Fixed dense full-token Qwen3-8B PP4. Each linear dW needs its forward input, each linear dX needs resident W. Bilinear QK/PV require both operands; no output tensor is saved merely because a GEMM produced it.",
            "Norm z/r is pre-gamma normalized value, not weighted GEMM input. SwiGLU a/s/u are not a*u. New identities distinguish these products instead of falsely aliasing them.",
            "Save_inputs preserves all added FP32 reference operands. Recompute_products reconstructs only weighted norm outputs and a*u, using public saved values; Q/K/V/context remain saved.",
            "Under existing recompute_silu, its sigmoid/a pair is reconstructed once before down-projection dW and retained through SwiGLU backward. Existing public two-vector workspace and scalar/special counts are reused, not added again.",
            "One layer backward at a time; product temporary is freed after its last GEMM consumer before the next reconstructed product. Reserve max one product buffer throughout each stage B, conservatively.",
            "Tensor objects explicitly label semantic producer and last consumer. Stage timing only resolves F/B envelopes; these are reservations, not exact physical allocation lifetimes.",
            "FP32 saved operands define a mathematical reference strategy. Vendor kernel dtype/packing, expanded-GQA materialization and allocator workspace remain implementation dependent.",
            "Token/label IDs, transient gradients, parameter/optimizer state, communication-to-internal-copy ownership, casting and other non-saved buffers are excluded. More complete GEMM saves still do not prove total training peak.",
        ],
    )


def markdown(result):
    lines = [
        "# Qwen8 PP4 GEMM 保存对象与重算",
        "",
        "逐矩阵所需输入按身份去重，列出原非矩阵保存引用、归stage和语义释放点。",
        "",
        "阶段F/B时间仅提供保守reservation包络，不是allocator实际峰值。",
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
