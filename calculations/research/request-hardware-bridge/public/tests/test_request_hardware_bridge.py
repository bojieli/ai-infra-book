import copy
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

for ancestor in Path(__file__).resolve().parents:
    if (ancestor / "src/infra_calc/sources.py").is_file():
        sys.path.insert(0, str(ancestor / "src"))
        break
from infra_calc import topics

topics.__path__.insert(
    0, str(Path(__file__).resolve().parents[1] / "src/infra_calc/topics")
)
from infra_calc.topics import request_hardware_bridge as m


class BridgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.default = m.calculate()

    def test_precision_and_conservation(self):
        for result, original in zip(
            self.default["models"], self.default["original_request"]["comparisons"]
        ):
            self.assertEqual(
                sum(result["matrix_buckets"].values()),
                original["summary"]["matrix_flops"],
            )
            self.assertEqual(len(result["calls"]), 4)
            self.assertIsNone(
                result["resource_bounds"]["accounted_serial_stage_lower_bound_seconds"]
            )
            self.assertIsNone(result["complete_runtime_seconds"])
            self.assertIn(
                "physical_hbm_bytes", result["resource_bounds"]["missing_resources"]
            )
        qwen = self.default["models"][0]
        expected = 2 * 36 * 32 * 128 * (128 * 129 // 2 + 129 + 130 + 131)
        self.assertEqual(
            qwen["matrix_buckets"]["matrix_pv_mixed_or_unresolved"], expected
        )
        self.assertIsNone(self.default["rates"]["matrix_pv_mixed_or_unresolved"])
        self.assertGreater(
            self.default["models"][3]["matrix_buckets"]["unclassified_matrix"], 0
        )
        self.assertEqual(
            self.default["models"][3]["capacity"]["status"], "checkpoint_shape_conflict"
        )
        self.assertNotIn("matrix_fp4", self.default["rates"])

    def test_explicit_provider_shared_resource_and_low_capacity(self):
        with patch.object(
            m.request_model_comparison,
            "calculate",
            return_value=copy.deepcopy(self.default["original_request"]),
        ):
            r = m.calculate(
                scalar_vector_provider=True,
                fp32_matrix_vector_provider=True,
                capacity_bytes=1_000_000,
            )
        for model in r["models"]:
            for call in model["calls"]:
                self.assertEqual(
                    call["work"]["vector_fp32"],
                    call["matrix_buckets"].get("matrix_fp32", 0)
                    + call["ordinary_scalar_flops"],
                )
                self.assertTrue(
                    any(
                        x["resource"].startswith("special:")
                        for stage in model["resource_bounds"]["stages"]
                        for x in stage["missing"]
                    )
                )
            self.assertIsNone(model["complete_runtime_seconds"])
        self.assertEqual(r["models"][0]["capacity"]["status"], "necessary_failure")
        self.assertEqual(
            r["models"][1]["capacity"]["status"],
            "source_cache_allocation_necessary_failure",
        )
        self.assertAlmostEqual(r["rates"]["vector_fp32"] / 1e12, 66.9)

    def test_g1_and_no_interface_alias_hbm(self):
        result = m.calculate(output_tokens=1)
        for model in result["models"]:
            self.assertEqual(len(model["calls"]), 1)
            self.assertEqual(model["links"]["prefix_restore_payload_bytes"], 0)
            self.assertIsNone(model["links"]["complete_link_bytes"])
            call = model["calls"][0]
            self.assertIsNone(call["work"]["physical_hbm_bytes"])
            self.assertTrue(
                all(
                    "unspecified" in row["physical_resource"]
                    for row in call["interface_normalized_seconds"].values()
                )
            )
        self.assertEqual(result["original_request"]["scenario"]["output_tokens"], 1)

    def test_replay_and_invalid(self):
        with patch.object(
            m.request_model_comparison,
            "calculate",
            return_value=copy.deepcopy(self.default["original_request"]),
        ):
            self.assertEqual(self.default, m.calculate(**self.default["scenario"]))
        for args in (
            {"output_tokens": 2},
            {"output_tokens": True},
            {"scalar_vector_provider": 1},
            {"capacity_bytes": 0},
        ):
            with self.assertRaises(ValueError):
                m.calculate(**args)
        self.assertIn("matrix_pv_mixed_or_unresolved", m.markdown(self.default))


if __name__ == "__main__":
    unittest.main()
