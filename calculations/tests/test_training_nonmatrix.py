import math
import sys
import unittest
from pathlib import Path

try:
    import torch
except ImportError:
    torch = None

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from infra_calc.topics import training_nonmatrix as m
from infra_calc.topics import training_matrix


def finite_difference(function, values, index, epsilon=1e-6):
    plus, minus = values[:], values[:]
    plus[index] += epsilon
    minus[index] -= epsilon
    return (function(plus) - function(minus)) / (2 * epsilon)


@unittest.skipIf(torch is None, 'Optional audit dependency torch is required for independent autograd')
class NumericTests(unittest.TestCase):
    def assert_vectors_close(self, actual, expected, tolerance=1e-10):
        a = torch.tensor(actual, dtype=torch.float64)
        b = torch.tensor(expected, dtype=torch.float64)
        self.assertTrue(torch.allclose(a, b, atol=tolerance, rtol=tolerance), (a, b))

    def test_rms_hidden_and_shared_head_gamma(self):
        for rows, width in ((2, 3), (6, 4)):
            x = [[(i * width + j - 3) / 7 for j in range(width)] for i in range(rows)]
            gamma = [(j + 1) / 5 for j in range(width)]
            dy = [[(i - j + 2) / 9 for j in range(width)] for i in range(rows)]
            out, dx, dg = m.rms_vjp(x, gamma, dy)
            tx = torch.tensor(x, dtype=torch.float64, requires_grad=True)
            tg = torch.tensor(gamma, dtype=torch.float64, requires_grad=True)
            ty = tx * torch.rsqrt(tx.square().mean(-1, keepdim=True) + 1e-6) * tg
            (ty * torch.tensor(dy, dtype=torch.float64)).sum().backward()
            self.assert_vectors_close(out, ty.detach().tolist())
            self.assert_vectors_close(dx, tx.grad.tolist(), 1e-10)
            self.assert_vectors_close(dg, tg.grad.tolist(), 1e-10)
            flat = [v for row in x for v in row]
            def loss(values):
                result = m.rms_vjp([values[i * width:(i + 1) * width] for i in range(rows)], gamma, dy)[0]
                return sum(result[i][j] * dy[i][j] for i in range(rows) for j in range(width))
            for i in range(len(flat)):
                self.assertAlmostEqual(finite_difference(loss, flat, i), dx[i // width][i % width], places=7)
            def gamma_loss(values):
                result = m.rms_vjp(x, values, dy)[0]
                return sum(result[i][j] * dy[i][j] for i in range(rows) for j in range(width))
            for i in range(width):
                self.assertAlmostEqual(finite_difference(gamma_loss, gamma, i), dg[i], places=7)

    def test_swiglu_derivatives(self):
        gate, up, dy = [-3., -.1, 0., 2.], [.7, -1., 2., 3.], [1., -.3, .7, -2.]
        out, dg, du = m.swiglu_vjp(gate, up, dy)
        g = torch.tensor(gate, dtype=torch.float64, requires_grad=True)
        u = torch.tensor(up, dtype=torch.float64, requires_grad=True)
        y = torch.nn.functional.silu(g) * u
        (y * torch.tensor(dy, dtype=torch.float64)).sum().backward()
        self.assert_vectors_close(out, y.detach().tolist())
        self.assert_vectors_close(dg, g.grad.tolist())
        self.assert_vectors_close(du, u.grad.tolist())
        for i in range(len(gate)):
            loss = lambda z: sum(a * b for a, b in zip(m.swiglu_vjp(z, up, dy)[0], dy))
            self.assertAlmostEqual(finite_difference(loss, gate, i), dg[i], places=7)
            up_loss = lambda z: sum(a * b for a, b in zip(m.swiglu_vjp(gate, z, dy)[0], dy))
            self.assertAlmostEqual(finite_difference(up_loss, up, i), du[i], places=7)

    def test_softmax_causal_rows_and_scale(self):
        for width in (1, 2, 5):
            values = [(i - 2) * .7 for i in range(width)]
            dy = [(-1)**i * (i + 1) / 3 for i in range(width)]
            p, dx = m.softmax_vjp(values, dy, .5)
            x = torch.tensor(values, dtype=torch.float64, requires_grad=True)
            y = torch.softmax(x * .5, -1)
            (y * torch.tensor(dy, dtype=torch.float64)).sum().backward()
            self.assert_vectors_close(p, y.detach().tolist())
            self.assert_vectors_close(dx, x.grad.tolist())
            for i in range(width):
                loss = lambda z: sum(a * b for a, b in zip(m.softmax_vjp(z, dy, .5)[0], dy))
                self.assertAlmostEqual(finite_difference(loss, values, i), dx[i], places=7)

    def test_mean_loss_and_masked_rows(self):
        values = [[-1000., 1000., 999.], [.2, -.4, .8]]
        labels = [2, 0]
        loss, grad = m.mean_cross_entropy(values, labels)
        logits = torch.tensor(values, dtype=torch.float64, requires_grad=True)
        reference = torch.nn.functional.cross_entropy(logits, torch.tensor(labels), reduction='mean')
        reference.backward()
        self.assertAlmostEqual(loss, reference.item(), places=12)
        self.assert_vectors_close(grad, logits.grad.tolist())
        flat = [v for row in values for v in row]
        for i in range(len(flat)):
            fn = lambda z: m.mean_cross_entropy([z[:3], z[3:]], labels)[0]
            self.assertAlmostEqual(finite_difference(fn, flat, i), grad[i // 3][i % 3], places=6)

    def test_selected_loss_gradient_scatter(self):
        full = torch.tensor([[.2, .4, -.1], [.9, .8, .7], [-.5, .3, .1]], dtype=torch.float64, requires_grad=True)
        labels = torch.tensor([1, 2])
        loss = torch.nn.functional.cross_entropy(full[[0, 2]], labels)
        loss.backward()
        _, selected_grad = m.mean_cross_entropy([full.detach()[0].tolist(), full.detach()[2].tolist()], labels.tolist())
        self.assert_vectors_close(full.grad.tolist(), [selected_grad[0], [0., 0., 0.], selected_grad[1]])

    def test_query_head_gradients_reduce_to_kv_heads(self):
        q = torch.arange(24, dtype=torch.float64).reshape(4, 2, 3) / 13
        kv = (torch.arange(12, dtype=torch.float64).reshape(2, 2, 3) / 7).requires_grad_()
        repeated = kv.repeat_interleave(2, dim=0)
        mask = torch.tril(torch.ones(2, 2, dtype=torch.float64))
        loss = ((q @ repeated.transpose(-1, -2)) * mask).sum()
        loss.backward()
        head_gradients = []
        for head in range(4):
            independent = kv.detach()[head // 2].clone().requires_grad_()
            ((q[head] @ independent.T) * mask).sum().backward()
            head_gradients.append(independent.grad)
        reduced = torch.stack([head_gradients[0] + head_gradients[1], head_gradients[2] + head_gradients[3]])
        self.assert_vectors_close(reduced.tolist(), kv.grad.tolist())

    def test_rotary_transpose_backward(self):
        x = torch.tensor([.2, -.7], dtype=torch.float64, requires_grad=True)
        angle = .6
        c, s = math.cos(angle), math.sin(angle)
        y = torch.stack([c * x[0] - s * x[1], s * x[0] + c * x[1]])
        dy = [.3, -.9]
        (y * torch.tensor(dy, dtype=torch.float64)).sum().backward()
        self.assert_vectors_close(x.grad.tolist(), [c * dy[0] + s * dy[1], -s * dy[0] + c * dy[1]])

    def test_adamw_matches_unfused_pytorch(self):
        for step in (1, 7):
            for decay in (0., .02):
                weights, gradients = [.4, -.7, .2], [.3, -.4, 0.]
                first, second = [.1, -.2, .05], [.2, .3, .1]
                result = m.adamw_update(weights, gradients, first, second, step, .001, .9, .99, 1e-8, decay)
                p = torch.tensor(weights, dtype=torch.float64, requires_grad=True)
                optimizer = torch.optim.AdamW([p], lr=.001, betas=(.9, .99), eps=1e-8, weight_decay=decay, foreach=False, fused=False)
                optimizer.state[p].update(step=torch.tensor(float(step - 1)), exp_avg=torch.tensor(first, dtype=torch.float64), exp_avg_sq=torch.tensor(second, dtype=torch.float64))
                p.grad = torch.tensor(gradients, dtype=torch.float64)
                optimizer.step()
                self.assert_vectors_close(result[0], p.detach().tolist())
                self.assert_vectors_close(result[1], optimizer.state[p]['exp_avg'].tolist())
                self.assert_vectors_close(result[2], optimizer.state[p]['exp_avg_sq'].tolist())


class AccountingTests(unittest.TestCase):
    def test_original_matrix_unchanged(self):
        r = m.calculate(tokens=8)
        old = training_matrix.calculate('qwen3-8b', tokens=8)
        self.assertEqual(r['training_matrix_original'], old)
        self.assertEqual(r['summary']['original_parameter_state_bytes'], old['summary']['unsharded_parameter_state_bytes'])

    def test_mask_and_compact_head(self):
        full = m.calculate(tokens=8)
        masked = m.calculate(tokens=8, supervised_tokens=4)
        compact = m.calculate(tokens=8, supervised_tokens=4, head_strategy='compact')
        self.assertEqual(full['summary']['original_training_matrix_flops'], masked['summary']['original_training_matrix_flops'])
        self.assertLess(compact['summary']['original_training_matrix_flops'], masked['summary']['original_training_matrix_flops'])
        by_name = lambda r: {x['name']: x for x in r['nonmatrix_operations']}
        self.assertEqual(by_name(full)['mean_cross_entropy']['backward_scalar_flops'], 2 * by_name(masked)['mean_cross_entropy']['backward_scalar_flops'])
        self.assertEqual(by_name(masked)['mean_cross_entropy'], by_name(compact)['mean_cross_entropy'])
        self.assertEqual(by_name(full)['input_rmsnorm'], by_name(compact)['input_rmsnorm'])
        self.assertEqual(compact['data_operations']['compact_hidden_gradient_zero_fp32_bytes'], 4 * 8 * 4096)
        self.assertEqual(masked['data_operations']['compact_hidden_gradient_zero_fp32_bytes'], 0)

    def test_recompute_operations_and_lifetime(self):
        saved, replay = m.calculate(tokens=8), m.calculate(tokens=8, activation_policy='recompute_silu')
        elements = 36 * 8 * 12288
        self.assertEqual(replay['summary']['backward_scalar_flops'] - saved['summary']['backward_scalar_flops'], elements)
        self.assertEqual(saved['summary']['nonlinear_saved_at_forward_end_bytes'] - replay['summary']['nonlinear_saved_at_forward_end_bytes'], 4 * elements)
        for r in (saved, replay):
            self.assertEqual(r['lifetime_events'][-1]['declared_subset_live_bytes'], 0)
            self.assertEqual(r['summary']['declared_saved_and_recomputed_subset_peak_bytes'], max(x['declared_subset_live_bytes'] for x in r['lifetime_events']))
            self.assertIsNone(r['summary']['complete_activation_peak_bytes'])

    def test_optimizer_and_total_count_units(self):
        r = m.calculate(tokens=8)
        p = 8190735360
        self.assertEqual(r['optimizer']['parameter_scalar_flops'], 14 * p)
        self.assertEqual(r['optimizer']['special_ops']['sqrt'], p)
        self.assertEqual(r['optimizer']['typed_conversions']['fp32_master_to_bf16_weights'], p)
        s = r['summary']
        self.assertEqual(s['accounted_matrix_plus_scalar_flops'], s['original_training_matrix_flops'] + s['forward_scalar_flops'] + s['backward_scalar_flops'] + s['optimizer_scalar_flops'])

    def test_markdown_retains_operator_lifetimes_and_unknowns(self):
        r = m.calculate(tokens=8)
        report = m.markdown(r)
        for row in r['nonmatrix_operations']:
            self.assertIn(row['name'], report)
            self.assertIn(str(row['backward_scalar_flops']), report)
        self.assertIn('unknown', report)
        self.assertIn('V4', report)
        self.assertIn('fp32_master_to_bf16_weights', report)
        self.assertIn('backward_last_use_release', report)

    def test_replay_and_invalid_inputs(self):
        r = m.calculate(tokens=8, supervised_tokens=4, beta1=0, weight_decay=0)
        self.assertEqual(m.calculate(**r['scenario']), r)
        for kwargs in ({'beta1': True}, {'beta2': 1}, {'learning_rate': float('nan')}, {'adam_step': 0}, {'epsilon': 0}, {'activation_policy': 'whole_layer_checkpoint'}):
            with self.assertRaises(ValueError):
                m.calculate(**kwargs)


if __name__ == '__main__':
    unittest.main()
