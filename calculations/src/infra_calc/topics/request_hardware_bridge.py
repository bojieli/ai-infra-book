"""Original four-model request arithmetic to conditional H100 resource ceilings."""

import json
from collections import Counter

from infra_calc import hardware
from infra_calc.models import qwen3
from infra_calc.schema import Scenario
from infra_calc.sources import model_config
from infra_calc.topics import (
    request_model_comparison,
    stage_resource_bounds,
    v4_prefix_continuation,
)

V4_FP8 = {"wq_a", "wq_b", "wkv_shared", "wo_b", "index_wq_b"}
V4_BF16 = {"wo_a_grouped", "index_weights_proj"}
V4_FP32 = {
    "compress_r128_wgate",
    "compress_r128_wkv",
    "compress_r4_wgate",
    "compress_r4_wkv",
    "index_compress_wgate",
    "index_compress_wkv",
}


def v4_matrices(ledger, groups=None):
    records = []

    def add(path, name, flops, bucket, layer_ids=None):
        records.append(
            dict(
                source_path=path,
                name=name,
                matrix_flops=flops,
                bucket=bucket,
                layer_ids=layer_ids,
            )
        )

    c = ledger["components"]
    for i, row in enumerate(c["attention"]["matrices"]):
        name = row["name"]
        bucket = (
            "matrix_fp8"
            if name in V4_FP8
            else (
                "matrix_bf16"
                if name in V4_BF16
                else "matrix_fp32" if name in V4_FP32 else "unclassified_matrix"
            )
        )
        add(
            f"components.attention.matrices[{i}]",
            name,
            row["matrix_flops"],
            bucket,
            row["layer_ids"],
        )
    for i, row in enumerate(
        c["attention"]["attention_layer_groups"] if groups is None else groups
    ):
        for key in ("qk_and_pv_matrix_flops", "actual_index_rectangular_matrix_flops"):
            add(
                f"components.attention.attention_layer_groups[{i}].{key}",
                key,
                row[key],
                "matrix_bf16",
                row["layer_ids"],
            )
    for i, row in enumerate(c["experts"]["matrices"]):
        bucket = (
            "matrix_fp32"
            if row["name"] == "router"
            else (
                "matrix_fp8"
                if row["name"]
                in {
                    "routed_gate",
                    "routed_up",
                    "routed_down",
                    "shared_gate",
                    "shared_up",
                    "shared_down",
                }
                else "unclassified_matrix"
            )
        )
        add(
            f"components.experts.matrices[{i}]",
            row["name"],
            row["matrix_flops"],
            bucket,
            row["layer_ids"],
        )
    for i, row in enumerate(c["hyper_connections"]["residual_operations"]):
        add(
            f"components.hyper_connections.residual_operations[{i}]",
            row["name"],
            row["matrix_flops"],
            "matrix_fp32",
        )
    add(
        "summary.vocabulary_head_matrix_flops",
        "last_logits",
        ledger["summary"]["vocabulary_head_matrix_flops"],
        "matrix_fp32",
    )
    return records


def qwen_matrices(ledger):
    return [
        dict(
            source_path=f"operators[{i}]",
            name=row["name"],
            matrix_flops=row["matrix_flops"] * row["repeats"],
            bucket=(
                "matrix_pv_mixed_or_unresolved"
                if row["name"] == "pv"
                else "matrix_bf16"
            ),
            shapes=row["shapes"],
            repeats=row["repeats"],
        )
        for i, row in enumerate(ledger["operators"])
        if row["matrix_flops"]
    ]


def k3_matrices(ledger, total=None):
    components = dict(ledger["matrix_components"])
    if total is not None:
        components["mla"] = total - sum(
            value for key, value in components.items() if key != "mla"
        )
    router = sum(
        row["matrix_flops"]
        for row in ledger["components"]["experts"]["matrices"]
        if row["name"] == "router"
    )
    records = [
        dict(
            source_path="components.experts.matrices[name=router]",
            name="router",
            matrix_flops=router,
            bucket="matrix_fp32",
        )
    ]
    for name, amount in components.items():
        if name == "experts":
            amount -= router
        if amount < 0:
            raise AssertionError("Negative component work")
        records.append(
            dict(
                source_path="matrix_components." + name,
                name=name + ("_excluding_router" if name == "experts" else ""),
                matrix_flops=amount,
                bucket="unclassified_matrix",
            )
        )
    return records


