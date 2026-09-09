"""Conditional serial-stage resource bounds, preserving precision and unknowns."""

import math
import json
from collections import Counter
from .. import hardware
from ..models import qwen3
from ..schema import Scenario
from ..sources import model_config, provenance, records
from . import v4_forward


def bounds(stages, rates):
    """Compare a serial sum of stage maxima with a pooled-resource maximum."""
    totals = Counter()
    unknown_work = set()
    results = []
    for stage in stages:
        times, missing = {}, []
        for resource, amount in stage["work"].items():
            if amount is None:
                unknown_work.add(resource)
                missing.append(dict(resource=resource, reason="unknown work"))
                continue
            if (
                type(amount) not in (int, float)
                or not math.isfinite(amount)
                or amount < 0
            ):
                raise ValueError("Work must be finite, nonnegative or explicit null")
            totals[resource] += amount
            if amount == 0:
                times[resource] = 0.0
                continue
            rate = rates.get(resource)
            if rate is None:
                missing.append(dict(resource=resource, reason="unknown rate"))
                continue
            if type(rate) not in (int, float) or not math.isfinite(rate) or rate <= 0:
                raise ValueError("Positive finite service rate required")
            value = amount / rate
            if not math.isfinite(value):
                raise ValueError("Resource time exceeds finite range")
            times[resource] = value
        known = max(times.values(), default=0.0)
        results.append(
            dict(
                id=stage["id"],
                resource_seconds=times,
                missing=missing,
                known_resource_max_seconds=known,
                accounted_stage_lower_bound_seconds=None if missing else known,
            )
        )
    global_times = {
        k: v / rates[k] for k, v in totals.items() if v and rates.get(k) is not None
    }
    missing = sorted(
        unknown_work | {k for k, v in totals.items() if v and rates.get(k) is None}
    )
    complete = not missing
    output = dict(
        stages=results,
        total_known_work=dict(totals),
        unknown_work_resources=sorted(unknown_work),
        missing_resources=missing,
        global_resource_seconds=global_times,
        known_global_max_seconds=max(global_times.values(), default=0.0),
        known_serial_stage_max_sum_seconds=sum(
            x["known_resource_max_seconds"] for x in results
        ),
        accounted_global_max_seconds=(
            max(global_times.values(), default=0.0) if complete else None
        ),
        accounted_serial_stage_lower_bound_seconds=(
            sum(x["known_resource_max_seconds"] for x in results) if complete else None
        ),
    )

    json.dumps(output, allow_nan=False)
    return output


def _stage(name):
    return dict(id=name, work=Counter(), operations=[])


def _add(stage, name, matrix=0, precision="BF16", scalar=0, special=None, detail=None):
    if matrix:
        resource = (
            "vector_fp32" if precision == "FP32" else "matrix_" + precision.lower()
        )
        stage["work"][resource] += matrix
    stage["work"]["vector_fp32"] += scalar
    for key, value in (special or {}).items():
        stage["work"]["special:" + key] += value
    stage["operations"].append(
        dict(
            name=name,
            matrix_flops=matrix,
            input_precision=precision if matrix else None,
            accumulator_precision="FP32" if matrix else None,
            sparsity="dense" if matrix else None,
            scalar_flops=scalar,
            special_ops=special or {},
            source_detail=detail,
        )
    )


