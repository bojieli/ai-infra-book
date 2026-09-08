"""
Timing utilities for benchmarking FlashInfer-Bench kernel solutions.
"""

from __future__ import annotations

import statistics
from multiprocessing import Lock
from multiprocessing.synchronize import Lock as LockType
from typing import Any, List

import torch
from flashinfer.testing import bench_gpu_time_with_cupti

from flashinfer_bench.compile import Runnable

# Device-specific lock registry to ensure multiprocess-safe benchmarking
_device_locks: dict[str, LockType] = {}
_registry_lock = Lock()


def _device_lock(device: str) -> LockType:
    """Get or create a multiprocessing lock for the specified device.

    This function maintains a registry of locks per device to ensure that
    benchmarking operations on the same device are serialized, preventing
    interference between concurrent measurements.

    Parameters
    ----------
    device : str
        The device identifier (e.g., "cuda:0", "cuda:1").

    Returns
    -------
    LockType
        A lock object specific to the given device.
    """
    with _registry_lock:
        lock = _device_locks.get(device)
        if lock is None:
            lock = Lock()
            _device_locks[device] = lock
        return lock


def time_runnable(fn: Runnable, args: List[Any], warmup: int, iters: int, device: str) -> float:
    """Time the execution of a value-returning style Runnable kernel.

    Uses CUPTI activity tracing for precise hardware-level kernel timing,
    with automatic fallback to CUDA events if CUPTI is unavailable.

    Parameters
    ----------
    fn : Runnable
        The kernel function to benchmark (must be value-returning style).
    args : List[Any]
        List of arguments in definition order.
    warmup : int
        Number of warmup iterations before timing.
    iters : int
        Number of timing iterations to average over.
    device : str
        The CUDA device to run the benchmark on.

    Returns
    -------
    float
        The median execution time in milliseconds.
    """
    lock = _device_lock(device)
    with lock:
        with torch.cuda.device(device):
            times = bench_gpu_time_with_cupti(
                fn=fn,
                dry_run_iters=warmup,
                repeat_iters=iters,
                input_args=tuple(args),
                cold_l2_cache=True,
                use_cuda_graph=False,
            )
            return statistics.median(times)
