"""Barrier timing and expanded-sample quantile checks."""
from fractions import Fraction
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from infra_calc.topics.collective_tail import calculate


class CollectiveTailTests(unittest.TestCase):
    def test_book_and_common_ready_origin(self):
        result=calculate();s=result['summary']
        self.assertEqual(s['payload_bytes_per_rank'],8388608)
        self.assertEqual(s['baseline_mean_exact_ns'],'2400000')
        self.assertEqual(s['faster_exchange_mean_exact_ns'],'2200000')
        self.assertEqual(s['aligned_ready_mean_exact_ns'],'400000')
        self.assertEqual(result['collective_observations'][0]['rank_wait_ns'],[2000000]*3+[0])
        row=dict(name='offset',count=1,ready_ns=[100,100,100,200],exchange_ns=5,recovery_ns=7)
        r=calculate(observations=[row],exchange_speedup=3,post_compute_ns=11)
        self.assertEqual(r['summary']['aligned_ready_mean_exact_ns'],'123')
        self.assertEqual(Fraction(r['summary']['faster_exchange_mean_exact_ns']),Fraction(659,3))

    def test_weighted_quantiles_by_expansion(self):
        for normal_count,fault_count in ((98,1),(97,2),(1,1)):
            rows=[dict(count=normal_count,ready_ns=[0,0],exchange_ns=400000,recovery_ns=0),
                  dict(count=1,ready_ns=[0,2000000],exchange_ns=400000,recovery_ns=0),
                  dict(count=fault_count,ready_ns=[0,0],exchange_ns=400000,recovery_ns=10000000)]
            r=calculate(observations=rows)
            for policy in r['completion_policies']:
                expanded=sorted(Fraction(row[policy['policy']+'_exact_ns']) for row in r['collective_observations'] for _ in range(row['count']))
                self.assertEqual(Fraction(policy['mean_exact_ns']),sum(expanded)/len(expanded))
                self.assertEqual(Fraction(policy['p99_exact_ns']),expanded[(99*len(expanded)+99)//100-1])
                self.assertEqual(Fraction(policy['p50_exact_ns']),expanded[(50*len(expanded)+99)//100-1])
            expected=2400000 if fault_count==1 and normal_count==98 else 10400000
            self.assertEqual(int(r['summary']['baseline_p99_exact_ns']),expected)

    def test_joint_tail_not_sum_of_marginals(self):
        rows=[dict(count=1,ready_ns=[0,100],exchange_ns=1,recovery_ns=0),
              dict(count=1,ready_ns=[0,0],exchange_ns=1,recovery_ns=100)]
        s=calculate(observations=rows)['summary']
        self.assertEqual(s['baseline_p99_exact_ns'],'101')
        for bad in ([],[dict(rows[0],count=0)],[rows[0],dict(rows[1],ready_ns=[0])]):
            with self.assertRaises(ValueError):calculate(observations=bad)
