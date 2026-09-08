"""TraceSet as a pure data warehouse for definitions, solutions, and traces."""

from __future__ import annotations

import shutil
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import safetensors.torch
import torch

from flashinfer_bench.env import get_fib_dataset_path

from .definition import Definition
from .json_utils import append_jsonl_file, load_json_file, load_jsonl_file
from .solution import Solution
from .trace import EvaluationStatus, Trace
from .utils import BaseModelWithDocstrings


class SpeedupMetrics(BaseModelWithDocstrings):
    """Score result based on average speedup over a baseline."""

    avg_speedup: float
    """Mean of ``baseline_latency / scored_latency`` across included workloads."""

    definitions: int
    """Number of definitions contributing to the score."""

    workloads: int
    """Number of workloads compared."""

    success_rate: float
    """Fraction of workloads with successful execution."""

    win_rate: float
    """Fraction of workloads where the scored entity beats the baseline."""

    best_solutions: Optional[Dict[str, str]] = None
    """Only used for author score calculation. Mapping from definition name to the best
    solution name for this author. None for solution score calculation."""


class TraceSetSummary(BaseModelWithDocstrings):
    """Aggregate counts and author rankings for a ``TraceSet``."""

    total: int
    """Total number of traces."""

    passed: int
    """Number of traces with successful evaluation."""

    failed: int
    """Number of traces with failed evaluation."""

    rankings: List[Tuple[str, SpeedupMetrics]]
    """Author rankings sorted by ``avg_speedup`` descending. Each entry is
    ``(author_name, score)``."""


