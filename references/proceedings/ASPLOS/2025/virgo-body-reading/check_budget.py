#!/usr/bin/env python3
"""A paper-derived FP16 tile budget, not a simulator or measured kernel result.

Run: python3 check_budget.py
Only Python's standard library is used. The program writes nothing.
"""
import json


def calculate():
    kib = 1024
    m, n, k = 128, 64, 128
    input_bytes = 2
    accumulator_bytes = 4  # Explicit teaching assumption; no kernel source audit.
    smem_capacity = 128 * kib  # Interpret the paper's "KB" SRAM sizes as KiB.
    accumulator_capacity = 32 * kib
    a = m * k * input_bytes
    b = k * n * input_bytes
    c = m * n * accumulator_bytes
    macs = m * n * k
    macs_per_cycle = 16 * 16
    cycles = macs // macs_per_cycle
    clock_hz = 400_000_000
    small_rf = 2 * (8 * 16 * 2) + 8 * 8 * 4
    enlarged_a = (2 * m) * k * input_bytes
    enlarged_c = (2 * m) * n * accumulator_bytes
    result = {
        "scope": "One FP16 GEMM tile and its M-doubling counterfactual; capacity and ideal compute lower bound only",
        "paper_version": "arXiv:2408.12073v2",
        "paper_pages": {"operation_tile": 8, "rf_baseline": 9, "hardware_budget": 10},
        "assumptions": [
            "A and B are FP16; C accumulation is budgeted at FP32 (teaching assumption, not independently verified Virgo kernel configuration).",
            "The paper's 128 KB shared memory and 32 KB accumulator memory are interpreted as binary KiB for this budget.",
            "Only A/B input tiles are double buffered; C has one live accumulator tile. No fused intermediate or concurrent tenant is included.",
            "One independent MAC is counted as two FLOPs. Fully occupied 16x16 FP16 array gives 256 MAC/cycle; startup, drain and stalls are excluded.",
            "Each K tile imports one unique copy of A and B; there is no inter-tile reuse in the illustrative DMA demand. This is not shared-memory read traffic."
        ],
        "tile_mnk": [m, n, k],
        "bytes": {
            "a_unique": a, "b_unique": b, "one_input_buffer": a + b,
            "two_input_buffers": 2 * (a + b), "shared_capacity": smem_capacity,
            "shared_remaining_before_other_live_data": smem_capacity - 2 * (a + b),
            "one_fp32_accumulator": c, "accumulator_capacity": accumulator_capacity,
            "accumulator_remaining": accumulator_capacity - c,
        },
        "ideal_compute": {
            "macs": macs, "flops": 2 * macs, "macs_per_cycle": macs_per_cycle,
            "cycles_lower_bound": cycles, "clock_hz": clock_hz,
            "seconds_lower_bound": cycles / clock_hz,
            "microseconds_lower_bound": cycles / clock_hz * 1_000_000,
        },
        "conditional_dma_supply": {
            "unique_input_bytes_per_tile": a + b,
            "required_average_bytes_per_cycle_at_ideal_compute_rate": (a + b) / cycles,
            "required_average_GB_per_second_decimal": (a + b) / cycles * clock_hz / 1_000_000_000,
            "scope": "Necessary average input supply under stated no-reuse assumption; not sufficient for complete overlap, not physical SMEM traffic or total bus traffic.",
        },
        "rf_context_not_a_second_workload": {
            "baseline_warp_fp_register_budget_bytes": kib,
            "volta_style_8x8x16_operand_plus_fp32_accumulator_bytes": small_rf,
            "volta_style_remaining_bytes": kib - small_rf,
            "hopper_style_16x16_fp32_accumulator_bytes": 16 * 16 * 4,
            "warning": "These are model configurations in the paper, not product per-warp hardware register limits.",
        },
        "fp16_total_mac_budget": {"volta_or_ampere_style": 8 * 32, "hopper_style": 4 * 64, "virgo": 16 * 16},
        "double_m_same_resources": {
            "tile_mnk": [2 * m, n, k],
            "two_input_buffers_bytes": 2 * (enlarged_a + b),
            "shared_over_capacity_bytes": 2 * (enlarged_a + b) - smem_capacity,
            "fp32_accumulator_bytes": enlarged_c,
            "accumulator_over_capacity_bytes": enlarged_c - accumulator_capacity,
            "both_capacity_constraints_fail": True,
        },
    }
    assert (a, b, c) == (32 * kib, 16 * kib, 32 * kib)
    assert result["bytes"]["two_input_buffers"] == 96 * kib
    assert cycles == 4096 and (a + b) / cycles == 12
    assert set(result["fp16_total_mac_budget"].values()) == {256}
    assert small_rf == 768
    assert result["double_m_same_resources"]["two_input_buffers_bytes"] == 160 * kib
    return result


if __name__ == "__main__":
    print(json.dumps(calculate(), indent=2, ensure_ascii=False))
