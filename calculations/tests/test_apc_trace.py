"""Raw hit denominators, preserved suffix work and replay-time partition."""
from fractions import Fraction
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from infra_calc.topics.apc_trace import calculate,read_records
from infra_calc.models import forward
from infra_calc.schema import Scenario


class ApcTraceTests(unittest.TestCase):
    def test_recorded_denominators_and_off_conditions(self):
        for name in ('cache6','gap6','pressure6'):
            r=calculate(name);s=r['summary']
            self.assertEqual(s['input_tokens'],19556)
            self.assertEqual(s['cached_tokens'],16304)
            self.assertEqual(s['request_hit_fraction_exact'],'11/12')
            self.assertEqual(Fraction(s['token_weighted_hit_fraction_exact']),Fraction(16304,19556))
            self.assertEqual(s['saved_matrix_flops'],236125039362048)
            self.assertNotEqual(s['token_weighted_hit_fraction_exact'],s['mean_per_request_cached_fraction_exact'])
        for name in ('pressure1','nocache6'):
            s=calculate(name)['summary']
            self.assertEqual(s['cached_tokens'],0)
            self.assertEqual(s['saved_matrix_flops'],0)

    def test_saved_work_identity_and_replay_partition(self):
        r=calculate('pressure6')
        for row in r['apc_rounds']:
            if row['cached_tokens']:
                expected=forward('qwen3-8b',Scenario(tokens=row['cached_tokens'],output_head='none'))['summary']['matrix_flops']
                self.assertEqual(row['saved_matrix_flops'],expected)
            self.assertGreater(row['hit_matrix_flops'],0)
        s=r['summary']
        self.assertAlmostEqual(s['agent_request_wall_s']+s['pressure_request_wall_s']+s['between_requests_s'],s['replay_elapsed_s'])
        self.assertGreater(s['pressure_request_wall_s'],s['agent_request_wall_s'])
        self.assertGreater(calculate('gap6')['summary']['between_requests_s'],2.2)

    def test_prompt_and_output_corruption_rejected(self):
        records,sources=read_records()
        records['results/cache6/requests.jsonl'][0]['prompt_sha256']='bad'
        with patch('infra_calc.topics.apc_trace.read_records',return_value=(records,sources)):
            with self.assertRaises(ValueError):calculate()
        with self.assertRaises(ValueError):calculate('missing')
