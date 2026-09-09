"""Keep base units explicit; no rounding is used in stored byte counts."""
import math

KiB = 2**10
MiB = 2**20
GiB = 2**30
GB = 10**9
TB = 10**12


def positive_int(value: int, name: str, *, allow_zero: bool = False) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{name} must be an integer")
    if value < (0 if allow_zero else 1):
        raise ValueError(f"{name} must be {'nonnegative' if allow_zero else 'positive'}")
    return value


def positive_number(value: float, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or (isinstance(value, float) and not math.isfinite(value)) or value <= 0:
        raise ValueError(f"{name} must be finite and positive")
    return value


def ceil_div(numerator: int, denominator: int) -> int:
    positive_int(numerator, "numerator", allow_zero=True)
    positive_int(denominator, "denominator")
    return (numerator + denominator - 1) // denominator
