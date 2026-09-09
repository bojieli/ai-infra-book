"""Independent local-shard formulas, BF16 compatibility and tail/budget checks."""

import unittest
from dense_quantized_placement import MODELS, calculate, markdown
from infra_calc.topics import dense_placement

DIMS = {
    "qwen3-8b": (4096, 12288, 36, 32, 8, 128, 151936, True),
    "qwen3-32b": (5120, 25600, 64, 64, 8, 128, 151936, True),
    "deepseek-r1-distill-llama-70b": (8192, 28672, 80, 64, 8, 128, 128256, False),
}


def hand(model, tp, pp, stage, bits, group):
    h, f, layers, q, kv, d, vocab, head_norms = DIMS[model]
    count = layers // pp + (stage < layers % pp)
    local_q, local_kv = q * d // tp, max(1, kv // tp) * d
    # Explicit seven projection matrices; no production tensor inventory used.
    matrices = [
        (local_q, h),
        (local_kv, h),
        (local_kv, h),
        (h, local_q),
        (f // tp, h),
        (f // tp, h),
        (h, f // tp),
    ]
    payload = count * sum(rows * ((width * bits + 7) // 8) for rows, width in matrices)
    scales = (
        0
        if bits == 16
        else count
        * sum(rows * ((width + group - 1) // group) * 2 for rows, width in matrices)
    )
    payload += 2 * count * (2 * h + (2 * d if head_norms else 0))
    payload += 2 * (vocab // tp) * h * (int(stage == 0) + int(stage == pp - 1))
    if stage == pp - 1:
        payload += 2 * h
    return payload, scales


class DenseQuantizedTests(unittest.TestCase):
    def test_three_models_three_organizations_independent_formula(self):
        for model in MODELS:
            for tp, pp in [(8, 1), (2, 4), (1, 8)]:
                r = calculate(model=model, tp=tp, pp=pp)
                for rank in r["ranks"]:
                    for form in rank["formats"]:
                        payload, scales = hand(
                            model, tp, pp, rank["stage"], form["bits"], 128
                        )
                        self.assertEqual(
                            (form["payload_bytes"], form["scale_bytes"]),
                            (payload, scales),
                        )

    def test_bf16_original_default_and_state_are_unchanged(self):
        for model in MODELS:
            old = dense_placement.calculate(model=model)
            r = calculate(model=model, length=8193)
            self.assertEqual(r["bf16_reference_summary"], old["summary"])
            for rank, card in zip(r["ranks"], old["placement_cards"]):
                self.assertEqual(
                    rank["original_bf16_resident_one_request_bytes"],
                    card["resident_bytes"],
                )
                self.assertEqual(
                    rank["formats"][0]["weight_bytes"], card["weight_bytes"]
                )
                for form in rank["formats"]:
                    self.assertEqual(form["kv_bytes_per_request"], card["kv_bytes"])
                for weight, original in zip(rank["weights"], card["weights"]):
                    self.assertEqual({key: weight[key] for key in original}, original)

    def test_true_tail_groups_after_column_shard(self):
        for model in MODELS:
            r = calculate(model=model, group_size=1000)
            for form in r["ranks"][0]["formats"]:
                self.assertEqual(
                    (form["payload_bytes"], form["scale_bytes"]),
                    hand(model, 8, 1, 0, form["bits"], 1000),
                )
        down = next(
            w
            for w in calculate(group_size=1000)["ranks"][0]["weights"]
            if ".down_proj." in w["name"]
        )
        self.assertEqual(down["shape"], [4096, 1536])
        self.assertEqual(down["storage"][2]["groups"], 4096 * 2 * 36)
        # Quantizing global K then dividing groups by8 would give13/8 groups;
        # the actual local shard needs two full scale records per row.
        self.assertNotEqual(down["storage"][2]["groups"] * 8, 4096 * 13 * 36)

    def test_kv_replication_and_dp_are_physical(self):
        for model in MODELS:
            r = calculate(model=model, tp=16, dp=2, group_size=1000)
            base = calculate(model=model, tp=16, group_size=1000)
            self.assertEqual(
                r["summary"][2]["physical_weight_bytes"],
                2 * base["summary"][2]["physical_weight_bytes"],
            )
            self.assertEqual(
                r["summary"][2]["maximum_global_requests"],
                2 * base["summary"][2]["maximum_global_requests"],
            )
            heads = [head for rank in base["ranks"] for head in rank["kv_head_ids"]]
            self.assertEqual(sorted(heads), sorted(list(range(8)) * 2))
            for rank in base["ranks"]:
                self.assertEqual(
                    (
                        rank["formats"][2]["payload_bytes"],
                        rank["formats"][2]["scale_bytes"],
                    ),
                    hand(model, 16, 1, 0, 4, 1000),
                )

    def test_worst_pipeline_rank_boundary(self):
        r = calculate(tp=1, pp=8)
        requirements = [
            rank["formats"][2]["weight_bytes"]
            + 2 * 2**30
            + 3 * rank["formats"][2]["kv_bytes_per_request"]
            for rank in r["ranks"]
        ]
        threshold = max(requirements)
        for offset, expected in [(-1, 2), (0, 3), (1, 3)]:
            self.assertEqual(
                calculate(tp=1, pp=8, capacity_bytes=threshold + offset)["summary"][2][
                    "maximum_global_requests"
                ],
                expected,
            )
        self.assertEqual(
            [len(rank["layer_ids"]) for rank in r["ranks"]], [5] * 4 + [4] * 4
        )
        tiny = calculate(capacity_bytes=1)
        self.assertEqual(tiny["summary"][0]["maximum_global_requests"], 0)
        self.assertFalse(tiny["summary"][0]["all_weights_workspace_fit"])

    def test_length_and_unquantized_exceptions(self):
        short, long = calculate(), calculate(length=32768)
        for rank in short["ranks"]:
            for weight in rank["weights"]:
                if not weight["low_bit_eligible"]:
                    self.assertEqual(
                        [s["total_bytes"] for s in weight["storage"]],
                        [weight["bytes"]] * 3,
                    )
        for a, b in zip(short["ranks"], long["ranks"]):
            self.assertEqual(
                a["formats"][2]["weight_bytes"], b["formats"][2]["weight_bytes"]
            )
            self.assertEqual(
                4 * a["formats"][2]["kv_bytes_per_request"],
                b["formats"][2]["kv_bytes_per_request"],
            )

    def test_full_rank_report(self):
        result = calculate(tp=2, pp=4)
        report = markdown(result)
        self.assertIn("不是实际运行峰值保证", report)
        for rank in result["ranks"]:
            self.assertIn(f"## Rank {rank['rank']}（", report)
            for weight in rank["weights"]:
                self.assertIn(weight["name"], report)
        self.assertIn("local K", report)

    def test_replay_and_validation(self):
        for model in MODELS:
            r = calculate(model=model)
            self.assertEqual(r["scenario"]["model"], model)
            self.assertEqual(calculate(**r["scenario"]), r)
        for kwargs in [
            dict(length=0),
            dict(length=True),
            dict(model="qwen3-235b-a22b"),
            dict(group_size=0),
            dict(tp=3),
            dict(workspace_bytes=-1),
        ]:
            with self.assertRaises(ValueError):
                calculate(**kwargs)


if __name__ == "__main__":
    unittest.main()
