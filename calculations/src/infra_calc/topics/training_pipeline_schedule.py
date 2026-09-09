"""PP4 Qwen3-8B synchronous GPipe/1F1B conditional event schedules."""

import math
from collections import Counter
from . import training_nonmatrix
from ..models import qwen3
from ..sources import model_config, provenance
from ..units import positive_int


def _vector(value, length, name):
    if not isinstance(value, (list, tuple)) or len(value) != length:
        raise ValueError(f"{name} requires {length} finite nonnegative values")
    if any(type(x) not in (int, float) or not math.isfinite(x) or x < 0 for x in value):
        raise ValueError(f"{name} requires finite nonnegative values")
    return list(value)


def _work(batch, tokens, policy):
    source = training_nonmatrix.calculate(
        batch=batch, tokens=tokens, activation_policy=policy
    )
    config = model_config("qwen3-8b")
    if config["num_hidden_layers"] != 36:
        raise ValueError("This fixed PP4 partition requires exactly 36 layers")
    stages = [
        dict(
            stage=s,
            layers=list(range(9 * s, 9 * (s + 1))),
            matrices=[],
            nonmatrix=[],
            parameters=0,
            saved_objects=[],
        )
        for s in range(4)
    ]
    for op in source["training_matrix_original"]["training_matrix_rows"]:
        owners = range(4) if op["repeats"] == 36 else [3]
        copies = 9 if op["repeats"] == 36 else 1
        for s in owners:
            stages[s]["matrices"].append(
                dict(
                    name=op["name"],
                    shapes=op["shapes"],
                    copies=copies,
                    forward_flops=op["forward_flops"] * copies,
                    backward_flops=2 * op["forward_flops"] * copies,
                )
            )
    setup = []
    for op in source["nonmatrix_operations"]:
        if op["name"] == "rotary_table_per_step":
            setup.append(op)
            continue
        if op["name"] == "embedding_scatter_add":
            owners, divisor = [0], 1
        elif op["name"] in ("final_rmsnorm", "mean_cross_entropy"):
            owners, divisor = [3], 1
        else:
            owners, divisor = range(4), 4
        for s in owners:
            row = dict(
                name=op["name"],
                forward_scalar_flops=op["forward_scalar_flops"] // divisor,
                backward_scalar_flops=op["backward_scalar_flops"] // divisor,
                forward_special_ops={
                    k: v // divisor for k, v in op["forward_special_ops"].items()
                },
                backward_special_ops={
                    k: v // divisor for k, v in op["backward_special_ops"].items()
                },
            )
            stages[s]["nonmatrix"].append(row)
    for item in source["saved_objects"]:
        stage = 3 if item["layer"] is None else item["layer"] // 9
        stages[stage]["saved_objects"].append(item)
    for weight in qwen3.weights(config):
        if weight.copies == 36:
            for stage in stages:
                stage["parameters"] += weight.parameters // 4
        else:
            owner = 0 if "embed_tokens" in weight.name else 3
            stages[owner]["parameters"] += weight.parameters
    for stage in stages:
        stage["forward_matrix_flops"] = sum(
            x["forward_flops"] for x in stage["matrices"]
        )
        stage["backward_matrix_flops"] = sum(
            x["backward_flops"] for x in stage["matrices"]
        )
        stage["forward_scalar_flops"] = sum(
            x["forward_scalar_flops"] for x in stage["nonmatrix"]
        )
        stage["backward_scalar_flops"] = sum(
            x["backward_scalar_flops"] for x in stage["nonmatrix"]
        )
        stage["nonlinear_saved_bytes_per_microbatch"] = sum(
            x["bytes"] for x in stage["saved_objects"]
        )
    return stages, setup, source


