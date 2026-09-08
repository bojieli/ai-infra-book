"""Configuration for benchmark execution."""

from __future__ import annotations

import warnings
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from pydantic import BaseModel, Field, model_validator


class EvalConfig(BaseModel):
    """Per-definition eval parameters. All fields Optional; None means inherit from parent layer."""

    warmup_runs: Optional[int] = Field(default=None, ge=0)
    """Warmup iterations before timing. `None` means inherit."""
    iterations: Optional[int] = Field(default=None, gt=0)
    """Timed iterations per trial. `None` means inherit."""
    num_trials: Optional[int] = Field(default=None, gt=0)
    """Number of benchmark trials. `None` means inherit."""
    rtol: Optional[float] = Field(default=None, gt=0)
    """Relative tolerance for numerical checks. `None` means inherit."""
    atol: Optional[float] = Field(default=None, gt=0)
    """Absolute tolerance for numerical checks. `None` means inherit."""
    required_matched_ratio: Optional[float] = Field(default=None, gt=0, le=1)
    """Minimum fraction of elements that must be within tolerance. `None` means inherit."""
    extra: Dict[str, Any] = Field(default_factory=dict)
    """Evaluator-specific parameters that do not belong in the shared schema."""


class ResolvedEvalConfig(BaseModel):
    """Resolved eval parameters with all fields populated. This is what evaluators consume."""

    warmup_runs: int = 10
    """Warmup iterations before timing."""
    iterations: int = 50
    """Timed iterations per trial."""
    num_trials: int = 3
    """Number of benchmark trials."""
    rtol: float = 1e-2
    """Relative tolerance for numerical checks."""
    atol: float = 1e-2
    """Absolute tolerance for numerical checks."""
    required_matched_ratio: Optional[float] = None
    """Minimum fraction of elements that must be within tolerance."""
    profile_baseline: bool = True
    """Whether to profile the reference implementation for baseline latency."""
    extra: Dict[str, Any] = Field(default_factory=dict)
    """Evaluator-specific parameters after all config layers have been merged."""


class BenchmarkConfig(BaseModel):
    """Configuration for benchmark runs. Mirrors the YAML structure exactly.

    All fields have default values to make configuration optional.
    """

    # System-level
    use_isolated_runner: bool = False
    """Whether to use the isolated runner instead of the persistent runner."""
    definitions: Optional[List[str]] = None
    """Optional allowlist of definition names to benchmark."""
    solutions: Optional[List[str]] = None
    """Optional allowlist of solution names to benchmark."""
    timeout_seconds: int = Field(default=300, gt=0)
    """Timeout in seconds for each solution evaluation."""
    profile_baseline: bool = True
    """Whether to profile the reference implementation for baseline latency."""
    log_dir: Optional[str] = None
    """Deprecated. Logs are embedded in trace evaluations."""

    # Top-level / CLI overrides. None means "not set at this layer" — falls through
    # to YAML layers and the hardcoded defaults in ResolvedEvalConfig. When non-None,
    # these win over op_type_config and definition_config (CLI has highest priority).
    warmup_runs: Optional[int] = Field(default=None, ge=0)
    """CLI override for warmup iterations. None means inherit from YAML / defaults."""
    iterations: Optional[int] = Field(default=None, gt=0)
    """CLI override for timed iterations per trial. None means inherit from YAML / defaults."""
    num_trials: Optional[int] = Field(default=None, gt=0)
    """CLI override for number of benchmark trials. None means inherit from YAML / defaults."""
    rtol: Optional[float] = Field(default=None, gt=0)
    """CLI override for relative tolerance. None means inherit from YAML / defaults."""
    atol: Optional[float] = Field(default=None, gt=0)
    """CLI override for absolute tolerance. None means inherit from YAML / defaults."""
    required_matched_ratio: Optional[float] = Field(default=None, gt=0, le=1)
    """CLI override for required matched ratio. None means inherit from YAML / defaults."""
    # Deprecated: use op_type_config/definition_config extra instead. Kept as
    # top-level CLI-style overrides for the same reason as the other eval fields:
    # None means "not set at this layer"; non-None wins over YAML layer.extra.
    sampling_validation_trials: Optional[int] = Field(default=None, gt=0)
    """Deprecated CLI override for Sampling evaluator validation rounds."""
    sampling_tvd_threshold: Optional[float] = Field(default=None, ge=0, le=1)
    """Deprecated CLI override for Sampling evaluator TVD threshold."""

    # Per op_type / per definition overrides
    op_type_config: Dict[str, EvalConfig] = Field(default_factory=dict)
    """Per-op-type eval overrides keyed by `definition.op_type`."""
    definition_config: Dict[str, EvalConfig] = Field(default_factory=dict)
    """Per-definition eval overrides keyed by `definition.name`."""

    @model_validator(mode="after")
    def _validate_fields(self) -> BenchmarkConfig:
        if self.log_dir is not None:
            warnings.warn(
                "log_dir is deprecated and ignored; logs are embedded in trace evaluations",
                DeprecationWarning,
                stacklevel=2,
            )
        return self

    @classmethod
    def from_yaml(cls, path: str, **overrides: Any) -> BenchmarkConfig:
        """Load config from a YAML file, with optional field overrides."""
        with open(path) as f:
            data = yaml.safe_load(f) or {}
        data.update(overrides)
        return cls.model_validate(data)

    @classmethod
    def default(cls, **overrides: Any) -> BenchmarkConfig:
        """Load the bundled eval_config.yaml if it exists, otherwise use defaults."""
        yaml_path = Path(__file__).parent / "eval_config.yaml"
        if yaml_path.exists():
            return cls.from_yaml(str(yaml_path), **overrides)
        return cls(**overrides)

    def resolve_eval_config(self, definition: Any) -> ResolvedEvalConfig:
        """Merge priority (lowest -> highest): ResolvedEvalConfig defaults ->
        op_type_config -> definition_config -> top-level / CLI overrides.

        Top-level fields win when non-None, so a CLI flag such as
        ``--required-matched-ratio 0.9`` is never silently shadowed by a value
        coming from the packaged ``eval_config.yaml``.
        """
        merged: Dict[str, Any] = {"profile_baseline": self.profile_baseline, "extra": {}}

        layers = [
            self.op_type_config.get(definition.op_type),
            self.definition_config.get(definition.name),
        ]
        for layer in layers:
            if layer is None:
                continue
            updates = {
                k: v for k, v in layer.model_dump(exclude={"extra"}).items() if v is not None
            }
            merged.update(updates)
            if layer.extra:
                merged["extra"].update(layer.extra)

        top_level = {
            "warmup_runs": self.warmup_runs,
            "iterations": self.iterations,
            "num_trials": self.num_trials,
            "rtol": self.rtol,
            "atol": self.atol,
            "required_matched_ratio": self.required_matched_ratio,
        }
        merged.update({k: v for k, v in top_level.items() if v is not None})

        extra_overrides = {
            "sampling_validation_trials": self.sampling_validation_trials,
            "sampling_tvd_threshold": self.sampling_tvd_threshold,
        }
        merged["extra"].update({k: v for k, v in extra_overrides.items() if v is not None})

        return ResolvedEvalConfig(**merged)
