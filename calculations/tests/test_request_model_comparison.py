import sys
import unittest
from collections import Counter
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from infra_calc.topics import request_model_comparison as m
from infra_calc.models import qwen3
from infra_calc.schema import Scenario
from infra_calc.topics import k3_forward, v4_forward, k3_checkpoint, v4_checkpoint


class ComparisonTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = m.calculate(prefix_tokens=125, new_tokens=3, output_tokens=4)

    def test_original_models_and_generation_contract(self):
        r = self.result
        self.assertEqual(tuple(x['model'] for x in r['comparisons']), m.MODELS)
        self.assertEqual(r['contract']['decode_forward_calls'], 3)
        self.assertEqual(r['contract']['final_retained_positions'], 131)
        for row in r['comparisons']:
            self.assertEqual(row['decode']['calls'], 3)
            self.assertEqual(row['prefill']['calls'], 3 if row['model'].startswith('deepseek') else 1)
            self.assertEqual(row['summary']['matrix_flops'], row['prefill']['totals']['matrix_flops'] + row['decode']['totals']['matrix_flops'])

    def test_decode_against_independent_full_calls(self):
        for model_row in self.result['comparisons']:
            for row in model_row['decode']['rows']:
                model, history = model_row['model'], row['input_position']
                if model == 'qwen3-8b':
                    direct = qwen3.calculate(model, Scenario(tokens=1, history=history))
                elif model == 'kimi-k3':
                    direct = k3_forward.calculate(tokens=1, history=history)
                else:
                    direct = v4_forward.calculate(model, tokens=1, history=history)
                norm = m.base_row(direct)
                for key in ('matrix_flops', 'accounted_scalar_flops'):
                    self.assertEqual(row[key], norm[key])
                self.assertEqual(Counter(row['special_ops']), Counter(norm['special_ops']))

    def test_first_output_has_zero_decode(self):
        r = m.calculate(new_tokens=1, output_tokens=1)
        for row in r['comparisons']:
            self.assertEqual(row['decode']['rows'], [])
            self.assertEqual(row['decode']['totals']['matrix_flops'], 0)
            self.assertEqual(row['summary']['final_state_resident_bytes'], row['prefill']['final_state_resident_bytes'])

    def test_compact_affine_state_and_operations(self):
        r = m.linear_decode('kimi-k3', 2, 128, 3, 'compact', 'balanced')
        last = k3_forward.calculate(batch=2, tokens=1, history=130, mla_path='compact')
        self.assertEqual(r['rows'][-1]['matrix_flops'], last['summary']['matrix_flops'])
        self.assertEqual(r['rows'][-1]['state_resident_after_bytes'], last['summary']['state_resident_after_bytes'])
        self.assertEqual(Counter(r['rows'][-1]['special_ops']), Counter(last['summary']['accounted_special_ops']))

    def test_checkpoint_reads_are_constant(self):
        with patch.object(k3_checkpoint, 'calculate', wraps=k3_checkpoint.calculate) as k3, patch.object(v4_checkpoint, 'calculate', wraps=v4_checkpoint.calculate) as v4:
            m.calculate(new_tokens=4, output_tokens=8)
            self.assertEqual(k3.call_count, 2)
            self.assertEqual(v4.call_count, 4)  # Two static phases for each V4 model.

    def test_batch_replication_and_source_allocation(self):
        doubled = m.calculate(prefix_tokens=125, new_tokens=3, output_tokens=4, batch=2)
        for one, two in zip(self.result['comparisons'], doubled['comparisons']):
            self.assertEqual(two['summary']['final_state_resident_bytes'], 2 * one['summary']['final_state_resident_bytes'])
            self.assertEqual(two['summary']['uniform_bf16_weight_comparison_bytes'], one['summary']['uniform_bf16_weight_comparison_bytes'])
            if two['source_cache_allocation']:
                self.assertEqual(two['source_cache_allocation']['max_seq_len'], 131)
                self.assertEqual(two['source_cache_allocation']['max_batch_size'], 2)
                self.assertEqual(two['source_cache_allocation']['bf16_cache_and_fp32_compressor_bytes'], 2 * one['source_cache_allocation']['bf16_cache_and_fp32_compressor_bytes'])

    def test_scenario_replay(self):
        replay = m.calculate(**self.result['scenario'])
        self.assertEqual(replay, self.result)

    def test_unknowns_and_conflict_retained(self):
        for row in self.result['comparisons']:
            self.assertIsNone(row['summary']['complete_hbm_traffic_bytes'])
            self.assertIsNone(row['summary']['quality_equivalence'])
        k3 = self.result['comparisons'][-1]
        self.assertFalse(k3['source_coverage']['config_checkpoint_shape_match'])
        self.assertTrue(any('A_log' in x for x in k3['source_coverage']['missing']))

    def test_markdown_complete_model_phase_and_unknowns(self):
        report = m.markdown(self.result)
        for row in self.result['comparisons']:
            self.assertIn(row['model'], report)
            self.assertIn(str(row['summary']['matrix_flops']), report)
            self.assertIn(str(row['summary']['final_state_resident_bytes']), report)
            for step in row['decode']['rows']:
                self.assertIn(str(step['matrix_flops']), report)
                for name in step['known_interfaces']:
                    self.assertIn(name, report)
        for name in ('A_log', 'complete_hbm_traffic_bytes', 'quality_equivalence', 'max_seq_len', 'unknown'):
            self.assertIn(name, report)

    def test_context_boundary_and_rejected_inputs(self):
        r = m.linear_decode('qwen3-8b', 1, 40959, 1, 'expanded', 'balanced')
        self.assertEqual(len(r['rows']), 1)
        for kwargs in ({'new_tokens': 0}, {'output_tokens': True}, {'prefix_tokens': -1}, {'new_tokens': 40960, 'output_tokens': 2}):
            with self.assertRaises(ValueError):
                m.calculate(**kwargs)


if __name__ == '__main__':
    unittest.main()
