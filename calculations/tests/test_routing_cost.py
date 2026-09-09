import sys
import unittest
from fractions import Fraction as F
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from infra_calc.topics.routing_cost import calculate


class RoutingCostTests(unittest.TestCase):
    def test_exact_book_crossover_and_deadline(self):
        r = calculate(b_hit_fraction='1291/1520')
        self.assertEqual(r['summary']['cost_crossover_b_hit_fraction_exact'], '1291/1520')
        self.assertEqual(r['routing_cost_rows'][0]['cost_per_quality_success_exact'],
                         r['routing_cost_rows'][1]['cost_per_quality_success_exact'])
        self.assertEqual(r['summary']['minimum_b_hit_for_joint_target_exact'], '45/49')
        self.assertFalse(r['summary']['b_meets_joint_target'])
        self.assertTrue(calculate(b_hit_fraction='45/49')['summary']['b_meets_joint_target'])

    def test_integer_cohort_keeps_failed_costs(self):
        r = calculate(tasks=10000, b_hit_fraction='1/2')
        b = r['routing_cost_rows'][1]
        # 5000 hits and 5000 misses; 4900 quality passes in each branch.
        bill = 5000*F(8200,10**6) + 5000*F(42400,10**6)
        self.assertEqual(F(b['total_cost_exact']), bill)
        self.assertEqual(F(b['cost_per_quality_success_exact']), bill/9800)
        self.assertEqual(F(b['cost_per_joint_success_exact']), bill/4900)
        self.assertEqual(b['billed_output_tokens'], 300)

    def test_deadline_boundaries(self):
        self.assertIsNone(calculate(deadline_seconds=3)['routing_cost_rows'][1]['cost_per_joint_success_exact'])
        self.assertEqual(calculate(deadline_seconds=12)['summary']['minimum_b_hit_for_joint_target_exact'], '0')
        self.assertEqual(calculate(deadline_seconds=10)['routing_cost_rows'][0]['joint_success_fraction_exact'], '4/5')
        for h in ('-1/2','3/2',0.5):
            with self.assertRaises(ValueError): calculate(b_hit_fraction=h)