def _orders(microbatches, policy):
    if policy == "gpipe":
        return [
            [("F", m) for m in range(microbatches)]
            + [("B", m) for m in reversed(range(microbatches))]
            for _ in range(4)
        ]
    orders = []
    for stage in range(4):
        warmup = min(3 - stage, microbatches)
        order = [("F", m) for m in range(warmup)]
        for i in range(microbatches - warmup):
            order.extend([("F", i + warmup), ("B", i)])
        order.extend(("B", i) for i in range(microbatches - warmup, microbatches))
        orders.append(order)
    return orders


def _schedule(nodes):
    """Deterministic nonpreemptive earliest-ready list scheduling on unary resources."""
    pending = dict(nodes)
    done, free = {}, {}
    while pending:
        ready = []
        for name, node in pending.items():
            if all(dep in done for dep in node["dependencies"]):
                start = max(
                    [free.get(node["resource"], 0.0)]
                    + [done[d]["end"] for d in node["dependencies"]]
                )
                ready.append((start, node["priority"], name))
        if not ready:
            raise ValueError("Pipeline ordering contains a dependency cycle")
        start, _, name = min(ready)
        node = pending.pop(name)
        end = start + node["duration"]
        if not math.isfinite(end):
            raise ValueError("Schedule time exceeds finite numeric range")
        done[name] = dict(node, id=name, start=start, end=end)
        free[node["resource"]] = end
    return done


def _peaks(intervals):
    result = []
    for stage in range(4):
        events = []
        for item in intervals:
            if item["stage"] != stage or item["start"] == item["end"]:
                continue
            events.extend(
                [
                    (item["start"], 1, item["bytes"], item["id"]),
                    (item["end"], 0, -item["bytes"], item["id"]),
                ]
            )
        live = peak = 0
        timeline = []
        for time, _, delta, identity in sorted(events):
            live += delta
            if live < 0:
                raise AssertionError("Negative reserved activation bytes")
            peak = max(peak, live)
            timeline.append(
                dict(time=time, object=identity, delta_bytes=delta, live_bytes=live)
            )
        if live:
            raise AssertionError("Activation reservations did not drain")
        result.append(
            dict(stage=stage, peak_declared_reserved_bytes=peak, events=timeline)
        )
    return result


