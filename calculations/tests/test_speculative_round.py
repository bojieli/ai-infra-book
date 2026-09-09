"""Round weighting, target KV rollback and all-accepted matrix identity."""
from fractions import Fraction
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from infra_calc.topics.speculative_round import calculate


class SpeculativeRoundTests(unittest.TestCase):
    def test_book_counts_and_time_denominator(self):
        r=calculate();s=r['summary']
        self.assertEqual(s['accepted_draft_tokens'],25)
        self.assertEqual(s['draft_acceptance_fraction_exact'],'5/8')
        self.assertEqual(s['delivered_tokens'],35)
        self.assertEqual(s['mean_delivered_tokens_exact'],'7/2')
        expanded=[row for row in r['speculative_outcomes'] for _ in range(row['count'])]
        time=sum(row['round_ns'] for row in expanded)
        outputs=sum(row['delivered_tokens'] for row in expanded)
        self.assertEqual(Fraction(s['time_per_delivered_token_exact_ns']),Fraction(time,outputs))
        self.assertEqual(s['unweighted_round_time_per_token_exact_ns'],'62000')
        self.assertEqual(s['matched_time_speedup_exact'],'7/6')

    def test_output_limit_and_state_partition(self):
        for limit in (None,1,2,5):
            r=calculate(remaining_output_tokens=limit);s=r['summary']
            for row in r['speculative_outcomes']:
                self.assertEqual(row['target_new_kv_kept_bytes']+row['target_new_kv_discarded_bytes'],s['target_verify_new_kv_bytes'])
                self.assertEqual(row['target_new_kv_kept_bytes'],row['delivered_tokens']*144*1024)
                self.assertLessEqual(row['target_final_kv_bytes'],s['target_peak_kv_bytes'])
            self.assertEqual(s['target_verify_matrix_flops_per_round'],78709719040)
        limited=calculate(remaining_output_tokens=1)['summary']
        self.assertEqual(limited['delivered_tokens'],10)
        self.assertEqual(limited['matched_time_speedup_exact'],'1/3')
        self.assertEqual(limited['accepted_draft_tokens'],25)

    def test_full_accept_matrix_identity_and_no_accept(self):
        for history in (0,1024):
            s=calculate(history=history,accepted_counts=[0,0,0,0,10])['summary']
            self.assertEqual(s['target_verify_matrix_flops_total'],s['matched_serial_matrix_flops_total'])
            self.assertEqual(s['total_discarded_target_kv_bytes'],0)
        none=calculate(accepted_counts=[10,0,0,0,0])['summary']
        self.assertEqual(none['mean_delivered_tokens_exact'],'1')
        self.assertEqual(none['total_discarded_target_kv_bytes'],40*144*1024)
        with self.assertRaises(ValueError):calculate(accepted_counts=[0]*5)
        with self.assertRaises(ValueError):calculate(accepted_counts=[1])
