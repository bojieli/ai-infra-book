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

infra_calc.topics.__path__.insert(
    0, str(Path(__file__).resolve().parents[1] / "src/infra_calc/topics")
)
from infra_calc.topics import v4_attention_projections as m


class ProjectionTests(unittest.TestCase):
    def fixture(self, groups=2):
        hidden, heads, d, q, o = 4, 2, 4, 3, 3
        matrix = lambda rows, cols, offset: [
            [((i * 3 + j + offset) % 13 - 6) / 11 for j in range(cols)]
            for i in range(rows)
        ]
        weights = dict(
            wq_a=matrix(q, hidden, 1),
            wq_b=matrix(heads * d, q, 2),
            wkv=matrix(d, hidden, 3),
            wo_a=[matrix(o, heads * d // groups, g + 1) for g in range(groups)],
            wo_b=matrix(hidden, groups * o, 4),
        )
        return (
            [0.2, -0.3, 0.7, 0.4],
            weights,
            [0.8, 1.2, 0.6],
            [1.1, 0.7, 0.9, 1.3],
            [0.31],
            [-0.2, 0.5, 0.8, -0.1],
        )

    def core(self, q, kv):
        return [
            [
                math.tanh(a + kv[j]) + 0.2 * sum(row[j] for row in q)
                for j, a in enumerate(head)
            ]
            for head in q
        ]

    def core_vjp(self, q, kv, g):
        local = [
            [(1 - math.tanh(a + kv[j]) ** 2) * g[h][j] for j, a in enumerate(head)]
            for h, head in enumerate(q)
        ]
        return [
            [a + 0.2 * sum(row[j] for row in g) for j, a in enumerate(head)]
            for head in local
        ], [sum(row[j] for row in local) for j in range(len(kv))]

    @unittest.skipIf(torch is None, "FP64 numerical audit requires torch")
    def test_all_vjps_against_autograd(self):
        for groups in [1, 2]:
            x, w, qg, kg, angles, up = self.fixture(groups)
            got = m.reference(
                x, w, qg, kg, 2, groups, angles, self.core, self.core_vjp, up
            )
            tensor = lambda a: torch.tensor(a, dtype=torch.float64, requires_grad=True)
            tx, tqg, tkg = tensor(x), tensor(qg), tensor(kg)
            tw = {k: tensor(v) for k, v in w.items()}
            norm = lambda a: a * (a.square().mean(-1, keepdim=True) + 1e-6).rsqrt()

            def rotate(a, inverse=False):
                # Source complex adjacent-pair path, independent of manual loop.
                c = torch.polar(
                    torch.ones(len(angles), dtype=torch.float64),
                    torch.tensor(angles, dtype=torch.float64),
                )
                if inverse:
                    c = c.conj()
                rotated = torch.view_as_real(
                    torch.view_as_complex(
                        a[..., -2:].contiguous().reshape(*a.shape[:-1], 1, 2)
                    )
                    * c
                ).flatten(-2)
                return torch.cat([a[..., :-2], rotated], -1)

            qr = norm(tw["wq_a"] @ tx) * tqg
            q = rotate(norm((tw["wq_b"] @ qr).reshape(2, 4)))
            kv = rotate(norm(tw["wkv"] @ tx) * tkg)
            core = (q + kv).tanh() + 0.2 * q.sum(0)
            outgroup = rotate(core, True).reshape(groups, -1)
            middle = torch.einsum("gri,gi->gr", tw["wo_a"], outgroup)
            out = tw["wo_b"] @ middle.flatten()
            (out * torch.tensor(up, dtype=torch.float64)).sum().backward()
            pairs = [
                (got["output"], out),
                (got["dx"], tx.grad),
                (got["dq_gamma"], tqg.grad),
                (got["dkv_gamma"], tkg.grad),
            ] + [(got["dweights"][k], v.grad) for k, v in tw.items()]
            for a, b in pairs:
                self.assertTrue(
                    torch.allclose(
                        torch.tensor(a, dtype=torch.float64), b, atol=2e-10, rtol=2e-10
                    )
                )

    def test_finite_difference_all_inputs_parameters(self):
        x, w, qg, kg, angles, up = self.fixture()
        result = m.reference(x, w, qg, kg, 2, 2, angles, self.core, self.core_vjp, up)

        def loss():
            out = m.reference(x, w, qg, kg, 2, 2, angles, self.core, self.core_vjp, up)[
                "output"
            ]
            return sum(a * b for a, b in zip(out, up))

        def check(values, grad):
            for i, v in enumerate(values):
                if isinstance(v, list):
                    check(v, grad[i])
                    continue
                values[i] = v + 1e-6
                plus = loss()
                values[i] = v - 1e-6
                minus = loss()
                values[i] = v
                self.assertAlmostEqual((plus - minus) / 2e-6, grad[i], places=7)

        for a, b in [
            (x, result["dx"]),
            (qg, result["dq_gamma"]),
            (kg, result["dkv_gamma"]),
        ] + [(w[k], result["dweights"][k]) for k in w]:
            check(a, b)

    def test_rope_adjoint_counts_and_saved_scope(self):
        x = [0.4, -0.2, 0.6, 0.8]
        g = [0.1, 0.3, -0.7, 0.5]
        angle = [0.29]
        self.assertAlmostEqual(
            sum(a * b for a, b in zip(m.rotate(x, angle), g)),
            sum(a * b for a, b in zip(x, m.rotate(g, angle, True))),
        )
        result = m.calculate(batch=2, tokens=3)
        self.assertEqual(result, m.calculate(**result["scenario"]))
        for row in result["matrices"]:
            self.assertEqual(row["forward_flops"], row["backward_dx_flops"])
            self.assertEqual(row["forward_flops"], row["backward_dw_flops"])
        self.assertEqual(
            result["rope"]["forward_scalar_flops"], 3 * 6 * 64 * (2 * 64 + 1)
        )
        self.assertFalse(result["coverage"]["core_work_included"])
        self.assertIsNone(result["coverage"]["actual_peak_bytes"])
        self.assertNotIn(
            "core_probabilities", result["saved_forward_boundary"]["buffers"]
        )


if __name__ == "__main__":
    unittest.main()
