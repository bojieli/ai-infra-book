"""Builtin config registry presets."""

from functools import cache

from .config import ApplyConfig, ApplyConfigRegistry


@cache
def get_default_registry() -> ApplyConfigRegistry:
    """Get the default config registry (cached).

    The default registry applies all kernels with the default ApplyConfig.
    """
    return ApplyConfigRegistry(default=ApplyConfig())