def map_call(
    model, position, total, ledger, kind, scalar_provider, fp32_provider, groups=None
):
    records = (
        qwen_matrices(ledger)
        if model == "qwen3-8b"
        else (
            v4_matrices(ledger, groups)
            if model.startswith("deepseek")
            else k3_matrices(
                ledger, total["matrix_flops"] if kind == "decode" else None
            )
        )
    )
    buckets = Counter()
    for row in records:
        buckets[row["bucket"]] += row["matrix_flops"]
    if sum(buckets.values()) != total["matrix_flops"]:
        raise AssertionError(f"{model} {kind} matrix mapping lost work")
    work = Counter()
    for bucket, amount in buckets.items():
        resource = (
            "vector_fp32" if bucket == "matrix_fp32" and fp32_provider else bucket
        )
        work[resource] += amount
    scalar_resource = "vector_fp32" if scalar_provider else "ordinary_scalar_unresolved"
    work[scalar_resource] += total["accounted_scalar_flops"]
    for name, amount in total["special_ops"].items():
        work["special:" + name] += amount
    work["physical_hbm_bytes"] = None
    return dict(
        id=f"{kind}:{position}",
        input_position=position,
        matrix_records=records,
        matrix_buckets=dict(buckets),
        ordinary_scalar_flops=total["accounted_scalar_flops"],
        special_ops=total["special_ops"],
        work=dict(work),
        known_interfaces=total.get("known_interfaces", {}),
    )


