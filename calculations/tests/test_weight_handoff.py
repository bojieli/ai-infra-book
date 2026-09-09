import sys
import unittest
from fractions import Fraction
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from infra_calc.topics.weight_handoff import calculate


class WeightHandoffTests(unittest.TestCase):
    def test_official_expert_geometry_and_uneven_ownership(self):
        r = calculate(expert_parallel=7, replicas=3)
        s = r['summary']
        self.assertEqual(s['expert_bf16_weight_bytes'], 94 * 128 * 3 * 4096 * 1536 * 2)
        owners = [e for row in r['weight_handoff_ranks'] for e in range(row['expert_start'], row['expert_stop'])]
        self.assertEqual(owners, list(range(128)))
        self.assertEqual(s['selective_unicast_egress_bytes'], 3 * (s['expert_bf16_weight_bytes'] + 7*s['nonexpert_bf16_weight_bytes']))
        self.assertEqual(s['full_unicast_egress_bytes'], 21*s['total_bf16_weight_bytes'])

    def test_phase_schedule_capacity_boundary(self):
        r = calculate(model='qwen3-8b', expert_parallel=1)
        s = r['summary']; weight = 8190735360 * 2
        self.assertEqual(s['phase_live_bytes']['restore_all_before_release'], 68*1024**3+weight)
        self.assertEqual(s['staged_peak_bytes'], 44*1024**3+weight)
        self.assertTrue(s['staged_allocations_fit'])
        self.assertFalse(s['restore_all_allocations_fit'])
        self.assertFalse(calculate(model='qwen3-8b', expert_parallel=1, capacity_bytes=s['staged_peak_bytes']-1)['summary']['staged_allocations_fit'])
        self.assertTrue(calculate(model='qwen3-8b', expert_parallel=1, capacity_bytes=s['staged_peak_bytes'])['summary']['staged_allocations_fit'])

    def test_independent_link_bounds_and_bad_scope(self):
        for producer, receiver in ((1, 10**12), (10**12, 1)):
            r = calculate(producer_bytes_per_second=producer, receiver_bytes_per_second=receiver)
            for row in r['weight_handoff_transfers']:
                bound = Fraction(row['transfer_bound_exact_seconds'])
                self.assertEqual(bound, max(Fraction(row['producer_egress_bytes'], producer), Fraction(row['largest_receiver_bytes'], receiver)))
        for args in ({'expert_parallel':129}, {'model':'qwen3-8b'}, {'replicas':0}):
            with self.assertRaises(ValueError): calculate(**args)
