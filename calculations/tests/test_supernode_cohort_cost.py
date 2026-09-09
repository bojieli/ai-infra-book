"""Hand-counted failure, capacity, deadline, and cost contract regressions."""
from fractions import Fraction
import unittest

from infra_calc.topics import supernode_cohort_cost as cohort


class CohortFailureBoundaryTests(unittest.TestCase):
    work = [('prefill', 101), ('decode', 37)]

    def run_schedule(self, requests=1, replicas=1, fault=3, recovery=4):
        return cohort.schedule(requests, replicas, [3, 2], self.work, fault, recovery)

    def test_nonfinal_stage_end_is_completed_work_but_request_restarts(self):
        result = self.run_schedule()
        failed, successful = result['attempts']
        self.assertEqual((failed['start_ms'], failed['end_ms']), (0, 3))
        self.assertTrue(failed['aborted'])
        self.assertEqual(failed['completed_stages'], [{'name': 'prefill', 'matrix_flops': 101}])
        self.assertIsNone(failed['partial_stage'])
        self.assertEqual(result['abandoned_completed_stage_matrix_flops'], 101)
        self.assertFalse(result['abandoned_partial_stage_work_unknown'])
        self.assertEqual((successful['start_ms'], successful['end_ms']), (7, 12))
        self.assertEqual(successful['completed_stage_matrix_flops'], 138)
        self.assertEqual(result['requests'][0]['attempts'], 2)

    def test_midstage_failure_does_not_invent_fractional_flops(self):
        result = self.run_schedule(fault=4)
        failed = result['attempts'][0]
        self.assertEqual(failed['partial_stage'], {'name': 'decode', 'elapsed_ms': 1, 'matrix_flops': None})
        self.assertEqual(result['abandoned_completed_stage_matrix_flops'], 101)
        self.assertTrue(result['abandoned_partial_stage_work_unknown'])
        self.assertEqual(result['requests'][0]['completion_ms'], 13)

    def test_final_completion_wins_failure_tie_without_restart(self):
        result = self.run_schedule(fault=5)
        self.assertEqual(len(result['attempts']), 1)
        self.assertEqual(result['requests'][0]['completion_ms'], 5)
        self.assertEqual(result['requests'][0]['attempts'], 1)
        self.assertFalse(result['fault_used'])
        self.assertEqual(result['abandoned_completed_stage_matrix_flops'], 0)

    def test_completion_tie_delays_queued_request_not_completed_request(self):
        result = self.run_schedule(requests=2, fault=5)
        self.assertEqual([r['completion_ms'] for r in result['requests']], [5, 14])
        self.assertEqual([r['attempts'] for r in result['requests']], [1, 1])
        self.assertEqual([r['start_ms'] for r in result['attempts']], [0, 9])
        self.assertTrue(result['fault_used'])
        self.assertFalse(any(a['aborted'] for a in result['attempts']))

    def test_other_replica_and_round_robin_queue_continue_during_recovery(self):
        result = self.run_schedule(requests=4, replicas=2)
        self.assertEqual([r['replica'] for r in result['requests']], [0, 1, 0, 1])
        self.assertEqual([r['completion_ms'] for r in result['requests']], [12, 5, 17, 10])
        self.assertEqual([r['latency_ms'] for r in result['requests']], [12, 5, 17, 10])
        self.assertEqual([r['attempts'] for r in result['requests']], [2, 1, 1, 1])
        self.assertEqual(result['horizon_ms'], 17)

    def test_failure_at_zero_has_no_spurious_abandoned_attempt(self):
        for recovery in (0, 4):
            with self.subTest(recovery=recovery):
                result = self.run_schedule(fault=0, recovery=recovery)
                self.assertTrue(result['fault_used'])
                self.assertEqual(len(result['attempts']), 1)
                self.assertEqual(result['attempts'][0]['start_ms'], recovery)
                self.assertEqual(result['requests'][0]['completion_ms'], recovery + 5)
                self.assertFalse(result['attempts'][0]['aborted'])