@dataclass
class TraceSet:
    """Stores a FlashInfer Trace dataset containing definitions, solutions, workloads, and traces.

    TraceSet serves as a centralized data warehouse for managing FlashInfer benchmark data.
    It provides efficient lookup and filtering capabilities for definitions, solutions, and
    execution traces organized by definition names.

    The data structure is optimized for fast lookups with dictionary-based storage where
    keys are definition names and values are lists of associated objects.
    """

    root: Optional[Path] = None
    """The root path of the TraceSet. If None, all add() or get() operations will be performed
    in-memory."""
    definitions: Dict[str, Definition] = field(default_factory=dict)
    """The definitions in the database. Map from definition name to Definition object."""
    solutions: Dict[str, List[Solution]] = field(default_factory=dict)
    """The solutions in the database. Map from definition name to all the solutions for that
    definition."""
    workloads: Dict[str, List[Trace]] = field(default_factory=dict)
    """The workload traces in the database. Map from definition name to all workload traces for that
    definition."""
    traces: Dict[str, List[Trace]] = field(default_factory=dict)
    """The traces in the database. Map from definition name to all traces for that definition."""
    _solution_by_name: Dict[str, Solution] = field(default_factory=dict, init=False, repr=False)
    """Fast lookup index: solution name -> Solution object. Automatically maintained."""
    _traces_by_solution: Dict[str, List[Trace]] = field(
        default_factory=dict, init=False, repr=False
    )
    """Fast lookup index: solution name -> list of Trace objects. Automatically maintained."""

    def __post_init__(self):
        """Initialize lookup indexes from existing data."""
        for solutions_list in self.solutions.values():
            for solution in solutions_list:
                if solution.name in self._solution_by_name:
                    raise ValueError(f"Duplicate solution name found: {solution.name}")
                self._solution_by_name[solution.name] = solution
        for traces_list in self.traces.values():
            for trace in traces_list:
                if trace.solution:
                    self._traces_by_solution.setdefault(trace.solution, []).append(trace)

    @property
    def definitions_path(self) -> Path:
        if self.root is None:
            raise ValueError("Root path is not set")
        return self.root / "definitions"

    @property
    def solutions_path(self) -> Path:
        if self.root is None:
            raise ValueError("Root path is not set")
        return self.root / "solutions"

    @property
    def workloads_path(self) -> Path:
        if self.root is None:
            raise ValueError("Root path is not set")
        return self.root / "workloads"

    @property
    def traces_path(self) -> Path:
        if self.root is None:
            raise ValueError("Root path is not set")
        return self.root / "traces"

    @property
    def blob_path(self) -> Path:
        if self.root is None:
            raise ValueError("Root path is not set")
        return self.root / "blob"

    @property
    def blob_workloads_path(self) -> Path:
        if self.root is None:
            raise ValueError("Root path is not set")
        return self.root / "blob" / "workloads"

    @classmethod
    def from_path(cls: type[TraceSet], path: Optional[str] = None) -> TraceSet:
        """Load a TraceSet from a directory structure.

        Loads a complete TraceSet by scanning the directory structure for:
        - definitions/: JSON files containing Definition objects
        - solutions/: JSON files containing Solution objects
        - workloads/: JSONL files containing Trace objects (workload traces)
        - traces/: JSONL files containing Trace objects (execution traces)

        Parameters
        ----------
        path : Optional[str], optional
            Root directory path containing the dataset structure. If None,
            the global environment variable FIB_DATASET_PATH is used. If
            FIB_DATASET_PATH is not set, ~/.cache/flashinfer_bench/dataset is used.

        Returns
        -------
        TraceSet
            A new TraceSet instance populated with data from the directory.

        Raises
        ------
        ValueError
            If duplicate definition names or solution names are found.
        FileNotFoundError
            If the specified path doesn't exist.
        """
        path = Path(path) if path else get_fib_dataset_path()

        # Create the path if it doesn't exist
        path.mkdir(parents=True, exist_ok=True)

        trace_set = cls(root=path)

        # Load json files from all subdirectories
        for p in sorted((trace_set.definitions_path.rglob("*.json"))):
            d = load_json_file(Definition, p)
            if d.name in trace_set.definitions:
                raise ValueError(f"Duplicate definition name: {d.name}")
            trace_set.definitions[d.name] = d

        seen_solutions = set()
        for p in sorted((trace_set.solutions_path.rglob("*.json"))):
            s = load_json_file(Solution, p)
            if s.name in seen_solutions:
                raise ValueError(f"Duplicate solution name: {s.name}")
            seen_solutions.add(s.name)
            trace_set.solutions.setdefault(s.definition, []).append(s)
            trace_set._solution_by_name[s.name] = s

        for p in sorted((trace_set.workloads_path.rglob("*.jsonl"))):
            for t in load_jsonl_file(Trace, p):
                assert t.is_workload_trace()
                trace_set.workloads.setdefault(t.definition, []).append(t)

        for p in sorted((trace_set.traces_path.rglob("*.jsonl"))):
            for t in load_jsonl_file(Trace, p):
                assert not t.is_workload_trace()
                trace_set.traces.setdefault(t.definition, []).append(t)
                if t.solution:
                    trace_set._traces_by_solution.setdefault(t.solution, []).append(t)

        return trace_set

    def to_dict(self) -> Dict[str, Any]:
        """Convert the TraceSet to a Python dict.

        Returns
        -------
        Dict[str, Any]
            A dictionary representation of the TraceSet.
        """
        return {
            "definitions": {
                name: definition.model_dump(mode="json")
                for name, definition in self.definitions.items()
            },
            "solutions": {
                name: [solution.model_dump(mode="json") for solution in solutions]
                for name, solutions in self.solutions.items()
            },
            "workload": {
                name: [workload.model_dump(mode="json") for workload in workloads]
                for name, workloads in self.workloads.items()
            },
            "traces": {
                name: [trace.model_dump(mode="json") for trace in traces]
                for name, traces in self.traces.items()
            },
        }

    def get_solution(self, name: str) -> Optional[Solution]:
        """Get a solution by name from all loaded solutions.

        Uses an O(1) index lookup for fast retrieval. Since solution names are unique
        across the entire dataset, this returns at most one solution.

        Parameters
        ----------
        name : str
            The name of the solution to retrieve.

        Returns
        -------
        Optional[Solution]
            The solution with the given name, or None if not found.
        """
        return self._solution_by_name.get(name)

    def filter_traces(self, def_name: str, atol: float = 1e-2, rtol: float = 1e-2) -> List[Trace]:
        """Filter traces for a definition based on error bounds.

        Returns only successful traces that meet the specified absolute and relative
        error tolerance criteria. This is useful for finding high-quality implementations
        that produce numerically accurate results.

        Parameters
        ----------
        def_name : str
            Name of the definition to filter traces for.
        atol : float, optional
            Maximum absolute error tolerance, by default 1e-2.
        rtol : float, optional
            Maximum relative error tolerance, by default 1e-2.

        Returns
        -------
        List[Trace]
            List of traces that passed evaluation and meet error criteria.
            Empty list if no traces match the criteria.
        """
        return [
            t
            for t in self.traces.get(def_name, [])
            if t.evaluation
            and t.evaluation.status == EvaluationStatus.PASSED
            and t.evaluation.correctness
            and t.evaluation.correctness.max_absolute_error <= atol
            and t.evaluation.correctness.max_relative_error <= rtol
        ]

    def get_best_trace(
        self,
        def_name: str,
        axes: Optional[Dict[str, int]] = None,
        max_abs_error: float = 1e-2,
        max_rel_error: float = 1e-2,
    ) -> Optional[Trace]:
        """Get the best performing trace for a definition based on speedup factor.

        Finds the trace with the highest speedup factor among those that meet the
        specified criteria including axis constraints and error tolerances.

        Parameters
        ----------
        def_name : str
            Name of the definition to find the best trace for.
        axes : Optional[Dict[str, int]], optional
            Dictionary of axis name to value pairs for exact matching.
            Only traces with exactly matching axis values will be considered.
            If None, all axis configurations are considered.
        max_abs_error : float, optional
            Maximum absolute error tolerance, by default 1e-2.
        max_rel_error : float, optional
            Maximum relative error tolerance, by default 1e-2.

        Returns
        -------
        Optional[Trace]
            The best performing trace meeting all criteria, or None if no traces
            match the requirements.
        """
        candidates = self.traces.get(def_name, [])

        # Axes exact match
        # TODO(shanli): advanced input filtering
        if axes:
            candidates = [
                t
                for t in candidates
                if all(t.workload.axes.get(ax) == val for ax, val in axes.items())
            ]

        # Filter by successful status
        candidates = [
            t for t in candidates if t.evaluation and t.evaluation.status == EvaluationStatus.PASSED
        ]

        # Filter by error bounds
        candidates = [
            t
            for t in candidates
            if t.evaluation.correctness.max_absolute_error <= max_abs_error
            and t.evaluation.correctness.max_relative_error <= max_rel_error
        ]

        # Return the one with best speedup
        if candidates:
            return max(
                candidates,
                key=lambda t: t.evaluation.performance.speedup_factor if t.evaluation else 0,
            )

        return None

    def summary(
        self,
        baseline_author: str = "baseline",
        op_type: Optional[str] = None,
        definition_name: Optional[str] = None,
    ) -> TraceSetSummary:
        """Get aggregate trace counts and author rankings for the current dataset.

        Returns
        -------
        TraceSetSummary
            Trace counts (``total``, ``passed``, ``failed``) and author
            ``rankings`` sorted by ``avg_speedup`` descending.
        """
        all_traces = [t for traces in self.traces.values() for t in traces]

        if not all_traces:
            return TraceSetSummary(total=0, passed=0, failed=0, rankings=[])

        passed = [
            t for t in all_traces if t.evaluation and t.evaluation.status == EvaluationStatus.PASSED
        ]

        rankings = self.rank_authors(
            baseline_author=baseline_author, op_type=op_type, definition_name=definition_name
        )

        return TraceSetSummary(
            total=len(all_traces),
            passed=len(passed),
            failed=len(all_traces) - len(passed),
            rankings=rankings,
        )

    def get_solution_score(
        self, solution_name: str, baseline_author: str = "baseline"
    ) -> Optional[SpeedupMetrics]:
        """Get the score for a single solution against the baseline.

        The baseline is determined by ``baseline_author``, which must map to
        exactly one solution in the same definition (0 or >1 raises ValueError).
        The baseline solution itself is not scored (returns None).

        For each workload (matched by ``workload.uuid``), the speedup is
        ``baseline_latency / solution_latency``. When a (solution, workload)
        pair has multiple traces, the lowest-latency passing trace is used.
        Only workloads where the baseline also has a passing trace participate.

        If the solution has any failed trace (``status != PASSED``), the entire
        score is 0. Otherwise the score is the mean speedup across workloads.

        Parameters
        ----------
        solution_name : str
            Solution name to score.
        baseline_author : str
            Author name to use as baseline (default: 'baseline').

        Returns
        -------
        SpeedupMetrics | None
            Score result, or ``None`` if the solution is unknown, is the
            baseline itself, or has no comparable workloads.

        Raises
        ------
        ValueError
            If the baseline author has zero or more than one solution for the
            definition, or if a PASSED trace has invalid performance data.
        """
        solution = self._solution_by_name.get(solution_name)
        if solution is None:
            return None

        def_name = solution.definition

        # Baseline must map to exactly one solution per definition
        baseline_solutions = [
            s for s in self.solutions.get(def_name, []) if s.author == baseline_author
        ]
        if len(baseline_solutions) == 0:
            raise ValueError(
                f"No baseline solution from author {baseline_author!r} "
                f"for definition {def_name!r}"
            )
        if len(baseline_solutions) > 1:
            raise ValueError(
                f"Multiple baseline solutions from author {baseline_author!r} "
                f"for definition {def_name!r}: {[s.name for s in baseline_solutions]}"
            )
        baseline_solution = baseline_solutions[0]

        # Baseline solution itself is excluded from scoring
        if solution.name == baseline_solution.name:
            return None

        solution_traces = self._traces_by_solution.get(solution_name, [])
        baseline_traces = self._traces_by_solution.get(baseline_solution.name, [])

        # Per-workload best passing latency for the solution.
        # Also track which workloads the solution touched and whether any trace failed.
        has_fail = False
        solution_best_latency: Dict[str, float] = {}
        solution_workload_uuids: set[str] = set()
        for t in solution_traces:
            if not t.evaluation:
                continue
            uuid = t.workload.uuid
            solution_workload_uuids.add(uuid)
            if t.evaluation.status != EvaluationStatus.PASSED:
                has_fail = True
                continue
            if not t.evaluation.performance or t.evaluation.performance.latency_ms <= 0:
                raise ValueError(
                    f"PASSED trace for solution {t.solution!r} workload {uuid!r} "
                    f"has invalid performance data"
                )
            latency = t.evaluation.performance.latency_ms
            if uuid not in solution_best_latency or latency < solution_best_latency[uuid]:
                solution_best_latency[uuid] = latency

        # Per-workload best passing latency for the baseline
        baseline_best_latency: Dict[str, float] = {}
        for t in baseline_traces:
            if not t.evaluation:
                continue
            uuid = t.workload.uuid
            if t.evaluation.status != EvaluationStatus.PASSED:
                continue
            if not t.evaluation.performance or t.evaluation.performance.latency_ms <= 0:
                raise ValueError(
                    f"PASSED trace for solution {t.solution!r} workload {uuid!r} "
                    f"has invalid performance data"
                )
            latency = t.evaluation.performance.latency_ms
            if uuid not in baseline_best_latency or latency < baseline_best_latency[uuid]:
                baseline_best_latency[uuid] = latency

        # Only workloads where baseline passed AND solution has at least one trace
        common = set(baseline_best_latency.keys()) & solution_workload_uuids
        if not common:
            return None

        workloads = len(common)

        # Any failed trace → entire solution scores 0
        if has_fail:
            return SpeedupMetrics(
                avg_speedup=0.0, definitions=1, workloads=workloads, success_rate=0.0, win_rate=0.0
            )

        # Compute per-workload speedup = baseline_latency / solution_latency
        speedups = []
        wins = 0
        for uuid in common:
            ratio = baseline_best_latency[uuid] / solution_best_latency[uuid]
            speedups.append(ratio)
            if ratio > 1.0:
                wins += 1

        return SpeedupMetrics(
            avg_speedup=sum(speedups) / workloads,
            definitions=1,
            workloads=workloads,
            success_rate=1.0,
            win_rate=wins / workloads,
            best_solutions=None,
        )

    def get_author_score(
        self,
        author: str,
        baseline_author: str = "baseline",
        op_type: Optional[str] = None,
        definition_name: Optional[str] = None,
    ) -> Optional[SpeedupMetrics]:
        """Get the score for a single author within the selected scope.

        Within each scoped definition, the author may own multiple solutions.
        Only the best-scoring one (highest ``avg_speedup``) is kept per
        definition. The author's final score is the mean of these
        per-definition best scores.

        Parameters
        ----------
        author : str
            Author name to score.
        baseline_author : str
            Author name to use as baseline (default: 'baseline').
        op_type : Optional[str]
            Operation type to score within.
        definition_name : Optional[str]
            Definition name to score within.

        Returns
        -------
        SpeedupMetrics | None
            Author score, or ``None`` if the author has no scorable solutions
            in scope.

        Raises
        ------
        KeyError
            If ``definition_name`` is provided but not found.
        ValueError
            If both ``op_type`` and ``definition_name`` are provided.
        """
        if op_type is not None and definition_name is not None:
            raise ValueError("Only one of 'op_type' or 'definition_name' may be provided")
        if definition_name is not None:
            if definition_name not in self.definitions:
                raise KeyError(f"Unknown definition: {definition_name!r}")
            scoped_defs = {definition_name}
        elif op_type is not None:
            scoped_defs = {name for name, d in self.definitions.items() if d.op_type == op_type}
        else:
            scoped_defs = set(self.definitions.keys())

        # For each definition, keep only the author's best solution
        per_def_best: List[SpeedupMetrics] = []
        best_solutions: Dict[str, str] = {}
        for def_name in scoped_defs:
            author_solutions = [s for s in self.solutions.get(def_name, []) if s.author == author]
            scored = [
                (s.name, self.get_solution_score(s.name, baseline_author)) for s in author_solutions
            ]
            valid = [(name, m) for name, m in scored if m is not None]
            if valid:
                best_name, best_metric = max(valid, key=lambda x: x[1].avg_speedup)
                per_def_best.append(best_metric)
                best_solutions[def_name] = best_name

        if not per_def_best:
            return None

        # Simple mean across definitions (not weighted by workload count)
        n = len(per_def_best)
        return SpeedupMetrics(
            avg_speedup=sum(s.avg_speedup for s in per_def_best) / n,
            definitions=n,
            workloads=sum(s.workloads for s in per_def_best),
            success_rate=sum(s.success_rate for s in per_def_best) / n,
            win_rate=sum(s.win_rate for s in per_def_best) / n,
            best_solutions=best_solutions,
        )

    def rank_authors(
        self,
        baseline_author: str = "baseline",
        op_type: Optional[str] = None,
        definition_name: Optional[str] = None,
    ) -> List[Tuple[str, SpeedupMetrics]]:
        """Rank all authors by average speedup within the selected scope.

        Collects all distinct authors from solutions in the scoped definitions,
        scores each via ``get_author_score``, filters out None results (e.g.
        baseline author), and sorts by ``avg_speedup`` descending.

        Parameters
        ----------
        baseline_author : str
            Author name to use as baseline (default: 'baseline').
        op_type : Optional[str]
            Operation type to rank within.
        definition_name : Optional[str]
            Definition name to rank within.

        Returns
        -------
        list[tuple[str, SpeedupMetrics]]
            ``(author_name, score)`` pairs sorted by ``avg_speedup``
            descending, then by author name.

        Raises
        ------
        KeyError
            If ``definition_name`` is provided but not found.
        ValueError
            If both ``op_type`` and ``definition_name`` are provided.
        ValueError
            If any included definition is missing a baseline solution from
            ``baseline_author``.
        """
        if op_type is not None and definition_name is not None:
            raise ValueError("Only one of 'op_type' or 'definition_name' may be provided")
        if definition_name is not None:
            if definition_name not in self.definitions:
                raise KeyError(f"Unknown definition: {definition_name!r}")
            scoped_defs = {definition_name}
        elif op_type is not None:
            scoped_defs = {name for name, d in self.definitions.items() if d.op_type == op_type}
        else:
            scoped_defs = set(self.definitions.keys())

        # Collect all distinct authors in scope
        authors: set[str] = set()
        for def_name in scoped_defs:
            for s in self.solutions.get(def_name, []):
                authors.add(s.author)

        # Score each author; baseline author will get None (excluded) and be filtered out
        rankings: List[Tuple[str, SpeedupMetrics]] = []
        for author in authors:
            result = self.get_author_score(
                author,
                baseline_author=baseline_author,
                op_type=op_type,
                definition_name=definition_name,
            )
            if result is not None:
                rankings.append((author, result))

        rankings.sort(key=lambda x: (-x[1].avg_speedup, x[0]))
        return rankings

    def backup_traces(self) -> None:
        """Backup the traces directory to a new directory. This is useful when we want to keep the
        old traces for reference.
        """
        if self.root is None:
            raise ValueError("Root path is not set")
        traces_path = self.traces_path
        backup_path = self.root / f"traces_bak_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Move traces directory to backup
        if traces_path.exists():
            shutil.move(str(traces_path), str(backup_path))
        else:
            backup_path.mkdir(parents=True, exist_ok=True)

        # Create new traces directory
        traces_path.mkdir(parents=True, exist_ok=True)

    def add_traces(self, traces: List[Trace]) -> None:
        """Add traces to the TraceSet, and store the traces to disk.

        Parameters
        ----------
        traces : List[Trace]
            The traces to add to the TraceSet.
        """
        buckets: Dict[Path, List[Trace]] = defaultdict(list)
        for trace in traces:
            # Add to in-memory database
            if trace.definition not in self.definitions:
                raise ValueError(
                    f"Add trace failed: Definition {trace.definition} not found in TraceSet"
                )
            self.traces.setdefault(trace.definition, []).append(trace)
            if trace.solution:
                self._traces_by_solution.setdefault(trace.solution, []).append(trace)

            # Add to disk bucket
            definition = self.definitions[trace.definition]
            if trace.solution is None:
                raise ValueError("Cannot add workload-only trace with add_traces")
            solution = self._solution_by_name.get(trace.solution)
            if solution is None:
                raise ValueError(f"Unknown solution: {trace.solution}")
            path = (
                self.traces_path / solution.author / definition.op_type / f"{definition.name}.jsonl"
            )
            buckets[path].append(trace)

        # Write to disk
        if self.root is not None:
            for path, traces in buckets.items():
                append_jsonl_file(traces, path)

    def add_workload_blob_tensor(
        self, def_name: str, workload_uuid: str, tensors: Dict[str, torch.Tensor]
    ) -> str:
        """Store a dict of workload blob tensors to a safetensors file, and return the saved file
        path relative to the TraceSet root.

        Parameters
        ----------
        def_name : str
            The def name of the tensor.
        workload_uuid : str
            The workload uuid of the tensor.
        tensors : Dict[str, torch.Tensor]
            The dict of tensors to store.

        Returns
        -------
        str
            The file path of the saved tensor.

        Raises
        ------
        ValueError
            If the root path is not set, or the constructed tensor path already exists.

        OSError
            If writing to disk fails.
        """
        if self.root is None:
            raise ValueError("Root path is not set")
        op_type = self.definitions[def_name].op_type
        file_path = (
            self.blob_workloads_path
            / op_type
            / def_name
            / f"{def_name}_{workload_uuid}.safetensors"
        )
        file_path.parent.mkdir(parents=True, exist_ok=True)
        # Throw error if the tensor path exists
        if file_path.exists():
            raise ValueError(f"Tensor save path already exists: {file_path}")
        cpu_tensors = {k: (v.cpu() if v.is_cuda else v) for k, v in tensors.items()}
        safetensors.torch.save_file(cpu_tensors, file_path)
        return str(file_path.relative_to(self.root))

    def get_workload_blob_tensor(self, path_str: str) -> Dict[str, torch.Tensor]:
        """Get a workload blob tensor from disk to CPU.

        Parameters
        ----------
        path_str : str
            The file path of the tensor relative to the TraceSet root.

        Returns
        -------
        Dict[str, torch.Tensor]
            The dict of tensors from the file.
        """
        if self.root is None:
            raise ValueError("Root path is not set")
        file_path = self.root / path_str
        if not file_path.exists():
            raise ValueError(f"File not found: {file_path}")
        return safetensors.torch.load_file(file_path, device="cpu")

    def add_workload_traces(self, traces: List[Trace]) -> None:
        """Add workload traces to the TraceSet, and store the traces to disk.

        Parameters
        ----------
        traces : List[Trace]
            The traces to add to the TraceSet.
        """
        buckets: Dict[Path, List[Trace]] = defaultdict(list)
        for trace in traces:
            # Add to in-memory database
            if trace.definition not in self.definitions:
                raise ValueError(
                    f"Add workload trace failed: Definition {trace.definition} "
                    "not found in TraceSet"
                )
            self.workloads.setdefault(trace.definition, []).append(trace)

            # Add to disk bucket
            definition = self.definitions[trace.definition]
            path = self.workloads_path / definition.op_type / f"{definition.name}.jsonl"
            buckets[path].append(trace)

        # Write to disk
        if self.root is not None:
            for path, traces in buckets.items():
                append_jsonl_file(traces, path)
