import math
from pathlib import Path
import sys
import unittest

HERE = Path(__file__).resolve().parent
for parent in HERE.parents:
    if (parent / "src/infra_calc/models").is_dir():
        sys.path.insert(0, str(parent / "src"))
        break
from infra_calc import topics

candidate = HERE.parent / "src/infra_calc/topics"
if (candidate / "real_scaling_lifecycle.py").exists():
    topics.__path__.insert(0, str(candidate))
from infra_calc.topics import real_scaling_lifecycle as module


class RealLifecycleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = module.calculate()

    def test_all_five_laws_independent_work(self):
        self.assertEqual(len(self.result["variants"]), 5)
        for variant in self.result["variants"]:
            law = variant["law"]
            for row in variant["lifecycle"]["rows"]:
                n = row["N"]
                d = law["D0"] * (
                    law["B"]
                    / (2.9 - law["E"] - law["A"] * (n / law["N0"]) ** (-law["alpha"]))
                ) ** (1 / law["beta"])
                self.assertTrue(math.isclose(d, row["D"], rel_tol=1e-12))
                self.assertEqual(row["prefill_proxy_flops_per_call"], 2 * n * 512)
                self.assertEqual(row["decode_proxy_flops_per_call"], 2 * n * 127)
                self.assertTrue(
                    math.isclose(row["training_proxy_flops"], 6 * n * d, rel_tol=1e-12)
                )
                self.assertTrue(
                    math.isclose(
                        row["cost_per_call"], 2 * n * (512 + 127) * 1e-18, rel_tol=1e-15
                    )
                )
        self.assertEqual(self.result["work_convention"]["additional_decode_steps"], 127)

    def test_crossover_two_lines_and_sides(self):
        count = 0
        for variant in self.result["variants"]:
            rows = {r["N"]: r for r in variant["lifecycle"]["rows"]}
            for cross in variant["crossing_checks"]:
                left, right = rows[cross["left_N"]], rows[cross["right_N"]]
                c = cross["calls"]
                l = left["upfront_cost"] + c * left["cost_per_call"]
                r = right["upfront_cost"] + c * right["cost_per_call"]
                self.assertTrue(math.isclose(l, r, rel_tol=1e-12))
                if c > 0:
                    before = (
                        left["upfront_cost"] + c * 0.99 * left["cost_per_call"]
                    ) - (right["upfront_cost"] + c * 0.99 * right["cost_per_call"])
                    after = (
                        left["upfront_cost"] + c * 1.01 * left["cost_per_call"]
                    ) - (right["upfront_cost"] + c * 1.01 * right["cost_per_call"])
                    self.assertLess(before * after, 0)
                count += 1
        self.assertGreater(count, 0)

    def test_extrapolation_explicit(self):
        rows = self.result["variants"][0]["lifecycle"]["rows"]
        self.assertEqual(
            [r["outside_fit_box"] for r in rows], [True, False, False, True]
        )
        self.assertGreater(rows[0]["extrapolation_factors"]["D"], 3.2)
        self.assertGreater(rows[-1]["extrapolation_factors"]["N"], 2.5)

    def test_one_returned_token_and_replay(self):
        result = module.calculate(returned_tokens=1)
        self.assertTrue(
            all(
                r["decode_proxy_flops_per_call"] == 0
                for v in result["variants"]
                for r in v["lifecycle"]["rows"]
                if r["feasible"]
            )
        )
        self.assertEqual(self.result, module.calculate(**self.result["scenario"]))

    def test_invalid_and_cost_units(self):
        for kwargs in [
            dict(returned_tokens=0),
            dict(returned_tokens=True),
            dict(calls=[-1]),
            dict(calls=[True]),
            dict(candidate_sizes=[1e9, 1e9]),
            dict(cost_per_proxy_flop=float("inf")),
        ]:
            with self.assertRaises(ValueError):
                module.calculate(**kwargs)
        altered = module.calculate(cost_per_proxy_flop=2e-18)
        self.assertTrue(any("2e-18 abstract cost units" in x for x in altered["scope"]))
        a = self.result["variants"][0]["lifecycle"]["rows"][0]
        b = altered["variants"][0]["lifecycle"]["rows"][0]
        self.assertEqual(b["upfront_cost"], a["upfront_cost"] * 2)


if __name__ == "__main__":
    unittest.main()
