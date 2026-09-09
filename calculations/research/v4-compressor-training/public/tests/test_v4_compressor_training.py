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
    dependency = ancestor / "v4-attention-projections/public/src/infra_calc/topics"
    if dependency.is_dir():
        infra_calc.topics.__path__.insert(0, str(dependency))
infra_calc.topics.__path__.insert(
    0, str(Path(__file__).resolve().parents[1] / "src/infra_calc/topics")
)
from infra_calc.topics import v4_compressor_training as m


class CompressorTests(unittest.TestCase):
    def fixture(self, ratio=2):
        x = [[(i * 2 + j) % 9 / 7 - 0.4 for j in range(3)] for i in range(2 * ratio)]
        wkv = [[(i + j - 2) / 7 for j in range(3)] for i in range(4)]
        wg = [[(2 * i - j + 1) / 11 for j in range(3)] for i in range(4)]
        ape = [[(i % 5 - j) / 13 for j in range(4)] for i in range(ratio)]
        gamma = [0.8, 1.1, 0.6, 1.3]
        angles = [[0.2], [0.7]]
        up = [[0.4, -0.3, 0.2, 0.8], [-0.1, 0.5, 0.2, -0.6]]
        return x, wkv, wg, ape, gamma, angles, up

    @unittest.skipIf(torch is None, "FP64 autograd requires torch")
    def test_actual_ratio128_and_small_autograd(self):
        for ratio in (2, 128):
            x, wk, wg, ape, gamma, angles, up = self.fixture(ratio)
            got = m.reference(x, wk, wg, ape, gamma, angles, up, ratio)
            tensors = [
                torch.tensor(a, dtype=torch.float64, requires_grad=True)
                for a in (x, wk, wg, ape, gamma)
            ]
            tx, tk, tg, ta, tn = tensors
            kv = (tx @ tk.T).reshape(2, ratio, 4)
            score = (tx @ tg.T).reshape(2, ratio, 4) + ta
            pooled = (score.softmax(1) * kv).sum(1)
            normalized = (
                pooled * (pooled.square().mean(-1, keepdim=True) + 1e-6).rsqrt() * tn
            )
            freq = torch.polar(
                torch.ones(2, 1, dtype=torch.float64),
                torch.tensor(angles, dtype=torch.float64),
            )
            rotated = torch.view_as_real(
                torch.view_as_complex(normalized[:, -2:].contiguous().reshape(2, 1, 2))
                * freq
            ).flatten(-2)
            out = torch.cat([normalized[:, :-2], rotated], -1)
            (out * torch.tensor(up, dtype=torch.float64)).sum().backward()
            for actual, expected in [(got["output"], out)] + [
                (got[k], v.grad)
                for k, v in zip(("dx", "dwkv", "dwgate", "dape", "dgamma"), tensors)
            ]:
                self.assertTrue(
                    torch.allclose(
                        torch.tensor(actual, dtype=torch.float64),
                        expected,
                        atol=2e-10,
                        rtol=2e-10,
                    )
                )

    def test_all_small_finite_differences(self):
        args = self.fixture()
        got = m.reference(*args, ratio=2)

        def loss():
            return sum(
                a * b
                for row, g in zip(m.reference(*args, ratio=2)["output"], args[-1])
                for a, b in zip(row, g)
            )

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

        for values, key in zip(args[:5], ("dx", "dwkv", "dwgate", "dape", "dgamma")):
            check(values, got[key])

    def test_boundary_contract_counts_and_source_positions(self):
        for tokens in (1, 127, 129, 255):
            with self.assertRaises(ValueError):
                m.calculate(tokens=tokens)
        a = m.calculate(tokens=128)
        b = m.calculate(batch=2, tokens=256)
        self.assertEqual(b, m.calculate(**b["scenario"]))
        self.assertEqual(b["execution"]["rope_positions"], [0, 128])
        self.assertEqual(
            b["totals"]["backward_matrix_flops"],
            4 * a["totals"]["backward_matrix_flops"],
        )
        self.assertEqual(b["scalar"]["backward_ape_reduce_flops"], 128 * 512 * (4 - 1))
        self.assertFalse(b["coverage"]["ratio4_overlap_vjp"])
        self.assertIsNone(b["source_state_boundary"]["online_gradient_contract"])
        with self.assertRaises(ValueError):
            m.reference(*self.fixture(4), ratio=4)

    def test_independent_blocks_and_online_slot_order(self):
        args = self.fixture(128)
        full = m.reference(*args)["output"]
        x, wk, wg, ape, gamma, angles, up = args
        # Functional source slot writes in order; no stop-gradient or restored-state claim.
        for block in range(2):
            state = [None] * 128
            for offset in range(128):
                state[offset] = x[block * 128 + offset]
            one = m.reference(state, wk, wg, ape, gamma, [angles[block]], [up[block]])[
                "output"
            ][0]
            self.assertEqual(one, full[block])


if __name__ == "__main__":
    unittest.main()
