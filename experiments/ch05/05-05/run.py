#!/usr/bin/env python3
"""Transpose one logical matrix from three physical layouts; inspect generated code."""
import argparse
import hashlib
import json
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
def transpose(X, Y, M: tl.constexpr, N: tl.constexpr,
              S0: tl.constexpr, S1: tl.constexpr, TILE: tl.constexpr):
    rows = tl.program_id(0) * TILE + tl.arange(0, TILE)
    cols = tl.program_id(1) * TILE + tl.arange(0, TILE)
    values = tl.load(X + rows[:, None] * S0 + cols[None, :] * S1,
                     (rows[:, None] < M) & (cols[None, :] < N), other=0)
    tl.store(Y + cols[None, :] * M + rows[:, None], values,
             (rows[:, None] < M) & (cols[None, :] < N))


def gpu_snapshot():
    return subprocess.check_output([
        "nvidia-smi", "--query-gpu=name,driver_version,memory.used,utilization.gpu,temperature.gpu,power.draw,clocks.sm",
        "--format=csv"], text=True).strip()


def experiment(out, trials, repeats):
    out.mkdir(parents=True, exist_ok=True)
    artifacts = out / "code"
    artifacts.mkdir(exist_ok=True)
    torch.manual_seed(505)
    rng = random.Random(505)
    report = {"environment": {"utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
              "host": platform.node(), "torch": torch.__version__, "triton": triton.__version__,
              "gpu": torch.cuda.get_device_name(), "capability": list(torch.cuda.get_device_capability()),
              "before": gpu_snapshot(), "shared_gpu": True},
              "method": {"dtype": "float16", "operation": "Y = X.T, materialized to a new contiguous output",
                         "trials": trials, "repeats": repeats, "warmup": 20,
                         "timing": "CUDA Graph containing repeated launches, events around replay; hot fixed buffers",
                         "compilation": "First invocation includes JIT/cache/module loading and synchronization; not pure compile time",
                         "layouts": ["contiguous", "transposed", "strided_columns"]},
              "rows": []}
    # Representative hidden width and an irregular shape force distinct masks/strides.
    for m, n in [(1024, 4096), (1003, 4093)]:
        logical = torch.randn((m, n), device="cuda", dtype=torch.float16)
        for layout in report["method"]["layouts"]:
            if layout == "contiguous":
                x = logical.clone()
            elif layout == "transposed":
                x = logical.T.contiguous().T
            else:
                storage = torch.empty((m, n * 2), device="cuda", dtype=torch.float16)
                x = storage[:, ::2]
                x.copy_(logical)
            y = torch.empty((n, m), device="cuda", dtype=torch.float16)
            reference = logical.T.contiguous()
            cases = []
            for tile, warps in [(16, 4), (32, 4), (64, 8)]:
                grid = (triton.cdiv(m, tile), triton.cdiv(n, tile))
                def launch(grid=grid, tile=tile, warps=warps):
                    return transpose[grid](x, y, m, n, *x.stride(), tile, num_warps=warps)
                start = time.perf_counter()
                compiled = launch()
                torch.cuda.synchronize()
                first_ms = (time.perf_counter() - start) * 1000
                torch.testing.assert_close(y, reference, rtol=0, atol=0)
                label = f"m{m}-n{n}-{layout}-t{tile}-w{warps}"
                code_files = {}
                for stage in ["ttir", "ttgir", "llir", "ptx", "cubin"]:
                    content = compiled.asm[stage]
                    p = artifacts / f"{label}.{stage}"
                    p.write_bytes(content if isinstance(content, bytes) else content.encode())
                    code_files[stage] = str(p.relative_to(out))
                ttgir = compiled.asm["ttgir"]
                ptx = compiled.asm["ptx"]
                row = {"m": m, "n": n, "layout": layout, "strides": list(x.stride()),
                       "tile": tile, "warps": warps, "grid": list(grid), "first_call_ms": first_ms,
                       "correctness": "bitwise_equal_to_torch_transpose", "registers": compiled.n_regs,
                       "shared_bytes": compiled.metadata.shared, "spills": compiled.n_spills,
                       "ir_convert_layout_count": ttgir.count("ttg.convert_layout"),
                       "ptx_barrier_count": ptx.count("bar.sync"),
                       "ptx_shared_load_count": ptx.count("ld.shared"),
                       "ptx_shared_store_count": ptx.count("st.shared"),
                       "code_files": code_files, "samples_us": []}
                for _ in range(20):
                    launch()
                graph = torch.cuda.CUDAGraph()
                with torch.cuda.graph(graph):
                    for _ in range(repeats):
                        launch()
                for _ in range(5):
                    graph.replay()
                cases.append((graph, row))
            torch.cuda.synchronize()
            for _ in range(trials):
                rng.shuffle(cases)
                for graph, row in cases:
                    a, b = torch.cuda.Event(enable_timing=True), torch.cuda.Event(enable_timing=True)
                    a.record()
                    graph.replay()
                    b.record()
                    b.synchronize()
                    row["samples_us"].append(a.elapsed_time(b) * 1000 / repeats)
            for graph, row in cases:
                graph.replay()
                torch.cuda.synchronize()
                torch.testing.assert_close(y, reference, rtol=0, atol=0)
                row["median_us"] = statistics.median(row["samples_us"])
                report["rows"].append(row)
                print(row["m"], row["n"], row["layout"], row["tile"], row["median_us"], flush=True)
            del cases, graph, x, y, reference
    # Masked edge cases independent of the timed shapes, all physical layouts.
    report["edge_checks"] = []
    for m, n in [(1, 1), (3, 67), (65, 2)]:
        logical = torch.arange(m * n, device="cuda").reshape(m, n).half()
        storage = torch.empty((m, n * 2), device="cuda", dtype=torch.float16)
        storage[:, ::2].copy_(logical)
        for layout, x in [("contiguous", logical), ("transposed", logical.T.contiguous().T),
                          ("strided_columns", storage[:, ::2])]:
            for tile, warps in [(16, 4), (32, 4), (64, 8)]:
                y = torch.full((n, m), float("nan"), device="cuda", dtype=torch.float16)
                transpose[(triton.cdiv(m, tile), triton.cdiv(n, tile))](
                    x, y, m, n, *x.stride(), tile, num_warps=warps)
                torch.testing.assert_close(y, logical.T, rtol=0, atol=0)
                report["edge_checks"].append({"shape": [m, n], "layout": layout,
                                              "tile": tile, "passed": True})
    report["environment"]["after"] = gpu_snapshot()
    (out / "results.json").write_text(json.dumps(report, indent=2) + "\n")
    root = Path(__file__).resolve().parent
    hashes = {"run.py": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    hashes.update({str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
                   for p in sorted(out.rglob("*")) if p.is_file() and p.name != "provenance.json"})
    (out / "provenance.json").write_text(json.dumps({"sha256": hashes}, indent=2) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--trials", type=int, default=11)
    parser.add_argument("--repeats", type=int, default=100)
    args = parser.parse_args()
    if args.trials < 3 or args.repeats < 1:
        parser.error("at least 3 trials and 1 repeat required")
    experiment(Path(__file__).resolve().parent / "results", args.trials, args.repeats)
