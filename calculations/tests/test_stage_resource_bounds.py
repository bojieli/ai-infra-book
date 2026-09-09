import copy
import unittest
from pathlib import Path
import sys
from unittest.mock import patch

for ancestor in Path(__file__).resolve().parents:
    if (ancestor / "src/infra_calc/sources.py").is_file():
        sys.path.insert(0, str(ancestor / "src"))
        break
from infra_calc import topics, hardware

topics.__path__.insert(
    0, str(Path(__file__).resolve().parents[1] / "src/infra_calc/topics")
)
from infra_calc.topics import stage_resource_bounds as m


class BoundsTests(unittest.TestCase):
    def test_serial_counterexample_and_zero_unknown(self):
        stages = [
            dict(id="a", work={"compute": 10, "bytes": 1}),
            dict(id="b", work={"compute": 1, "bytes": 10, "absent": 0}),
        ]
        r = m.bounds(stages, {"compute": 1, "bytes": 1})
        self.assertEqual(r["accounted_serial_stage_lower_bound_seconds"], 20)
        self.assertEqual(r["accounted_global_max_seconds"], 11)
        self.assertEqual(r["missing_resources"], [])

    def test_unknown_positive_and_unknown_work(self):
        r = m.bounds(
            [dict(id="a", work={"compute": 10, "unknown": 1, "bytes": None})],
            {"compute": 2},
        )
        self.assertIsNone(r["accounted_serial_stage_lower_bound_seconds"])
        self.assertEqual(r["known_serial_stage_max_sum_seconds"], 5)
        self.assertEqual(set(r["missing_resources"]), {"unknown", "bytes"})
        with self.assertRaises(ValueError):
            m.bounds([dict(id="x", work={"x": 1})], {"x": 0})

    def test_real_conservation_precision_and_replay(self):
        for model in ["qwen3-8b", "deepseek-v4-flash"]:
            for batch, tokens, history in [(1, 1, 0), (2, 128, 0), (4, 1, 8192)]:
                r = m.calculate(
                    model=model, batch=batch, tokens=tokens, history=history
                )
                self.assertEqual(r, m.calculate(**r["scenario"]))
                self.assertEqual(
                    sum(
                        o.get("matrix_flops", 0)
                        for s in r["stages"]
                        for o in s["operations"]
                    ),
                    r["baseline_work"]["matrix_flops"],
                )
                self.assertIsNone(r["summary"]["full_request_latency_bound_seconds"])
                if model == "deepseek-v4-flash":
                    for s in r["stages"]:
                        for o in s["operations"]:
                            if o["name"].startswith("routed_") and o.get(
                                "matrix_flops"
                            ):
                                self.assertEqual(o["input_precision"], "FP8")
                    self.assertIn(
                        "interface_bytes", r["resource_bounds"]["missing_resources"]
                    )
                    self.assertEqual(
                        r["capacity"]["runtime_status"],
                        "runtime_unknown_checkpoint_comparison",
                    )

    def test_official_three_families_and_no_substitution(self):
        for device in ["h100-sxm", "m4-max-40gpu-128gb", "atlas-300i-a2-64gb"]:
            r = m.calculate(device=device, tokens=1)
            self.assertIsNone(
                r["resource_bounds"]["accounted_serial_stage_lower_bound_seconds"]
            )
            self.assertTrue(r["resource_bounds"]["missing_resources"])
        fake = copy.deepcopy(hardware.select_device("h100-sxm"))
        fake["peak_rates"] = [
            x
            for x in fake["peak_rates"]
            if x["input_precision"] in ("TF32", "INT8") or x["sparsity"] == "structured"
        ]
        with patch.object(m.hardware, "select_device", return_value=fake):
            r = m.calculate(tokens=1)
        self.assertIsNone(r["precision_admission"]["matrix_bf16"]["official_peak"])
        self.assertIsNone(r["precision_admission"]["vector_fp32"]["official_peak"])

    def test_explicit_supply_perturbation_and_capacity_failure(self):
        base = m.calculate(tokens=1)
        assumed = {
            k: 1e10
            for s in base["stages"]
            for k in s["work"]
            if k.startswith("special:")
        }
        r = m.calculate(tokens=1, assumed_rates=assumed)
        self.assertIsNotNone(
            r["resource_bounds"]["accounted_serial_stage_lower_bound_seconds"]
        )
        self.assertGreaterEqual(
            r["resource_bounds"]["accounted_serial_stage_lower_bound_seconds"],
            r["resource_bounds"]["accounted_global_max_seconds"],
        )
        fast = m.calculate(
            tokens=1, assumed_rates=assumed, rate_multipliers={"interface_bytes": 2}
        )
        self.assertLessEqual(
            fast["resource_bounds"]["accounted_serial_stage_lower_bound_seconds"],
            r["resource_bounds"]["accounted_serial_stage_lower_bound_seconds"],
        )
        self.assertEqual(fast["baseline_work"], r["baseline_work"])
        big = m.calculate(device="rtx4090", batch=32, tokens=1, history=32767)
        self.assertEqual(big["capacity"]["runtime_status"], "fails_necessary_capacity")
        self.assertIsNone(
            big["summary"]["necessary_capacity_not_failed_accounted_bound_seconds"]
        )

    def test_unknown_capacity_does_not_admit(self):
        device = copy.deepcopy(hardware.select_device("h100-sxm"))
        device["memory"]["nominal_capacity"] = None
        baseline = m.calculate(tokens=1)
        rates = {
            key: 1e10
            for stage in baseline["stages"]
            for key in stage["work"]
            if key.startswith("special:")
        }
        with patch.object(m.hardware, "select_device", return_value=device):
            result = m.calculate(tokens=1, assumed_rates=rates)
        self.assertEqual(
            result["capacity"]["runtime_status"], "necessary_capacity_unknown"
        )
        self.assertIsNone(
            result["summary"]["necessary_capacity_not_failed_accounted_bound_seconds"]
        )

    def test_v4_supplied_interface_never_closes_runtime(self):
        base = m.calculate(model="deepseek-v4-flash", tokens=1)
        rates = {
            k: 1e12
            for s in base["stages"]
            for k, v in s["work"].items()
            if k != "interface_bytes"
        }
        r = m.calculate(
            model="deepseek-v4-flash",
            tokens=1,
            assumed_rates=rates,
            stage_interface_bytes=[1000] * len(base["stages"]),
        )
        self.assertIsNotNone(
            r["resource_bounds"]["accounted_serial_stage_lower_bound_seconds"]
        )
        self.assertIsNone(r["summary"]["full_request_latency_bound_seconds"])
        self.assertIsNone(
            r["summary"]["necessary_capacity_not_failed_accounted_bound_seconds"]
        )
        self.assertIsNone(r["capacity"]["full_runtime_feasibility"])


if __name__ == "__main__":
    unittest.main()
