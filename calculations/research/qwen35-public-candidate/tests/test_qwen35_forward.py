import unittest
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from infra_calc.topics.qwen35_forward import calculate, expected_shapes, EVIDENCE


class ShapeTests(unittest.TestCase):
    def test_independent_base_parameter_closed_form(self):
        # No use of adapter weights/shapes to construct this count.
        h = 4096
        v = 248320
        f = 1024
        e = 512
        d = 256
        global_weights = 2 * v * h + h
        common = 60 * (2 * h + e * h + 3 * e * h * f + 3 * h * f + h)
        full = 15 * (h * (2 * 32 * d + 2 * 2 * d) + h * 32 * d + 2 * d)
        lin = 45 * (h * (12288 + 8192 + 64 + 64) + 8192 * h + 12288 * 4 + 64 + 64 + 128)
        self.assertEqual(global_weights + common + full + lin, 396346350336)
        r = calculate(tokens=1, history=3)
        self.assertEqual(
            r["summary"]["base_text_parameters"], global_weights + common + full + lin
        )
        self.assertEqual(len(r["weights"]), 1038)
        self.assertEqual(r["summary"]["base_checkpoint_bytes"], 792692717952)

    def test_all_shapes_against_raw_headers(self):
        c = json.loads((EVIDENCE / "model/config.json").read_text())["text_config"]
        expected = expected_shapes(c)
        actual = {}
        for f in (EVIDENCE / "headers").glob("*.json"):
            for n, t in json.loads(f.read_text()).items():
                if n in expected:
                    actual[n] = t["shape"]
        self.assertEqual(expected, actual)

    def test_replay_and_no_input_mutation(self):
        histogram = [1] * 10 + [0] * 502
        before = histogram[:]
        r = calculate(tokens=1, history=8, routing_counts=histogram)
        self.assertEqual(histogram, before)
        self.assertEqual(r, calculate(**r["scenario"]))

    def test_layer_and_state_conservation(self):
        r = calculate(batch=3, tokens=17, history=19)
        self.assertEqual(
            sum(x["kind"] == "linear_attention" for x in r["execution"]["layer_dag"]),
            45,
        )
        st = r["state"]
        self.assertEqual(
            st["full_kv_after_bytes"] - st["full_kv_before_bytes"],
            st["full_kv_append_bytes"],
        )
        self.assertEqual(st["linear_recurrent_fp32_bytes"], 3 * 45 * 64 * 128 * 128 * 4)

    def test_chunk_boundary_and_path(self):
        for T, chunks in [(1, 1), (64, 1), (65, 2), (8192, 128)]:
            r = calculate(tokens=T)
            path = r["execution"]["linear_path"]
            self.assertEqual(path["kind"], "reference_chunk_nonexport")
            self.assertEqual(path["chunk_iterations"], chunks)
            self.assertEqual(path["padded_tokens"], chunks * 64)
        self.assertEqual(
            calculate(tokens=1, history=1)["execution"]["linear_path"]["kind"],
            "reference_recurrent",
        )
        self.assertEqual(
            calculate(tokens=2, history=1)["execution"]["linear_path"]["kind"],
            "reference_chunk_nonexport",
        )

    def test_chunk_matrices_independent_formula(self):
        r = calculate(batch=2, tokens=65)
        actual = sum(
            o["matrix_flops"] * o["repeats"]
            for o in r["operators"]
            if o["name"].startswith("linear.chunk.")
        )
        C = 64
        k = v = 128
        groups = 45 * 2 * 64 * 2
        per = 4 * C * C * k + 4 * C * k * v + 2 * C * C * v + 2 * k * C * v
        self.assertEqual(actual, groups * per)
        for op in r["operators"]:
            if op["name"].startswith("linear.chunk."):
                self.assertEqual(op["weight_read_bytes"], 0)

    def test_routed_matrix_assignment_conservation(self):
        r = calculate(batch=2, tokens=3)
        self.assertEqual(sum(r["execution"]["expert_histogram"]), 60)
        routed = sum(
            o["matrix_flops"] * o["repeats"]
            for o in r["operators"]
            if o["name"].startswith("moe.expert")
        )
        self.assertEqual(routed, 60 * 60 * 6 * 4096 * 1024)

    def test_output_head_scope(self):
        allr = calculate(batch=2, tokens=3)
        last = calculate(batch=2, tokens=3, output_head="last")
        none = calculate(batch=2, tokens=3, output_head="none")
        self.assertEqual(
            allr["summary"]["matrix_flops"] - last["summary"]["matrix_flops"],
            2 * 4 * 4096 * 248320,
        )
        self.assertEqual(
            last["summary"]["matrix_flops"] - none["summary"]["matrix_flops"],
            2 * 2 * 4096 * 248320,
        )

    def test_valid_vs_rectangular_attention(self):
        r = calculate(batch=2, tokens=3, history=5)
        self.assertEqual(
            r["auxiliary_metrics"]["full_attention_valid_matrix_flops"],
            15 * 4 * 32 * 256 * 2 * (15 + 6),
        )
        self.assertGreater(
            r["auxiliary_metrics"]["full_attention_rectangular_matrix_flops"],
            r["auxiliary_metrics"]["full_attention_valid_matrix_flops"],
        )

    def test_conv_and_delta_paths_have_distinct_record_past_condition(self):
        normal = calculate(tokens=1, history=8)
        recorded = calculate(tokens=1, history=8, record_past=True)
        self.assertEqual(
            normal["execution"]["linear_path"], recorded["execution"]["linear_path"]
        )
        self.assertEqual(normal["execution"]["conv_path"], "causal_conv1d_update")
        self.assertEqual(
            recorded["execution"]["conv_path"],
            "update_conv_state_then_causal_conv1d_fn",
        )
        self.assertIsNone(recorded["state"]["record_past_extra_allocation_bytes"])

    def test_reject_bad_inputs(self):
        for kwargs in [
            dict(tokens=0),
            dict(history=-1),
            dict(batch=True),
            dict(tokens=262145),
            dict(chunk_size=32),
            dict(tokens=1, routing_counts=[10] + [0] * 511),
        ]:
            with self.assertRaises(ValueError):
                calculate(**kwargs)

    def test_totals_and_explicit_gaps(self):
        r = calculate(tokens=65)
        for key in [
            "matrix_flops",
            "scalar_flops",
            "weight_read_bytes",
            "activation_read_bytes",
            "activation_write_bytes",
        ]:
            self.assertEqual(
                r["summary"][key], sum(o[key] * o["repeats"] for o in r["operators"])
            )
        self.assertFalse(r["summary"]["full_forward_exact"])
        self.assertTrue(r["gaps"])
        self.assertFalse(
            any(
                w["name"].startswith("mtp.") or "visual" in w["name"]
                for w in r["weights"]
            )
        )


class PublicReportTests(unittest.TestCase):
    def test_reference_report_keeps_scopes(self):
        from infra_calc.topics.qwen35_forward import markdown

        text = markdown(calculate(tokens=1, history=8))
        self.assertIn("full_forward_exact | False", text)
        self.assertIn("禁止将两者相加", text)
        self.assertIn("conv.additional_padded_and_discarded_products", text)
        self.assertIn("固定原件", text)


if __name__ == "__main__":
    unittest.main()
