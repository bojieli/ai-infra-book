"""Exact independent conservation and decision-boundary review."""

from fractions import Fraction
from pathlib import Path
import hashlib
import importlib.util
import json
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "src"))
source = (
    ROOT
    / "research/architecture-variants/src/infra_calc/topics/architecture_variants.py"
)
spec = importlib.util.spec_from_file_location("independent_variants", source)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
results = []
for alignment in [1, 2, 64, 128, 256, 512, 1024]:
    # Alignment1 can produce odd FFN widths, hence use legalTP1 here.
    r = m.calculate(ffn_alignment=alignment, tp=1)
    for v in r["variants"]:
        c = v["config"]
        h = c["hidden_size"]
        l = c["num_hidden_layers"]
        d = 128
        q = c["num_attention_heads"]
        k = c["num_key_value_heads"]
        f = c["intermediate_size"]
        voc = 151936
        linear = 2 * h * q * d + 2 * h * k * d + 3 * h * f
        norm = (2 * h + 2 * d) * l + h
        p = 2 * voc * h + l * linear + norm
        assert p == v["actual_parameters"]
        ideal = Fraction(v["ideal_ffn_width_exact"])
        if v["name"] != "baseline":
            assert f % alignment == 0
            for other in [f - alignment, f + alignment]:
                if other > 0:
                    assert abs(Fraction(f) - ideal) <= abs(Fraction(other) - ideal)
        assert abs(v["parameter_delta"]) <= Fraction(
            v["max_rounding_error_parameters_exact"]
        )
        assert v["exact_equal_parameters"] == (p == 8190735360)
        results.append(
            dict(
                alignment=alignment,
                name=v["name"],
                parameters=p,
                ffn=f,
                delta=p - 8190735360,
            )
        )
# Halfway positive-width alignment tie must choose upper neighbor.
assert m.nearest_aligned(Fraction(192), 128) == 256
for batch, tokens, history, tp in [(1, 1, 8192, 2), (2, 7, 13, 2), (3, 29, 0, 1)]:
    r = m.calculate(batch=batch, tokens=tokens, history=history, tp=tp)
    baseline = r["variants"][0]
    for v in r["variants"]:
        c = v["config"]
        w = v["work"]
        h = c["hidden_size"]
        l = c["num_hidden_layers"]
        d = 128
        q = c["num_attention_heads"]
        k = c["num_key_value_heads"]
        f = c["intermediate_size"]
        voc = 151936
        # Enumerate one rank matrix shapes and every replicated norm vector.
        params_rank = (
            2 * voc // tp * h
            + l
            * (
                2 * (q // tp) * d * h
                + 2 * (k // tp) * d * h
                + 3 * h * (f // tp)
                + 2 * h
                + 2 * d
            )
            + h
        )
        assert w["per_rank_weight_bytes"] == 2 * params_rank
        assert (
            w["per_rank_kv_bytes"] == batch * (history + tokens) * l * (k // tp) * d * 4
        )
        pairs = sum(history + i + 1 for i in range(tokens)) * batch
        total = (
            2 * batch * tokens * l * (2 * h * q * d + 2 * h * k * d + 3 * h * f)
            + 4 * pairs * l * q * d
            + 2 * batch * voc * h
        )
        assert w["matrix_flops"] == total
        ring = (
            Fraction(2 * (tp - 1), tp)
            * batch
            * tokens
            * h
            * 2
            * (2 * l if tp > 1 else 0)
        )
        assert Fraction(w["per_rank_ring_wire_bytes_exact"]) == ring
    for comp, v in zip(r["comparisons"], r["variants"][1:]):
        bw = baseline["work"]
        vw = v["work"]
        a = bw["per_rank_live_budget_bytes"]
        b = vw["per_rank_live_budget_bytes"]
        interval = comp["capacity_interval_where_only_smaller_fits_bytes"]
        if a == b:
            assert interval is None
        else:
            lo, hi = interval
            assert [lo, hi] == [min(a, b), max(a, b) - 1]
            for cap, winner_count in [(lo - 1, 0), (lo, 1), (hi, 1), (hi + 1, 2)]:
                assert int(cap >= a) + int(cap >= b) == winner_count
        # Differences must reproduce direct two-term subpath service over exact rates.
        for rate, alpha in [
            (Fraction(10**9), Fraction(0)),
            (Fraction(10**11), Fraction(1, 10**6)),
        ]:
            direct = (
                Fraction(vw["per_rank_ring_wire_bytes_exact"]) / rate
                + vw["sequential_collectives"] * alpha
            ) - (
                Fraction(bw["per_rank_ring_wire_bytes_exact"]) / rate
                + bw["sequential_collectives"] * alpha
            )
            delta = (
                Fraction(comp["per_rank_ring_wire_delta_exact"]) / rate
                + comp["sequential_collectives_delta"] * alpha
            )
            assert direct == delta
r = m.calculate()
b, e = r["variants"][0], r["variants"][-1]
assert b["actual_parameters"] == e["actual_parameters"] == 8190735360
assert b["work"]["matrix_flops"] == e["work"]["matrix_flops"]
assert (
    b["work"]["kv_bytes_per_token_per_request"]
    == 4 * e["work"]["kv_bytes_per_token_per_request"]
)
for tp in (3, 4, 8, 16):
    try:
        m.calculate(tp=tp)
    except ValueError:
        pass
    else:
        raise AssertionError("Fractional-head whole-family TP should reject")
(HERE / "architecture_variants.snapshot.py").write_bytes(source.read_bytes())
(HERE / "results.json").write_text(
    json.dumps(
        dict(
            candidate_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
            alignment_variant_checks=len(results),
            alignment_results=results,
            request_geometries=3,
            all_comparison_capacity_edges_verified=True,
            exact_ring_difference_verified=True,
            unsupported_family_tp_rejected=[3, 4, 8, 16],
        ),
        indent=2,
    )
    + "\n"
)
print(
    "42 alignment variants,18 request-variant oracles and all capacity/ring edges passed"
)
