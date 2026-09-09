# Copyright (c) 2025, NVIDIA CORPORATION.  All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import sys
import time
from contextlib import contextmanager
from typing import Callable, Generator, Optional, Sequence, Union

import numpy as np


class Timer:
    """A utility for timing code execution.

    Supports two usage patterns:
    1. Explicit start/stop: timer.start("label"), timer.stop("label")
    2. Context manager: with timer.time("label"): ...

    The timer keeps track of multiple timing measurements for each label,
    and supports different reductions on these measurements (mean, median,
    min, max, std dev).

    Example usage:
    ```
    timer = Timer()

    # Method 1: start/stop
    timer.start("load_data")
    data = load_data()
    timer.stop("load_data")

    # Method 2: context manager
    with timer.time("model_forward"):
        model_outputs = model(inputs)

    # Multiple timing measurements for the same operation
    for batch in dataloader:
        with timer.time("model_forward_multiple"):
            outputs = model(batch)

    # Get all times for one label
    model_forward_times = timer.get_elapsed("model_forward_multiple")

    # Get reductions for one label
    mean_forward_time = timer.reduce("model_forward_multiple")
    max_forward_time = timer.reduce("model_forward_multiple", "max")
    ```
    """

    # Define valid reduction types and their corresponding NumPy functions
    _REDUCTION_FUNCTIONS: dict[str, Callable[[Sequence[float]], float]] = {
        "mean": np.mean,
        "median": np.median,
        "min": np.min,
        "max": np.max,
        "std": np.std,
        "sum": np.sum,
        "count": len,
    }

    def __init__(self) -> None:
        # Dictionary mapping labels to lists of elapsed times
        # We store a list of times for each label rather than a single value
        # to support multiple timing runs with the same label (e.g., in loops)
        # This allows calculating reductions like mean, min, max, and std dev
        self._timers: dict[str, list[float]] = {}
        self._start_times: dict[str, float] = {}

    def start(self, label: str) -> None:
        """Start timing for the given label."""
        if label in self._start_times:
            raise ValueError(f"Timer '{label}' is already running")
        self._start_times[label] = time.perf_counter()

    def stop(self, label: str) -> float:
        """Stop timing for the given label and return the elapsed time.

        Args:
            label: The label to stop timing for

        Returns:
            The elapsed time in seconds

        Raises:
            ValueError: If the timer for the given label is not running
        """
        if label not in self._start_times:
            raise ValueError(
                f"Timer '{label}' is not running. Running times: {self._start_times.keys()}"
            )

        elapsed = time.perf_counter() - self._start_times[label]
        if label not in self._timers:
            self._timers[label] = []
        self._timers[label].append(elapsed)
        del self._start_times[label]
        return elapsed

    @contextmanager
    def time(self, label: str) -> Generator[None, None, None]:
        """Context manager for timing a block of code.

        Args:
            label: The label to use for this timing

        Yields:
            None
        """
        self.start(label)
        try:
            yield
        finally:
            self.stop(label)

    def get_elapsed(self, label: str) -> list[float]:
        """Get all elapsed time measurements for a specific label.

        Args:
            label: The timing label to get elapsed times for

        Returns:
            A list of all elapsed time measurements in seconds

        Raises:
            KeyError: If the label doesn't exist
        """
        if label not in self._timers:
            raise KeyError(f"No timings recorded for '{label}'")

        return self._timers[label]

    def get_latest_elapsed(self, label: str) -> float:
        """Get the most recent elapsed time measurement for a specific label.

        Args:
            label: The timing label to get the latest elapsed time for

        Returns:
            The most recent elapsed time measurement in seconds

        Raises:
            KeyError: If the label doesn't exist
            IndexError: If the label exists but has no measurements
        """
        if label not in self._timers:
            raise KeyError(f"No timings recorded for '{label}'")

        if not self._timers[label]:
            raise IndexError(f"No measurements recorded for '{label}'")

        return self._timers[label][-1]

    def reduce(self, label: str, operation: str = "mean") -> float:
        """Apply a reduction function to timing measurements for the specified label.

        Args:
            label: The timing label to get reduction for
            operation: The type of reduction to apply. Valid options are:
                - "mean": Average time (default)
                - "median": Median time
                - "min": Minimum time
                - "max": Maximum time
                - "std": Standard deviation
                - "sum": Total time
                - "count": Number of measurements

        Returns:
            A single float with the reduction result

        Raises:
            KeyError: If the label doesn't exist
            ValueError: If an invalid operation is provided
        """
        if operation not in self._REDUCTION_FUNCTIONS:
            valid_reductions = ", ".join(self._REDUCTION_FUNCTIONS.keys())
            raise ValueError(
                f"Invalid operation '{operation}'. Valid options are: {valid_reductions}"
            )

        if label not in self._timers:
            raise KeyError(f"No timings recorded for '{label}'")

        reduction_func = self._REDUCTION_FUNCTIONS[operation]
        return reduction_func(self._timers[label])

    def get_timing_metrics(
        self, reduction_op: Union[str, dict[str, str]] = "mean"
    ) -> dict[str, float | list[float]]:
        """Get all timing measurements with optional reduction.

        Args:
            reduction_op: Either a string specifying a reduction operation to apply to all labels,
                         or a dictionary mapping specific labels to reduction operations.
                         Valid reduction operations are: "mean", "median", "min", "max", "std", "sum", "count".
                         If a label is not in the dictionary, no reduction is applied and all measurements are returned.

        Returns:
            A dictionary mapping labels to either:
            - A list of all timing measurements for that label (if no reduction specified)
            - A single float with the reduction result (if reduction specified)

        Raises:
            ValueError: If an invalid reduction operation is provided
        """
        if isinstance(reduction_op, str):
            reduction_op = {label: reduction_op for label in self._timers}

        results: dict[str, float | list[float]] = {}
        for label, op in reduction_op.items():
            if label not in self._timers:
                continue

            if op in self._REDUCTION_FUNCTIONS:
                results[label] = self.reduce(label, op)
            else:
                results[label] = self._timers[label]

        # Add any labels not in the reduction_op dictionary
        for label in self._timers:
            if label not in reduction_op:
                results[label] = self._timers[label]

        return results

    def reset(self, label: Optional[str] = None) -> None:
        """Reset timings for the specified label or all labels.

        Args:
            label: Optional label to reset. If None, resets all timers.
        """
        if label:
            if label in self._timers:
                del self._timers[label]
            if label in self._start_times:
                del self._start_times[label]
        else:
            self._timers = {}
            self._start_times = {}


