import unittest
import sys
from pathlib import Path

for ancestor in Path(__file__).resolve().parents:
    if (ancestor / "src/infra_calc/models").is_dir():
        sys.path.insert(0, str(ancestor / "src"))
        break
from infra_calc.topics.dense_placement import calculate

MODEL = "deepseek-r1-distill-llama-70b"
H, L, Q, K, D, F, V = 8192, 80, 64, 8, 128, 28672, 128256
PARAMS = 70553706496
NORM = (2 * L + 1) * H
KV_PROJ = 2 * L * H * K * D


class Placement(unittest.TestCase):
    def test_physical_weight_conservation(self):
        for tp, pp, dp in [
            (8, 1, 1),
            (4, 2, 1),
            (2, 4, 1),
            (1, 8, 1),
            (4, 1, 2),
            (16, 1, 1),
        ]:
            r = calculate(MODEL, tp=tp, pp=pp, dp=dp)
            replication = max(1, tp // K)
            expected = 2 * dp * (PARAMS + (tp - 1) * NORM + (replication - 1) * KV_PROJ)
            self.assertEqual(r["summary"]["physical_weight_bytes"], expected)
            self.assertEqual(
                r["summary"]["physical_kv_bytes"],
                dp * replication * 2 * L * K * D * 8193 * 2,
            )
            self.assertEqual(r["summary"]["cards"], tp * pp * dp)

    def test_exact_rank_storage_oracle(self):
        for tp, pp in [(8, 1), (4, 2), (2, 4), (1, 8), (16, 1), (8, 3)]:
            r = calculate(MODEL, tp=tp, pp=pp, batch_per_replica=3)
            for card in r["placement_cards"]:
                n = len(card["layer_ids"])
                rank = card["tp_rank"]
                stage = card["stage"]
                qids = list(range(rank * (Q // tp), (rank + 1) * (Q // tp)))
                kids = sorted(set(q // 8 for q in qids))
                local = n * (
                    2 * H * len(qids) * D
                    + 2 * H * len(kids) * D
                    + 3 * H * (F // tp)
                    + 2 * H
                )
                if stage == 0:
                    local += V // tp * H
                if stage == pp - 1:
                    local += V // tp * H + H
                self.assertEqual(card["query_head_ids"], qids)
                self.assertEqual(card["kv_head_ids"], kids)
                self.assertEqual(card["weight_bytes"], 2 * local)
                self.assertEqual(card["kv_bytes"], 2 * n * 3 * 8193 * len(kids) * D * 2)
                self.assertFalse(
                    any(
                        ".q_norm." in t["name"] or ".k_norm." in t["name"]
                        for t in card["weights"]
                    )
                )
                for t in card["weights"]:
                    if len(t["shape"]) == 1:
                        self.assertEqual(t["shape"], [H])

    def test_matrix_flops_and_replication(self):
        for tp, pp, dp in [(8, 1, 1), (2, 4, 1), (16, 1, 2)]:
            batch, tokens, history = 2, 3, 7
            r = calculate(
                MODEL,
                tp=tp,
                pp=pp,
                dp=dp,
                batch_per_replica=batch,
                tokens=tokens,
                history=history,
            )
            ratio = max(1, tp // K)
            linear = (
                2 * batch * tokens * L * (2 * H * H + 2 * H * K * D * ratio + 3 * H * F)
            )
            head = 2 * batch * V * H
            pairs = batch * (tokens * history + tokens * (tokens + 1) // 2)
            attention = 4 * L * Q * D * pairs
            self.assertEqual(
                r["summary"]["physical_matrix_flops"], dp * (linear + head + attention)
            )

    def test_endpoints_and_peak_boundary(self):
        r = calculate(MODEL, tp=4, pp=2)
        peak = max(c["resident_bytes"] for c in r["placement_cards"])
        for budget, fit in [(peak - 1, False), (peak, True), (peak + 1, True)]:
            s = calculate(MODEL, tp=4, pp=2, capacity_bytes=budget)["summary"]
            self.assertEqual(s["all_cards_fit_declared_budget"], fit)
        for c in r["placement_cards"]:
            names = {t["name"] for t in c["weights"]}
            self.assertEqual("model.embed_tokens.weight" in names, c["stage"] == 0)
            self.assertEqual("lm_head.weight" in names, c["stage"] == 1)
            self.assertEqual("model.norm.weight" in names, c["stage"] == 1)

    def test_reject_fractional_partitions(self):
        for kwargs in [
            dict(tp=3),
            dict(tp=128),
            dict(pp=81),
            dict(tp=True),
            dict(history=131072, tokens=1),
        ]:
            with self.assertRaises(ValueError):
                calculate(MODEL, **kwargs)


if __name__ == "__main__":
    unittest.main()
