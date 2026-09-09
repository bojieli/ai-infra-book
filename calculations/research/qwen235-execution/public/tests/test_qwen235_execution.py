import copy
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
from infra_calc.topics import qwen235_execution as m


class ExecutionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = m.calculate(tokens=2)

    def test_assignments_work_and_capacity(self):
        result = self.result
        self.assertEqual(
            result["summary"]["expert_matrix_flops"],
            result["summary"]["expected_unique_expert_matrix_flops"],
        )
        self.assertEqual(
            sum(row["rows"] for rank in result["ranks"] for row in rank["experts"]),
            result["summary"]["assignments"] * 2,
        )
        self.assertEqual(result["summary"]["dispatch_wire_bytes"], 0)
        self.assertEqual(result, m.calculate(**result["scenario"]))
        for rank in result["ranks"]:
            self.assertEqual(
                rank["conditional_resident_bytes"],
                rank["bf16_weight_bytes"]
                + rank["bf16_kv_bytes"]
                + rank["workspace_reserved_bytes"],
            )
        boundary = max(rank["conditional_resident_bytes"] for rank in result["ranks"])
        self.assertTrue(
            m.calculate(tokens=2, capacity_bytes=boundary)["summary"][
                "all_necessary_capacity_fits"
            ]
        )
        self.assertFalse(
            m.calculate(tokens=2, capacity_bytes=boundary - 1)["summary"][
                "all_necessary_capacity_fits"
            ]
        )

    def test_same_histogram_different_remote_tokens(self):
        table = copy.deepcopy(self.result["route_table"])
        k = len(table[0]["experts"])
        for row in table:
            row["experts"] = (
                list(range(k)) if row["position"] == 0 else list(range(32, 32 + k))
            )
        pure = m.calculate(tokens=2, routes=table)
        mixed = copy.deepcopy(table)
        for row in mixed:
            offset = 0 if row["position"] == 0 else k // 2
            row["experts"] = list(range(offset, offset + k // 2)) + list(
                range(32 + offset, 32 + offset + k // 2)
            )
        joint = m.calculate(tokens=2, routes=mixed)
        self.assertEqual(
            [[r["rows"] for r in rank["experts"]] for rank in pure["ranks"]],
            [[r["rows"] for r in rank["experts"]] for rank in joint["ranks"]],
        )
        self.assertEqual(
            pure["summary"]["expert_matrix_flops"],
            joint["summary"]["expert_matrix_flops"],
        )
        self.assertGreater(
            joint["summary"]["total_wire_bytes"], pure["summary"]["total_wire_bytes"]
        )

    def test_pp_endpoints_and_consumers(self):
        result = m.calculate(tp=1, ep=4, pp=2, tokens=1)
        transfers = [msg for msg in result["messages"] if msg["phase"] == "pp_transfer"]
        self.assertEqual(len(transfers), 1)
        self.assertEqual((transfers[0]["source"], transfers[0]["target"]), (0, 4))
        self.assertEqual(
            sum(msg["phase"] == "pp_replicate" for msg in result["messages"]), 3
        )
        for msg in result["messages"]:
            self.assertNotEqual(msg["source"], msg["target"])
            self.assertTrue(msg["token_ids"])
            self.assertEqual(
                msg["wire_bytes"], msg["payload_bytes"] + msg["metadata_bytes"]
            )
            if msg["phase"] == "tp_reduce":
                self.assertEqual(
                    result["ranks"][msg["source"]]["expert_rank"],
                    result["ranks"][msg["target"]]["expert_rank"],
                )
        self.assertIsNone(result["summary"]["full_request_runtime_seconds"])

    def test_small_moe_tp_ep_reconstruction(self):
        import torch

        torch.manual_seed(131)
        r, h, f, e, k = 3, 4, 6, 8, 2
        x = torch.randn(r, h, dtype=torch.float64)
        w1 = torch.randn(e, f, h, dtype=torch.float64)
        w3 = torch.randn(e, f, h, dtype=torch.float64)
        w2 = torch.randn(e, h, f, dtype=torch.float64)
        ids = [[0, 7], [2, 3], [0, 5]]
        weights = [[0.3, 0.7], [0.6, 0.4], [0.2, 0.8]]
        direct = torch.zeros(r, h, dtype=torch.float64)
        for token in range(r):
            for expert, weight in zip(ids[token], weights[token]):
                direct[token] += weight * (
                    w2[expert]
                    @ (
                        torch.nn.functional.silu(w1[expert] @ x[token])
                        * (w3[expert] @ x[token])
                    )
                )
        for tp, ep in ((2, 4), (1, 4), (2, 2)):
            partial = torch.zeros(ep, tp, r, h, dtype=torch.float64)
            for owner in range(ep):
                for tensor in range(tp):
                    start, end = tensor * (f // tp), (tensor + 1) * (f // tp)
                    for token in range(r):
                        for expert, weight in zip(ids[token], weights[token]):
                            if expert // (e // ep) == owner:
                                z = torch.nn.functional.silu(
                                    w1[expert, start:end] @ x[token]
                                ) * (w3[expert, start:end] @ x[token])
                                partial[owner, tensor, token] += weight * (
                                    w2[expert, :, start:end] @ z
                                )
            # Same order as message phases: TP root reduce, EP root reduce, broadcasts.
            tp_roots = partial.sum(1)
            combined = tp_roots[0].clone()
            for owner in range(1, ep):
                combined += tp_roots[owner]
            torch.testing.assert_close(combined, direct, rtol=1e-12, atol=1e-12)

    def test_invalid_route_and_resource_inputs(self):
        for kwargs in (
            {"tokens": 0},
            {"tokens": 9, "length": 8},
            {"link_bytes_per_second": float("nan")},
            {"startup_seconds": -1},
            {"requests": True},
        ):
            with self.assertRaises(ValueError):
                m.calculate(**kwargs)
        table = copy.deepcopy(self.result["route_table"])
        table[0]["experts"][0] = table[0]["experts"][1]
        with self.assertRaises(ValueError):
            m.calculate(tokens=2, routes=table)


if __name__ == "__main__":
    unittest.main()
