"""Untrained expert-granularity variants around the fixed Qwen235 checkpoint."""

import json
import math
from collections import Counter, defaultdict
from fractions import Fraction

from infra_calc.models import qwen3_moe
from infra_calc.sources import model_config
from infra_calc.topics import (
    architecture_variants,
    qwen235_execution,
    qwen235_placement,
)


def calculate(
    experts=128,
    top_k=8,
    alignment=128,
    tp=2,
    ep=4,
    pp=1,
    requests=1,
    tokens=16,
    length=8192,
    capacity_bytes=80 * 10**9,
    workspace_bytes=2 * 2**30,
    route_policy="balanced",
    routes=None,
    wire_element_bytes=2,
    row_metadata_bytes=16,
):
    for name, value in dict(
        experts=experts,
        top_k=top_k,
        alignment=alignment,
        requests=requests,
        tokens=tokens,
        wire_element_bytes=wire_element_bytes,
    ).items():
        if type(value) is not int or value <= 0:
            raise ValueError(f"{name} requires a positive integer")
    if (
        type(row_metadata_bytes) is not int
        or row_metadata_bytes < 0
        or top_k > experts
        or tokens > length
    ):
        raise ValueError("Invalid route/metadata/token range")
    c = model_config(qwen235_placement.MODEL)
    h, f0, e0, k0, layers = [
        c[key]
        for key in (
            "hidden_size",
            "moe_intermediate_size",
            "num_experts",
            "num_experts_per_tok",
            "num_hidden_layers",
        )
    ]
    placement = qwen235_placement.calculate(
        tp=tp,
        ep=ep,
        pp=pp,
        length=length,
        capacity_bytes=capacity_bytes,
        workspace_bytes=workspace_bytes,
    )
    if experts % ep:
        raise ValueError("EP must divide variant expert count")
    ideal = Fraction(e0 * f0, experts)
    f = f0 if experts == e0 else architecture_variants.nearest_aligned(ideal, alignment)
    if f % tp:
        raise ValueError("TP must divide aligned expert intermediate width")
    r = requests * tokens
    table = (
        qwen235_execution.synthetic_routes(
            layers, requests, tokens, experts, top_k, route_policy
        )
        if routes is None
        else routes
    )
    if not isinstance(table, list) or len(table) != layers * r:
        raise ValueError("Require complete per-layer cohort route table")
    keyed = {}
    for record in table:
        if not isinstance(record, dict) or set(record) != {
            "layer",
            "request_id",
            "position",
            "experts",
            "weights",
        }:
            raise ValueError("Invalid record schema")
        identity = tuple(record[key] for key in ("layer", "request_id", "position"))
        if (
            any(
                type(v) is not int or not 0 <= v < bound
                for v, bound in zip(identity, (layers, requests, tokens))
            )
            or identity in keyed
        ):
            raise ValueError("Invalid/duplicate route identity")
        ids, weights = record["experts"], record["weights"]
        if (
            not isinstance(ids, list)
            or len(ids) != top_k
            or any(type(i) is not int or not 0 <= i < experts for i in ids)
            or len(set(ids)) != top_k
        ):
            raise ValueError("Expected distinct valid expert IDs")
        if (
            not isinstance(weights, list)
            or len(weights) != top_k
            or any(
                isinstance(w, bool)
                or not isinstance(w, (int, float))
                or not math.isfinite(w)
                or w < 0
                for w in weights
            )
            or not math.isclose(sum(weights), 1.0, abs_tol=1e-12, rel_tol=1e-10)
        ):
            raise ValueError("Expected finite normalized route weights")
        keyed[identity] = record
    table = [keyed[key] for key in sorted(keyed)]
    by_layer = defaultdict(list)
    for row in table:
        by_layer[row["layer"]].append(row)
    ranks = []
    for rr in placement["ranks"]:
        count = rr["layer_range"][1] - rr["layer_range"][0]
        old_expert = sum(
            t["storage"][0]["total_bytes"]
            for t in rr["tensors"]
            if t["category"] == "expert"
        )
        old_router = sum(
            t["storage"][0]["total_bytes"]
            for t in rr["tensors"]
            if t["category"] == "router"
        )
        nonvariant = rr["formats"][0]["weight_bytes"] - old_expert - old_router
        expert_bytes = 2 * count * (experts // ep) * 3 * h * (f // tp)
        router_bytes = 2 * count * experts * h
        weight = nonvariant + expert_bytes + router_bytes
        kv = requests * rr["formats"][0]["kv_bytes_per_request"]
        ranks.append(
            dict(
                rank=rr["rank"],
                pipeline_stage=rr["pipeline_stage"],
                expert_rank=rr["expert_rank"],
                tensor_rank=rr["tensor_rank"],
                layer_range=rr["layer_range"],
                expert_range=[
                    rr["expert_rank"] * (experts // ep),
                    (rr["expert_rank"] + 1) * (experts // ep),
                ],
                unchanged_weight_bytes=nonvariant,
                expert_weight_bytes=expert_bytes,
                replicated_router_weight_bytes=router_bytes,
                total_bf16_weight_bytes=weight,
                bf16_kv_bytes=kv,
                workspace_reserved_bytes=workspace_bytes,
                conditional_resident_bytes=weight + kv + workspace_bytes,
                necessary_capacity_fits=weight + kv + workspace_bytes <= capacity_bytes,
                expert_matrix_flops=0,
                expert_matrices=[],
            )
        )

    def rank(stage, owner, tensor):
        return (stage * ep + owner) * tp + tensor

    stages = {
        layer: rr["pipeline_stage"]
        for rr in ranks
        for layer in range(*rr["layer_range"])
    }
    messages = []

    def send(layer, phase, source, target, ids):
        ids = sorted(ids)
        if not ids or source == target:
            return
        messages.append(
            dict(
                layer=layer,
                phase=phase,
                source=source,
                target=target,
                token_ids=ids,
                payload_bytes=len(ids) * h * wire_element_bytes,
                metadata_bytes=len(ids) * row_metadata_bytes,
                wire_bytes=len(ids) * (h * wire_element_bytes + row_metadata_bytes),
            )
        )

    histograms = []
    for layer in range(layers):
        histogram = [0] * experts
        active = [set() for _ in range(ep)]
        for row in by_layer[layer]:
            token = row["request_id"] * tokens + row["position"]
            for expert in row["experts"]:
                histogram[expert] += 1
                active[expert // (experts // ep)].add(token)
        qwen3_moe.routing_counts(r, experts, top_k, "explicit", histogram)
        histograms.append(
            dict(
                layer=layer,
                counts=histogram,
                token_destinations=[
                    dict(
                        token=i,
                        ep_owners=[owner for owner in range(ep) if i in active[owner]],
                    )
                    for i in range(r)
                ],
            )
        )
        stage = stages[layer]
        for owner in range(ep):
            for tensor in range(tp):
                rr = ranks[rank(stage, owner, tensor)]
                for expert in range(*rr["expert_range"]):
                    n = histogram[expert]
                    per = 2 * n * h * (f // tp)
                    rr["expert_matrix_flops"] += 3 * per
                    rr["expert_matrices"].append(
                        dict(
                            layer=layer,
                            expert=expert,
                            token_rows=n,
                            gate=dict(
                                input=[n, h],
                                weight=[f // tp, h],
                                output=[n, f // tp],
                                flops=per,
                            ),
                            up=dict(
                                input=[n, h],
                                weight=[f // tp, h],
                                output=[n, f // tp],
                                flops=per,
                            ),
                            down=dict(
                                input=[n, f // tp],
                                weight=[h, f // tp],
                                output=[n, h],
                                flops=per,
                            ),
                        )
                    )
            for tensor in range(1, tp):
                send(
                    layer,
                    "tp_reduce",
                    rank(stage, owner, tensor),
                    rank(stage, owner, 0),
                    active[owner],
                )
        for owner in range(1, ep):
            send(
                layer,
                "ep_reduce",
                rank(stage, owner, 0),
                rank(stage, 0, 0),
                active[owner],
            )
        for owner in range(1, ep):
            send(
                layer,
                "ep_broadcast",
                rank(stage, 0, 0),
                rank(stage, owner, 0),
                range(r),
            )
        for owner in range(ep):
            for tensor in range(1, tp):
                send(
                    layer,
                    "tp_broadcast",
                    rank(stage, owner, 0),
                    rank(stage, owner, tensor),
                    range(r),
                )
        if layer + 1 < layers and stages[layer + 1] != stage:
            send(
                layer, "pp_transfer", rank(stage, 0, 0), rank(stage + 1, 0, 0), range(r)
            )
            for target in range(
                rank(stage + 1, 0, 0) + 1, rank(stage + 1, 0, 0) + tp * ep
            ):
                send(layer, "pp_replicate", rank(stage + 1, 0, 0), target, range(r))
    original = placement["evidence"]["unique_parameters"]
    expert_budget = layers * 3 * h * experts * f
    target = layers * 3 * h * e0 * f0
    router = layers * h * experts
    total = original - target - layers * h * e0 + expert_budget + router
    expected = layers * 6 * r * top_k * h * f
    assert sum(rr["expert_matrix_flops"] for rr in ranks) == expected
    busiest = max(rr["expert_matrix_flops"] for rr in ranks)
    return dict(
        schema="qwen235-expert-granularity-v1",
        scenario=dict(
            experts=experts,
            top_k=top_k,
            alignment=alignment,
            tp=tp,
            ep=ep,
            pp=pp,
            requests=requests,
            tokens=tokens,
            length=length,
            capacity_bytes=capacity_bytes,
            workspace_bytes=workspace_bytes,
            route_policy=route_policy,
            routes=routes,
            wire_element_bytes=wire_element_bytes,
            row_metadata_bytes=row_metadata_bytes,
        ),
        sources=placement["sources"],
        baseline_checkpoint_evidence=placement["evidence"],
        geometry=dict(
            hidden=h,
            layers=layers,
            experts=experts,
            intermediate=f,
            top_k=top_k,
            ideal_intermediate_exact=str(ideal),
            baseline_experts=e0,
            baseline_intermediate=f0,
            baseline_top_k=k0,
        ),
        parameters=dict(
            baseline_total=original,
            variant_total=total,
            total_delta=total - original,
            expert_target=target,
            expert_total=expert_budget,
            expert_delta=expert_budget - target,
            expert_relative_delta_exact=str(Fraction(expert_budget - target, target)),
            expert_alignment_error_bound_exact=str(
                Fraction(layers * 3 * h * experts * alignment, 2)
            ),
            exact_expert_budget=expert_budget == target,
            router_total=router,
            unchanged_nonexpert_nonrouter_total=original - target - layers * h * e0,
            active_expert_parameters_per_token_all_layers=layers * top_k * 3 * h * f,
            active_expert_parameters_per_token_per_layer=top_k * 3 * h * f,
        ),
        route_table=table,
        histograms=histograms,
        ranks=ranks,
        messages=messages,
        summary=dict(
            assignments=layers * r * top_k,
            expert_matrix_flops=expected,
            router_matrix_flops_per_logical_cohort=2 * layers * r * h * experts,
            router_matrix_flops_if_executed_on_all_tp_ep_replicas=2
            * layers
            * r
            * h
            * experts
            * tp
            * ep,
            total_wire_bytes=sum(msg["wire_bytes"] for msg in messages),
            dispatch_wire_bytes=0,
            busiest_expert_compute_ranks=[
                rr["rank"] for rr in ranks if rr["expert_matrix_flops"] == busiest
            ],
            all_necessary_capacity_fits=all(
                rr["necessary_capacity_fits"] for rr in ranks
            ),
            actual_runtime_seconds=None,
            actual_peak_bytes=None,
            trained_quality=None,
            tensor_core_utilization=None,
        ),
        scope=[
            "Only E128/F1536/K8 matches the released expert architecture; changed E/F/K is untrained and not a checkpoint conversion. Baseline configuration H/L/attention/vocabulary/KV and exact checkpoint index remain fixed.",
            "Expert parameter budget is nearest aligned E*F target; changing E also changes the full router matrix, so exact expert-budget equality does not imply exact total-model equality. Both deltas are reported.",
            "Active parameters refer specifically to K expert matrices per token, not embedding rows/head/norm or a full-model activated-parameter marketing label.",
            "Same-cohort replicated attention inputs across EP/TP need no dispatch. TP partial reduction, EP sum/broadcast and TP broadcast use actual unique token sets. PP hidden transfer plus next-stage fanout occurs once per boundary; no independent EP request cohorts.",
            "Wire bytes follow public qwen235_execution ownership policy, but do not claim measured communication or equivalent rounded numerics. Router full-score GEMM is separately reported for logical cohort and explicit all-replica execution; no top-k implementation FLOPs are guessed.",
            "Per-rank BF16 weights replace only expert/router terms of verified placement; all attention/norm/endpoint weights and KV keep original physical replication. Workspace remains an unproved caller reserve; success is necessary-only.",
            "No trained quality, actual Tensor Core utilization, tile padding, scalar/router selection runtime, full forward latency or real peak is inferred. Matrix shapes are sufficient inputs for a later explicitly chosen kernel model, not performance predictions.",
        ],
    )


def markdown(result):
    return (
        "# Qwen235 expert granularity\n\nOnly the baseline is a released checkpoint; variants are untrained designs.\n\n```json\n"
        + json.dumps(result, indent=2, allow_nan=False)
        + "\n```\n"
    )
