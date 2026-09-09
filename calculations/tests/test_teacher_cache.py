import unittest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from infra_calc.topics import teacher_cache


class TeacherCacheTests(unittest.TestCase):
    def test_official_shapes_and_all_replay_work(self):
        for model, hidden, vocabulary in (
            ('qwen3-8b', 4096, 151936),
            ('deepseek-v4-flash', 4096, 129280),
            ('kimi-k3', 7168, 163840),
        ):
            s = teacher_cache.calculate(model=model, tokens=9, replays=3)['summary']
            self.assertEqual(s['hidden_cache_bytes'], 9 * hidden * 2)
            self.assertEqual(s['full_logits_cache_bytes'], 9 * vocabulary * 2)
            self.assertEqual(s['hidden_total_head_flops'], 3 * 2 * 9 * hidden * vocabulary)
            self.assertEqual(s['logits_total_head_flops'], 2 * 9 * hidden * vocabulary)
            self.assertEqual(s['hidden_total_cache_io_bytes'], 4 * 9 * hidden * 2)

    def test_chunk_live_set_and_tail(self):
        s = teacher_cache.calculate(tokens=9, chunk_tokens=4, dtype='fp32')['summary']
        # Enumerate all token chunks, independently derive maximum live elements.
        chunks = [list(range(9))[start:start+4] for start in range(0, 9, 4)]
        live = [4 * (4096 * 151936 + len(c) * (4096 + 151936)) for c in chunks]
        self.assertEqual(s['head_live_tensor_bytes'], max(live))
        self.assertEqual(s['head_tail_tokens'], len(chunks[-1]))
        self.assertEqual(s['head_chunk_count'], len(chunks))
        self.assertEqual(teacher_cache.calculate(tokens=9, chunk_tokens=20)['summary']['head_tail_tokens'], 9)

    def test_exact_crossover_and_rejections(self):
        from fractions import Fraction
        # For r=2: equality when 3*(logits-hidden)/B = one head FLOPs/F.
        delta = 2 * (151936 - 4096)
        work = 2 * 4096 * 151936
        s = teacher_cache.calculate(tokens=1, replays=2,
                                   bandwidth_bytes_per_second=3*delta,
                                   head_flops_per_second=work)['summary']
        self.assertEqual(Fraction(s['serial_budget_difference_hidden_minus_logits_exact_seconds']), 0)
        self.assertFalse(s['hidden_serial_budget_is_lower'])
        for args in ({'tokens': 0}, {'replays': True}, {'dtype': 'fp8'}, {'model': 'unknown'}):
            with self.assertRaises(ValueError):
                teacher_cache.calculate(**args)
