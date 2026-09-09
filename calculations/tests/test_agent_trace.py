"""Recorded cohort checks and serial-path conservation for Agent imports."""
import sys
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from infra_calc.topics.agent_trace import calculate, read_trace


class AgentTraceTests(unittest.TestCase):
    def test_pinned_observed_counts_and_quality(self):
        off=calculate()['summary']; on=calculate(trace='thinking-on')['summary']
        self.assertEqual((off['turns'],off['input_tokens'],off['cached_input_tokens'],off['output_tokens']), (12,19556,16304,765))
        self.assertEqual((on['turns'],on['output_tokens']), (4,2733))
        self.assertEqual((off['value_and_input_passed'],on['value_and_input_passed']), (315,1013))
        self.assertEqual((off['including_alias_check_passed'],on['including_alias_check_passed']), (1,710))
        self.assertLess(on['cached_prefill_matrix_flops'],on['cold_prefill_matrix_flops'])
        self.assertIsNone(on['actual_cache_peak_bytes'])

    def test_replacement_preserves_all_unselected_time(self):
        original=calculate(trace='thinking-on')
        replaced=calculate(trace='thinking-on',model_speedup=2,selected_turn=0)
        old=original['summary']; new=replaced['summary']
        self.assertAlmostEqual(old['measured_elapsed_seconds']-new['counterfactual_elapsed_seconds'],original['agent_rounds'][0]['measured_model_seconds']/2)
        self.assertAlmostEqual(old['measured_elapsed_seconds'],old['measured_model_seconds']+old['measured_tool_seconds']+old['measured_other_seconds'])
        self.assertAlmostEqual(old['counterfactual_elapsed_seconds'],old['measured_elapsed_seconds'])
        self.assertEqual(original['agent_rounds'][0]['finish_reason'],'length')
        for a,b in zip(original['agent_rounds'][1:],replaced['agent_rounds'][1:]): self.assertEqual(a,b)
        with self.assertRaises(ValueError): calculate(selected_turn=12)

    def test_input_copies_match_declared_origins(self):
        import hashlib
        book=Path(__file__).resolve().parents[2]
        for mode in ('thinking-off','thinking-on'):
            _,records=read_trace(mode)
            for record in records:
                self.assertEqual(hashlib.sha256((book/record['origin']).read_bytes()).hexdigest(),record['sha256'])
