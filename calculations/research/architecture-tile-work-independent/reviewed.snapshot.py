"""Declared tile arithmetic for existing deep/narrow and shallow/wide variants."""

import json
import math
from fractions import Fraction

from infra_calc.topics import architecture_variants, gemm_tiles

NAMES = ("deeper_same_width", "shallower_wider")


def matrix_tile(m, k, n, tile_m, tile_k, tile_n):
    ledger = gemm_tiles.account(m, k, n, tile_m, tile_k, tile_n)
    return {
        key: ledger[key]
        for key in (
            "m_blocks",
            "k_blocks",
            "n_blocks",
            "output_tiles",
            "valid_matrix_flops",
            "fully_padded_matrix_flops",
        )
    }


def calculate(
    batch=1,
    tokens=129,
    history=0,
    tile_m=64,
    tile_n=128,
    tile_k=64,
    ffn_alignment=128,
    matrix_rate_flops_per_second=100e12,
    variant_rates=None,
):
    if (
        isinstance(matrix_rate_flops_per_second, bool)
        or not isinstance(matrix_rate_flops_per_second, (int, float))
        or not math.isfinite(matrix_rate_flops_per_second)
        or matrix_rate_flops_per_second <= 0
    ):
        raise ValueError("Matrix rate must be finite and positive")
    if variant_rates is not None:
        if not isinstance(variant_rates, dict) or set(variant_rates) - set(NAMES):
            raise ValueError("Unknown variant rate key")
        for rate in variant_rates.values():
            if (
                isinstance(rate, bool)
                or not isinstance(rate, (int, float))
                or not math.isfinite(rate)
                or rate <= 0
            ):
                raise ValueError("Variant rates must be finite and positive")
    # Validates positive tile dimensions through the existing public rule.
    matrix_tile(1, 1, 1, tile_m, tile_k, tile_n)
    base = architecture_variants.calculate(
        batch=batch, tokens=tokens, history=history, tp=1, ffn_alignment=ffn_alignment
    )
    variants = []
    for original in base["variants"]:
        if original["name"] not in NAMES:
            continue
        config = original["config"]
        rows = []
        for op in original["work"]["operators"]:
            if not op["matrix_flops"]:
                continue
            if op["category"] == "linear":
                m, k = op["shapes"]["input"]
                n = op["shapes"]["output"][1]
                repeats = op["repeats"]
                per_valid = op["matrix_flops"]
            elif op["name"] in ("qk", "pv"):
                b, heads, t, d = (
                    op["shapes"]["Q"]
                    if op["name"] == "qk"
                    else (
                        batch,
                        config["num_attention_heads"],
                        tokens,
                        config["head_dim"],
                    )
                )
                m, k, n = (
                    (tokens, d, history + tokens)
                    if op["name"] == "qk"
                    else (tokens, history + tokens, d)
                )
                repeats = op["repeats"] * b * heads
                per_valid = 2 * d * (tokens * history + tokens * (tokens + 1) // 2)
                if per_valid * repeats != op["matrix_flops"] * op["repeats"]:
                    raise AssertionError(
                        "Causal attention accounting does not match public operator"
                    )
            else:
                raise ValueError(f"Unclassified matrix {op['name']}")
            tiled = matrix_tile(m, k, n, tile_m, tile_k, tile_n)
            rectangle = tiled["valid_matrix_flops"]
            padded = tiled["fully_padded_matrix_flops"]
            assert per_valid <= rectangle <= padded
            rows.append(
                dict(
                    name=op["name"],
                    mnk=[m, n, k],
                    multiplicity=repeats,
                    valid_per_instance_flops=per_valid,
                    rectangular_per_instance_flops=rectangle,
                    padded_per_instance_flops=padded,
                    tile_blocks=tiled,
                    valid_flops=per_valid * repeats,
                    rectangular_flops=rectangle * repeats,
                    padded_flops=padded * repeats,
                    causal_rectangle_extra_flops=(rectangle - per_valid) * repeats,
                    tile_padding_extra_flops=(padded - rectangle) * repeats,
                    valid_fraction_of_padded_exact=str(Fraction(per_valid, padded)),
                )
            )
        valid = sum(row["valid_flops"] for row in rows)
        padded = sum(row["padded_flops"] for row in rows)
        rectangle = sum(row["rectangular_flops"] for row in rows)
        assert valid == original["work"]["matrix_flops"]
        rate = (variant_rates or {}).get(original["name"], matrix_rate_flops_per_second)
        service = padded / rate
        if not math.isfinite(service):
            raise ValueError("Conditional service exceeds finite range")
        variants.append(
            dict(
                name=original["name"],
                architecture=dict(
                    layers=config["num_hidden_layers"],
                    hidden=config["hidden_size"],
                    ffn=config["intermediate_size"],
                    heads=config["num_attention_heads"],
                    head_dim=config["head_dim"],
                ),
                parameters=original["actual_parameters"],
                parameter_delta=original["parameter_delta"],
                matrices=rows,
                valid_flops=valid,
                rectangular_flops=rectangle,
                padded_flops=padded,
                causal_rectangle_extra_flops=rectangle - valid,
                tile_padding_extra_flops=padded - rectangle,
                valid_fraction_of_padded_exact=str(Fraction(valid, padded)),
                padded_over_valid_exact=str(Fraction(padded, valid)),
                declared_padded_matrix_flops_per_second=rate,
                conditional_matrix_service_seconds=service,
                effective_valid_matrix_flops_per_second=valid / service,
                full_forward_runtime_seconds=None,
                actual_tensor_core_utilization=None,
            )
        )
    by_name = {row["name"]: row for row in variants}
    deep, wide = [by_name[name] for name in NAMES]
    threshold = Fraction(wide["padded_flops"], deep["padded_flops"])
    return dict(
        schema="architecture-tile-work-v1",
        scenario=dict(
            batch=batch,
            tokens=tokens,
            history=history,
            tile_m=tile_m,
            tile_n=tile_n,
            tile_k=tile_k,
            ffn_alignment=ffn_alignment,
            matrix_rate_flops_per_second=matrix_rate_flops_per_second,
            variant_rates=variant_rates,
        ),
        sources=base["sources"],
        variants=variants,
        comparison=dict(
            shallow_to_deep_valid_flop_ratio_exact=str(
                Fraction(wide["valid_flops"], deep["valid_flops"])
            ),
            shallow_to_deep_padded_flop_ratio_exact=str(threshold),
            shallow_faster_iff="rate_shallow / rate_deep > padded_shallow / padded_deep under the declared aggregate matrix-service model",
            actual_declared_rate_ratio_exact=str(
                Fraction(str(wide["declared_padded_matrix_flops_per_second"]))
                / Fraction(str(deep["declared_padded_matrix_flops_per_second"]))
            ),
            shallow_has_lower_conditional_matrix_service=wide[
                "conditional_matrix_service_seconds"
            ]
            < deep["conditional_matrix_service_seconds"],
        ),
        scope=[
            "Reuse existing Qwen8 parameter-budget variants: deeper_same_width is relatively deeper/narrower (48x4096) versus shallower_wider (24x5120). Both are untrained; released Qwen8 supplies the baseline parameter budget only.",
            "One logical unsharded model, tp=1; all matrix operators including Q/K/V/O, gate/up/down, QK/PV and last-position vocabulary head per sequence are counted. Nonmatrix arithmetic, KV copies and communication remain external.",
            "Caller tile M/N/K is a declared fully padded GEMM rule, matching gemm_tiles.account and quantized_gemm ceil geometry, not a fixed official backend kernel. No quantization or hardware peak is inferred.",
            "Attention executes a declared full rectangular GEMM per batch/query-head, then causal masking. Public valid causal FLOPs, extra rectangle work and tile tail padding are distinct; they must not be added twice. GQA sharing can reduce bytes but does not reduce per-query-head attention products.",
            "Only arithmetic fields are reused from gemm_tiles; its BF16 interface assumptions are not applied to FP32 attention probabilities. No HBM or working-buffer feasibility is claimed by this adapter.",
            "Padded work divided by caller padded-arithmetic service rate defines conditional matrix service. Effective valid FLOPs/s and valid/padded fractions are arithmetic quantities, not measured Tensor Core utilization or whole-model latency. Scalar/special kernels, launch dependencies and residency can change observed ordering.",
            "Variant-specific positive rates are optional explicit assumptions; the exact rate-ratio threshold exposes where the ordering changes. Parameter-budget error remains visible; neither equal quality nor a hardware recommendation is inferred.",
        ],
    )


def markdown(result):
    lines = [
        "# Architecture tile work",
        "",
        "Declared tile arithmetic, not measured hardware utilization.",
        "",
        "| Variant / operator | M,N,K | Count | Valid FLOPs | Rectangular FLOPs | Padded FLOPs |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for variant in result["variants"]:
        for row in variant["matrices"]:
            lines.append(
                f"| {variant['name']} / {row['name']} | {row['mnk']} | {row['multiplicity']} | {row['valid_flops']} | {row['rectangular_flops']} | {row['padded_flops']} |"
            )
    return (
        "\n".join(lines)
        + "\n\n```json\n"
        + json.dumps(result, indent=2, allow_nan=False)
        + "\n```\n"
    )
