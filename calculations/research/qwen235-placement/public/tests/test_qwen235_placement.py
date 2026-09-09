"""Independent ownership and closed-form storage checks for declared placement."""

import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from infra_calc.topics.qwen235_placement import calculate, markdown


def hand_rank(tp, ep, layer_count, endpoints, bits, group=128):
    """Closed form directly from fixed dimensions, independent of tensor iteration."""
    h, f, d, q, kv, e, v = 4096, 1536, 128, 64, 4, 128, 151936
    local_kv = max(1, kv // tp)
    expert_elements = (e // ep) * 3 * h * (f // tp)
    attention_elements = 2 * h * (q * d // tp) + 2 * h * local_kv * d
    unquantized = 128 * h + 2 * h + 2 * d
    if bits == 16:
        payload = layer_count * 2 * (expert_elements + attention_elements + unquantized)
        metadata = 0
    else:
        payload = layer_count * (
            (expert_elements + attention_elements) * bits // 8 + 2 * unquantized
        )
        ceil = lambda a: (a + group - 1) // group
        # gate/up output-row partition; down input-column partition.
        expert_groups = (e // ep) * (2 * (f // tp) * ceil(h) + h * ceil(f // tp))
        attention_groups = (q * d // tp + 2 * local_kv * d) * ceil(h) + h * ceil(
            q * d // tp
        )
        metadata = layer_count * 2 * (expert_groups + attention_groups)
    payload += endpoints * 2 * (v // tp) * h
    return payload, metadata


class PlacementTests(unittest.TestCase):
    def test_four_organizations_closed_forms(self):
        for tp, ep, pp in [(2, 4, 1), (4, 2, 1), (2, 2, 2), (1, 1, 8)]:
            r = calculate(tp=tp, ep=ep, pp=pp)
            for rank in r["ranks"]:
                stage = rank["pipeline_stage"]
                endpoints = int(stage == 0) + int(stage == pp - 1)
                layers = rank["layer_range"][1] - rank["layer_range"][0]
                for form in rank["formats"]:
                    payload, metadata = hand_rank(
                        tp, ep, layers, endpoints, form["bits"]
                    )
                    if stage == pp - 1:
                        payload += 2 * 4096
                    self.assertEqual(form["payload_bytes"], payload)
                    self.assertEqual(form["scale_bytes"], metadata)
                    self.assertEqual(
                        form["kv_bytes_per_request"],
                        4 * layers * max(1, 4 // tp) * 128 * 8192,
                    )

    def test_physical_replication_conservation(self):
        for tp, ep, pp in [(2, 4, 1), (8, 1, 1), (1, 1, 8)]:
            r = calculate(tp=tp, ep=ep, pp=pp)
            layer_experts = 128 * 3 * 4096 * 1536
            layer_qo = 2 * 4096 * 64 * 128
            layer_kv = 2 * 4096 * 4 * 128
            layer_norm_router = 128 * 4096 + 2 * 4096 + 2 * 128
            physical = 94 * (
                layer_experts
                + ep * layer_qo
                + ep * max(1, tp // 4) * layer_kv
                + ep * tp * layer_norm_router
            )
            physical += ep * 2 * 151936 * 4096 + ep * tp * 4096
            self.assertEqual(r["cohort"][0]["physical_weight_bytes"], 2 * physical)
            self.assertEqual(r["evidence"]["unique_parameters"], 235093634560)
            self.assertEqual(r["evidence"]["index_tensor_count"], 36945)

    def test_gqa_tp8_replication_matches_q_heads(self):
        r = calculate(tp=8, ep=1)
        for rank in r["ranks"]:
            self.assertEqual(
                rank["kv_head_range"], [rank["rank"] // 2, rank["rank"] // 2 + 1]
            )
            q0, q1 = rank["q_head_range"]
            self.assertEqual(q0 // 16, rank["kv_head_range"][0])
            self.assertEqual((q1 - 1) // 16, rank["kv_head_range"][0])

    def test_post_shard_group_tail(self):
        r = calculate(group_size=1000)
        for form in r["ranks"][0]["formats"]:
            payload, metadata = hand_rank(2, 4, 94, 2, form["bits"], group=1000)
            self.assertEqual(form["payload_bytes"], payload + 8192)
            self.assertEqual(form["scale_bytes"], metadata)
        down = next(t for t in r["ranks"][0]["tensors"] if ".down_proj." in t["name"])
        self.assertEqual(down["local_shape"], [4096, 768])
        self.assertEqual(down["storage"][2]["groups"], 94 * 4096)

    def test_capacity_boundaries_and_length_scaling(self):
        r = calculate()
        form = r["ranks"][0]["formats"][2]
        threshold = form["weight_bytes"] + 2 * 2**30 + 3 * form["kv_bytes_per_request"]
        for offset, expected in [(-1, 2), (0, 3), (1, 3)]:
            self.assertEqual(
                calculate(capacity_bytes=threshold + offset)["cohort"][2][
                    "maximum_requests"
                ],
                expected,
            )
        longer = calculate(length=32768)
        self.assertEqual(
            longer["ranks"][0]["formats"][0]["kv_bytes_per_request"],
            4 * form["kv_bytes_per_request"],
        )
        failed = calculate(capacity_bytes=24 * 10**9)
        self.assertFalse(failed["cohort"][0]["all_weights_workspace_fit"])
        self.assertEqual(failed["cohort"][0]["maximum_requests"], 0)

    def test_rank_ownership_coverage(self):
        r = calculate(tp=2, ep=2, pp=2)
        # Every layer/expert pair appears once per TP replica group; local
        # complementary row/column intervals reconstruct each expert matrix.
        for stage in range(2):
            stage_ranks = [
                rank for rank in r["ranks"] if rank["pipeline_stage"] == stage
            ]
            for expert in range(128):
                for projection, axis_size in [
                    ("gate_proj", 1536),
                    ("up_proj", 1536),
                    ("down_proj", 1536),
                ]:
                    name = f"model.layers.{{layer}}.mlp.experts.{expert}.{projection}.weight"
                    shards = [
                        t
                        for rank in stage_ranks
                        for t in rank["tensors"]
                        if t["name"] == name
                    ]
                    self.assertEqual(
                        sorted((t["shard_start"], t["shard_end"]) for t in shards),
                        [(0, axis_size // 2), (axis_size // 2, axis_size)],
                    )
        self.assertEqual(r["ranks"][0]["layer_range"], [0, 47])
        self.assertEqual(r["ranks"][-1]["layer_range"], [47, 94])
        pp8 = calculate(tp=1, ep=1, pp=8)
        self.assertEqual(
            [rank["layer_range"][1] - rank["layer_range"][0] for rank in pp8["ranks"]],
            [12] * 6 + [11] * 2,
        )

    def test_report_complete_rank_and_tensor_coverage(self):
        result = calculate(tp=8, ep=1)
        report = markdown(result)
        self.assertIn("不是运行峰值保证", report)
        self.assertIn("235,093,634,560", report)
        for rank in result["ranks"]:
            self.assertIn(f"## Rank {rank['rank']}（", report)
            for tensor in rank["tensors"]:
                self.assertIn(tensor["name"], report)
        kv_line = next(
            line for line in report.splitlines() if ".k_proj.weight |" in line
        )
        self.assertIn("| 94 | 2 |", kv_line)
        failed_report = markdown(calculate(capacity_bytes=24 * 10**9))
        self.assertIn("False", failed_report)
        self.assertIn("无 zero point", report)

    def test_replay_and_invalid_inputs(self):
        r = calculate()
        self.assertEqual(r, calculate(**r["scenario"]))
        for kwargs in [
            dict(tp=3),
            dict(ep=True),
            dict(length=40961),
            dict(workspace_bytes=-1),
            dict(group_size=0),
        ]:
            with self.assertRaises(ValueError):
                calculate(**kwargs)


if __name__ == "__main__":
    unittest.main()