def workload(model, batch, tokens, history, routing):
    if model == "qwen3-8b":
        config = model_config(model)
        result = qwen3.calculate(
            model, Scenario(batch=batch, tokens=tokens, history=history, score_bytes=2)
        )
        stages = (
            [_stage("input")]
            + [_stage(f"layer:{i}") for i in range(36)]
            + [_stage("head")]
        )
        for op in result["operators"]:
            owners = (
                stages[1:-1]
                if op["repeats"] == 36
                else [
                    (
                        stages[0]
                        if op["name"] in ("embedding", "rope_table")
                        else stages[-1]
                    )
                ]
            )
            for stage in owners:
                _add(
                    stage,
                    op["name"],
                    op["matrix_flops"],
                    "BF16",
                    op["scalar_flops"],
                    op["special_ops"],
                    op["shapes"],
                )
                stage["work"]["interface_bytes"] += (
                    op["weight_read_bytes"]
                    + op["activation_read_bytes"]
                    + op["activation_write_bytes"]
                )
        capacity = dict(
            comparison_bytes=result["summary"]["minimum_required_weight_and_kv_bytes"],
            applicable_necessary_condition=True,
            definition="Declared uniform BF16 weights plus BF16 KV after this call; excludes workspace/activations",
        )
        baseline = dict(
            matrix_flops=result["summary"]["matrix_flops"],
            scalar_flops=result["summary"]["scalar_flops"],
            special_ops=result["summary"]["special_ops"],
        )
        gaps = [
            "Sampling/tokenizer/launch/allocator and unexpanded dtype conversions/workspace remain outside the reference.",
            "BF16 score/probability materialization is explicitly selected; scalar reductions FP32. No source backend or exact casting cost inferred.",
        ]
    elif model == "deepseek-v4-flash":
        result = v4_forward.calculate(model, batch, tokens, history, routing)
        config = model_config(model, reference=True)
        L = config["n_layers"]
        M = batch * tokens
        H = config["dim"]
        stages = (
            [_stage("input")]
            + [_stage(f"layer:{i}") for i in range(L)]
            + [_stage("head")]
        )

        def each(row):
            ids = row["layer_ids"]
            return [(stages[i + 1], len(ids)) for i in ids]

        att = result["components"]["attention"]
        expert = result["components"]["experts"]
        hc = result["components"]["hyper_connections"]
        for row in att["matrices"]:
            name = row["name"]
            precision = (
                "FP32"
                if "compress" in name
                else "BF16" if name in ("wo_a_grouped", "index_weights_proj") else "FP8"
            )
            for stage, n in each(row):
                _add(
                    stage,
                    name,
                    row["matrix_flops"] // n,
                    precision,
                    detail=row["weight_storage_each"],
                )
        for row in att["attention_layer_groups"]:
            for stage, n in each(row):
                _add(
                    stage, "selected_QK_PV", row["qk_and_pv_matrix_flops"] // n, "BF16"
                )
                _add(
                    stage,
                    "index_rectangular_QK",
                    row["actual_index_rectangular_matrix_flops"] // n,
                    "BF16",
                )
        for row in expert["matrices"]:
            for stage, n in each(row):
                _add(
                    stage,
                    row["name"],
                    row["matrix_flops"] // n,
                    "FP32" if row["name"] == "router" else "FP8",
                    detail=row["weight_storage_each"],
                )
        for component in (att, expert):
            for row in component["non_matrix_operations"]:
                for stage, n in each(row):
                    _add(
                        stage,
                        row["name"],
                        scalar=row["scalar_flops"] // n,
                        special={k: v // n for k, v in row["special_ops"].items()},
                    )
        for row in att["sparse_kernel_groups"]:
            for stage, n in each(row):
                _add(
                    stage,
                    "online_sparse_softmax",
                    scalar=row["online_softmax_scalar_flops"] // n,
                    special={
                        "exp": row["exp_ops"] // n,
                        "compare_max": row["max_comparisons"] // n,
                    },
                )
        for row in hc["residual_operations"]:
            owners = stages[1:-1] if row["repeats"] == 2 * L else [stages[-1]]
            divisor = L if row["repeats"] == 2 * L else 1
            for stage in owners:
                _add(
                    stage,
                    "hc:" + row["name"],
                    row["matrix_flops"] // divisor,
                    "FP32",
                    row["scalar_flops"] // divisor,
                    {k: v // divisor for k, v in row["special_ops"].items()},
                )
        routed = expert["routed_expert_format"]["summary"]
        for stage in stages[1:-1]:
            _add(
                stage,
                "external_norms",
                scalar=2 * M * (4 * H + 1),
                special={"rsqrt": 2 * M},
            )
            _add(
                stage,
                "routed_quantization_and_scale",
                scalar=(
                    routed["logical_scale_accumulation_flops"]
                    + routed["activation_quantization_scalar_flops"]
                )
                // L,
            )
        _add(stages[-1], "final_norm", scalar=M * (4 * H + 1), special={"rsqrt": M})
        _add(
            stages[-1],
            "last_logits",
            result["summary"]["vocabulary_head_matrix_flops"],
            "FP32",
        )
        for stage in stages:
            stage["work"]["interface_bytes"] = None
        stages[0]["operations"].append(
            dict(
                name="embedding",
                known_payload_bytes=result["summary"]["embedding_lookup_payload_bytes"],
            )
        )
        capacity = dict(
            comparison_bytes=result["summary"]["base_checkpoint_payload_bytes"]
            + result["summary"]["state_resident_after_bytes"],
            applicable_necessary_condition=False,
            definition="Checkpoint base storage plus logical state comparison only; runtime dtypes/aliases differ, hash I64 versus runtime I32. Not a proved runtime minimum.",
        )
        baseline = dict(
            matrix_flops=result["summary"]["matrix_flops_effective_attention"],
            scalar_flops=result["summary"]["accounted_scalar_flops"],
            special_ops=result["summary"]["accounted_special_ops"],
        )
        gaps = result["coverage"]["missing"] + [
            "V4 complete stage interface traffic and actual resident conversions are unknown.",
            "Effective matrix work and accounted scalar work retain original coverage; source tile work is not added on top.",
        ]
    else:
        raise ValueError("Only fixed Qwen3-8B and DeepSeek-V4-Flash accounts supported")
    for stage in stages:
        stage["work"] = dict(stage["work"])
    observed_matrix = sum(
        op.get("matrix_flops", 0) for s in stages for op in s["operations"]
    )
    observed_scalar = sum(
        op.get("scalar_flops", 0) for s in stages for op in s["operations"]
    )
    observed_special = Counter()
    for stage in stages:
        for op in stage["operations"]:
            observed_special.update(op.get("special_ops", {}))
    if (
        observed_matrix != baseline["matrix_flops"]
        or observed_scalar != baseline["scalar_flops"]
        or dict(observed_special) != baseline["special_ops"]
    ):
        raise AssertionError("Staged work differs from original model subtotal")
    return stages, capacity, baseline, gaps


def calculate(
    model="qwen3-8b",
    device="h100-sxm",
    batch=1,
    tokens=128,
    history=0,
    routing="balanced",
    assumed_rates=None,
    rate_multipliers=None,
    stage_interface_bytes=None,
):
    stages, capacity, baseline, gaps = workload(model, batch, tokens, history, routing)
    selected = hardware.select_device(device)
    if selected["spec_scope"] != "single_device":
        raise ValueError("No implicit multi-device execution/communication mapping")
    if stage_interface_bytes is not None:
        if len(stage_interface_bytes) != len(stages) or any(
            type(x) is not int or x < 0 for x in stage_interface_bytes
        ):
            raise ValueError(
                "Explicit interface bytes require a nonnegative integer per stage"
            )
        for stage, amount in zip(stages, stage_interface_bytes):
            stage["work"]["interface_bytes"] = amount
    matrix_unit = (
        "cube"
        if selected["vendor"] == "Huawei"
        else "gpu" if selected["vendor"] == "Apple" else "tensor"
    )
    admissions = {}
    rates = {}
    for resource, precision, unit in [
        ("matrix_bf16", "BF16", matrix_unit),
        ("matrix_fp8", "FP8", matrix_unit),
        ("vector_fp32", "FP32", "vector"),
    ]:
        try:
            peak = hardware.select_peak(selected, precision, "FP32", unit, "dense")
            rate = peak["tera_ops_per_second"] * 1e12
            reason = None
        except ValueError as error:
            peak = None
            rate = None
            reason = str(error)
        admissions[resource] = dict(
            input_precision=precision,
            accumulator="FP32",
            unit=unit,
            sparsity="dense",
            official_peak=peak,
            unavailable_reason=reason,
        )
        rates[resource] = rate
    rates["interface_bytes"] = selected["memory"]["bandwidth_bytes_per_second"]
    demanded = {resource for s in stages for resource in s["work"]}
    for resource in demanded:
        rates.setdefault(resource, None)
    assumed_rates = {} if assumed_rates is None else dict(assumed_rates)
    rate_multipliers = {} if rate_multipliers is None else dict(rate_multipliers)
    for resource, value in assumed_rates.items():
        if (
            resource not in demanded
            or type(value) not in (int, float)
            or not math.isfinite(value)
            or value <= 0
        ):
            raise ValueError(
                "Assumed rate must name a demanded resource and be positive finite"
            )
        rates[resource] = value
    for resource, value in rate_multipliers.items():
        if (
            resource not in demanded
            or rates.get(resource) is None
            or type(value) not in (int, float)
            or not math.isfinite(value)
            or value <= 0
        ):
            raise ValueError(
                "Perturbation requires an existing known positive resource rate"
            )
        rates[resource] *= value
    result = bounds(stages, rates)
    compute_stages = [
        dict(s, work={k: v for k, v in s["work"].items() if k != "interface_bytes"})
        for s in stages
    ]
    compute = bounds(compute_stages, rates)
    memory = selected["memory"]
    unit = memory.get("capacity_unit")
    nominal = memory.get("nominal_capacity")
    capacity_bytes = (
        nominal * {"GB": 10**9, "GiB": 2**30, "TB": 10**12, "TiB": 2**40}[unit]
        if nominal is not None and unit in ("GB", "GiB", "TB", "TiB")
        else None
    )
    exceeds = (
        capacity["comparison_bytes"] > capacity_bytes
        if capacity_bytes is not None
        else None
    )
    capacity.update(
        device_nominal_bytes=capacity_bytes,
        comparison_exceeds_nominal=exceeds,
        runtime_status=(
            "fails_necessary_capacity"
            if exceeds and capacity["applicable_necessary_condition"]
            else (
                "necessary_only"
                if capacity["applicable_necessary_condition"]
                else "runtime_unknown_checkpoint_comparison"
            )
        ),
        full_runtime_feasibility=None,
    )
    source_ids = selected["source_ids"]
    sources = provenance(model) + [
        {k: r[k] for k in ("file", "url", "revision", "sha256")}
        for r in records()
        if r.get("id") in source_ids
    ]
    output = dict(
        calculation="stage-resource-bounds",
        schema_version=1,
        scenario=dict(
            model=model,
            device=device,
            batch=batch,
            tokens=tokens,
            history=history,
            routing=routing,
            assumed_rates=assumed_rates,
            rate_multipliers=rate_multipliers,
            stage_interface_bytes=stage_interface_bytes,
        ),
        sources=sources,
        device=dict(id=device, vendor=selected["vendor"], memory=memory),
        stages=stages,
        precision_admission=admissions,
        effective_resource_rates=rates,
        baseline_work=baseline,
        resource_bounds=result,
        compute_only_bounds=compute,
        capacity=capacity,
        coverage_gaps=gaps,
        summary=dict(
            accounted_serial_stage_lower_bound_seconds=result[
                "accounted_serial_stage_lower_bound_seconds"
            ],
            accounted_global_max_seconds=result["accounted_global_max_seconds"],
            full_request_latency_bound_seconds=None,
            measured_latency_seconds=None,
            necessary_capacity_not_failed_accounted_bound_seconds=(
                result["accounted_serial_stage_lower_bound_seconds"]
                if capacity["runtime_status"] == "necessary_only" and not exceeds
                else None
            ),
        ),
        assumptions=[
            "Stages are complete serial decoder layers, with ideal overlap inside each layer. Sum of stage resource maxima is distinct from a pooled global maximum; neither is a measured runtime.",
            "FP32 F.linear is mapped to an explicitly chosen IEEE FP32 vector execution policy, not inferred actual backend dispatch. TF32 is not admitted. Ordinary scalar and FP32 matrix work share one vector budget. The FP32 scalar provider is a declared logical execution policy, not proof of every source elementwise machine dtype.",
            "V4 FP4 stored experts execute FP8xFP8 after conversion in the pinned kernel; no native FP4 or structured-sparse peak substitution. BF16/FP8 accumulation requires exact FP32 admission.",
            "Named special and conversion primitive rates are not inferred from vector FLOPs. Missing positive work/rates propagate null; zero work needs no rate. Supplying rates is a hypothetical provider contract, not official disclosure.",
            "Interface demands are a conditional materialized-operand contract, not observed HBM or an unconditional whole-graph traffic bound. Qwen score/probability interfaces use BF16 explicitly; FP32 scalar reductions remain separate.",
            "V4 lacks a complete stage interface account; caller-provided bytes can define a conditional budget but cannot close model coverage, runtime capacity or missing operations.",
            "Nominal memory is not full available allocation, especially Apple unified memory. Necessary-condition success is not proof of actual full-peak feasibility; V4 checkpoint comparison is not a runtime capacity lower bound.",
            "Official peaks and bandwidth are preserved alongside hypothetical rates/perturbations. No hardware pricing, measured efficiency, or missing peak imputation.",
        ],
    )

    json.dumps(output, allow_nan=False)
    return output


def markdown(result):
    lines = [
        "# Serial-stage resource bounds",
        "",
        "Conditional known-work service bounds; full runtime remains unknown.",
        "",
        "| Field | Value |",
        "|---|---|",
    ]

    def visit(value, path=""):
        if isinstance(value, dict) and value:
            for k, v in value.items():
                visit(v, f"{path}.{k}" if path else k)
        elif isinstance(value, list) and value:
            for i, v in enumerate(value):
                visit(v, f"{path}[{i}]")
        else:
            text = "unknown (null)" if value is None else str(value)
            lines.append(
                f"| {path} | "
                + text.replace("|", "&#124;").replace("\n", "<br>")
                + " |"
            )

    visit(result)
    return "\n".join(lines) + "\n"
