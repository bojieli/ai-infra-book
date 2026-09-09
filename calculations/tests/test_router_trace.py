import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from infra_calc.topics.router_trace import calculate,read_records


class RouterTraceTests(unittest.TestCase):
    def test_raw_hit_totals_and_actual_destinations(self):
        raw,_=read_records();requests=[json.loads(line) for line in raw['results/requests.jsonl'].splitlines()]
        for policy,expected in [('round_robin',13458),('cache_aware',16376),('power_of_two',13458)]:
            result=calculate(policy);s=result['summary']
            rows=[r for r in requests if r['policy']==policy]
            self.assertEqual(s['cached_tokens'],sum(r['response']['meta_info']['cached_tokens'] for r in rows))
            self.assertEqual(s['cached_tokens'],expected)
            self.assertEqual(s['prompt_tokens'],19556)
            self.assertEqual(s['replay_window_s'],rows[-1]['end_s']-rows[0]['start_s'])
        r=calculate()['router_request_rows']
        self.assertEqual({row['worker'] for row in r},{1})

    def test_saved_matrix_independent_prefix_formula(self):
        # Cached prefill positions omit backbone projection/MLP and causal pairs,
        # while both full and hit paths have the same one-position output head.
        r=calculate()
        total=0
        h,f,l,q,d,kv=4096,12288,36,32,128,8
        linear_per_token=l*2*(h*(q*d+2*kv*d)+q*d*h+3*h*f)
        for row in r['router_request_rows']:
            cached=row['cached_tokens']
            saving=cached*linear_per_token+4*l*q*d*(cached*(cached+1)//2)
            self.assertEqual(row['full_matrix_flops']-row['executed_logical_matrix_flops'],saving)
            total+=saving
        self.assertEqual(total,r['summary']['saved_matrix_flops'])

    def test_unavailable_prefix_rejected(self):
        raw,sources=read_records();rows=[json.loads(line) for line in raw['results/requests.jsonl'].splitlines()]
        rows[0]['response']['meta_info']['cached_tokens']=1
        raw['results/requests.jsonl']='\n'.join(json.dumps(row) for row in rows)
        with patch('infra_calc.topics.router_trace.read_records',return_value=(raw,sources)):
            with self.assertRaisesRegex(ValueError,'completed same-worker prefix'):calculate()
