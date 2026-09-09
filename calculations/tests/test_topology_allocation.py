"""Exact lifetime crossover, exhaustive independent placements and cut bounds."""
from fractions import Fraction
from itertools import combinations
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from infra_calc.topics.topology_allocation import calculate,pack_windows


class TopologyAllocationTests(unittest.TestCase):
    def test_ring_cost_and_integer_payback(self):
        for tokens,count in ((1024,256),(1,261580)):
            r=calculate(tokens=tokens);s=r['summary']
            self.assertEqual(s['per_rank_send_bytes'],14*tokens*1024)
            self.assertEqual(s['startup_ns'],70000)
            self.assertEqual(Fraction(s['before_exact_ns']),70000+Fraction(s['per_rank_send_bytes']*10**9,25*10**9))
            self.assertEqual(s['strictly_faster_calls'],count)
            saving=Fraction(s['saving_exact_ns'])
            self.assertGreater(count*saving,100000000)
            self.assertLessEqual((count-1)*saving,100000000)
        self.assertFalse(calculate(calls=255)['summary']['new_path_wins_within_lifetime'])
        self.assertTrue(calculate(calls=256)['summary']['new_path_wins_within_lifetime'])
        self.assertIsNone(calculate(new_bandwidth_bytes_per_second=25*10**9)['summary']['strictly_faster_calls'])

    def test_periodic_placement_independent_combinations(self):
        for free in (list(range(8)),list(range(16)),[r*4+c for r in range(4) for c in range(4) if (r+c)%2==0]):
            result=pack_windows(free)
            candidates=[set(w['cells']) for w in result['candidate_windows']]
            best=0
            for count in range(1,len(free)//4+1):
                if any(len(set().union(*group))==4*count for group in combinations(candidates,count)):best=count
            self.assertEqual(result['maximum_simultaneous_allocations'],best)
        self.assertEqual(len(pack_windows(range(8))['candidate_windows']),4)
        self.assertEqual(pack_windows(range(8))['maximum_simultaneous_allocations'],2)
        for dr in range(4):
            translated=[((r+dr)%4)*4+c for r in (0,1) for c in range(4)]
            self.assertEqual(pack_windows(translated)['maximum_simultaneous_allocations'],2)

    def test_directed_cut_and_input_bounds(self):
        s=calculate()['summary']
        self.assertEqual(s['cut_offered_bytes_per_second'],100*10**9)
        self.assertFalse(s['cut_demand_fits'])
        self.assertEqual(s['equal_flow_rate_upper_bytes_per_second'],12.5*10**9)
        self.assertEqual(s['full_rate_simultaneous_flows'],2)
        self.assertEqual(calculate(flows=1)['summary']['equal_flow_rate_upper_bytes_per_second'],25*10**9)
        with self.assertRaises(ValueError):pack_windows([16])
