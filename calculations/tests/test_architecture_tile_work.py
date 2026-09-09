import sys
import unittest
from fractions import Fraction
from pathlib import Path

for ancestor in Path(__file__).resolve().parents:
    if (ancestor / "src/infra_calc/sources.py").is_file():
        sys.path.insert(0, str(ancestor / "src"))
        break
from infra_calc import topics

topics.__path__.insert(
    0, str(Path(__file__).resolve().parents[1] / "src/infra_calc/topics")
)
from infra_calc.topics import architecture_tile_work as m


class TileTests(unittest.TestCase):
    def test_small_tile_enumeration(self):
        for rows, k, n, tm, tk, tn in (
            (3, 5, 4, 2, 3, 3),
            (1, 2, 1, 4, 4, 4),
            (4, 6, 8, 2, 3, 4),
        ):
            result = m.matrix_tile(rows, k, n, tm, tk, tn)
            valid = padded = 0
            for i0 in range(0, rows, tm):
                for j0 in range(0, n, tn):
                    for k0 in range(0, k, tk):
                        for i in range(tm):
                            for j in range(tn):
                                for p in range(tk):
                                    padded += 2
                                    if i0 + i < rows and j0 + j < n and k0 + p < k:
                                        valid += 2
            self.assertEqual(result["valid_matrix_flops"], valid)
            self.assertEqual(result["fully_padded_matrix_flops"], padded)

    def test_causal_rectangle_and_conservation(self):
        result = m.calculate(batch=2, tokens=3, history=2)
        pairs = sum(j <= 2 + i for i in range(3) for j in range(5))
        for variant in result["variants"]:
            for row in variant["matrices"]:
                if row["name"] in ("qk", "pv"):
                    self.assertEqual(row["valid_per_instance_flops"], 2 * 128 * pairs)
                self.assertEqual(
                    row["padded_flops"],
                    row["valid_flops"]
                    + row["causal_rectangle_extra_flops"]
                    + row["tile_padding_extra_flops"],
                )
            self.assertEqual(
                sum(row["valid_flops"] for row in variant["matrices"]),
                variant["valid_flops"],
            )
        self.assertEqual(result, m.calculate(**result["scenario"]))

    def test_rate_threshold_and_decode(self):
        a = m.calculate(tokens=1, history=8192)
        for variant in a["variants"]:
            self.assertEqual(variant["causal_rectangle_extra_flops"], 0)
        threshold = float(
            Fraction(a["comparison"]["shallow_to_deep_padded_flop_ratio_exact"])
        )
        for multiple, expected in ((0.5, False), (2, True)):
            b = m.calculate(
                tokens=1,
                history=8192,
                variant_rates={"shallower_wider": 100e12 * threshold * multiple},
            )
            self.assertEqual(
                b["comparison"]["shallow_has_lower_conditional_matrix_service"],
                expected,
            )
            self.assertIsNone(b["variants"][0]["actual_tensor_core_utilization"])
            self.assertIsNone(b["variants"][0]["full_forward_runtime_seconds"])

    def test_invalid(self):
        for args in (
            {"tile_m": 0},
            {"tile_n": True},
            {"matrix_rate_flops_per_second": float("nan")},
            {"variant_rates": {"bogus": 1}},
            {"variant_rates": {"shallower_wider": 0}},
        ):
            with self.assertRaises(ValueError):
                m.calculate(**args)


if __name__ == "__main__":
    unittest.main()