def convert_to_seconds(time_string: str) -> int:
    """Converts a time string in the format 'DD:HH:MM:SS' to total seconds.

    Args:
        time_string (str): Time duration string, e.g., '00:03:45:00'.

    Returns:
        int: Total time in seconds.
    """
    days, hours, minutes, seconds = map(int, time_string.split(":"))
    return days * 86400 + hours * 3600 + minutes * 60 + seconds


class TimeoutChecker:
    def __init__(
        self, timeout: Optional[str] = "00:03:45:00", fit_last_save_time: bool = False
    ):
        """Initializes the TimeoutChecker.

        Args:
            timeout (str or None): Timeout in format 'DD:HH:MM:SS'. If None, timeout is considered infinite.
            fit_last_save_time (bool): If True, considers average iteration time when checking timeout.
        """
        super().__init__()
        self.last_save_time = (
            float("inf") if timeout is None else convert_to_seconds(timeout)
        )
        self.start_time = time.time()
        self.last_saved = False
        self.iteration_times = []
        self.previous_iteration_time: Optional[float] = None
        self.fit_last_save_time = fit_last_save_time

    def check_save(self):
        # Flush
        sys.stdout.flush()
        sys.stderr.flush()

        # Already saved after timeout
        if self.last_saved:
            return False

        current_time = time.time()
        elapsed_time = current_time - self.start_time

        if self.fit_last_save_time and self.iteration_times:
            average_iteration_time = sum(self.iteration_times) / len(
                self.iteration_times
            )
            if elapsed_time + average_iteration_time >= self.last_save_time:
                self.last_saved = True
                return True

        if elapsed_time >= self.last_save_time:
            self.last_saved = True
            return True

        return False

    def start_iterations(self):
        self.previous_iteration_time = time.time()

    def mark_iteration(self):
        sys.stdout.flush()
        sys.stderr.flush()

        current_time = time.time()
        if self.previous_iteration_time is not None:
            elapsed_time = current_time - self.previous_iteration_time
            self.previous_iteration_time = current_time
        self.iteration_times.append(elapsed_time)
