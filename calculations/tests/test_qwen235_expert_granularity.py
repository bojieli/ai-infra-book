import copy
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
from infra_calc.topics import qwen235_expert_granularity as m
from infra_calc.topics import qwen235_execution, qwen235_placement


class GranularityTests(unittest.TestCase):
    def test_real_baseline_crosscheck(self):
        for tp, ep, pp in ((2, 4, 1), (1, 4, 2)):
            result = m.calculate(tp=tp, ep=ep, pp=pp, tokens=2)
            baseline = qwen235_execution.calculate(tp=tp, ep=ep, pp=pp, tokens=2)
            self.assertEqual(result["parameters"]["total_delta"], 0)
            self.assertEqual(
                result["summary"]["expert_matrix_flops"],
                baseline["summary"]["expert_matrix_flops"],
            )
            self.assertEqual(
                result["summary"]["total_wire_bytes"],
                baseline["summary"]["total_wire_bytes"],
            )
            self.assertEqual(result["route_table"], baseline["route_table"])
            for a, b in zip(result["ranks"], baseline["ranks"]):
                self.assertEqual(a["total_bf16_weight_bytes"], b["bf16_weight_bytes"])
                self.assertEqual(a["bf16_kv_bytes"], b["bf16_kv_bytes"])
                self.assertEqual(
                    a["expert_matrix_flops"], b["work"]["expert_matrix_flops"]
                )
            self.assertEqual(result, m.calculate(**result["scenario"]))

    def test_exact_budget_and_activation(self):
        base = m.calculate(tokens=2)
        for experts, top in ((64, 4), (256, 16)):
            result = m.calculate(experts=experts, top_k=top, tokens=2)
            self.assertEqual(
                result["parameters"]["expert_total"], base["parameters"]["expert_total"]
            )
            self.assertEqual(
                result["parameters"]["active_expert_parameters_per_token_all_layers"],
                base["parameters"]["active_expert_parameters_per_token_all_layers"],
            )
            g = result["geometry"]
            self.assertEqual(
                result["parameters"]["total_delta"],
                g["layers"] * g["hidden"] * (experts - 128),
            )
            for rank in result["ranks"]:
                for row in rank["expert_matrices"]:
                    for name in ("gate", "up", "down"):
                        op = row[name]
                        self.assertEqual(
                            op["flops"],
                            2 * op["input"][0] * op["input"][1] * op["weight"][0],
                        )
            self.assertIsNone(result["summary"]["trained_quality"])
        reduced = m.calculate(experts=256, top_k=8, tokens=2)
        self.assertEqual(
            reduced["summary"]["expert_matrix_flops"] * 2,
            base["summary"]["expert_matrix_flops"],
        )

    def test_nonexact_alignment(self):
        result = m.calculate(experts=160, top_k=10, tokens=2)
        self.assertEqual(result["geometry"]["intermediate"], 1280)
        p = result["parameters"]
        self.assertNotEqual(p["expert_delta"], 0)
        self.assertLessEqual(
            abs(p["expert_delta"]), Fraction(p["expert_alignment_error_bound_exact"])
        )
        self.assertEqual(
            Fraction(p["expert_relative_delta_exact"]),
            Fraction(p["expert_delta"], p["expert_target"]),
        )

    def test_route_sets_and_capacity_boundary(self):
        result = m.calculate(tokens=2)
        pure = copy.deepcopy(result["route_table"])
        for row in pure:
            row["experts"] = (
                list(range(8)) if row["position"] == 0 else list(range(32, 40))
            )
        mixed = copy.deepcopy(pure)
        for row in mixed:
            off = 4 * row["position"]
            row["experts"] = list(range(off, off + 4)) + list(range(32 + off, 36 + off))
        a, b = m.calculate(tokens=2, routes=pure), m.calculate(tokens=2, routes=mixed)
        self.assertEqual(
            [x["counts"] for x in a["histograms"]],
            [x["counts"] for x in b["histograms"]],
        )
        self.assertGreater(
            b["summary"]["total_wire_bytes"], a["summary"]["total_wire_bytes"]
        )
        boundary = max(rank["conditional_resident_bytes"] for rank in result["ranks"])
        self.assertTrue(
            m.calculate(tokens=2, capacity_bytes=boundary)["summary"][
                "all_necessary_capacity_fits"
            ]
        )
        self.assertFalse(
            m.calculate(tokens=2, capacity_bytes=boundary - 1)["summary"][
                "all_necessary_capacity_fits"
            ]
        )

    def test_invalid_variant(self):
        for args in (
            {"experts": 127},
            {"experts": 4, "top_k": 8},
            {"alignment": 0},
            {"routes": []},
            {"top_k": True},
        ):
            with self.assertRaises(ValueError):
                m.calculate(**args)


if __name__ == "__main__":
    unittest.main()
