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
from infra_calc.topics import v4_moe_training as m


class MoETests(unittest.TestCase):
    def fixture(self):
        matrix = lambda rows, cols, offset: [
            [((i * 2 + j + offset) % 9 - 4) / 13 for j in range(cols)]
            for i in range(rows)
        ]
        expert = lambda offset: dict(
            w1=matrix(2, 3, offset),
            w3=matrix(2, 3, offset + 2),
            w2=matrix(3, 2, offset + 3),
        )
        return (
            [0.4, -0.7, 0.2],
            matrix(3, 3, 1),
            [expert(i) for i in range(3)],
            expert(4),
            [0, 2],
            [0.3, -0.6, 0.8],
        )

    @unittest.skipIf(torch is None, "FP64 autograd requires torch")
    def test_all_inputs_parameters_and_router_scores(self):
        for limit in (0.05, 10.0):
            x, gate, experts, shared, ids, up = self.fixture()
            got = m.reference(x, gate, experts, shared, ids, up, limit=limit)
            tensor = lambda a: torch.tensor(a, dtype=torch.float64, requires_grad=True)
            tx, tgate = tensor(x), tensor(gate)
            te = [{k: tensor(v) for k, v in e.items()} for e in experts]
            ts = {k: tensor(v) for k, v in shared.items()}
            logits = tgate @ tx
            logits.retain_grad()
            scores = torch.nn.functional.softplus(logits).sqrt()
            p = scores[ids] / scores[ids].sum() * 1.5

            def forward(weights, route=None):
                gate = (weights["w1"] @ tx).clamp(max=limit)
                up = (weights["w3"] @ tx).clamp(-limit, limit)
                activation = torch.nn.functional.silu(gate) * up
                if route is not None:
                    activation = activation * route
                return weights["w2"] @ activation

            output = sum(forward(te[i], p[j]) for j, i in enumerate(ids)) + forward(ts)
            (output * torch.tensor(up, dtype=torch.float64)).sum().backward()
            pairs = [
                (got["output"], output),
                (got["dx"], tx.grad),
                (got["drouter_weight"], tgate.grad),
                (got["drouter_logits"], logits.grad),
            ]
            for i, e in enumerate(te):
                for name, v in e.items():
                    pairs.append(
                        (
                            got["dexperts"][i][name],
                            v.grad if v.grad is not None else torch.zeros_like(v),
                        )
                    )
            for name, v in ts.items():
                pairs.append((got["dshared"][name], v.grad))
            for actual, expected in pairs:
                self.assertTrue(
                    torch.allclose(
                        torch.tensor(actual, dtype=torch.float64),
                        expected,
                        atol=1e-12,
                        rtol=1e-12,
                    )
                )
            if limit == 10:
                self.assertGreater(logits.grad.abs().sum().item(), 0)

    def test_complete_small_finite_differences(self):
        args = self.fixture()
        got = m.reference(*args)

        def loss():
            return sum(a * b for a, b in zip(m.reference(*args)["output"], args[-1]))

        def check(values, gradient):
            if isinstance(values, dict):
                for key, value in values.items():
                    check(value, gradient[key])
                return
            for i, v in enumerate(values):
                if isinstance(v, (list, dict)):
                    check(v, gradient[i])
                    continue
                values[i] = v + 1e-6
                plus = loss()
                values[i] = v - 1e-6
                minus = loss()
                values[i] = v
                self.assertAlmostEqual((plus - minus) / 2e-6, gradient[i], places=8)

        for values, key in zip(
            args[:4], ("dx", "drouter_weight", "dexperts", "dshared")
        ):
            check(values, got[key])

    def test_histogram_load_and_full_parameter_scope(self):
        balanced = m.calculate()
        concentrated = m.calculate(routing="concentrated")
        self.assertEqual(sum(balanced["routing_histogram"]), 128 * 6)
        self.assertEqual(balanced["routing_scope"]["visited_experts"], 256)
        self.assertEqual(concentrated["routing_scope"]["visited_experts"], 6)
        self.assertEqual(balanced["totals"], concentrated["totals"])
        self.assertEqual(
            balanced["parameters"]["routed_expert_weights"],
            concentrated["parameters"]["routed_expert_weights"],
        )
        self.assertNotEqual(
            balanced["parameters"]["visited_expert_gradient_parameters"],
            concentrated["parameters"]["visited_expert_gradient_parameters"],
        )
        self.assertEqual(
            sum(r["forward_matrix_flops"] for r in balanced["routed_experts"]),
            6 * 128 * 6 * 4096 * 2048,
        )
        self.assertEqual(balanced, m.calculate(**balanced["scenario"]))
        bad = [0] * 256
        bad[0] = 129
        with self.assertRaises(ValueError):
            m.calculate(counts=bad)

    def test_hash_router_gradient_work_and_route_position(self):
        hash_layer = m.calculate(layer_id=0)
        score_layer = m.calculate(layer_id=3)
        self.assertEqual(
            hash_layer["router"]["backward_matrix_flops"],
            score_layer["router"]["backward_matrix_flops"],
        )
        self.assertEqual(
            score_layer["router"]["forward_scalar_flops"]
            - hash_layer["router"]["forward_scalar_flops"],
            128 * 256,
        )
        self.assertEqual(
            hash_layer["scalar"]["routed_weight_backward_flops"],
            128 * 6 * (3 * 2048 - 1),
        )
        self.assertEqual(
            hash_layer["scalar"]["routed_forward_weight_product_flops"], 128 * 6 * 2048
        )
        self.assertFalse(hash_layer["coverage"]["qat_numerical_equivalence"])
        self.assertIsNone(hash_layer["coverage"]["actual_peak_bytes"])
        args = list(self.fixture())
        args[4] = [0, 0]
        with self.assertRaises(ValueError):
            m.reference(*args)


if __name__ == "__main__":
    unittest.main()