def calculate(
    microbatches=8,
    microbatch_size=1,
    tokens=128,
    policy="1f1b",
    forward_seconds=(0.01, 0.01, 0.01, 0.01),
    backward_seconds=(0.02, 0.02, 0.02, 0.02),
    activation_transfer_seconds=(0.001, 0.001, 0.001),
    gradient_transfer_seconds=(0.001, 0.001, 0.001),
    link_mode="independent_directional",
    activation_policy="save_nonlinear",
    additional_saved_bytes=(0, 0, 0, 0),
    optimizer_seconds=(0.001, 0.001, 0.001, 0.001),
    setup_seconds=0.0,
):
    for name, value in [
        ("microbatches", microbatches),
        ("microbatch_size", microbatch_size),
        ("tokens", tokens),
    ]:
        positive_int(value, name)
    if policy not in ("gpipe", "1f1b"):
        raise ValueError("policy must be gpipe or 1f1b")
    if link_mode not in ("independent_directional", "shared_half_duplex"):
        raise ValueError("Unknown link serialization contract")
    forward_seconds = _vector(forward_seconds, 4, "forward_seconds")
    backward_seconds = _vector(backward_seconds, 4, "backward_seconds")
    activation_transfer_seconds = _vector(
        activation_transfer_seconds, 3, "activation_transfer_seconds"
    )
    gradient_transfer_seconds = _vector(
        gradient_transfer_seconds, 3, "gradient_transfer_seconds"
    )
    optimizer_seconds = _vector(optimizer_seconds, 4, "optimizer_seconds")
    additional_saved_bytes = _vector(
        additional_saved_bytes, 4, "additional_saved_bytes"
    )
    if any(type(x) is not int for x in additional_saved_bytes):
        raise ValueError("additional_saved_bytes must contain integer byte counts")
    _vector([setup_seconds], 1, "setup_seconds")
    stages, setup, source = _work(microbatch_size, tokens, activation_policy)
    config = model_config("qwen3-8b")
    orders = _orders(microbatches, policy)
    nodes = {}

    def add(name, kind, stage, mb, duration, resource, deps, priority):
        nodes[name] = dict(
            kind=kind,
            stage=stage,
            microbatch=mb,
            duration=duration,
            resource=resource,
            dependencies=list(dict.fromkeys(deps)),
            priority=priority,
        )

    add("setup", "setup", None, None, setup_seconds, "setup", [], 0)
    for stage, order in enumerate(orders):
        previous = "setup"
        for kind, mb in order:
            name = f"{kind}:{stage}:{mb}"
            deps = [previous]
            if kind == "F" and stage:
                deps.append(f"A:{stage-1}:{mb}")
            if kind == "B":
                deps.append(f"F:{stage}:{mb}")
                if stage < 3:
                    deps.append(f"G:{stage+1}:{mb}")
                if policy == "gpipe":
                    deps.append(f"F:3:{microbatches-1}")
            add(
                name,
                kind,
                stage,
                mb,
                (forward_seconds if kind == "F" else backward_seconds)[stage],
                f"compute:{stage}",
                deps,
                2 if kind == "B" else 3,
            )
            previous = name
    for stage in range(3):
        for mb in range(microbatches):
            resource = (
                "link:shared"
                if link_mode == "shared_half_duplex"
                else f"link:A:{stage}"
            )
            add(
                f"A:{stage}:{mb}",
                "A",
                stage,
                mb,
                activation_transfer_seconds[stage],
                resource,
                [f"F:{stage}:{mb}"],
                1,
            )
            resource = (
                "link:shared"
                if link_mode == "shared_half_duplex"
                else f"link:G:{stage}"
            )
            add(
                f"G:{stage+1}:{mb}",
                "G",
                stage + 1,
                mb,
                gradient_transfer_seconds[stage],
                resource,
                [f"B:{stage+1}:{mb}"],
                1,
            )
    all_gradients = [
        f"B:{stage}:{mb}" for stage in range(4) for mb in range(microbatches)
    ]
    for stage in range(4):
        add(
            f"U:{stage}",
            "update",
            stage,
            None,
            optimizer_seconds[stage],
            f"compute:{stage}",
            all_gradients,
            4,
        )
    events = _schedule(nodes)
    gradient_ready = max(events[name]["end"] for name in all_gradients)
    makespan = max(e["end"] for e in events.values())
    intervals = []

    def reserve(identity, stage, start, end, amount, kind):
        intervals.append(
            dict(
                id=identity, stage=stage, start=start, end=end, bytes=amount, kind=kind
            )
        )

    for stage in range(4):
        saved = (
            stages[stage]["nonlinear_saved_bytes_per_microbatch"]
            + additional_saved_bytes[stage]
        )
        for mb in range(microbatches):
            f, b = events[f"F:{stage}:{mb}"], events[f"B:{stage}:{mb}"]
            reserve(
                f"saved:{stage}:{mb}",
                stage,
                f["start"],
                b["end"],
                saved,
                "declared_saved_reservation",
            )
            if activation_policy == "recompute_silu":
                # One layer's two FP32 temporary vectors at a time; reserve for whole stage B.
                amount = 8 * microbatch_size * tokens * config["intermediate_size"]
                reserve(
                    f"recompute:{stage}:{mb}",
                    stage,
                    b["start"],
                    b["end"],
                    amount,
                    "recompute_workspace_reservation",
                )
    activation_bytes = 2 * microbatch_size * tokens * config["hidden_size"]
    gradient_bytes = 4 * microbatch_size * tokens * config["hidden_size"]
    for event in events.values():
        if event["kind"] not in ("A", "G"):
            continue
        kind, stage, mb = event["kind"], event["stage"], event["microbatch"]
        target = stage + 1 if kind == "A" else stage - 1
        compute_kind = "F" if kind == "A" else "B"
        amount = activation_bytes if kind == "A" else gradient_bytes
        reserve(
            event["id"] + ":send",
            stage,
            events[f"{compute_kind}:{stage}:{mb}"]["end"],
            event["end"],
            amount,
            "send_buffer",
        )
        reserve(
            event["id"] + ":receive",
            target,
            event["start"],
            events[f"{compute_kind}:{target}:{mb}"]["start"],
            amount,
            "receive_buffer",
        )
    peaks = _peaks(intervals)
    zero_nodes = {
        name: dict(node, duration=0 if node["kind"] in ("A", "G") else node["duration"])
        for name, node in nodes.items()
    }
    no_transfer = max(e["end"] for e in _schedule(zero_nodes).values())
    stage_summary = []
    for stage in range(4):
        useful = microbatches * (forward_seconds[stage] + backward_seconds[stage])
        stage_summary.append(
            dict(
                stage=stage,
                forward_backward_service_seconds=useful,
                idle_during_training_seconds=gradient_ready - setup_seconds - useful,
                update_seconds=optimizer_seconds[stage],
                peak_declared_reserved_bytes=peaks[stage][
                    "peak_declared_reserved_bytes"
                ],
            )
        )
    params = sum(stage["parameters"] for stage in stages)
    for stage in stages:
        stage["microbatch_gradient_accumulation_additions"] = (
            microbatches - 1
        ) * stage["parameters"]
        stage["mean_gradient_scale_operations"] = (
            stage["parameters"] if microbatches > 1 else 0
        )
        stage["optimizer_parameter_scalar_flops"] = 14 * stage["parameters"]
    scenario = dict(
        microbatches=microbatches,
        microbatch_size=microbatch_size,
        tokens=tokens,
        policy=policy,
        forward_seconds=forward_seconds,
        backward_seconds=backward_seconds,
        activation_transfer_seconds=activation_transfer_seconds,
        gradient_transfer_seconds=gradient_transfer_seconds,
        link_mode=link_mode,
        activation_policy=activation_policy,
        additional_saved_bytes=additional_saved_bytes,
        optimizer_seconds=optimizer_seconds,
        setup_seconds=setup_seconds,
    )
    return dict(
        calculation="qwen8-training-pipeline-schedule",
        schema_version=1,
        scenario=scenario,
        sources=provenance("qwen3-8b"),
        partition=dict(model="qwen3-8b", stages=4, layers_per_stage=9),
        work=dict(
            per_microbatch_stages=stages,
            once_per_step_rotary_setup=setup,
            per_microbatch_public_data_operations=source["data_operations"],
            all_microbatches_forward_matrix_flops=microbatches
            * sum(s["forward_matrix_flops"] for s in stages),
            all_microbatches_backward_matrix_flops=microbatches
            * sum(s["backward_matrix_flops"] for s in stages),
            all_microbatches_forward_scalar_flops=microbatches
            * sum(s["forward_scalar_flops"] for s in stages)
            + sum(s["forward_scalar_flops"] for s in setup),
            all_microbatches_backward_scalar_flops=microbatches
            * sum(s["backward_scalar_flops"] for s in stages),
            step_parameter_accumulation_and_mean_scalar_flops=(microbatches - 1)
            * params
            + (params if microbatches > 1 else 0),
            total_parameters=params,
            once_per_step_optimizer=source["optimizer"],
            gradient_accumulation="First microbatch initializes dense stage parameter gradient; remaining M-1 add, then divide by M once. Equal token/label counts per microbatch.",
        ),
        stage_orders=[
            [dict(kind=k, microbatch=mb) for k, mb in order] for order in orders
        ],
        events=sorted(
            events.values(), key=lambda e: (e["start"], e["priority"], e["id"])
        ),
        activation_intervals=intervals,
        activation_timelines=peaks,
        stages=stage_summary,
        transfers=dict(
            activation_bytes_per_boundary=activation_bytes,
            gradient_bytes_per_boundary=gradient_bytes,
            forward_messages=3 * microbatches,
            backward_messages=3 * microbatches,
            total_payload_bytes=3 * microbatches * (activation_bytes + gradient_bytes),
        ),
        summary=dict(
            total_sequences=microbatches * microbatch_size,
            total_tokens=microbatches * microbatch_size * tokens,
            gradient_ready_seconds=gradient_ready,
            step_makespan_seconds=makespan,
            zero_transfer_counterfactual_seconds=no_transfer,
            exposed_transfer_makespan_delta_seconds=makespan - no_transfer,
            useful_forward_backward_device_seconds=sum(
                s["forward_backward_service_seconds"] for s in stage_summary
            ),
            reserved_activation_scope_peak_bytes=[
                s["peak_declared_reserved_bytes"] for s in stage_summary
            ],
            complete_training_activation_peak_bytes=None,
            measured_runtime_seconds=None,
        ),
        assumptions=[
            "Fixed non-interleaved synchronous PP4; one compute stream per stage, nonpreemptive events. Optimizer is one logical update after every microbatch gradient, with parallel stage-local updates. No stale weights.",
            "Service times are explicit conditional inputs, not vendor peaks or measurements. F/B services include the selected nonlinear recompute policy, parameter accumulation, label handling and any unexpanded kernels; the scalar/matrix work ledger does not derive these seconds.",
            "GPipe runs all forwards before reverse-order backwards. 1F1B uses stage-dependent warmup, FIFO microbatch backwards and cooldown. Compute and links overlap subject to dependencies and declared unary resources.",
            "Independent directional mode gives each boundary/direction a dedicated serialized link. Shared half duplex uses one resource for every boundary and direction. Deterministic earliest-ready tie ordering is part of the contract; no claim of globally optimal communication arbitration.",
            "Saved bytes reuse public nonlinear objects and optional explicit extra bytes. Reserve the entire per-stage subset from forward START through backward END. This is a deliberate conservative reservation, not exact within-stage allocation times or full model peak.",
            "Recompute_silu only replaces saved nonlinear SiLU state and reserves one layer temporary pair throughout B. It is not full-layer checkpointing. Do not infer lower service time from reduced saved bytes.",
            "Transfers use separate packed BF16 hidden activation and FP32 hidden-gradient buffers. Receiver buffer starts at transfer START and is released at consumer START; sender is live from producer END to transfer END. Copies into internal backward state are outside the partial memory ledger.",
            "RoPE table work is once per step; setup_seconds includes distribution or an explicitly supplied local preparation strategy. Embedding belongs to stage0, head/final norm/loss to stage3. Dense full-token supervision, no historical KV, no MoE.",
            "Gradient contributions use equal per-microbatch mean losses then average gradients once before update. Accumulation counts are separate from each public per-microbatch VJP; update hyperparameter coefficients execute once, not M times.",
            "Idle time includes fill/drain, ordering and dependency waits; exposed transfer is a counterfactual makespan difference, not the sum of link busy times. Parameter/optimizer state, GEMM saved inputs not explicitly supplied, full temporary gradients and allocator workspaces are excluded from reported activation peak.",
        ],
    )


def markdown(result):
    lines = [
        "# Qwen3-8B PP4 training schedule",
        "",
        "Conditional GPipe/1F1B event execution and declared activation reservations; not measured runtime.",
        "",
        "| Field | Value |",
        "|---|---|",
    ]

    def visit(value, path=""):
        if isinstance(value, dict) and value:
            for key, item in value.items():
                visit(item, f"{path}.{key}" if path else key)
        elif isinstance(value, list) and value:
            for i, item in enumerate(value):
                visit(item, f"{path}[{i}]")
        else:
            text = "unknown (null)" if value is None else str(value)
            lines.append(
                f"| {path} | "
                + text.replace("|", "&#124;").replace("\n", "<br>")
                + " |"
            )

    visit(result)
    return "\n".join(lines) + "\n"
