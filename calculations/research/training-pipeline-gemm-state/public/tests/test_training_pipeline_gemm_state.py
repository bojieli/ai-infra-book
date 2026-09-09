from pathlib import Path
import sys
import unittest

for ancestor in Path(__file__).resolve().parents:
    if (ancestor / "src/infra_calc/sources.py").is_file():
        sys.path.insert(0, str(ancestor / "src"))
        break
import infra_calc.topics

infra_calc.topics.__path__.insert(
    0, str(Path(__file__).resolve().parents[1] / "src/infra_calc/topics")
)
from infra_calc.topics import training_pipeline_gemm_state as m
from infra_calc.topics import training_matrix, training_nonmatrix


class GemmStateTests(unittest.TestCase):
    def test_each_matrix_instance_and_operand_identity(self):
        result = m.calculate(tokens=3, microbatch_size=2, microbatches=2)
        original = training_matrix.calculate(tokens=3, batch=2)
        expected = {
            (row["name"], layer)
            for row in original["training_matrix_rows"]
            for layer in (range(row["repeats"]) if row["repeats"] > 1 else [None])
        }
        actual = {
            (row["matrix"], row["layer"]) for row in result["matrix_vjp_requirements"]
        }
        self.assertEqual(actual, expected)
        objects = {o["id"]: o for o in result["tensor_objects"]}
        nonlinear = {o["id"]: o for o in result["reused_nonlinear_saved_objects"]}
        self.assertEqual(len(objects), 36 * 7 + 1)
        for requirement in result["matrix_vjp_requirements"]:
            for identity in requirement["saved_operand_ids"]:
                self.assertIn(identity, objects.keys() | nonlinear.keys())
        for layer in range(36):
            rows = {
                r["matrix"]: r
                for r in result["matrix_vjp_requirements"]
                if r["layer"] == layer
            }
            self.assertEqual(
                rows["q_proj"]["saved_operand_ids"], rows["k_proj"]["saved_operand_ids"]
            )
            self.assertEqual(
                rows["k_proj"]["saved_operand_ids"], rows["v_proj"]["saved_operand_ids"]
            )
            self.assertEqual(
                rows["gate_proj"]["saved_operand_ids"],
                rows["up_proj"]["saved_operand_ids"],
            )
            self.assertIn(rows["pv"]["saved_operand_ids"][0], nonlinear)
            self.assertEqual(
                objects[rows["qk"]["saved_operand_ids"][1]]["shape"], [2, 8, 3, 128]
            )
            self.assertEqual(
                objects[rows["pv"]["saved_operand_ids"][1]]["shape"], [2, 8, 3, 128]
            )
            self.assertEqual(
                objects[rows["o_proj"]["saved_operand_ids"][0]]["shape"], [6, 4096]
            )

    def test_recompute_products_cost_and_no_silu_double_count(self):
        for activation in ("save_nonlinear", "recompute_silu"):
            saved = m.calculate(tokens=3, microbatches=2, activation_policy=activation)
            recomputed = m.calculate(
                tokens=3,
                microbatches=2,
                activation_policy=activation,
                gemm_policy="recompute_products",
            )
            self.assertEqual(
                saved["work"]["original_pipeline_work"],
                recomputed["work"]["original_pipeline_work"],
            )
            expected = 36 * 3 * (2 * 4096 + 12288) + 3 * 4096
            self.assertEqual(
                recomputed["work"]["extra_per_microbatch_scalar_flops"], expected
            )
            self.assertEqual(recomputed["work"]["extra_special_calls"], 0)
            self.assertEqual(saved["work"]["extra_per_microbatch_scalar_flops"], 0)
            self.assertEqual(
                recomputed["reservation"][
                    "additional_product_workspace_bytes_per_stage"
                ],
                [4 * 3 * 12288] * 4,
            )
            source = training_nonmatrix.calculate(
                tokens=3, activation_policy=activation
            )
            self.assertEqual(
                recomputed["reused_nonlinear_saved_objects"], source["saved_objects"]
            )
            a = sum(saved["reservation"]["added_persistent_bytes_per_microbatch_stage"])
            b = sum(
                recomputed["reservation"]["added_persistent_bytes_per_microbatch_stage"]
            )
            self.assertEqual(a - b, 4 * expected)

    def test_product_reconstruction_is_not_false_alias(self):
        z = [0.5, -0.2, 0.8]
        gamma = [1.2, 0.7, -0.4]
        y = [a * b for a, b in zip(z, gamma)]
        self.assertNotEqual(y, z)
        a = [0.3, -0.7, 0.9]
        u = [1.1, 0.4, -0.2]
        product = [v * w for v, w in zip(a, u)]
        self.assertNotEqual(product, a)
        # dW uses the weighted/product input, not its nonlinear operands alone.
        gout = [0.2, -0.6]
        dw = [[g * x for x in y] for g in gout]
        restored = [[g * (gamma[j] * z[j]) for j in range(3)] for g in gout]
        self.assertEqual(dw, restored)

    def test_interval_peak_and_stage_assignments(self):
        for policy in ("gpipe", "1f1b"):
            result = m.calculate(
                tokens=2,
                microbatches=3,
                policy=policy,
                activation_policy="recompute_silu",
                gemm_policy="recompute_products",
            )
            for stage in range(4):
                intervals = [
                    i
                    for i in result["reservation"]["combined_intervals"]
                    if i["stage"] == stage
                ]
                times = sorted({i[k] for i in intervals for k in ("start", "end")})
                peak = max(
                    sum(
                        i["bytes"]
                        for i in intervals
                        if i["start"] <= (a + b) / 2 < i["end"]
                    )
                    for a, b in zip(times, times[1:])
                )
                self.assertEqual(
                    peak, result["reservation"]["combined_peak_declared_bytes"][stage]
                )
            self.assertEqual(
                result["schedule"]["summary"]["reserved_activation_scope_peak_bytes"],
                result["reservation"]["combined_peak_declared_bytes"],
            )
            self.assertIsNone(
                result["coverage"]["complete_training_activation_peak_bytes"]
            )
            self.assertEqual(result, m.calculate(**result["scenario"]))
            for obj in result["tensor_objects"]:
                self.assertEqual(
                    obj["stage"], 3 if obj["layer"] is None else obj["layer"] // 9
                )


if __name__ == "__main__":
    unittest.main()
