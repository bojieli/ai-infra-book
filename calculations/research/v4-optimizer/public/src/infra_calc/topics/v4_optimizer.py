"""Declared V4 optimizer arithmetic over verified checkpoint logical shapes.

The report defines the polynomial and coefficients, not an executable optimizer.
This ledger counts a selected real-arithmetic factorization, not GPU instructions.
"""

import json
import math
import re
from collections import Counter

from infra_calc.sources import model_config, provenance, read_source
from infra_calc.topics.v4_checkpoint import calculate as checkpoint

COEFFICIENTS = [(3.4445, -4.7750, 2.0315)] * 8 + [(2.0, -1.5, 0.5)] * 2


def matrix_work(rows, columns, orientation="smaller_gram"):
    """One independent matrix, factored Eq. 28, ten NS iterations."""
    if any(type(x) is not int or x <= 0 for x in (rows, columns)):
        raise ValueError("Positive integer matrix dimensions required")
    if orientation not in ("smaller_gram", "stored_left_gram"):
        raise ValueError("Unknown orientation")
    n, m = (
        (min(rows, columns), max(rows, columns))
        if orientation == "smaller_gram"
        else (rows, columns)
    )
    e = n * m
    return {
        "oriented_shape": [n, m],
        "parameters": e,
        "iterations": 10,
        "gemms_per_iteration": [
            {"name": "A=X@X.T", "mnk": [n, n, m], "flops": 2 * n * n * m},
            {"name": "B=A@A", "mnk": [n, n, n], "flops": 2 * n**3},
            {"name": "C@X", "mnk": [n, m, n], "flops": 2 * n * n * m},
        ],
        "matrix_flops": 10 * (4 * n * n * m + 2 * n**3),
        "ordinary_scalar_operations": 11 * e + 10 * (3 * n * n + 2 * e),
        "scalar_detail": {
            "momentum_and_nesterov": 4 * e,
            "frobenius_square_sum_epsilon_divide": 3 * e,
            "polynomial_combine": 10 * (3 * n * n + 2 * e),
            "rescale_decay_update": 4 * e,
        },
        "special_operations": {"sqrt": 1},
        "fp32_persistent_state_bytes": {"master_weight": 4 * e, "momentum": 4 * e},
        "fp32_gradient_input_bytes": 4 * e,
        "tensor_interfaces_per_iteration_bytes": {
            "gemm_operand_reads": 4 * (3 * e + 3 * n * n),
            "gemm_outputs": 4 * (2 * n * n + e),
            "scalar_combine_reads": 4 * (2 * n * n + 2 * e),
            "scalar_combine_writes": 4 * (n * n + e),
        },
        "individual_temporary_bytes": {
            "X": 4 * e,
            "A": 4 * n * n,
            "B": 4 * n * n,
            "C": 4 * n * n,
            "CX": 4 * e,
        },
    }


def muon_reference(
    weight,
    gradient,
    momentum,
    learning_rate=2.7e-4,
    mu=0.95,
    weight_decay=0.1,
    gamma=0.18,
    norm_epsilon=0.0,
    orientation="smaller_gram",
):
    """Small FP64 torch oracle. No cast/STE or zero-norm policy is implied."""
    import torch

    rows, columns = weight.shape
    matrix_work(rows, columns, orientation)
    updated_momentum = mu * momentum + gradient
    x = mu * updated_momentum + gradient
    transpose = orientation == "smaller_gram" and rows > columns
    if transpose:
        x = x.T
    denominator = torch.sqrt(torch.sum(x * x)) + norm_epsilon
    if denominator.item() <= 0 or not math.isfinite(denominator.item()):
        raise ValueError("Undefined normalization; choose explicit positive epsilon")
    x = x / denominator
    for a, b, c in COEFFICIENTS:
        gram = x @ x.T
        square = gram @ gram
        combined = b * gram + c * square
        x = a * x + combined @ x
    if transpose:
        x = x.T
    rescale = math.sqrt(max(rows, columns)) * gamma
    update = x * rescale
    decay = 1 - learning_rate * weight_decay
    return weight * decay - learning_rate * update, updated_momentum


