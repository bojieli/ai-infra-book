import sys
import unittest
from fractions import Fraction as F
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from infra_calc.topics.retry_paths import calculate, default_nodes


class RetryPathTests(unittest.TestCase):
    def test_independent_reach_and_terminal_probabilities(self):
        r=calculate();s=r['summary']
        self.assertEqual(F(s['success_probability_exact']), F(4,5)+F(3,25)*F(3,5)+(F(2,25)+F(3,25)*F(2,5))*F(49,50))
        self.assertEqual(F(s['quality_and_deadline_probability_exact']), F(4,5)+F(3,25)*F(3,5)+F(2,25)*F(49,50))
        self.assertEqual(F(s['expected_resources_per_submission']['cost']), F(1,100)+F(3,25)*F(3,500)+F(16,125)*F(3,100))
        self.assertEqual(F(s['expected_resources_per_submission']['resident_byte_seconds']), 2*1024**3*F(s['expected_resources_per_submission']['seconds']))

    def test_exhaustive_integer_cohort_keeps_all_costs(self):
        # Expand 12500 independent submissions into exact terminal counts.
        counts=[10000,900,588,12,980,20]
        costs=[F(1,100),F(16,1000),F(46,1000),F(46,1000),F(4,100),F(4,100)]
        r=calculate(submitted_tasks=12500);s=r['summary']
        bill=sum(n*c for n,c in zip(counts,costs))
        self.assertEqual(F(s['total_expected_cost_exact']), bill)
        self.assertEqual(F(s['cost_per_quality_success_exact']),bill/(12500-32))
        self.assertEqual(F(s['cost_per_quality_and_deadline_success_exact']),bill/(10000+900+980))

    def test_absorbing_failure_and_invalid_graphs(self):
        nodes=[dict(id='x',cost=1,seconds=2,cpu_seconds=1,resident_bytes=0,outcomes=[dict(probability=1,target='failure')])]
        self.assertIsNone(calculate(nodes=nodes,start='x')['summary']['cost_per_quality_success_exact'])
        nodes[0]['outcomes'][0]['target']='x'
        with self.assertRaises(ValueError):calculate(nodes=nodes,start='x')
        nodes=default_nodes();nodes[0]['outcomes'][0]['probability']='1/2'
        with self.assertRaises(ValueError):calculate(nodes=nodes)
