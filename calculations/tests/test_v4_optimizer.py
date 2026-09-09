import math
import sys
import unittest
from pathlib import Path

for ancestor in Path(__file__).resolve().parents:
    if (ancestor / "src/infra_calc/sources.py").is_file():
        sys.path.insert(0, str(ancestor / "src"))
        break
from infra_calc import topics

topics.__path__.insert(
    0, str(Path(__file__).resolve().parents[1] / "src/infra_calc/topics")
)
from infra_calc.topics import v4_optimizer as m


class OptimizerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.default = m.calculate()
        cls.resolved = m.calculate(
            include_mtp=True, sink_policy="row_muon", head_mixer_policy="adamw"
        )

    def test_inventory_and_group_conservation(self):
        for result in (self.default, self.resolved):
            target = result["inventory"]["base_logical_parameters"]
            if result["scenario"]["include_mtp"]:
                target += result["inventory"]["mtp_logical_parameters"]
            self.assertEqual(sum(g["parameters"] for g in result["groups"]), target)
            for g in result["groups"]:
                self.assertEqual(
                    math.prod(g["logical_tensor_shape"]) * g["tensor_count"],
                    g["parameters"],
                )
                if g["optimizer"] == "muon":
                    self.assertEqual(
                        math.prod(g["independent_matrix_shape"]) * g["matrix_count"],
                        g["parameters"],
                    )
            self.assertEqual(result, m.calculate(**result["scenario"]))
        self.assertGreater(self.default["summary"]["unresolved_parameters"], 0)
        self.assertTrue(
            self.resolved["scope"]["conditional_selected_parameter_updates_covered"]
        )
        self.assertFalse(self.resolved["scope"]["full_optimizer_exact"])
        self.assertGreater(
            self.resolved["summary"]["external_router_bias_parameters"], 0
        )

    def test_official_exceptions_and_packing(self):
        groups = self.resolved["groups"]
        for g in groups:
            name = g["name_pattern"]
            if name.endswith(
                ("_base", "_scale", "norm.weight", "head.weight", "embed.weight")
            ):
                self.assertEqual(g["optimizer"], "adamw", name)
            if ".ffn.experts." in name:
                self.assertEqual(g["optimizer"], "muon")
                self.assertEqual(sorted(g["logical_tensor_shape"]), [2048, 4096])
        base_experts = [
            g
            for g in groups
            if g["owner"] == "base" and ".ffn.experts." in g["name_pattern"]
        ]
        self.assertEqual(sum(g["tensor_count"] for g in base_experts), 43 * 256 * 3)
        self.assertEqual(
            sum(g["parameters"] for g in base_experts), 43 * 256 * 3 * 2048 * 4096
        )

    def test_hand_counts_and_orientation(self):
        for rows, cols in ((2, 3), (3, 2), (1, 7), (4, 4)):
            result = m.matrix_work(rows, cols)
            n, k = min(rows, cols), max(rows, cols)
            self.assertEqual(
                result["matrix_flops"], 10 * (4 * n * n * k + 2 * n * n * n)
            )
            self.assertEqual(
                result["ordinary_scalar_operations"],
                11 * n * k + 10 * (3 * n * n + 2 * n * k),
            )
            self.assertEqual(
                sum(result["scalar_detail"].values()),
                result["ordinary_scalar_operations"],
            )
        self.assertGreater(
            m.matrix_work(8, 2, "stored_left_gram")["matrix_flops"],
            m.matrix_work(8, 2)["matrix_flops"],
        )

    def test_reference_against_direct_polynomial(self):
        try:
            import torch
        except ImportError:
            self.skipTest("optional PyTorch numerical oracle unavailable")

        torch.manual_seed(918)
        for rows, cols in ((2, 3), (3, 2), (1, 5)):
            w, g, momentum = [
                torch.randn(rows, cols, dtype=torch.float64) for _ in range(3)
            ]
            updated_momentum = 0.95 * momentum + g
            x = 0.95 * updated_momentum + g
            x = x / torch.linalg.vector_norm(x)
            for a, b, c in m.COEFFICIENTS:
                gram = x @ x.T
                x = a * x + b * (gram @ x) + c * ((gram @ gram) @ x)
            expected = (
                w * (1 - 2.7e-4 * 0.1) - 2.7e-4 * x * math.sqrt(max(rows, cols)) * 0.18
            )
            for orientation in ("smaller_gram", "stored_left_gram"):
                actual, new_momentum = m.muon_reference(
                    w, g, momentum, orientation=orientation
                )
                torch.testing.assert_close(actual, expected, atol=2e-13, rtol=2e-13)
                torch.testing.assert_close(
                    new_momentum, updated_momentum, atol=0, rtol=0
                )
        z = torch.zeros(2, 3, dtype=torch.float64)
        with self.assertRaises(ValueError):
            m.muon_reference(z, z, z)
        actual, _ = m.muon_reference(z, z, z, norm_epsilon=1e-7)
        self.assertEqual(actual.count_nonzero(), 0)

    def test_report_and_invalid_inputs(self):
        report = m.markdown(self.default)
        for key in (
            "tensor_interfaces_per_iteration_bytes",
            "actual_hbm_bytes",
            "unresolved",
            "ns_coefficients",
        ):
            self.assertIn(key, report)
        for scenario in (
            {"adam_step": True},
            {"norm_epsilon": float("nan")},
            {"learning_rate": -1},
            {"sink_policy": "adamw"},
            {"wo_a_partition": "head"},
        ):
            with self.assertRaises(ValueError):
                m.calculate(**scenario)


if __name__ == "__main__":
    unittest.main()
