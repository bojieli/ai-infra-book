"""Architecture adapters; each declares the exact structure and execution path covered."""
"""Explicit model dispatch; unknown architectures never fall back to Dense."""
from . import qwen3, qwen3_moe, llama70
from ..schema import Scenario
from ..sources import model_config


def forward(model: str, scenario: Scenario, routing: str = "balanced", counts: list[int] | None = None) -> dict:
    kind = model_config(model)["model_type"]
    if kind == "qwen3_moe":
        return qwen3_moe.calculate(model, scenario, routing, counts)
    if kind == "qwen3":
        if counts is not None or routing != "balanced":
            raise ValueError("Dense models do not have expert routing inputs")
        return qwen3.calculate(model, scenario)
    if kind == "llama" and model == llama70.MODEL:
        if counts is not None or routing != "balanced":
            raise ValueError("Dense models do not have expert routing inputs")
        return llama70.calculate(model, scenario)
    raise ValueError(f"Full forward adapter not yet implemented for {model}: {kind}")
