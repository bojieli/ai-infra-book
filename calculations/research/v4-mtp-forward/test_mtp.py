import unittest
from calculate import calculate, checkpoint
from infra_calc.sources import model_config


class MTPTests(unittest.TestCase):
    def test_closed_matrix(self):
        c = model_config("deepseek-v4-flash", reference=True)
        h, q, d, heads, g, o, f, E, K, V = [
            c[k]
            for k in (
                "dim",
                "q_lora_rank",
                "head_dim",
                "n_heads",
                "o_groups",
                "o_lora_rank",
                "moe_inter_dim",
                "n_routed_experts",
                "n_activated_experts",
                "vocab_size",
            )
        ]
        for b, t, s in [(1, 1, 0), (2, 16, 0), (1, 129, 0), (1, 1, 128)]:
            r = calculate(b, t, s)
            m = b * t
            pairs = sum(min(p + 1, 128) for p in range(s, s + t))
            attention = (
                2 * m * (h * q + q * heads * d + h * d + heads * d * o + g * o * h)
                + 4 * b * heads * d * pairs
            )
            experts = 2 * m * h * E + 6 * m * (K + 1) * h * f
            hc = 2 * (2 * m * 4 * h * 24) + 2 * m * 4 * h * 4
            total = attention + experts + hc + 10 * m * h * h + 2 * b * h * V
            self.assertEqual(total, r["summary"]["matrix_flops"])
            self.assertEqual(r, calculate(**r["scenario"]))
            self.assertEqual(r["components"]["experts"]["geometry"]["hash_layers"], [])
            self.assertEqual(r["components"]["experts"]["geometry"]["moe_layers"], [43])
            self.assertEqual(r["source_ratio"], 0)

    def test_checkpoint_conservation_and_state(self):
        for t in (1, 128, 129):
            r = calculate(tokens=t)
            self.assertEqual(r["summary"]["own_logical_parameters"], 6610048891)
            self.assertEqual(r["checkpoint"]["verified_keys"], 1575)
            self.assertEqual(r["checkpoint"]["own_checkpoint_bytes"], 3593787756)
            self.assertEqual(
                r["state"]["valid_window_after_bytes"], min(t, 128) * 512 * 2
            )
            self.assertEqual(r["state"]["cache_write_bytes"], min(t, 128) * 512 * 2)
            self.assertEqual(
                r["state"]["registered_cache_bf16_bytes"], 4 * 128 * 512 * 2
            )
            self.assertEqual(r["state"]["compressor_bytes"], 0)

    def test_last_head_and_helper_isolation(self):
        before = model_config("deepseek-v4-flash", reference=True)
        a = calculate(tokens=1)
        b = calculate(tokens=16)
        self.assertEqual(
            a["summary"]["shared_last_head_flops"],
            b["summary"]["shared_last_head_flops"],
        )
        self.assertEqual(before, model_config("deepseek-v4-flash", reference=True))
        self.assertEqual(len(b["fp8_linear_calls"]), 9)
        self.assertNotIn(
            "embedding_repeat_output_bytes",
            b["components"]["hyper_connections"]["summary"],
        )

    def test_routed_quantization_specials(self):
        c = model_config("deepseek-v4-flash", reference=True)
        for batch, tokens in ((1, 1), (2, 129)):
            r = calculate(batch=batch, tokens=tokens)
            cells = batch * tokens * c["n_activated_experts"] * (
                2 * c["dim"] + c["moe_inter_dim"]
            )
            x = r["routed_activation_quantization_special_ops"]
            self.assertEqual(x["activation_abs_ops"], cells)
            self.assertEqual(x["activation_max_comparisons"], cells)
            self.assertEqual(x["activation_clamp_comparisons"], 2 * cells)
            self.assertEqual(x["activation_round_scale_calls"], cells // 128)
            for key, value in x.items():
                self.assertEqual(
                    r["summary"]["special_ops"][key],
                    value + sum(row[key] for row in r["fp8_linear_calls"]),
                )

    def test_invalid(self):
        for kwargs in [
            dict(batch=True),
            dict(tokens=0),
            dict(start_pos=-1),
            dict(tokens=2, start_pos=1),
            dict(batch=5),
            dict(start_pos=4096),
        ]:
            with self.assertRaises(ValueError):
                calculate(**kwargs)


if __name__ == "__main__":
    unittest.main()
