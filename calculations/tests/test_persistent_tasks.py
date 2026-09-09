"""Task accounting, independent pipeline formula and live interval enumeration."""
from fractions import Fraction
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from infra_calc.topics.persistent_tasks import calculate


class PersistentTaskTests(unittest.TestCase):
    def test_uniform_pipeline_closed_form(self):
        r=calculate();s=r['summary']
        p=Fraction(2*64*4096*12288*10**9,200*10**12)+700
        c=Fraction(64*12288*10**9,20*10**9)+700
        expected=5000+p+c+7*max(p,c)
        self.assertEqual(Fraction(s['persistent_finish_exact_ns']),expected)
        self.assertEqual(s['persistent_device_tasks'],16)
        self.assertEqual(s['completion_event_publications'],16)
        self.assertEqual(s['intertask_dependency_edges'],8)
        self.assertEqual(s['intermediate_write_read_bytes'],24*2**20)
        self.assertEqual(s['persistent_intermediate_live_peak_bytes'],6*2**20)
        slow=calculate(task_dispatch_ns=50000)['summary']
        self.assertGreater(slow['persistent_finish_ns'],slow['barrier_finish_ns'])

    def test_tail_dependencies_and_peak(self):
        r=calculate(tokens=513);rows=r['persistent_tiles'];s=r['summary']
        self.assertEqual(rows[-1]['rows'],1)
        self.assertEqual(sum(x['matrix_flops'] for x in rows),2*513*4096*12288)
        self.assertEqual(s['persistent_device_tasks'],18)
        intervals=[];previous_p=previous_c=0
        for row in rows:
            t={k:Fraction(v) for k,v in row['exact_ns'].items()}
            self.assertGreaterEqual(t['producer_start'],previous_p)
            self.assertGreaterEqual(t['consumer_start'],previous_c)
            self.assertGreaterEqual(t['consumer_start'],t['producer_ready'])
            previous_p=t['producer_ready'];previous_c=t['consumer_done']
            intervals.append((t['producer_start'],t['consumer_done'],row['intermediate_bytes']))
        boundaries=sorted({v for a,b,size in intervals for v in (a,b)})
        sampled=max(sum(size for a,b,size in intervals if a <= (x+y)/2 < b) for x,y in zip(boundaries,boundaries[1:]))
        self.assertEqual(sampled,s['persistent_intermediate_live_peak_bytes'])

    def test_no_overlap_one_tile_and_zero_overhead(self):
        s=calculate(tile_rows=512)['summary']
        self.assertEqual(Fraction(s['barrier_finish_exact_ns'])-Fraction(s['persistent_finish_exact_ns']),3600)
        s=calculate(tile_rows=512,host_launch_ns=0,task_dispatch_ns=0,event_publish_ns=0)['summary']
        self.assertEqual(s['barrier_finish_exact_ns'],s['persistent_finish_exact_ns'])
        with self.assertRaises(ValueError):calculate(tile_rows=0)
