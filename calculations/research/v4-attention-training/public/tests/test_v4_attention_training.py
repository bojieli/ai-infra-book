import math
from pathlib import Path
import sys
import unittest

try:
    import torch
except ImportError:
    torch = None

for ancestor in Path(__file__).resolve().parents:
    if (ancestor / "src/infra_calc/sources.py").is_file():
        sys.path.insert(0, str(ancestor / "src"))
        break
else:
    raise RuntimeError("Cannot locate the calculation source package")
import infra_calc.topics

candidate_topics = Path(__file__).resolve().parents[1] / "src/infra_calc/topics"
infra_calc.topics.__path__.insert(0, str(candidate_topics))
from infra_calc.topics import v4_attention_training as m


class AttentionTests(unittest.TestCase):
    def fixture(self):
        q = [[[0.2, -0.4, 0.7], [0.6, 0.3, -0.5]], [[0.5, 0.9, -0.1], [-0.2, 0.8, 0.4]]]
        kv = [[0.3, -0.2, 0.5], [-0.6, 0.4, 0.1], [0.7, 0.8, -0.3]]
        sink = [0.4, -0.2]
        indices = [[0, -1, 0, 1], [2, 0, -1, 2]]
        g = [[[0.1, 0.2, -0.3], [-0.4, 0.7, 0.5]], [[0.3, 0.2, 0.8], [-0.1, 0.4, -0.6]]]
        return q, kv, sink, indices, g

    @unittest.skipIf(torch is None, "FP64 numerical audit requires torch")
    def test_autograd_shared_kv_duplicates_and_sink(self):
        q, kv, sink, indices, g = self.fixture()
        got = m.reference(q, kv, sink, indices, g)
        tq, tk, ts = [
            torch.tensor(a, dtype=torch.float64, requires_grad=True)
            for a in (q, kv, sink)
        ]
        outputs = []
        for t, row in enumerate(indices):
            ids = [i for i in row if i != -1]
            selected = tk[ids]
            logits = tq[t] @ selected.T / math.sqrt(3)
            all_logits = torch.cat([logits, ts[:, None]], dim=1)
            weights = all_logits.softmax(-1)
            outputs.append(weights[:, :-1] @ selected)
        out = torch.stack(outputs)
        (out * torch.tensor(g, dtype=torch.float64)).sum().backward()
        for actual, expected in [
            (got["output"], out),
            (got["dq"], tq.grad),
            (got["dkv"], tk.grad),
            (got["dsink"], ts.grad),
        ]:
            self.assertTrue(
                torch.allclose(
                    torch.tensor(actual, dtype=torch.float64),
                    expected,
                    atol=1e-12,
                    rtol=1e-12,
                )
            )
        self.assertGreater(ts.grad.abs().sum().item(), 0)

    def test_central_difference_all_inputs_and_padding(self):
        q, kv, sink, indices, g = self.fixture()
        got = m.reference(q, kv, sink, indices, g)

        def loss():
            out = m.reference(q, kv, sink, indices)["output"]
            return sum(
                out[t][h][d] * g[t][h][d]
                for t in range(2)
                for h in range(2)
                for d in range(3)
            )

        def check(values, gradients):
            for i, v in enumerate(values):
                if isinstance(v, list):
                    check(v, gradients[i])
                    continue
                values[i] = v + 1e-6
                plus = loss()
                values[i] = v - 1e-6
                minus = loss()
                values[i] = v
                self.assertAlmostEqual((plus - minus) / 2e-6, gradients[i], places=8)

        for values, gradient in [
            (q, got["dq"]),
            (kv, got["dkv"]),
            (sink, got["dsink"]),
        ]:
            check(values, gradient)
        compact = [[i for i in row if i != -1] for row in indices]
        self.assertEqual(got, m.reference(q, kv, sink, compact, g))
        unique = [list(dict.fromkeys(row)) for row in compact]
        self.assertNotEqual(
            got["output"], m.reference(q, kv, sink, unique, g)["output"]
        )

    def test_single_key_sink_closed_form(self):
        r = m.reference([[[1.0]]], [[2.0]], [0.0], [[0]], [[[3.0]]], scale=1.0)
        p = 1 / (1 + math.exp(-2))
        self.assertAlmostEqual(r["dsink"][0], -6 * p * (1 - p))
        self.assertAlmostEqual(r["dkv"][0][0], 3 * p + 6 * p * (1 - p))
        self.assertAlmostEqual(r["dq"][0][0][0], 12 * p * (1 - p))

    def test_ledger_replay_and_invalid_boundaries(self):
        r = m.calculate(
            batch=2,
            tokens=2,
            kv_tokens=3,
            heads=2,
            head_dim=3,
            indices=[[0, -1, 0, 1], [2, 0, -1, 2]],
        )
        a = 2 * 2 * 6
        self.assertEqual(r["totals"]["backward_matrix_flops"], 8 * a * 3)
        self.assertEqual(
            r["totals"]["backward_scalar_flops"], 5 * a + 2 * a * 3 + 2 * (4 - 1)
        )
        self.assertEqual(
            r["reference_data_ops"]["dkv_zero_initialization_bytes"], 4 * 2 * 3 * 3
        )
        self.assertEqual(
            r["saved_forward_boundary"]["buffers"]["kv_fp32_shared_key_value"],
            4 * 2 * 3 * 3,
        )
        self.assertEqual(r, m.calculate(**r["scenario"]))
        self.assertIn("unknown (null)", m.markdown(r))
        for ids in [[[-1]], [[1]], [[-2]], [[True]]]:
            with self.assertRaises(ValueError):
                m.calculate(tokens=1, indices=ids)
        with self.assertRaises(ValueError):
            m.calculate(tokens=2, indices=[[0], [0, 1]])
        self.assertFalse(r["coverage"]["quantized_kernel_value_equivalence"])


if __name__ == "__main__":
    unittest.main()