class CohortCapacityAndCostTests(unittest.TestCase):
    @staticmethod
    def candidates(result):
        return {row['tp']: row for row in result['candidates']}

    def test_capacity_failure_excludes_32b_tp2_before_scheduling_and_cost(self):
        result = cohort.calculate(model='qwen3-32b', deadline_ms=600)
        rows = self.candidates(result)
        rejected = rows[2]
        self.assertFalse(rejected['capacity_fits'])
        self.assertTrue(any(c['resident_bytes'] > 24_000_000_000 for c in rejected['placement_cards']))
        self.assertIsNone(rejected['schedule'])
        self.assertIsNone(rejected['cost'])
        self.assertIsNone(rejected['valid_requests'])
        self.assertFalse(rejected['slo_eligible'])
        self.assertNotIn(rejected['id'], result['selection']['eligible'])
        self.assertNotIn(rejected['id'], result['selection']['winners'])
        self.assertTrue(rows[4]['capacity_fits'])
        self.assertTrue(rows[8]['capacity_fits'])
        for row in rows.values():
            # P=256,G=8: prefill supplies first output, final KV length263.
            self.assertEqual(sum(c['kv_bytes'] for c in row['placement_cards']), row['replicas'] * 262144 * 263)

    def test_all_reserved_cards_horizon_and_external_fee_charged_once(self):
        result = cohort.calculate(requests=4, deadline_ms=250, fault_at_ms=50, recovery_ms=20, recovery_fee='1')
        rows = self.candidates(result)
        # TP8 requests finish132,194,256,318; TP4 finish170,100,270,200;
        # TP2 finish230,160,160,160. Every reservation still owns all8cards.
        for tp, horizon, valid, expected_total in ((8, 318, 2, Fraction(443, 125)),
                                                   (4, 270, 3, Fraction(79, 25)),
                                                   (2, 230, 4, Fraction(71, 25))):
            with self.subTest(tp=tp):
                row = rows[tp]
                cost = row['cost']
                self.assertEqual(row['schedule']['horizon_ms'], horizon)
                self.assertEqual(row['valid_requests'], valid)
                self.assertEqual(Fraction(cost['subtotals_exact']['steady_service']), Fraction(8 * horizon, 1000))
                self.assertEqual(Fraction(cost['subtotals_exact']['recovery_and_replay']), 1)
                for name, amount in cost['subtotals_exact'].items():
                    if name not in ('steady_service', 'recovery_and_replay'):
                        self.assertEqual(Fraction(amount), 0)
                self.assertEqual(Fraction(cost['full_declared_cost_exact']), expected_total)
                self.assertEqual(Fraction(cost['cost_per_slo_valid_request_exact']), expected_total / valid)
                self.assertFalse(cost['observed_or_measured'])
        self.assertEqual(result['selection']['required_valid_requests'], 3)
        self.assertFalse(rows[8]['slo_eligible'])
        self.assertTrue(rows[4]['slo_eligible'])
        self.assertEqual(result['selection']['winners'], ['tp2-replicas4'])
        self.assertEqual(Fraction(result['selection']['minimum_cost_per_valid_request_exact']), Fraction(71, 100))

    def test_deadline_equality_counts_and_denominator_excludes_late_responses(self):
        result = cohort.calculate(requests=4, deadline_ms=62)
        rows = self.candidates(result)
        self.assertEqual([r['completion_ms'] for r in rows[8]['schedule']['requests']], [62, 124, 186, 248])
        self.assertEqual(rows[8]['valid_requests'], 1)
        self.assertEqual(Fraction(rows[8]['cost']['cost_per_slo_valid_request_exact']), Fraction(248 * 8, 1000))
        self.assertEqual(rows[4]['valid_requests'], 0)
        self.assertIsNone(rows[4]['cost']['cost_per_slo_valid_request_exact'])
        self.assertEqual(result['selection']['eligible'], [])
        self.assertEqual(result['selection']['winners'], [])
        self.assertIsNone(result['selection']['minimum_cost_per_valid_request_exact'])

    def test_recovery_fee_not_charged_without_an_affected_workload(self):
        healthy = self.candidates(cohort.calculate(requests=1, recovery_fee='7/3'))
        late_fault = self.candidates(cohort.calculate(requests=1, fault_at_ms=1000, recovery_ms=400, recovery_fee='7/3'))
        for tp in (2, 4, 8):
            with self.subTest(tp=tp):
                self.assertFalse(late_fault[tp]['schedule']['fault_used'])
                self.assertEqual(healthy[tp]['cost'], late_fault[tp]['cost'])
                self.assertEqual(Fraction(late_fault[tp]['cost']['subtotals_exact']['recovery_and_replay']), 0)

    def test_fractional_slo_threshold_rounds_up(self):
        result = cohort.calculate(requests=3, deadline_ms=600, minimum_valid_fraction='3/4')
        self.assertEqual(result['selection']['required_valid_requests'], 3)
        result = cohort.calculate(requests=3, deadline_ms=600, minimum_valid_fraction='1/2')
        self.assertEqual(result['selection']['required_valid_requests'], 2)


if __name__ == '__main__':
    unittest.main()
