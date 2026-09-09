"""Independent parameter identity and loss-mask invariants for training work."""
import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from infra_calc.topics.training_matrix import calculate
from infra_calc.sources import model_config


class TrainingMatrixTests(unittest.TestCase):
    def test_dense_parameter_identity_and_attention(self):
        c = model_config('qwen3-8b')
        b, t = 2, 17
        s = calculate(batch=b, tokens=t)['summary']
        h, v, l, d = (c[k] for k in ('hidden_size', 'vocab_size', 'num_hidden_layers', 'head_dim'))
        # Embedding lookup and all normalization parameters are outside GEMMs.
        nonmatrix = h * v + l * (2 * h + 2 * d) + h
        attention = 12 * l * c['num_attention_heads'] * d * b * t * (t + 1) // 2
        self.assertEqual(s['attention_training_matrix_flops'], attention)
        self.assertEqual(s['training_matrix_flops'], 6 * (s['parameters'] - nonmatrix) * b * t + attention)
        self.assertEqual(s['unsharded_parameter_state_bytes'], 18 * s['parameters'])

    def test_mask_is_not_automatic_gemm_compaction(self):
        full = calculate(tokens=8)
        masked = calculate(tokens=8, supervised_tokens=3)
        compact = calculate(tokens=8, supervised_tokens=3, head_strategy='compact')
        self.assertEqual(full['training_matrix_rows'], masked['training_matrix_rows'])
        c = model_config('qwen3-8b')
        self.assertEqual(full['summary']['training_matrix_flops'] - compact['summary']['training_matrix_flops'],
                         6 * 5 * c['hidden_size'] * c['vocab_size'])
        head = compact['training_matrix_rows'][-1]
        self.assertEqual(head['shapes']['d_weight_matmul'], [[c['vocab_size'], 3], [3, c['hidden_size']]])
        self.assertEqual(head['shapes']['d_input_matmul'], [[3, c['vocab_size']], [c['vocab_size'], c['hidden_size']]])

    def test_moe_expert_work_and_resident_state(self):
        balanced = calculate(model='qwen3-235b-a22b', tokens=32)
        concentrated = calculate(model='qwen3-235b-a22b', tokens=32, routing='concentrated')
        c = model_config('qwen3-235b-a22b')
        expert = sum(row['training_matrix_flops'] for row in balanced['training_matrix_rows'] if row['name'].startswith('expert_'))
        self.assertEqual(expert, 18 * c['num_hidden_layers'] * 32 * c['num_experts_per_tok'] * c['hidden_size'] * c['moe_intermediate_size'])
        self.assertEqual(balanced['summary']['training_matrix_flops'], concentrated['summary']['training_matrix_flops'])
        self.assertEqual(balanced['summary']['unsharded_parameter_state_bytes'], concentrated['summary']['unsharded_parameter_state_bytes'])
        self.assertEqual(concentrated['summary']['active_experts_per_layer'], c['num_experts_per_tok'])
        self.assertEqual(balanced['summary']['active_experts_per_layer'], c['num_experts'])

    def test_reject_unsupported_or_inconsistent_inputs(self):
        for args in [dict(model='kimi-k3'), dict(tokens=4, supervised_tokens=5),
                     dict(supervised_tokens=0), dict(head_strategy='automatic'), dict(gradient_bytes=True)]:
            with self.assertRaises(ValueError):
                calculate(**args)
        s = calculate(master_weight_bytes=0, gradient_bytes=2)['summary']
        self.assertEqual(s['unsharded_parameter_state_bytes'], 12 * s['parameters'])


if __name__ == '__main__':
    unittest.main()
