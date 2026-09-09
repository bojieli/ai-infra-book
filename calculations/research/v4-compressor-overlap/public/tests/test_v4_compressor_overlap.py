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
import infra_calc.topics

for ancestor in Path(__file__).resolve().parents:
    p = ancestor / "v4-attention-projections/public/src/infra_calc/topics"
    if p.is_dir():
        infra_calc.topics.__path__.insert(0, str(p))
infra_calc.topics.__path__.insert(
    0, str(Path(__file__).resolve().parents[1] / "src/infra_calc/topics")
)
from infra_calc.topics import v4_compressor_overlap as m


class OverlapTests(unittest.TestCase):
    def fixture(self, tokens):
        x = [[(i * 2 + j) % 7 / 9 - 0.3 for j in range(3)] for i in range(tokens)]
        wk = [[(i + j - 2) / 7 for j in range(3)] for i in range(4)]
        wg = [[(2 * i - j + 1) / 11 for j in range(3)] for i in range(4)]
        ape = [[(i - j) / 13 for j in range(4)] for i in range(4)]
        gamma = [0.8, 1.2]
        angles = [[0.2 + 0.3 * i] for i in range(tokens // 4)]
        up = [[0.4, -0.3] for _ in angles]
        sk = [[(i - j + 1) / 17 for j in range(4)] for i in range(8)]
        ss = [[(2 * i + j - 3) / 23 for j in range(4)] for i in range(8)]
        return x, wk, wg, ape, gamma, angles, up, sk, ss

    @unittest.skipIf(torch is None, "FP64 autograd requires torch")
    def test_source_overlap_and_returned_states_autograd(self):
        for tokens in (1, 3, 4, 5, 8, 9):
            args = self.fixture(tokens)
            got = m.reference(*args)
            x, wk, wg, ape, gamma, angles, up, sk, ss = args
            tensors = [
                torch.tensor(a, dtype=torch.float64, requires_grad=True)
                for a in args[:5]
            ]
            tx, tk, tg, ta, tn = tensors
            blocks = tokens // 4
            tail = tokens % 4
            kv = tx @ tk.T
            score = tx @ tg.T + ta[torch.arange(tokens) % 4]
            outputs = []
            for block in range(blocks):
                oldkv = (
                    kv[4 * (block - 1) : 4 * block, :2]
                    if block
                    else torch.zeros(4, 2, dtype=torch.float64)
                )
                oldscore = (
                    score[4 * (block - 1) : 4 * block, :2]
                    if block
                    else torch.full((4, 2), float("-inf"), dtype=torch.float64)
                )
                vals = torch.cat([oldkv, kv[4 * block : 4 * (block + 1), 2:]], 0)
                scores = torch.cat(
                    [oldscore, score[4 * block : 4 * (block + 1), 2:]], 0
                )
                pooled = (scores.softmax(0) * vals).sum(0)
                normal = pooled * (pooled.square().mean() + 1e-6).rsqrt() * tn
                freq = torch.polar(
                    torch.ones(1, dtype=torch.float64),
                    torch.tensor(angles[block], dtype=torch.float64),
                )
                outputs.append(
                    torch.view_as_real(
                        torch.view_as_complex(normal.reshape(1, 2)) * freq
                    ).flatten()
                )
            # Only fresh-state writes are differentiable, constant slots have no loss term.
            writes = (
                [(slot, (blocks - 1) * 4 + slot) for slot in range(4)] if blocks else []
            ) + [(4 + i, blocks * 4 + i) for i in range(tail)]
            loss = sum(
                (out * torch.tensor(up[i], dtype=torch.float64)).sum()
                for i, out in enumerate(outputs)
            )
            loss = loss + sum(
                (kv[token] * torch.tensor(sk[slot], dtype=torch.float64)).sum()
                + (score[token] * torch.tensor(ss[slot], dtype=torch.float64)).sum()
                for slot, token in writes
            )
            loss.backward()
            if blocks:
                self.assertTrue(
                    torch.allclose(
                        torch.tensor(got["output"]),
                        torch.stack(outputs).detach().float(),
                        atol=1e-6,
                    )
                )
            for key, tensor in zip(("dx", "dwkv", "dwgate", "dape", "dgamma"), tensors):
                expected = (
                    tensor.grad if tensor.grad is not None else torch.zeros_like(tensor)
                )
                self.assertTrue(
                    torch.allclose(
                        torch.tensor(got[key], dtype=torch.float64),
                        expected,
                        atol=2e-10,
                        rtol=2e-10,
                    ),
                    key,
                )

    def test_all_parameter_finite_difference_with_tail(self):
        args = self.fixture(5)
        got = m.reference(*args)

        def loss():
            out = m.reference(*args)
            value = sum(
                a * b for row, g in zip(out["output"], args[6]) for a, b in zip(row, g)
            )
            for slot, _ in out["writes"]:
                value += sum(
                    a * b for a, b in zip(out["state_kv"][slot], args[7][slot])
                )
                value += sum(
                    a * b for a, b in zip(out["state_score"][slot], args[8][slot])
                )
            return value

        def check(values, gradient):
            for i, v in enumerate(values):
                if isinstance(v, list):
                    check(v, gradient[i])
                    continue
                values[i] = v + 1e-6
                plus = loss()
                values[i] = v - 1e-6
                minus = loss()
                values[i] = v
                self.assertAlmostEqual((plus - minus) / 2e-6, gradient[i], places=7)

        for values, key in zip(args[:5], ("dx", "dwkv", "dwgate", "dape", "dgamma")):
            check(values, got[key])

    def test_tail_gradient_and_constant_state_slots(self):
        args = list(self.fixture(5))
        with_state = m.reference(*args)
        zeros = [[0.0] * 4 for _ in range(8)]
        no_state = m.reference(*args[:7], zeros, zeros)
        self.assertEqual(no_state["dx"][-1], [0.0] * 3)
        self.assertGreater(sum(abs(v) for v in with_state["dx"][-1]), 0)
        args[7][7] = [999.0] * 4
        args[8][7] = [999.0] * 4
        self.assertEqual(with_state["dx"], m.reference(*args)["dx"])
        self.assertEqual(with_state["state_score"][7], [float("-inf")] * 4)

    def test_ledger_tail_and_prefill_boundaries(self):
        for tokens in (1, 3, 4, 5, 8, 9):
            result = m.calculate(batch=2, tokens=tokens)
            self.assertEqual(result, m.calculate(**result["scenario"]))
            self.assertEqual(result["dimensions"]["tail"], tokens % 4)
            self.assertEqual(
                result["scalar"]["backward_ape_reduce_flops"],
                2 * 512 * (2 * tokens - min(tokens, 4)),
            )
            self.assertIsNone(result["coverage"]["actual_peak_bytes"])
            if tokens < 4:
                self.assertEqual(result["special_ops"]["exp_calls"], 0)
                self.assertEqual(result["scalar"]["backward_norm_flops"], 0)
            else:
                self.assertEqual(
                    result["declared_source_difference"][
                        "source_extra_forward_ape_additions_for_last_complete_state"
                    ],
                    8 * 2 * 512,
                )


if __name__ == "__main__":
    unittest.main()