def calculate(
    model="deepseek-v4-flash",
    include_mtp=False,
    orientation="smaller_gram",
    wo_a_partition="source_groups",
    sink_policy="unresolved",
    head_mixer_policy="unresolved",
    learning_rate=2.7e-4,
    norm_epsilon=0.0,
    adam_step=1,
):
    if model not in ("deepseek-v4-flash", "deepseek-v4-pro"):
        raise ValueError("V4 Flash/Pro only")
    if type(include_mtp) is not bool:
        raise ValueError("include_mtp must be bool")
    if orientation not in ("smaller_gram", "stored_left_gram"):
        raise ValueError("Unknown orientation")
    if wo_a_partition not in ("source_groups", "stored_matrix"):
        raise ValueError("Unknown wo_a partition")
    if sink_policy not in ("unresolved", "row_muon"):
        raise ValueError("Unknown sink policy")
    if head_mixer_policy not in ("unresolved", "adamw", "muon"):
        raise ValueError("Unknown head mixer policy")
    if type(adam_step) is not int or adam_step < 1:
        raise ValueError("adam_step must be a positive integer")
    for name, value in (
        ("learning_rate", learning_rate),
        ("norm_epsilon", norm_epsilon),
    ):
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
            or value < 0
        ):
            raise ValueError(f"{name} must be finite and nonnegative")
    verified = checkpoint(model)
    config = model_config(model, reference=True)
    index = json.loads(read_source(f"sources/{model}/model.safetensors.index.json"))
    grouped = {}
    excluded = Counter()
    counts = Counter()
    for shard in sorted(set(index["weight_map"].values())):
        header = json.loads(read_source(f"sources/{model}/headers/{shard}.json"))
        for name, tensor in header.items():
            if name == "__metadata__":
                continue
            owner = "mtp" if name.startswith("mtp.") else "base"
            shape = list(tensor["shape"])
            if name.endswith(".scale") or name.endswith(".tid2eid"):
                excluded[
                    owner
                    + (
                        "_quant_scale_elements"
                        if name.endswith(".scale")
                        else "_hash_elements"
                    )
                ] += math.prod(shape)
                continue
            if tensor["dtype"] == "I8":
                shape[-1] *= 2
            parameters = math.prod(shape)
            counts[owner + "_logical_parameters"] += parameters
            if owner == "mtp" and not include_mtp:
                excluded["mtp_logical_parameters"] += parameters
                continue
            family, reason = (
                "muon",
                "report all other modules; stored matrix is independent unless explicitly partitioned",
            )
            if name.endswith("ffn.gate.bias"):
                family, reason = (
                    "external_router_bias",
                    "auxiliary-loss-free load balancing update, not differentiable route selection",
                )
            elif name.endswith("attn_sink"):
                family, reason = (
                    ("muon" if sink_policy == "row_muon" else "unresolved"),
                    "report omits vector matrixization; row_muon is explicit assumption",
                )
            elif name.endswith("hc_head_fn"):
                family, reason = (
                    head_mixer_policy,
                    "head module versus mHC projection boundary explicitly selected",
                )
            elif (
                name.endswith(("embed.weight", "head.weight"))
                or "norm.weight" in name
                or re.search(r"hc_.*_(base|scale)$", name)
            ):
                family, reason = (
                    "adamw",
                    "report embedding/head/RMSNorm/mHC static bias and gate exception",
                )
            independent_shape = shape.copy()
            matrices = 1
            if family == "muon":
                if len(shape) == 1:
                    independent_shape = [1, shape[0]]
                elif len(shape) != 2:
                    raise ValueError(f"Unclassified Muon shape: {name}")
                if (
                    name.endswith("attn.wo_a.weight")
                    and wo_a_partition == "source_groups"
                ):
                    matrices = config["o_groups"]
                    if shape[0] % matrices:
                        raise ValueError("wo_a groups do not divide rows")
                    independent_shape[0] //= matrices
            template = re.sub(r"\.(\d+)\.", ".{i}.", name)
            key = (
                owner,
                template,
                family,
                tuple(shape),
                tuple(independent_shape),
                matrices,
            )
            if key not in grouped:
                grouped[key] = dict(
                    owner=owner,
                    name_pattern=template,
                    optimizer=family,
                    logical_tensor_shape=shape,
                    independent_matrix_shape=independent_shape,
                    independent_matrices_per_tensor=matrices,
                    tensor_count=0,
                    parameters=0,
                    reason=reason,
                    example_tensor=name,
                )
            grouped[key]["tensor_count"] += 1
            grouped[key]["parameters"] += parameters
    if (
        counts["base_logical_parameters"]
        != verified["base_logical_parameters_excluding_scales_and_hash"]
    ):
        raise AssertionError("Checkpoint logical parameter conservation failed")
    totals = Counter(
        {
            key + "_parameters": 0
            for key in ("muon", "adamw", "unresolved", "external_router_bias")
        }
    )
    groups = list(grouped.values())
    for group in groups:
        p = group["parameters"]
        family = group["optimizer"]
        totals[family + "_parameters"] += p
        if family == "muon":
            work = matrix_work(*group["independent_matrix_shape"], orientation)
            multiplicity = (
                group["tensor_count"] * group["independent_matrices_per_tensor"]
            )
            assert work["parameters"] * multiplicity == p
            group["per_matrix_reference"] = work
            group["matrix_count"] = multiplicity
            for field in ("matrix_flops", "ordinary_scalar_operations"):
                group[field] = multiplicity * work[field]
                totals[field] += group[field]
            totals["normalization_sqrt"] += multiplicity
        elif family == "adamw":
            group["ordinary_scalar_operations"] = 14 * p
            group["special_operations"] = {"sqrt": p}
            totals["ordinary_scalar_operations"] += 14 * p
            totals["adam_sqrt"] += p
    muon_p, adam_p = totals["muon_parameters"], totals["adamw_parameters"]
    shape_count = len(
        {
            tuple(g["independent_matrix_shape"])
            for g in groups
            if g["optimizer"] == "muon"
        }
    )
    totals["shared_step_scalar_operations"] = (6 if adam_p else 0) + (
        2 if muon_p else 0
    )
    totals["ordinary_scalar_operations"] += totals["shared_step_scalar_operations"]
    totals["shape_setup_scalar_multiply"] = shape_count
    totals["shape_setup_sqrt"] = shape_count
    scenario = dict(
        model=model,
        include_mtp=include_mtp,
        orientation=orientation,
        wo_a_partition=wo_a_partition,
        sink_policy=sink_policy,
        head_mixer_policy=head_mixer_policy,
        learning_rate=learning_rate,
        norm_epsilon=norm_epsilon,
        adam_step=adam_step,
    )
    return {
        "schema": "v4-optimizer-reference-v1",
        "scenario": scenario,
        "groups": groups,
        "summary": dict(totals),
        "inventory": dict(counts),
        "excluded_inventory": dict(excluded),
        "checkpoint_verification": verified,
        "state_interfaces": {
            "declared_fp32_master_weights_bytes": 4 * (muon_p + adam_p),
            "declared_fp32_muon_momentum_bytes": 4 * muon_p,
            "declared_fp32_adam_m_v_bytes": 8 * adam_p,
            "declared_fp32_gradient_input_bytes": 4 * (muon_p + adam_p),
            "runtime_training_weight_copies_bytes": None,
            "distributed_padding_and_replication_bytes": None,
            "actual_peak_bytes": None,
            "actual_hbm_bytes": None,
        },
        "algorithm": {
            "mu": 0.95,
            "weight_decay": 0.1,
            "gamma": 0.18,
            "adam_beta1": 0.9,
            "adam_beta2": 0.95,
            "adam_epsilon": 1e-20,
            "ns_coefficients": COEFFICIENTS,
            "adam_pow_per_step": 2 if adam_p else 0,
        },
        "scope": {
            "full_optimizer_exact": False,
            "conditional_selected_parameter_updates_covered": totals[
                "unresolved_parameters"
            ]
            == 0,
            "router_bias_update_count_unknown": totals[
                "external_router_bias_parameters"
            ],
            "reference_precision": "real arithmetic; declared FP32 state/interfaces, report BF16 NS matmuls not emulated",
            "normalization": "Frobenius sqrt(sum squares)+explicit epsilon; epsilon=0 excludes zero Nesterov matrices",
            "source_algorithm_vs_kernel": "three-GEMM factored polynomial per iteration; transpose is explicit algebraic assumption, not disclosed kernel",
            "distributed": "full independent matrices required; dense capped ZeRO and MoE per-expert ownership; no rank layout or padding ratio assumed",
            "lifetimes": "master and momentum/moments persist across steps; gradient consumed this step; NS X/A/B/C/CX are per-matrix temporaries; views/transposes not charged as physical copies",
            "interfaces": "logical FP32 tensor accesses, not measured HBM; GEMM input duplicate operands counted per role; scalar fusion/alias and casts unknown",
            "excluded": "gradient production, load balancing bias rule, distributed synchronization, cast/quantization, optimizer implementation instruction count, actual peak/runtime",
        },
        "sources": provenance(model)
        + [
            {
                "file": "references/text/deepseek-v4.txt",
                "url": "https://arxiv.org/pdf/2606.19348",
                "revision": "2606.19348v1",
                "sha256": "3fa26fbc1ca9fdbfee428100894e467e0c1c967945c6f4a1a19203a71730e5d7",
                "locators": [
                    "section 2.4 Algorithm 1 and Eq.28",
                    "section 3.4.1",
                    "section 4.2.2",
                ],
                "kind": "archived report text, bound by source-evidence.json",
            }
        ],
    }


def markdown(result):
    lines = [
        "# DeepSeek V4 optimizer reference",
        "",
        "Explicit grouping and factored ten-step hybrid Newton–Schulz; full runtime remains unknown.",
        "",
        "| Pattern | Family | Tensor shape | Count | Independent shape | Matrices/tensor | Parameters | Matrix FLOPs | Scalar operations |",
        "|---|---|---|---:|---|---:|---:|---:|---:|",
    ]
    for g in result["groups"]:
        lines.append(
            f"| {g['name_pattern']} | {g['optimizer']} | {g['logical_tensor_shape']} | {g['tensor_count']} | {g['independent_matrix_shape']} | {g['independent_matrices_per_tensor']} | {g['parameters']} | {g.get('matrix_flops', 0)} | {g.get('ordinary_scalar_operations', 'unknown')} |"
        )
    lines += [
        "",
        "Complete per-matrix operations, state, interface bytes, assumptions and source hashes:",
        "",
        "```json",
        json.dumps(result, indent=2, allow_nan=False),
        "```",
        "",
    ]
    return "\n".join(lines)
