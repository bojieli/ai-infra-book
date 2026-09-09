#!/usr/bin/env python3
"""Standalone SwiGLU fusion experiment. Requires CUDA, torch and triton."""
import argparse
import json
import math
import platform
import random
import statistics
import subprocess
import time
from pathlib import Path

import torch
import triton
import triton.language as tl


@triton.jit
def silu_kernel(G, T, N: tl.constexpr, BLOCK: tl.constexpr):
    i = tl.program_id(0) * BLOCK + tl.arange(0, BLOCK)
    g = tl.load(G + i, i < N, 0).to(tl.float32)
    tl.store(T + i, g / (1.0 + tl.exp(-g)), i < N)


@triton.jit
def mul_kernel(T, U, O, N: tl.constexpr, BLOCK: tl.constexpr):
    i = tl.program_id(0) * BLOCK + tl.arange(0, BLOCK)
    t = tl.load(T + i, i < N, 0).to(tl.float32)
    u = tl.load(U + i, i < N, 0).to(tl.float32)
    tl.store(O + i, t * u, i < N)


@triton.jit
def fused_kernel(G, U, O, N: tl.constexpr, BLOCK: tl.constexpr):
    i = tl.program_id(0) * BLOCK + tl.arange(0, BLOCK)
    g = tl.load(G + i, i < N, 0).to(tl.float32)
    u = tl.load(U + i, i < N, 0).to(tl.float32)
    # Preserve the BF16 intermediate rounding used by the unfused path.
    s = (g / (1.0 + tl.exp(-g))).to(O.dtype.element_ty).to(tl.float32)
    tl.store(O + i, s * u, i < N)


def snapshot():
    return subprocess.check_output([
        "nvidia-smi", "--query-gpu=name,driver_version,memory.used,utilization.gpu,temperature.gpu,power.draw,clocks.sm",
        "--format=csv"], text=True).strip()


