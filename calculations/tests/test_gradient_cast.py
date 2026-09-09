from fractions import Fraction as F
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from infra_calc.topics.gradient_cast import calculate


class GradientCastTests(unittest.TestCase):
    def test_independent_paths_and_buffers(self):
        r=calculate();n=12288*4096
        self.assertEqual(r['summary']['gradient_elements'],n)
        self.assertEqual(F(r['summary']['equal_time_link_bytes_per_second_exact']),F(250*10**9,7))
        self.assertEqual(r['summary']['fastest_fitting_buffers'],['cpu'])
        for p in r['gradient_cast_paths']:
            cpu=p['cast_location']=='cpu'
            expected=F(2*n if cpu else 4*n,32*10**9)+F(6*n,(100 if cpu else 1500)*10**9)
            self.assertEqual(F(p['ready_exact_seconds']),expected)
            for tier in ('host','gpu'):
                events=sorted({F(b[k]) for b in p['buffers'] for k in ('start_exact_seconds','end_exact_seconds')})
                peak=max(sum(b['bytes'] for b in p['buffers'] if b['tier']==tier and F(b['start_exact_seconds']) <= (a+z)/2 < F(b['end_exact_seconds'])) for a,z in zip(events,events[1:]))
                self.assertEqual(peak,p['host_peak_bytes' if tier=='host' else 'gpu_peak_including_common_bytes'])
        self.assertEqual([p['host_peak_bytes'] for p in r['gradient_cast_paths']],[288*1024**2,192*1024**2])

    def test_capacity_and_equality(self):
        fast=dict(link_bytes_per_second=300*10**9)
        self.assertEqual(calculate(**fast)['summary']['fastest_fitting_buffers'],['gpu'])
        self.assertEqual(calculate(**fast,extra_gpu_budget_bytes=192*1024**2-1)['summary']['fastest_fitting_buffers'],['cpu'])
        self.assertEqual(calculate(**fast,extra_gpu_budget_bytes=192*1024**2)['summary']['fastest_fitting_buffers'],['gpu'])
        self.assertEqual(calculate(**fast,host_budget_bytes=192*1024**2-1)['summary']['fastest_fitting_buffers'],[])
        # CPU/GPU 6 and 12 GB/s gives exact integer link crossover 4 GB/s.
        equal=calculate(cpu_cast_bytes_per_second=6*10**9,gpu_cast_bytes_per_second=12*10**9,link_bytes_per_second=4*10**9)
        self.assertEqual(equal['summary']['fastest_without_capacity'],['cpu','gpu'])

    def test_startups_and_expert_scope(self):
        r=calculate(gpu_cast_startup_ns=10**9)
        self.assertIsNone(r['summary']['equal_time_link_bytes_per_second_exact'])
        self.assertEqual(r['summary']['fastest_without_capacity'],['cpu'])
        moe=calculate(model='qwen3-235b-a22b')
        self.assertEqual(moe['summary']['gradient_elements'],1536*4096)
        for kw in ({'link_bytes_per_second':0},{'cpu_cast_startup_ns':-1},{'extra_gpu_budget_bytes':True}):
            with self.assertRaises(ValueError):calculate(**kw)
