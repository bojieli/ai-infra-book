import importlib.util
import sys
import unittest
from collections import Counter
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / 'calculations/src'))
MODULE = Path(__file__).resolve().parents[1] / 'src/infra_calc/topics/v4_prefix_continuation.py'
spec = importlib.util.spec_from_file_location('prefix_candidate', MODULE)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
from infra_calc.topics import v4_forward, v4_checkpoint, v4_attention


class PrefixContinuationTests(unittest.TestCase):
    def test_every_small_step_matches_full_forward(self):
        for model in ('deepseek-v4-flash', 'deepseek-v4-pro'):
            r = m.calculate(model, prefix_tokens=125, new_tokens=5)
            for row in r['steps']:
                direct = v4_forward.calculate(model, tokens=1, history=row['input_position'])['summary']
                for key in ('matrix_flops_effective_attention',
                            'matrix_flops_with_reference_sparse_and_expert_tiles',
                            'accounted_scalar_flops', 'state_resident_after_bytes'):
                    self.assertEqual(row[key], direct[key])
                self.assertEqual(Counter(row['accounted_special_ops']), Counter(direct['accounted_special_ops']))

    def test_first_step_completes_block(self):
        r = m.calculate(prefix_tokens=127, new_tokens=2, batch=3)
        self.assertEqual(r['steps'][0]['completed_ratios'], [4, 128])
        self.assertEqual(r['steps'][1]['completed_ratios'], [])
        direct = v4_forward.calculate('deepseek-v4-flash', batch=3, tokens=1, history=128)
        self.assertEqual(r['steps'][1]['accounted_scalar_flops'], direct['summary']['accounted_scalar_flops'])

    def test_book_all_boundaries_and_state_growth(self):
        r = m.calculate()
        self.assertEqual(r['compression_boundaries']['4'], list(range(6148, 8193, 4)))
        self.assertEqual(r['compression_boundaries']['128'], list(range(6272, 8193, 128)))
        self.assertEqual(len(r['steps']), 2048)
        self.assertEqual(r['summary']['discarded_intermediate_vocabulary_heads'], 2047)
        # Flash: 21 CSA layers x (512 main +128 index), 20 HCA x512;
        # BF16 caches. Ring and compressor capacity do not grow at this length.
        expected_growth = 21 * 512 * (512 + 128) * 2 + 20 * 16 * 512 * 2
        self.assertEqual(r['summary']['state_growth_bytes'], expected_growth)
        self.assertEqual(sum(s['known_interfaces']['completed_cache_entry_write_bytes'] for s in r['steps']), expected_growth)

    def test_checkpoint_parsed_once(self):
        with patch.object(v4_checkpoint, 'calculate', wraps=v4_checkpoint.calculate) as read:
            m.calculate(new_tokens=5)
            self.assertEqual(read.call_count, 1)

    def test_totals_conserve_rows_and_types(self):
        r = m.calculate(prefix_tokens=125, new_tokens=5)
        for key in ('matrix_flops_effective_attention', 'matrix_flops_with_reference_sparse_and_expert_tiles', 'accounted_scalar_flops'):
            self.assertEqual(r['summary'][key], sum(s[key] for s in r['steps']))
        total = Counter()
        for s in r['steps']:
            total.update(s['accounted_special_ops'])
        self.assertEqual(total, Counter(r['summary']['accounted_special_ops']))
        self.assertIsNone(r['summary']['complete_hbm_traffic_bytes'])
        self.assertIsNone(r['summary']['complete_scalar_flops'])
        self.assertFalse(r['coverage']['parallel_cached_chunk'])

    def test_allocation_and_fp32_slots(self):
        r = m.calculate(prefix_tokens=127, new_tokens=2, allocated_max_seq_len=256,
                        allocated_max_batch_size=4)
        self.assertGreater(r['source_cache_allocation']['bf16_history_and_fp32_compressor_bytes'],
                           r['summary']['final_state_resident_bytes'])
        first, second = r['steps']
        self.assertEqual(first['known_interfaces']['compressor_fp32_slot_write_bytes'],
                         21 * 2 * 2 * (512 + 128) * 4 + 20 * 2 * 512 * 4)
        self.assertEqual(first['known_interfaces']['overlap_roll_fp32_write_bytes'],
                         21 * 2 * 4 * 2 * (512 + 128) * 4)
        self.assertEqual(second['known_interfaces']['overlap_roll_fp32_write_bytes'], 0)
        with self.assertRaises(ValueError):
            m.calculate(allocated_max_seq_len=4096)

    def test_invalid_scope(self):
        with self.assertRaises(ValueError):
            m.calculate(prefix_tokens=0)
        with self.assertRaises(ValueError):
            m.calculate(new_tokens=True)
        with self.assertRaises(ValueError):
            v4_attention.calculate('deepseek-v4-flash', history=6144, tokens=2048)


if __name__ == '__main__':
    unittest.main()