def calculate(
    output_tokens=4,
    scalar_vector_provider=False,
    fp32_matrix_vector_provider=False,
    capacity_bytes=None,
):
    if output_tokens not in (1, 4) or type(output_tokens) is not int:
        raise ValueError("Fixed G1 or G4 scenarios only")
    if (
        type(scalar_vector_provider) is not bool
        or type(fp32_matrix_vector_provider) is not bool
    ):
        raise ValueError("Provider switches must be bool")
    if capacity_bytes is not None and (
        type(capacity_bytes) is not int or capacity_bytes <= 0
    ):
        raise ValueError("Capacity override must be positive bytes")
    original = request_model_comparison.calculate(
        prefix_tokens=0,
        new_tokens=128,
        output_tokens=output_tokens,
        batch=1,
        k3_mla_path="expanded",
        routing="balanced",
    )
    device = hardware.select_device("h100-sxm")
    admitted = {}
    rates = {}
    for resource, precision, unit in (
        ("matrix_bf16", "BF16", "tensor"),
        ("matrix_fp8", "FP8", "tensor"),
        ("vector_fp32", "FP32", "vector"),
    ):
        peak = hardware.select_peak(device, precision, "FP32", unit, "dense")
        admitted[resource] = peak
        rates[resource] = peak["tera_ops_per_second"] * 1e12
    rates["physical_hbm_bytes"] = device["memory"]["bandwidth_bytes_per_second"]
    capacity = (
        (
            device["memory"]["nominal_capacity"] * 10**9
            if device["memory"]["nominal_capacity"] is not None
            else None
        )
        if capacity_bytes is None
        else capacity_bytes
    )
    models = []
    for comparison in original["comparisons"]:
        model = comparison["model"]
        prefill = comparison["prefill"]
        ledger = prefill["source_ledger"]
        calls = [
            map_call(
                model,
                0,
                prefill["totals"],
                ledger,
                "prefill",
                scalar_vector_provider,
                fp32_matrix_vector_provider,
            )
        ]
        for row in comparison["decode"]["rows"]:
            position = row["input_position"]
            groups = None
            if model == "qwen3-8b":
                step = qwen3.calculate(
                    model, Scenario(batch=1, tokens=1, history=position)
                )
            elif model.startswith("deepseek"):
                step = comparison["decode"]["source_ledger"]["static_base_forward"]
                config = model_config(model, reference=True)
                groups = v4_prefix_continuation.attention_step(
                    config, 1, position, step["components"]["attention"]
                )["groups"]
            else:
                step = comparison["decode"]["first_call_ledger"]
            calls.append(
                map_call(
                    model,
                    position,
                    row,
                    step,
                    "decode",
                    scalar_vector_provider,
                    fp32_matrix_vector_provider,
                    groups,
                )
            )
        totals = Counter()
        for call in calls:
            totals.update(call["matrix_buckets"])
        if sum(totals.values()) != comparison["summary"]["matrix_flops"]:
            raise AssertionError("Request matrix conservation failed")
        if (
            sum(call["ordinary_scalar_flops"] for call in calls)
            != comparison["summary"]["accounted_scalar_flops"]
        ):
            raise AssertionError("Scalar conservation failed")
        specials = Counter()
        for call in calls:
            specials.update(call["special_ops"])
        if dict(specials) != comparison["summary"]["special_ops"]:
            raise AssertionError("Special conservation failed")
        uniform = comparison["summary"]["uniform_bf16_weight_comparison_bytes"]
        state = comparison["summary"]["final_state_resident_bytes"]
        representation = dict(
            uniform_bf16_weight_comparison_bytes=uniform,
            logical_final_state_bytes=state,
            checkpoint_payload_bytes=None,
            source_cache_allocation=comparison["source_cache_allocation"],
        )
        if model == "qwen3-8b":
            necessary = uniform + state
            capacity_status = (
                "necessary_failure"
                if capacity is not None and necessary > capacity
                else "necessary_only" if capacity is not None else "unknown_capacity"
            )
            runtime = "unknown_backend_and_transients"
        elif model.startswith("deepseek"):
            necessary = None
            representation["checkpoint_payload_bytes"] = ledger["summary"][
                "base_checkpoint_payload_bytes"
            ]
            allocation = comparison["source_cache_allocation"][
                "bf16_cache_and_fp32_compressor_bytes"
            ]
            representation["source_cache_allocation_exceeds_capacity"] = (
                None if capacity is None else allocation > capacity
            )
            capacity_status = (
                "source_cache_allocation_necessary_failure"
                if capacity is not None and allocation > capacity
                else "runtime_representation_unknown"
            )
            runtime = "source_kernel_h100_compatibility_unverified"
        else:
            necessary = None
            representation["checkpoint_payload_bytes"] = ledger["summary"][
                "text_checkpoint_payload_bytes"
            ]
            capacity_status = "checkpoint_shape_conflict"
            runtime = "unmodified_checkpoint_not_shape_compatible"
            representation["checkpoint_compatibility"] = ledger["checkpoint"][
                "runtime_compatibility"
            ]
        for call in calls:
            call["interface_normalized_seconds"] = {
                key: dict(
                    bytes=value,
                    seconds=value / rates["physical_hbm_bytes"],
                    physical_resource="unspecified; bandwidth denominator only, not HBM traffic",
                )
                for key, value in call["known_interfaces"].items()
            }
        for call in calls:
            for resource in call["work"]:
                rates.setdefault(resource, None)
        models.append(
            dict(
                model=model,
                calls=calls,
                matrix_buckets=dict(totals),
                resource_bounds=stage_resource_bounds.bounds(calls, rates),
                capacity=dict(
                    official_nominal_bytes=(
                        device["memory"]["nominal_capacity"] * 10**9
                        if device["memory"]["nominal_capacity"] is not None
                        else None
                    ),
                    scenario_limit_bytes=capacity,
                    status=capacity_status,
                    necessary_resident_bytes=necessary,
                    representations=representation,
                ),
                implementation_admission=runtime,
                links=dict(
                    prefix_restore_payload_bytes=0,
                    complete_link_bytes=None,
                    complete_link_seconds=None,
                    reason="No placement/offload/topology contract; S0 does not prove all links idle",
                ),
                complete_runtime_seconds=None,
                quality_equivalence=None,
            )
        )
    return dict(
        schema="request-hardware-bridge-v1",
        scenario=dict(
            output_tokens=output_tokens,
            scalar_vector_provider=scalar_vector_provider,
            fp32_matrix_vector_provider=fp32_matrix_vector_provider,
            capacity_bytes=capacity_bytes,
        ),
        original_request=original,
        device=device,
        official_dense_peaks=admitted,
        rates=rates,
        models=models,
        scope=[
            "Original S0/P128/B1/G4 or G1 four-model request preserved in full; G-1 decode calls and original FP32 Qwen probability representation unchanged.",
            "BF16/FP8 Tensor FP32-accumulator dense peaks are arithmetic interpretations, not proof of actual kernel dispatch. FP8 supporting evidence remains attached; no structured sparse peak or TF32 substitution.",
            "Qwen PV is mixed FP32 P/BF16 V with positive work and no admitted rate. V4 routed FP4 is storage converted to selected FP8 execution, not an FP4 peak. K3 nonrouter matrices remain positive unclassified work.",
            "FP32 matrix vector and scalar vector providers are separate explicit switches. When both selected, demand shares one vector resource; ordinary scalar FLOPs are not certified machine instructions. Named specials have no guessed rate.",
            "Physical HBM demand is null for each call; known interfaces remain separate overlapping/alternative views normalized by a denominator only. Do not sum interface times or compare them as actual traffic.",
            "Calls are sequential resource stages; sum of known call maxima and pooled known max are partial arithmetic comparisons. Unknown work/rates propagate complete bounds to null. No executable latency or model ranking is emitted.",
            "Qwen BF16 weights+KV is a necessary single-device no-offload representation; workspace unknown. V4 checkpoint/hash/runtime differences and K3 A_log conflict prohibit admission by checkpoint bytes. No hidden TP/EP/PP layout inferred from oversized models.",
        ],
    )


def markdown(result):
    return (
        "# Four-model request to conditional H100 resources\n\nUnknown execution and physical-traffic fields remain explicit.\n\n```json\n"
        + json.dumps(result, indent=2, allow_nan=False)
        + "\n```\n"
    )
