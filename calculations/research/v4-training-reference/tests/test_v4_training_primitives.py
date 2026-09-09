import importlib.util
import sys
import unittest
from pathlib import Path
import torch

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "calculations/src"))
spec = importlib.util.spec_from_file_location(
    "primitive",
    Path(__file__).resolve().parents[1]
    / "src/infra_calc/topics/v4_training_primitives.py",
)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class PrimitiveTests(unittest.TestCase):
    def close(self, a, b, tolerance=1e-9):
        self.assertTrue(
            torch.allclose(
                torch.tensor(a, dtype=torch.float64),
                torch.tensor(b, dtype=torch.float64),
                atol=tolerance,
                rtol=tolerance,
            )
        )

    def test_router_selected_weight_derivative(self):
        for indices in ([1, 3], [0, 2]):
            values, upstream = [-0.8, 0.9, 0.2, 1.7], [0.4, -0.7]
            out, grad = m.router_vjp(values, indices, upstream)
            z = torch.tensor(values, dtype=torch.float64, requires_grad=True)
            scores = torch.nn.functional.softplus(z).sqrt()[indices]
            weights = 1.5 * scores / scores.sum()
            (weights * torch.tensor(upstream, dtype=torch.float64)).sum().backward()
            self.close(out, weights.detach().tolist())
            self.close(grad, z.grad.tolist())
            for j in range(len(values)):
                plus, minus = values[:], values[:]
                plus[j] += 1e-6
                minus[j] -= 1e-6
                loss = lambda a: sum(
                    v * g
                    for v, g in zip(m.router_vjp(a, indices, upstream)[0], upstream)
                )
                self.assertAlmostEqual(
                    (loss(plus) - loss(minus)) / 2e-6, grad[j], places=7
                )

    def test_bias_only_selection_and_hash_still_scores(self):
        z = torch.tensor([-0.8, 0.9, 0.2, 1.7], dtype=torch.float64, requires_grad=True)
        bias = torch.tensor(
            [0.01, 0.02, 0.03, 0.04], dtype=torch.float64, requires_grad=True
        )
        scores = torch.nn.functional.softplus(z).sqrt()
        ids = (scores + bias).topk(2).indices
        weights = 1.5 * scores[ids] / scores[ids].sum()
        weights[0].backward()
        self.assertIsNone(bias.grad)
        self.assertGreater(z.grad.abs().sum().item(), 0)
        _, hash_grad = m.router_vjp(z.detach().tolist(), [0, 2], [1.0, 0.0])
        self.assertNotEqual(hash_grad[0], 0)

    def torch_split(self, mixes, scales, base, hc, iterations, epsilon):
        pre = torch.sigmoid(mixes[:hc] * scales[0] + base[:hc]) + epsilon
        post = 2 * torch.sigmoid(mixes[hc : 2 * hc] * scales[1] + base[hc : 2 * hc])
        comb = (mixes[2 * hc :] * scales[2] + base[2 * hc :]).reshape(hc, hc).softmax(
            -1
        ) + epsilon
        comb = comb / (comb.sum(-2, keepdim=True) + epsilon)
        for _ in range(iterations - 1):
            comb = comb / (comb.sum(-1, keepdim=True) + epsilon)
            comb = comb / (comb.sum(-2, keepdim=True) + epsilon)
        return pre, post, comb

    def test_all_split_adjoints_and_finite_difference(self):
        for hc, iterations in ((2, 1), (2, 2), (4, 20)):
            width = hc * (hc + 2)
            mixes = [(i - 3) / 11 for i in range(width)]
            base = [(i % 3 - 1) / 13 for i in range(width)]
            scale = [0.7, -0.4, 1.2]
            pg, qg = [(i + 1) / 7 for i in range(hc)], [(i - 2) / 9 for i in range(hc)]
            cg = [[(i * hc + j - 3) / 17 for j in range(hc)] for i in range(hc)]
            r = m.sinkhorn_vjp(mixes, scale, base, pg, qg, cg, hc, iterations, 1e-3)
            x = torch.tensor(mixes, dtype=torch.float64, requires_grad=True)
            a = torch.tensor(scale, dtype=torch.float64, requires_grad=True)
            b = torch.tensor(base, dtype=torch.float64, requires_grad=True)
            pre, post, comb = self.torch_split(x, a, b, hc, iterations, 1e-3)
            (
                (pre * torch.tensor(pg, dtype=torch.float64)).sum()
                + (post * torch.tensor(qg, dtype=torch.float64)).sum()
                + (comb * torch.tensor(cg, dtype=torch.float64)).sum()
            ).backward()
            self.close(r["pre"], pre.detach().tolist())
            self.close(r["post"], post.detach().tolist())
            self.close(r["comb"], comb.detach().tolist())
            self.close(r["dmixes"], x.grad.tolist())
            self.close(r["dscale"], a.grad.tolist())
            self.close(r["dbase"], b.grad.tolist())

            def scalar(values):
                z = m.sinkhorn_vjp(
                    values, scale, base, pg, qg, cg, hc, iterations, 1e-3
                )
                return (
                    sum(x * y for x, y in zip(z["pre"], pg))
                    + sum(x * y for x, y in zip(z["post"], qg))
                    + sum(
                        z["comb"][i][j] * cg[i][j] for i in range(hc) for j in range(hc)
                    )
                )

            for j in range(width):
                plus, minus = mixes[:], mixes[:]
                plus[j] += 1e-6
                minus[j] -= 1e-6
                self.assertAlmostEqual(
                    (scalar(plus) - scalar(minus)) / 2e-6, r["dmixes"][j], places=7
                )
            self.assertEqual(r["normalization_stages"], 2 * iterations - 1)

    def test_counts_and_scope(self):
        r = m.calculate(tokens=3)
        self.assertEqual(r["router"]["hash_layers"], 3)
        self.assertEqual(r["sinkhorn_split"]["normalizations_per_occurrence"], 39)
        self.assertEqual(
            r["router"]["backward_score_matrix_flops"],
            2 * r["router"]["forward_score_matrix_flops"],
        )
        self.assertIsNone(r["coverage"]["complete_training_backward_flops"])
        self.assertFalse(r["coverage"]["full_mhc_x_weight_vjp"])
        self.assertEqual(m.calculate(**r["scenario"]), r)


if __name__ == "__main__":
    unittest.main()
