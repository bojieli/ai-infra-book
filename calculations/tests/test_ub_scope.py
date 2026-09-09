import unittest
import sys
from fractions import Fraction
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from infra_calc.topics.ub_scope import calculate


class UBScopeTests(unittest.TestCase):
    def test_eight_physical_cards_same_requests_final_state(self):
        r=calculate(decode_steps=3)
        for candidate in r['scope_candidates']:
            cards=candidate['placement_cards']
            self.assertEqual(len(cards),8)
            self.assertEqual({c['physical_card'] for c in cards},set(range(8)))
            self.assertEqual(candidate['summary']['final_cache_positions'],8195)
            for c in cards:
                self.assertEqual(c['resident_bytes'],c['weight_bytes']+c['kv_bytes']+c['workspace_bytes'])
            self.assertEqual(len({c['server'] for c in cards}),candidate['servers'])
        # Equal logical model parameters, no accidental DP demand duplication.
        a,b=r['scope_candidates']
        self.assertEqual(a['placement_summary']['logical_parameters_per_replica'],b['placement_summary']['logical_parameters_per_replica'])
        self.assertEqual(a['placement_summary']['global_requests'],b['placement_summary']['global_requests'])

    def test_shared_nic_replica_bytes_and_feedback_executions(self):
        r=calculate(batch=2,decode_steps=7)
        cross=r['scope_candidates'][1]
        remote=[x for x in cross['handoff_operations'] if x['interface']=='shared_interserver_egress']
        self.assertEqual(len(remote),2)
        hidden,token=remote
        self.assertEqual(hidden['charged_resource_bytes_per_forward'],4*2*2*5120)
        self.assertEqual(token['charged_resource_bytes_per_forward'],2*4)
        self.assertEqual(hidden['network_send_bytes_all_forwards'],hidden['network_send_bytes_per_forward']*7)
        self.assertEqual(hidden['startup_rounds_all_forwards'],7)
        names={x['name'] for x in cross['handoff_operations']}
        self.assertTrue({'vocabulary_embedding_reduce','last_position_logits_all_gather','selected_token_first_stage_broadcast'}<=names)

    def test_exact_bandwidth_tie_and_two_sides(self):
        r=calculate();threshold=Fraction(r['scope_crossover']['remote_bandwidth_threshold_bytes_per_second_exact'])
        self.assertEqual(calculate(remote_bytes_per_second=str(threshold))['scope_crossover']['communication_only_preference'],'tie')
        self.assertEqual(calculate(remote_bytes_per_second=str(threshold/2))['scope_crossover']['communication_only_preference'],'single_server_tp8')
        self.assertEqual(calculate(remote_bytes_per_second=str(threshold*2))['scope_crossover']['communication_only_preference'],'two_servers_tp4_pp2')
        blocked=calculate(remote_startup_ns=10_000_000)
        self.assertIsNone(blocked['scope_crossover']['remote_bandwidth_threshold_bytes_per_second_exact'])

    def test_startup_crossover_and_card_capacity_are_independent(self):
        r=calculate();ns=Fraction(r['scope_crossover']['remote_startup_threshold_seconds_exact'])*10**9
        self.assertEqual(calculate(remote_startup_ns=ns.numerator//ns.denominator)['scope_crossover']['communication_only_preference'],'two_servers_tp4_pp2')
        self.assertEqual(calculate(remote_startup_ns=ns.numerator//ns.denominator+1)['scope_crossover']['communication_only_preference'],'single_server_tp8')
        boundary=r['scope_candidates'][1]['summary']['maximum_card_resident_bytes']
        small=calculate(capacity_bytes=boundary)
        self.assertFalse(small['scope_candidates'][0]['summary']['all_cards_fit'])
        self.assertTrue(small['scope_candidates'][1]['summary']['all_cards_fit'])
        self.assertFalse(small['scope_crossover']['both_capacity_feasible'])

    def test_no_iteration_prediction_and_invalid_inputs(self):
        r=calculate()
        for c in r['scope_candidates']:self.assertIsNone(c['summary']['predicted_iteration_seconds'])
        self.assertIn('a-story-of-unified-bus',r['historical_sources'][0]['url'])
        for args in [dict(decode_steps=0),dict(batch=True),dict(remote_bytes_per_second=0),dict(local_startup_ns=-1)]:
            with self.assertRaises(ValueError):calculate(**args)


if __name__=='__main__':unittest.main()
