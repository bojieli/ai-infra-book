"""Independent message enumeration and official GQA geometry checks."""
from fractions import Fraction as F
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from infra_calc.topics.pd_af_handoff import calculate


class HandoffTests(unittest.TestCase):
    def test_book_and_startup_boundary(self):
        result=calculate(startup_ns=0)
        s=result['summary']
        self.assertEqual(s['pd_snapshot_bytes'],1024**3)
        self.assertEqual(s['af_total_bytes'],512*1024)
        self.assertEqual(s['af_directional_messages'],64)
        self.assertEqual(F(s['pd_serialized_ns_exact']),F(1024**3,25))
        boundary=F(s['equal_time_startup_ns_exact'])
        for latency in (int(boundary),int(boundary)+1):
            r=calculate(startup_ns=latency)['summary']
            self.assertEqual(r['af_faster_at_selected_startup'],latency<boundary)

    def test_hops_enumerated_and_buffers(self):
        for path in ('direct','host-staged'):
            r=calculate(path=path,length=7,batch=3,decode_steps=2,
                        network_bandwidth=19*10**9,staging_bandwidth=31*10**9)
            for case in r['handoff_cases']:
                messages=[case['smallest_message_bytes']+(i<case['larger_messages'])
                          for i in range(case['messages'])]
                self.assertEqual(sum(messages),case['payload_bytes'])
                bandwidths=[19*10**9] if path=='direct' else [31*10**9,19*10**9,31*10**9]
                time=sum((5000+F(size*10**9,bw) for size in messages for bw in bandwidths),F(0))
                self.assertEqual(time,F(case['serialized_ns_exact']))
            self.assertEqual(F(r['summary']['byte_matched_extra_ns_exact']),
                             (128-1)*5000*len(bandwidths))
            buffers=r['endpoint_buffers']['pd']
            self.assertEqual(buffers['source_gpu_live_bytes'],r['summary']['pd_snapshot_bytes'])
            self.assertEqual(buffers['source_host_staging_bytes'],
                             r['summary']['pd_snapshot_bytes'] if path=='host-staged' else 0)

    def test_official_models_and_invalid_boundaries(self):
        for model,layers,kv_heads in [('qwen3-8b',36,8),('qwen3-235b-a22b',94,4)]:
            s=calculate(model=model,batch=4,decode_steps=3)['summary']
            self.assertEqual(s['pd_snapshot_bytes'],4*8192*2*layers*kv_heads*128*2)
            self.assertEqual(s['af_total_bytes'],4*4096*2*2*layers*3)
        for args in ({'model':'kimi-k3'},{'element_bytes':3},{'startup_ns':-1},{'batch':True}):
            with self.assertRaises(ValueError):calculate(**args)
