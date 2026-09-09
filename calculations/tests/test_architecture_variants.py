"""Independent closed-form and exact capacity-boundary checks."""
import importlib.util
import sys
import unittest
from fractions import Fraction
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from infra_calc.topics import architecture_variants as m


class ArchitectureVariantsTest(unittest.TestCase):
    def test_parameter_independent_expansion(self):
        for row in m.calculate()["variants"]:
            c = row["config"]
            h, f, layers = c["hidden_size"], c["intermediate_size"], c["num_hidden_layers"]
            k, d, vocab = c["num_key_value_heads"], c["head_dim"], c["vocab_size"]
            expected = 2 * vocab * h + h + layers * (2 * h * h + 2 * h * k * d + 3 * h * f + 2 * h + 2 * d)
            self.assertEqual(row["actual_parameters"], expected)
            self.assertEqual(row["actual_parameters"], row["target_parameters"] + row["parameter_delta"])
            self.assertLessEqual(abs(row["parameter_delta"]), Fraction(row["max_rounding_error_parameters_exact"]))

    def test_exact_equal_parameter_different_cache(self):
        rows = m.calculate()["variants"]
        baseline, changed = rows[0], rows[-1]
        self.assertEqual(baseline["actual_parameters"], 8190735360)
        self.assertEqual(changed["actual_parameters"], baseline["actual_parameters"])
        self.assertEqual(changed["config"]["intermediate_size"], 12800)
        self.assertEqual(4 * changed["work"]["kv_bytes_per_token_per_request"], baseline["work"]["kv_bytes_per_token_per_request"])
        self.assertEqual(changed["work"]["matrix_flops"], baseline["work"]["matrix_flops"])

    def test_matrices_prefill_prefix_and_decode(self):
        for batch, tokens, history in ((1, 8192, 0), (3, 7, 11), (64, 1, 8192)):
            for row in m.calculate(batch=batch, tokens=tokens, history=history)["variants"]:
                c = row["config"]
                h, f, layers = c["hidden_size"], c["intermediate_size"], c["num_hidden_layers"]
                k, d, v = c["num_key_value_heads"], c["head_dim"], c["vocab_size"]
                pairs = batch * (tokens * history + tokens * (tokens + 1) // 2)
                projection = 2 * layers * batch * tokens * (2 * h * h + 2 * h * k * d + 3 * h * f)
                attention = 4 * layers * pairs * h
                head = 2 * batch * h * v
                self.assertEqual(row["work"]["matrix_flops"], projection + attention + head)

    def test_tp_weight_and_state_conservation(self):
        for row in m.calculate(tp=2, batch=3)["variants"]:
            c, w = row["config"], row["work"]
            norms = c["num_hidden_layers"] * (2 * c["hidden_size"] + 2 * c["head_dim"]) + c["hidden_size"]
            self.assertEqual(2 * w["per_rank_weight_bytes"], 2 * row["actual_parameters"] + 2 * norms)
            self.assertEqual(2 * w["per_rank_kv_bytes"], 3 * 8193 * w["kv_bytes_per_token_per_request"])
            self.assertEqual(w["per_rank_kv_bytes"], w["per_rank_old_history_read_bytes"] + w["per_rank_kv_append_bytes"])

    def test_actual_capacity_flip(self):
        d = m.calculate()
        baseline = d["variants"][0]["work"]["per_rank_live_budget_bytes"]
        changed = d["variants"][-1]["work"]["per_rank_live_budget_bytes"]
        self.assertLess(changed, baseline)
        at_changed = m.calculate(capacity_bytes=changed)["variants"]
        before_changed = m.calculate(capacity_bytes=changed - 1)["variants"]
        at_baseline = m.calculate(capacity_bytes=baseline)["variants"]
        self.assertTrue(at_changed[-1]["work"]["batch_fits"])
        self.assertFalse(before_changed[-1]["work"]["batch_fits"])
        self.assertFalse(at_changed[0]["work"]["batch_fits"])
        self.assertTrue(at_baseline[0]["work"]["batch_fits"])

    def test_ring_bytes_and_single_device(self):
        for row in m.calculate(tp=2, batch=3, tokens=7)["variants"]:
            c, w = row["config"], row["work"]
            self.assertEqual(Fraction(w["per_rank_ring_wire_bytes_exact"]), 2 * c["num_hidden_layers"] * 3 * 7 * c["hidden_size"] * 2)
        for row in m.calculate(tp=1)["variants"]:
            self.assertEqual(row["work"]["sequential_collectives"], 0)
            self.assertEqual(Fraction(row["work"]["per_rank_ring_wire_bytes_exact"]), 0)

    def test_explicit_shape_rejections(self):
        with self.assertRaises(ValueError):
            m.calculate(tp=8)  # Not all variants have eight independent KV heads.
        with self.assertRaises(ValueError):
            m.calculate(tp=True)
        with self.assertRaises(ValueError):
            m.calculate(ffn_alignment=0)
        with self.assertRaises(ValueError):
            m.calculate(tokens=40961, history=0)


if __name__ == "__main__":
    unittest.main()
