"""Independent request work, scheduling identities and resource boundaries."""
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from infra_calc.topics.iteration_batching import calculate,POLICIES,DEFAULT_REQUESTS
from infra_calc.models import forward
from infra_calc.schema import Scenario


class IterationBatchingTests(unittest.TestCase):
    def test_per_request_work_and_history_conservation(self):
        expected=0
        for request in DEFAULT_REQUESTS:
            p,g=request['prompt_tokens'],request['output_tokens']
            expected+=forward('qwen3-8b',Scenario(tokens=p))['summary']['matrix_flops']
            expected+=sum(forward('qwen3-8b',Scenario(tokens=1,history=p+i))['summary']['matrix_flops'] for i in range(g-1))
        for policy in POLICIES:
            r=calculate(policy=policy)
            self.assertEqual(r['summary']['total_matrix_flops'],expected)
            self.assertEqual(r['summary']['total_scheduled_tokens'],188)
            for req in r['batching_requests']:
                self.assertEqual(req['computed'],req['prompt_tokens']+req['output_tokens']-1)
                self.assertEqual(len(req['delivery_ns']),req['output_tokens'])
                plans=[p for step in r['batching_steps'] for p in step['plans'] if p['request']==req['id']]
                cursor=0
                for p in plans:
                    self.assertEqual(p['history_tokens'],cursor);cursor+=p['new_tokens']

    def test_refill_timing_and_chunk_budget(self):
        fixed=calculate(policy='fixed');continuous=calculate(policy='continuous');chunked=calculate()
        f={r['id']:r for r in fixed['batching_requests']};c={r['id']:r for r in continuous['batching_requests']}
        self.assertEqual(f['r2']['admitted_ns'],max(f['r0']['finish_ns'],f['r1']['finish_ns']))
        self.assertEqual(c['r2']['admitted_ns'],c['r1']['finish_ns'])
        self.assertLess(chunked['summary']['max_itl_ns'],continuous['summary']['max_itl_ns'])
        for step in chunked['batching_steps']:
            self.assertLessEqual(step['new_tokens'],32)
            for p in step['plans']:
                self.assertLessEqual(p['new_tokens'],16 if p['phase']=='prefill' else 1)

    def test_single_request_clock_and_capacity(self):
        req=[dict(id='one',arrival_ns=123,prompt_tokens=3,output_tokens=4)]
        for policy in POLICIES:
            r=calculate(policy=policy,requests=req,step_base_ns=10,per_new_token_ns=2,per_causal_pair_ns=3)
            # One 3-token prefill then 3 decodes: 6 input positions, all
            # 6*7/2 causal pairs, four invocation base costs.
            self.assertEqual(r['summary']['finish_ns'],123+4*10+6*2+21*3)
        cap=20*1024**2;r=calculate(kv_capacity_bytes=cap)
        self.assertLessEqual(r['summary']['peak_reserved_kv_bytes'],cap)
        self.assertLessEqual(r['summary']['peak_live_kv_bytes'],r['summary']['peak_reserved_kv_bytes'])
        for step in r['batching_steps']:
            self.assertLessEqual(step['live_kv_bytes_during_step'],cap)
        with self.assertRaises(ValueError):calculate(kv_capacity_bytes=1)
        with self.assertRaises(ValueError):calculate(token_budget=1,max_sequences=2)
