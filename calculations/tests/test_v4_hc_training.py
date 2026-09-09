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
from infra_calc.topics import v4_hc_training as m


class HCGradientTests(unittest.TestCase):
    def close(self, got, want):
        self.assertTrue(
            torch.allclose(
                torch.tensor(got, dtype=torch.float64),
                want.detach(),
                atol=2e-9,
                rtol=2e-9,
            )
        )

    def fixture(self, c, h):
        x = [[(i * h + j - 2) / 9 for j in range(h)] for i in range(c)]
        w = [
            [((i * 3 + j) % 11 - 5) / 17 for j in range(c * h)]
            for i in range(c * (c + 2))
        ]
        base = [(i % 3 - 1) / 7 for i in range(c * (c + 2))]
        scale = [0.8, -0.3, 1.1]
        up = [[(i * 2 + j - 1) / 5 for j in range(h)] for i in range(c)]
        return x, w, scale, base, up

    @unittest.skipIf(
        torch is None, "FP64 numeric audit requires torch; skips are not passes"
    )
    def test_all_parameter_and_input_adjoints(self):
        for c, h, iters in [(2, 3, 1), (2, 2, 2), (4, 3, 20)]:
            x, w, scale, base, up = self.fixture(c, h)
            inner = lambda y: [math.tanh(a) + 0.2 * a for a in y]
            inner_vjp = lambda y, g: [
                (1 - math.tanh(a) ** 2 + 0.2) * b for a, b in zip(y, g)
            ]
            r = m.vjp(x, w, scale, base, inner, inner_vjp, up, iters, 1e-3, 2e-3)
            tensors = [
                torch.tensor(a, dtype=torch.float64, requires_grad=True)
                for a in (x, w, scale, base)
            ]
            tx, tw, ts, tb = tensors
            flat = tx.flatten()
            mixes = (tw @ flat) * (flat.square().mean() + 2e-3).rsqrt()
            pre = torch.sigmoid(mixes[:c] * ts[0] + tb[:c]) + 1e-3
            post = 2 * torch.sigmoid(mixes[c : 2 * c] * ts[1] + tb[c : 2 * c])
            comb = (mixes[2 * c :] * ts[2] + tb[2 * c :]).reshape(c, c).softmax(
                -1
            ) + 1e-3
            comb = comb / (comb.sum(0, keepdim=True) + 1e-3)
            for _ in range(iters - 1):
                comb = comb / (comb.sum(1, keepdim=True) + 1e-3)
                comb = comb / (comb.sum(0, keepdim=True) + 1e-3)
            y = (pre[:, None] * tx).sum(0)
            z = y.tanh() + 0.2 * y
            # Direct broadcast source orientation, not the candidate's loop.
            out = post[:, None] * z[None, :] + (comb[:, :, None] * tx[:, None, :]).sum(
                0
            )
            (out * torch.tensor(up, dtype=torch.float64)).sum().backward()
            self.close(r["output"], out)
            for key, t in zip(("dx", "dweight", "dscale", "dbase"), tensors):
                self.close(r[key], t.grad)
            branches = r["x_gradient_branches"]
            reconstructed = [
                [
                    branches["residual"][i][j]
                    + branches["pre"][i][j]
                    + branches["linear"][i * h + j]
                    + branches["rms"][i * h + j]
                    for j in range(h)
                ]
                for i in range(c)
            ]
            self.assertEqual(reconstructed, r["dx"])
            self.assertGreater(sum(abs(v) for v in branches["rms"]), 0)

    @unittest.skipIf(
        torch is None, "FP64 numeric audit requires torch; skips are not passes"
    )
    def test_central_difference_input_and_weight(self):
        x, w, scale, base, up = self.fixture(2, 2)
        inner = lambda y: [a * a + 0.3 * a for a in y]
        inner_vjp = lambda y, g: [(2 * a + 0.3) * b for a, b in zip(y, g)]
        r = m.vjp(x, w, scale, base, inner, inner_vjp, up, 2)

        def loss():
            out = m.forward(x, w, scale, base, inner, 2)["output"]
            return sum(a * b for row, g in zip(out, up) for a, b in zip(row, g))

        for values, derivatives in [(x, r["dx"]), (w, r["dweight"])]:
            for i, row in enumerate(values):
                for j, v in enumerate(row):
                    row[j] = v + 1e-6
                    plus = loss()
                    row[j] = v - 1e-6
                    minus = loss()
                    row[j] = v
                    self.assertAlmostEqual(
                        (plus - minus) / 2e-6, derivatives[i][j], places=7
                    )

    def test_counts_replay_and_aliases(self):
        a = m.calculate(tokens=1)
        b = m.calculate(batch=2, tokens=3)
        d = a["dimensions"]
        c = d["hc"]
        h = d["hidden"]
        n = d["flat"]
        v = d["mix_width"]
        q = d["sublayer_occurrences"]
        self.assertEqual(a["outer_backward_scalar_flops"], q * (5 * n + 3 * v + 3))
        self.assertEqual(
            a["totals"]["backward_matrix_flops"],
            q * (4 * v * n + 6 * c * h + 4 * c * c * h),
        )
        self.assertEqual(
            b["totals"]["backward_matrix_flops"],
            6 * a["totals"]["backward_matrix_flops"],
        )
        self.assertEqual(b, m.calculate(**b["scenario"]))
        buffers = a["saved_forward_boundary"]["per_sublayer_buffers"]
        self.assertEqual(buffers["x_fp32_residual_alias"], 4 * n)
        self.assertNotIn("final_comb", buffers)
        self.assertIsNone(a["coverage"]["full_runtime_peak_bytes"])
        self.assertEqual(
            a["totals"]["backward_scalar_flops"],
            a["outer_backward_scalar_flops"]
            + a["reused_split"]["backward_scalar_flops"],
        )


if __name__ == "__main__":
    unittest.main()