def run(out, trials, repeats):
    out.mkdir(parents=True, exist_ok=True)
    torch.manual_seed(20260908)
    random.seed(20260908)
    torch.cuda.init()
    props = torch.cuda.get_device_properties(0)
    report = {"kind": "hardware_measurement", "environment": {
        "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "host": platform.node(), "torch": torch.__version__, "triton": triton.__version__,
        "device": props.name, "capability": list(torch.cuda.get_device_capability()),
        "total_memory_bytes": props.total_memory, "before": snapshot(),
        "condition": "Shared GPU; other resident services were not stopped. No exclusive-clock control."},
        "method": {"trials": trials, "repeats_per_trial": repeats, "warmup": 20,
                   "timing": "CUDA events around repeated launches; CPU submission gaps are included",
                   "traffic": "Logical tensor interface bytes, not measured DRAM transactions",
                   "cache": "Warm reuse of the same buffers; no L2 flush",
                   "chain": "BF16 gate -> FP32 SiLU -> BF16 intermediate -> FP32 multiply with BF16 up -> BF16 output"},
        "rows": []}
    configs = [(256, 4), (1024, 4), (4096, 8)]
    # Actual Qwen3-8B FFN activation widths plus a masked-tail validation case.
    for m in [1, 32, 1024]:
        n = m * 12288
        g = torch.randn(n, device="cuda", dtype=torch.bfloat16)
        u = torch.randn_like(g)
        o = torch.empty_like(g)
        t = torch.empty_like(g)
        cases = []
        reference = (torch.nn.functional.silu(g.float()).bfloat16().float() * u.float()).bfloat16()
        for block, warps in configs:
            grid = (triton.cdiv(n, block),)
            def separated(block=block, warps=warps, grid=grid):
                silu_kernel[grid](g, t, n, block, num_warps=warps)
                mul_kernel[grid](t, u, o, n, block, num_warps=warps)
            def fused(block=block, warps=warps, grid=grid):
                fused_kernel[grid](g, u, o, n, block, num_warps=warps)
            for mode, fn in [("separate", separated), ("fused", fused)]:
                start = time.perf_counter()
                fn()
                torch.cuda.synchronize()
                first_call_ms = (time.perf_counter() - start) * 1000
                torch.testing.assert_close(o, reference, rtol=0.016, atol=0.002)
                error = float((o.float() - reference.float()).abs().max())
                if mode == "fused":
                    k = fused_kernel[grid](g, u, o, n, block, num_warps=warps)
                    kernel = {"registers_per_thread": k.n_regs, "shared_bytes": k.metadata.shared,
                              "spills": k.n_spills}
                    if m == 1:
                        (out / f"fused-b{block}-w{warps}.ptx").write_text(k.asm["ptx"])
                else:
                    k1 = silu_kernel[grid](g, t, n, block, num_warps=warps)
                    k2 = mul_kernel[grid](t, u, o, n, block, num_warps=warps)
                    kernel = {"registers_per_thread": [k1.n_regs, k2.n_regs],
                              "shared_bytes": [k1.metadata.shared, k2.metadata.shared],
                              "spills": [k1.n_spills, k2.n_spills]}
                row = {"tokens": m, "width": 12288, "mode": mode, "block": block, "warps": warps,
                       "logical_bytes": n * (10 if mode == "separate" else 6),
                       "required_tensor_bytes": n * (8 if mode == "separate" else 6),
                       "intermediate_bytes": n * (2 if mode == "separate" else 0),
                       "kernel": kernel, "first_call_ms": first_call_ms,
                       "max_abs_error": error, "samples_us": [], "graph_samples_us": []}
                # required_tensor_bytes excludes validation tensors and the unused scratch
                # retained by this interleaved harness. It is a live-tensor count, not VRAM telemetry.
                for _ in range(20):
                    fn()
                cases.append((fn, row))
        torch.cuda.synchronize()
        for trial in range(trials):
            order = list(cases)
            random.shuffle(order)
            for fn, row in order:
                a, b = torch.cuda.Event(enable_timing=True), torch.cuda.Event(enable_timing=True)
                a.record()
                for _ in range(repeats):
                    fn()
                b.record()
                b.synchronize()
                row["samples_us"].append(a.elapsed_time(b) * 1000 / repeats)
        for _, row in cases:
            row["median_us"] = statistics.median(row["samples_us"])
            row["min_us"] = min(row["samples_us"])
            row["max_us"] = max(row["samples_us"])
        # Capture repeated calls to separate kernel execution from Python launch gaps.
        graph_cases = []
        for fn, row in cases:
            graph = torch.cuda.CUDAGraph()
            with torch.cuda.graph(graph):
                for _ in range(repeats):
                    fn()
            for _ in range(5):
                graph.replay()
            graph_cases.append((graph, row))
        torch.cuda.synchronize()
        for _ in range(trials):
            random.shuffle(graph_cases)
            for graph, row in graph_cases:
                a, b = torch.cuda.Event(enable_timing=True), torch.cuda.Event(enable_timing=True)
                a.record()
                graph.replay()
                b.record()
                b.synchronize()
                row["graph_samples_us"].append(a.elapsed_time(b) * 1000 / repeats)
        for _, row in cases:
            row["graph_median_us"] = statistics.median(row["graph_samples_us"])
            report["rows"].append(row)
        del graph_cases, graph, g, u, o, t, reference, cases
    # Boundary validation is separate from the benchmark shapes.
    validations = []
    for n in [1, 257, 12289]:
        g = torch.linspace(-40, 40, n, device="cuda").bfloat16()
        u = torch.linspace(-3, 3, n, device="cuda").bfloat16()
        o, t = torch.empty_like(g), torch.empty_like(g)
        ref = (torch.nn.functional.silu(g.float()).bfloat16().float() * u.float()).bfloat16()
        for block, warps in configs:
            grid = (triton.cdiv(n, block),)
            silu_kernel[grid](g, t, n, block, num_warps=warps)
            mul_kernel[grid](t, u, o, n, block, num_warps=warps)
            separated_output = o.clone()
            fused_kernel[grid](g, u, o, n, block, num_warps=warps)
            torch.testing.assert_close(o, separated_output, rtol=0, atol=0)
            torch.testing.assert_close(o, ref, rtol=0.016, atol=0.002)
            validations.append({"n": n, "block": block, "warps": warps, "fused_vs_separate": "bitwise_equal",
                                "max_abs_error": float((o.float() - ref.float()).abs().max())})
    report["boundary_validation"] = validations
    report["environment"]["after"] = snapshot()
    (out / "results.json").write_text(json.dumps(report, indent=2) + "\n")
    for m in [1, 32, 1024]:
        rows = [r for r in report["rows"] if r["tokens"] == m]
        best = {mode: min((r for r in rows if r["mode"] == mode), key=lambda r: r["median_us"])
                for mode in ["separate", "fused"]}
        print(m, {k: round(v["median_us"], 3) for k, v in best.items()},
              "speedup", round(best["separate"]["median_us"] / best["fused"]["median_us"], 3))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=Path(__file__).parent / "results")
    parser.add_argument("--trials", type=int, default=11)
    parser.add_argument("--repeats", type=int, default=100)
    args = parser.parse_args()
    if args.trials < 3 or args.repeats < 1:
        parser.error("use at least 3 trials and 1 repeat")
    run(args.out, args.trials, args.repeats)
