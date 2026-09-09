"""Decoder geometry, parameter and object-lifetime checks without tensor allocation."""

import json
import math
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from infra_calc.topics.flux_vae_decode import calculate, markdown
from infra_calc.topics.image_stages import vae_stage


class DecoderTests(unittest.TestCase):
    def test_default_matches_existing_matrix_ledger(self):
        r = calculate()
        old = vae_stage("flux2-klein-4b", 1024, 1024, 1, 2)
        self.assertEqual(r["latent_shape"], [1, 32, 128, 128])
        self.assertEqual(r["output_shape"], [1, 3, 1024, 1024])
        self.assertEqual(
            r["summary"]["dense_matrix_and_conv_flops"],
            old["dense_kernel_and_attention_flops"],
        )
        self.assertEqual(
            r["summary"]["nonpadding_matrix_and_conv_flops"],
            old["nonpadding_and_attention_flops"],
        )
        self.assertEqual(
            sum(o["kind"] in ("conv2d", "linear_1x1") for o in r["operators"]), 40
        )
        self.assertEqual(sum(o["kind"] == "groupnorm" for o in r["operators"]), 30)
        self.assertEqual(sum(o["kind"] == "nearest2d" for o in r["operators"]), 3)
        self.assertEqual(
            sum(o["kind"] == "residual_rescale" for o in r["operators"]), 15
        )

    def test_independent_parameter_formula(self):
        def conv(ci, co, k=3):
            return ci * co * k * k + co

        def residual(ci, co):
            return (
                2 * ci
                + 2 * co
                + conv(ci, co)
                + conv(co, co)
                + (conv(ci, co, 1) if ci != co else 0)
            )

        expected = conv(32, 32, 1) + conv(32, 512)
        expected += 2 * residual(512, 512) + 2 * 512 + 4 * (512 * 512 + 512)
        current = 512
        for i, co in enumerate([512, 512, 256, 128]):
            expected += residual(current, co) + 2 * residual(co, co)
            current = co
            if i < 3:
                expected += conv(co, co)
        expected += 2 * 128 + conv(128, 3)
        self.assertEqual(expected, 49620259)
        self.assertEqual(calculate()["summary"]["decoder_weight_parameters"], expected)

    def test_all_tensor_reads_have_prior_producer(self):
        r = calculate(height=64, width=128)
        for o in r["operators"]:
            for name in o["inputs"]:
                self.assertLess(r["tensors"][name]["producer"], o["id"])
                self.assertGreaterEqual(r["tensors"][name]["last_use"], o["id"])
        self.assertEqual(
            r["lifetime_events"][-1]["live_tensors"], ["latent", "decoder.output"]
        )
        self.assertEqual(r["summary"]["persistent_decode_cache_bytes"], 0)

    def test_independent_liveness_interval_peak(self):
        r = calculate(height=64, width=64, attention="eager")
        peaks = []
        for index in range(len(r["operators"])):
            active = [
                t["bytes"]
                for t in r["tensors"].values()
                if t["producer"] <= index <= t["last_use"]
            ]
            peaks.append(sum(active))
        self.assertEqual(
            max(peaks), r["summary"]["declared_tensor_boundary_peak_bytes"]
        )
        scratch = r["tensors"]["mid.attention.beta0_scratch"]
        qk = next(o["id"] for o in r["operators"] if o["name"] == "mid.attention.qk")
        self.assertEqual(scratch["last_use"], qk)
        softmax = next(
            o["id"] for o in r["operators"] if o["name"] == "mid.attention.softmax"
        )
        self.assertEqual(r["tensors"]["mid.attention.upcast"]["last_use"], softmax)

    def test_sdpa_has_no_inferred_score_tensor(self):
        r = calculate()
        self.assertFalse(any(len(t["shape"]) == 3 for t in r["tensors"].values()))
        eager = calculate(attention="eager")
        self.assertGreater(
            eager["summary"]["declared_tensor_boundary_peak_bytes"],
            r["summary"]["declared_tensor_boundary_peak_bytes"],
        )
        self.assertEqual(
            eager["summary"]["dense_matrix_and_conv_flops"],
            r["summary"]["dense_matrix_and_conv_flops"],
        )
        self.assertEqual(eager["summary"]["scalar_flops"], r["summary"]["scalar_flops"])

    def test_fp32_same_dtype_cast_alias(self):
        r = calculate(height=64, width=64, attention="eager", dtype="fp32")
        self.assertFalse(any(o["kind"] == "cast" for o in r["operators"]))
        self.assertEqual(r["summary"]["decoder_weight_bytes"], 4 * 49620259)

    def test_scale_batch_and_workspace(self):
        a = calculate(height=64, width=64)
        b = calculate(height=64, width=64, batch=2, workspace_bytes=123)
        self.assertEqual(
            b["summary"]["dense_matrix_and_conv_flops"],
            2 * a["summary"]["dense_matrix_and_conv_flops"],
        )
        self.assertEqual(
            b["summary"]["declared_tensor_boundary_peak_bytes"],
            2 * a["summary"]["declared_tensor_boundary_peak_bytes"],
        )
        self.assertEqual(
            b["summary"]["conditional_weights_boundary_workspace_bytes"],
            b["summary"]["declared_tensor_boundary_peak_bytes"]
            + b["summary"]["decoder_weight_bytes"]
            + 123,
        )
        self.assertIsNone(a["summary"]["conditional_weights_boundary_workspace_bytes"])

    def test_tiny_conv_padding_hand_count(self):
        r = calculate(height=8, width=8)
        conv = next(o for o in r["operators"] if o["name"] == "decoder.input")
        self.assertEqual(conv["matrix_flops"], 2 * 32 * 512 * 9)
        self.assertEqual(conv["nonpadding_matrix_flops"], 2 * 32 * 512)
        nearest = next(o for o in r["operators"] if o["kind"] == "nearest2d")
        self.assertEqual(nearest["output_bytes"], 4 * nearest["input_bytes"])

    def test_groupnorm_biased_variance_numeric(self):
        # Two contiguous groups, population (not sample) variance.
        x = [1.0, 3.0, 2.0, 6.0]
        out = []
        for group in [x[:2], x[2:]]:
            mean = sum(group) / 2
            var = sum((z - mean) ** 2 for z in group) / 2
            out.extend(2 * (z - mean) / math.sqrt(var + 1e-6) + 1 for z in group)
        self.assertAlmostEqual(out[0], -0.99999900000075)
        self.assertAlmostEqual(out[3], 2.999999750000047)
        r = calculate(height=8, width=8)
        norm = next(o for o in r["operators"] if o["kind"] == "groupnorm")
        elements = math.prod(r["tensors"][norm["output"]]["shape"])
        self.assertEqual(norm["scalar_flops"], 7 * elements + 32)

    def test_large_shape_layout_interface(self):
        for kwargs in [dict(batch=64), dict(height=8192, width=8192)]:
            result = calculate(**kwargs, workspace_bytes=123)
            summary = result["summary"]
            self.assertTrue(summary["layout_copy_bytes_unknown"])
            self.assertIsNone(summary["conditional_weights_boundary_workspace_bytes"])
            for row in summary["upsample_contiguous_interfaces"]:
                if row["triggered"]:
                    self.assertIsNone(row["materialized_copy_bytes"])
                    self.assertGreater(row["input_bytes"], 0)

    def test_markdown_operator_and_lifetime_coverage(self):
        result = calculate(height=64, width=64)
        report = markdown(result)
        self.assertIn("49,620,259", report)
        self.assertIn("不是 HBM 实测", report)
        for operator in result["operators"]:
            self.assertIn(operator["name"], report)

    def test_replay_and_reject_invalid(self):
        r = calculate(height=64, width=128)
        self.assertEqual(r, calculate(**r["scenario"]))
        for kwargs in [
            dict(height=7),
            dict(batch=True),
            dict(dtype="fp16"),
            dict(attention="flash"),
            dict(workspace_bytes=-1),
        ]:
            with self.assertRaises(ValueError):
                calculate(**kwargs)


if __name__ == "__main__":
    unittest.main()
