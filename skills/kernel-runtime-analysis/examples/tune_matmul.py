"""Select a verified CPU matmul traversal using measured local wall times."""
import argparse
import ctypes as C
import json
from pathlib import Path
import platform
import random
from statistics import median
import subprocess
import tempfile
from time import perf_counter_ns


def workload(shape, kernel):
    m, n, k = shape
    rng = random.Random(71)
    scalar = C.c_int32
    a = (scalar * (m*k))(*(rng.randrange(-4, 5) for _ in range(m*k)))
    b = (scalar * (k*n))(*(rng.randrange(-4, 5) for _ in range(k*n)))
    c = (scalar * (m*n))()
    reference = [sum(a[i*k+p] * b[p*n+j] for p in range(k))
                 for i in range(m) for j in range(n)]

    def run(tile, verify=False):
        if verify:
            # Every expected value is small. Poison the reusable output so a
            # candidate that skips a store cannot inherit a previous pass.
            C.memset(c, 0x5A, C.sizeof(c))
        start = perf_counter_ns()
        kernel(m, n, k, tile, a, b, c)
        elapsed = perf_counter_ns() - start
        if verify and list(c) != reference:
            raise ValueError(f"incorrect output for shape {shape} and tile {tile}")
        return elapsed
    return run


def tune(kernel, budget):
    shape = (96, 96, 96)
    checks = [workload(s, kernel) for s in [(1, 1, 1), (3, 7, 5), (4, 65, 9)]]
    benchmark = workload(shape, kernel)
    trials = []
    times = {}
    for tile in [0, 8, 16, 32, 64]:
        # Active contiguous slices of one B row and one C row for this comparison.
        active_bytes = 8 * (tile or 1)
        trial = dict(tile=tile, active_slice_bytes=active_bytes)
        trials.append(trial)
        if tile and active_bytes > budget:
            trial["result"] = "over budget"
            continue
        try:
            for run in checks + [benchmark]:
                run(tile, verify=True)
        except ValueError as error:
            if tile == 0:
                raise
            trial["result"] = str(error)
            continue
        times[tile] = []
        trial["result"] = "verified"
    rng = random.Random(19)
    for _ in range(11):
        order = list(times)
        rng.shuffle(order)
        for tile in order:
            times[tile].append(benchmark(tile))
    medians = {tile: median(samples) for tile, samples in times.items()}
    for trial in trials:
        if trial["tile"] in times:
            trial["median_ns"] = medians[trial["tile"]]
    fastest = min(medians, key=medians.get)
    selected = fastest if medians[fastest] <= 0.95 * medians[0] else 0
    benchmark(selected, verify=True)
    return dict(shape=shape, architecture=platform.machine(), slice_budget_bytes=budget,
                selected_tile=selected, trials=trials)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--slice-budget-bytes", type=int, default=256)
    args = parser.parse_args()
    if args.slice_budget_bytes < 8:
        parser.error("the baseline requires at least 8 bytes")
    with tempfile.TemporaryDirectory() as directory:
        lib = Path(directory) / "matmul.so"
        subprocess.run(["cc", "-O2", "-shared", "-fPIC", Path(__file__).with_name("matmul.c"),
                        "-o", lib], check=True)
        kernel = C.CDLL(str(lib)).matmul
        kernel.argtypes = [C.c_int] * 4 + [C.POINTER(C.c_int32)] * 3
        kernel.restype = None
        print(json.dumps(tune(kernel, args.slice_budget_bytes), indent=2))


if __name__ == "__main__":
    main()
