"""Same-cohort Qwen235 expert execution joined to eight-rank placement."""

import json
import math
from collections import Counter, defaultdict

from infra_calc.sources import model_config
from infra_calc.topics import qwen235_placement


def _positive(value, name, allow_zero=False):
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(value)
        or value < 0
        or (not allow_zero and value == 0)
    ):
        raise ValueError(f"Invalid {name}")


def synthetic_routes(layers, requests, tokens, experts, top_k, policy):
    """Explicit synthetic IDs, never called observed checkpoint routing."""
    if policy not in ("balanced", "hot"):
        raise ValueError("Unknown synthetic policy")
    result = []
    for layer in range(layers):
        for request in range(requests):
            for position in range(tokens):
                row = request * tokens + position
                ids = (
                    [(row * top_k + j) % experts for j in range(top_k)]
                    if policy == "balanced"
                    else list(range(top_k))
                )
                result.append(
                    dict(
                        layer=layer,
                        request_id=request,
                        position=position,
                        experts=ids,
                        weights=[1 / top_k] * top_k,
                    )
                )
    return result


def calculate(
    tp=2,
    ep=4,
    pp=1,
    requests=1,
    tokens=16,
    length=8192,
    capacity_bytes=80 * 10**9,
    workspace_bytes=2 * 2**30,
    routes=None,
    route_policy="balanced",
    wire_element_bytes=2,
    row_metadata_bytes=16,
    link_bytes_per_second=100e9,
    startup_seconds=1e-6,
    rank_matrix_flops_per_second=100e12,
):
    for name, value in dict(
        requests=requests, tokens=tokens, wire_element_bytes=wire_element_bytes
    ).items():
        if type(value) is not int or value <= 0:
            raise ValueError(f"{name} must be a positive integer")
    if type(row_metadata_bytes) is not int or row_metadata_bytes < 0:
        raise ValueError("row metadata must be nonnegative integer bytes")
    if tokens > length:
        raise ValueError("Current tokens exceed retained sequence length")
    for name, value in dict(
        link_bytes_per_second=link_bytes_per_second,
        rank_matrix_flops_per_second=rank_matrix_flops_per_second,
    ).items():
        _positive(value, name)
    _positive(startup_seconds, "startup_seconds", True)
    placement = qwen235_placement.calculate(
        tp=tp,
        ep=ep,
        pp=pp,
        length=length,
        capacity_bytes=capacity_bytes,
        workspace_bytes=workspace_bytes,
    )
    config = model_config(qwen235_placement.MODEL)
    h, f, e, k, layers = [
        config[key]
        for key in (
            "hidden_size",
            "moe_intermediate_size",
            "num_experts",
            "num_experts_per_tok",
            "num_hidden_layers",
        )
    ]
    r = requests * tokens
    table = (
        synthetic_routes(layers, requests, tokens, e, k, route_policy)
        if routes is None
        else routes
    )
    if not isinstance(table, list) or len(table) != layers * r:
        raise ValueError("One route record for every layer/request/position required")
    keyed = {}
    for record in table:
        if not isinstance(record, dict) or set(record) != {
            "layer",
            "request_id",
            "position",
            "experts",
            "weights",
        }:
            raise ValueError("Invalid route record schema")
        identity = tuple(record[key] for key in ("layer", "request_id", "position"))
        for value, bound in zip(identity, (layers, requests, tokens)):
            if type(value) is not int or not 0 <= value < bound:
                raise ValueError("Route identity outside declared cohort")
        if identity in keyed:
            raise ValueError("Duplicate route identity")
        ids, weights = record["experts"], record["weights"]
        if (
            not isinstance(ids, list)
            or len(ids) != k
            or len(set(ids)) != k
            or any(type(i) is not int or not 0 <= i < e for i in ids)
        ):
            raise ValueError("Routes require distinct valid expert IDs")
        if not isinstance(weights, list) or len(weights) != k:
            raise ValueError("Wrong route weight count")
        for weight in weights:
            _positive(weight, "route weight", True)
        if not math.isclose(sum(weights), 1.0, rel_tol=1e-10, abs_tol=1e-12):
            raise ValueError("Qwen selected normalized route weights must sum to one")
        keyed[identity] = record
    table = [keyed[key] for key in sorted(keyed)]
    by_layer = defaultdict(list)
    for row in table:
        by_layer[row["layer"]].append(row)
    ranks = placement["ranks"]

    def rank(stage, owner, tensor):
        return (stage * ep + owner) * tp + tensor

    layer_stage = {
        layer: rr["pipeline_stage"]
        for rr in ranks
        for layer in range(*rr["layer_range"])
    }
    rank_work = [Counter() for _ in ranks]
    rank_expert_rows = [[] for _ in ranks]
    messages = []
    phases = []
    token_identity = {str(i): [i // tokens, i % tokens] for i in range(r)}

    def message(layer, phase, source, target, selected):
        selected = sorted(selected)
        if source == target or not selected:
            return
        payload = len(selected) * h * wire_element_bytes
        metadata = len(selected) * row_metadata_bytes
        messages.append(
            dict(
                layer=layer,
                phase=phase,
                source=source,
                target=target,
                token_ids=selected,
                payload_bytes=payload,
                metadata_bytes=metadata,
                wire_bytes=payload + metadata,
                conditional_service_seconds=startup_seconds
                + (payload + metadata) / link_bytes_per_second,
            )
        )

    for layer in range(layers):
        stage = layer_stage[layer]
        histogram = Counter()
        active = defaultdict(set)
        for row in by_layer[layer]:
            token = row["request_id"] * tokens + row["position"]
            for expert in row["experts"]:
                histogram[expert] += 1
                active[expert // (e // ep)].add(token)
        layer_flops = {}
        for owner in range(ep):
            for tensor in range(tp):
                device = rank(stage, owner, tensor)
                local = 0
                for expert in range(owner * (e // ep), (owner + 1) * (e // ep)):
                    n = histogram[expert]
                    work = 6 * n * h * (f // tp)
                    rank_expert_rows[device].append(
                        dict(
                            layer=layer,
                            expert=expert,
                            rows=n,
                            gate_up_input=[n, h],
                            gate_up_weight=[f // tp, h],
                            down_input=[n, f // tp],
                            down_weight=[h, f // tp],
                            matrix_flops=work,
                            matrix_operand_interfaces=dict(
                                weight_bf16_read_bytes=6 * h * (f // tp) if n else 0,
                                activation_fp32_read_bytes=4
                                * (2 * n * h + n * (f // tp)),
                                activation_fp32_write_bytes=4
                                * (2 * n * (f // tp) + n * h),
                            ),
                        )
                    )
                    local += work
                rank_work[device]["expert_matrix_flops"] += local
                rank_work[device]["expert_sigmoid_calls"] += sum(
                    histogram[x]
                    for x in range(owner * (e // ep), (owner + 1) * (e // ep))
                ) * (f // tp)
                rank_work[device]["expert_silu_product_scalar_operations"] += (
                    2
                    * sum(
                        histogram[x]
                        for x in range(owner * (e // ep), (owner + 1) * (e // ep))
                    )
                    * (f // tp)
                )
                # Qwen routing weight is applied after the down projection.
                rank_work[device][
                    "route_weight_and_zero_accumulation_scalar_operations"
                ] += (
                    2
                    * sum(
                        histogram[x]
                        for x in range(owner * (e // ep), (owner + 1) * (e // ep))
                    )
                    * h
                )
                layer_flops[device] = local
            # Sum TP partial down outputs only where this EP has contributions.
            for tensor in range(1, tp):
                message(
                    layer,
                    "tp_reduce",
                    rank(stage, owner, tensor),
                    rank(stage, owner, 0),
                    active[owner],
                )
            rank_work[rank(stage, owner, 0)]["tp_reduction_scalar_adds"] += (
                len(active[owner]) * h * (tp - 1)
            )
        for owner in range(1, ep):
            message(
                layer,
                "ep_reduce",
                rank(stage, owner, 0),
                rank(stage, 0, 0),
                active[owner],
            )
            rank_work[rank(stage, 0, 0)]["ep_reduction_scalar_adds"] += (
                len(active[owner]) * h
            )
        # Every EP needs every token before its next replicated attention layer.
        for owner in range(1, ep):
            message(
                layer,
                "ep_broadcast",
                rank(stage, 0, 0),
                rank(stage, owner, 0),
                range(r),
            )
        for owner in range(ep):
            for tensor in range(1, tp):
                message(
                    layer,
                    "tp_broadcast",
                    rank(stage, owner, 0),
                    rank(stage, owner, tensor),
                    range(r),
                )
        phases.append(
            dict(
                layer=layer,
                phase="expert_matrices",
                conditional_bound_seconds=max(layer_flops.values())
                / rank_matrix_flops_per_second,
            )
        )
        for phase in ("tp_reduce", "ep_reduce", "ep_broadcast", "tp_broadcast"):
            selected = [
                msg
                for msg in messages
                if msg["layer"] == layer and msg["phase"] == phase
            ]
            # Shared injection at each source/destination, full-duplex independent NICs.
            outgoing, incoming = Counter(), Counter()
            for msg in selected:
                outgoing[msg["source"]] += msg["conditional_service_seconds"]
                incoming[msg["target"]] += msg["conditional_service_seconds"]
            phases.append(
                dict(
                    layer=layer,
                    phase=phase,
                    conditional_bound_seconds=max(
                        [0.0] + list(outgoing.values()) + list(incoming.values())
                    ),
                )
            )
        if layer + 1 < layers and layer_stage[layer + 1] != stage:
            target_stage = stage + 1
            message(
                layer,
                "pp_transfer",
                rank(stage, 0, 0),
                rank(target_stage, 0, 0),
                range(r),
            )
            for target in range(
                rank(target_stage, 0, 0) + 1, rank(target_stage, 0, 0) + tp * ep
            ):
                message(
                    layer, "pp_replicate", rank(target_stage, 0, 0), target, range(r)
                )
            for phase in ("pp_transfer", "pp_replicate"):
                selected = [
                    msg
                    for msg in messages
                    if msg["layer"] == layer and msg["phase"] == phase
                ]
                phases.append(
                    dict(
                        layer=layer,
                        phase=phase,
                        conditional_bound_seconds=sum(
                            msg["conditional_service_seconds"] for msg in selected
                        ),
                    )
                )
    per_rank = []
    for rr, work, expert_rows in zip(ranks, rank_work, rank_expert_rows):
        fmt = rr["formats"][0]
        residency = (
            fmt["weight_bytes"]
            + workspace_bytes
            + requests * fmt["kv_bytes_per_request"]
        )
        per_rank.append(
            dict(
                rank=rr["rank"],
                pipeline_stage=rr["pipeline_stage"],
                expert_rank=rr["expert_rank"],
                tensor_rank=rr["tensor_rank"],
                layer_range=rr["layer_range"],
                expert_range=rr["expert_range"],
                work=dict(work),
                experts=expert_rows,
                bf16_weight_bytes=fmt["weight_bytes"],
                bf16_kv_bytes=requests * fmt["kv_bytes_per_request"],
                workspace_reserved_bytes=workspace_bytes,
                conditional_resident_bytes=residency,
                necessary_capacity_fits=residency <= capacity_bytes,
                sent_wire_bytes=sum(
                    msg["wire_bytes"] for msg in messages if msg["source"] == rr["rank"]
                ),
                received_wire_bytes=sum(
                    msg["wire_bytes"] for msg in messages if msg["target"] == rr["rank"]
                ),
            )
        )
    scenario = dict(
        tp=tp,
        ep=ep,
        pp=pp,
        requests=requests,
        tokens=tokens,
        length=length,
        capacity_bytes=capacity_bytes,
        workspace_bytes=workspace_bytes,
        routes=routes,
        route_policy=route_policy,
        wire_element_bytes=wire_element_bytes,
        row_metadata_bytes=row_metadata_bytes,
        link_bytes_per_second=link_bytes_per_second,
        startup_seconds=startup_seconds,
        rank_matrix_flops_per_second=rank_matrix_flops_per_second,
    )
    maximum = max(row["work"].get("expert_matrix_flops", 0) for row in per_rank)
    if any(
        not math.isfinite(phase["conditional_bound_seconds"]) for phase in phases
    ) or not math.isfinite(sum(phase["conditional_bound_seconds"] for phase in phases)):
        raise ValueError("Conditional resource bound exceeds finite numeric range")
    return dict(
        schema="qwen235-cohort-execution-v1",
        scenario=scenario,
        sources=placement["sources"],
        placement_evidence=placement["evidence"],
        route_table=table,
        token_identity=token_identity,
        ranks=per_rank,
        messages=messages,
        phases=phases,
        summary=dict(
            assignments=layers * r * k,
            expert_matrix_flops=sum(
                row["work"].get("expert_matrix_flops", 0) for row in per_rank
            ),
            expected_unique_expert_matrix_flops=layers * 6 * r * k * h * f,
            busiest_expert_compute_ranks=[
                row["rank"]
                for row in per_rank
                if row["work"].get("expert_matrix_flops", 0) == maximum
            ],
            dispatch_wire_bytes=0,
            total_wire_bytes=sum(msg["wire_bytes"] for msg in messages),
            conditional_phase_barrier_bound_seconds=sum(
                phase["conditional_bound_seconds"] for phase in phases
            ),
            all_necessary_capacity_fits=all(
                row["necessary_capacity_fits"] for row in per_rank
            ),
            full_request_runtime_seconds=None,
            actual_peak_bytes=None,
        ),
        metadata=dict(
            route_table_logical_bytes=layers * r * (24 + 8 * k),
            route_record_format="int64 layer/request/position, int32 expert ID + FP32 normalized weight per selection",
            transport_row_metadata_bytes=row_metadata_bytes,
            route_table_replication="logical host/input table; GPU materialization and distribution not inferred",
        ),
        scope=[
            "One same cohort across EP/TP; input to each MoE layer is already replicated attention output. No fabricated dispatch or separate EP data-parallel throughput.",
            "Expert subaccount only. Attention/router/norm/embedding/head arithmetic and their TP collectives remain outside; last layer produces replicated hidden values ready for head, not logits. Routes are explicit conditional inputs, not measured routing.",
            "TP reduces weighted local down outputs, EP combines active-token contributions, then EP/TP broadcast complete outputs. Scalar weighting is performed on partial down outputs: algebraically equivalent in real arithmetic, not a BF16 rounding-equivalence claim.",
            "Declared FP32 mathematical expert/reduction arithmetic; configurable wire element bytes is storage/transport, with rounding/cast work not simulated. No low-bit execution inferred from placement storage.",
            "PP transport represents completed block hidden values; omitted attention/residual/norm computations produce these values externally. PP transfer is a single root-to-root hidden transfer per boundary, with next-stage replication separately charged. Missing attention computations occur between these MoE subgraphs; the phase barrier sum is a conditional subaccount bound, not whole-model wall time.",
            "Resource inputs are scenario assumptions, not official measured device throughput. Full-duplex per-rank send/receive service, sequential named phases, no overlapping layers. Missing scalar/selection/packing/cast rates prevent a complete runtime bound.",
            "BF16 placement weights and per-request KV match the exact same layout; workspace is a caller reservation, not proven sufficient. Capacity failure is a necessary rejection, success is necessary-only. Communication allocations, gradient/state and runtime peak are not inferred.",
        ],
    )


def markdown(result):
    return (
        "# Qwen235 same-cohort expert execution\n\nConditional expert matrices, message ownership and necessary capacity; full runtime unknown.\n\n```json\n"
        + json.dumps(result, indent=2, allow_nan=False)
        + "\n```\n"
    )
