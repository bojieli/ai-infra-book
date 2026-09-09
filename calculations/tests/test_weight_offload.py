"""Independent closed-form transfer schedules and safe buffer lifetimes."""
from fractions import Fraction as F
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from infra_calc.topics.weight_offload import calculate


class WeightOffloadTests(unittest.TestCase):
    def test_byte_geometry_and_amortization(self):
        a=calculate()['summary'];b=calculate(buffer_slots=2)['summary']
        self.assertEqual(a['ffn_bytes_per_layer'],3*4096*12288*2)
        self.assertEqual(a['net_gpu_weight_bytes_saved'],2*8192*36*8*128*2*2)
        self.assertEqual(a['equivalent_independent_kv_requests'],2)
        self.assertEqual(b['equivalent_independent_kv_requests'],1)
        self.assertEqual(calculate(batch=4)['summary']['per_forward_h2d_bytes'],a['per_forward_h2d_bytes'])
        self.assertEqual(F(calculate(tokens=2048,history=0)['summary']['copy_service_per_input_token_ns_exact'])*2048,F(a['per_forward_copy_service_ns_exact']))

    def test_independent_slow_and_fast_link_formulas(self):
        copy=F(288*2**20*10**9,24*2**30)
        self.assertEqual(F(calculate()['summary']['scheduled_finish_ns_exact']),9*(copy+1000000))
        self.assertEqual(F(calculate(buffer_slots=2)['summary']['scheduled_finish_ns_exact']),9*copy+1000000)
        fast=calculate(bandwidth_bytes_per_second=384*2**30)
        self.assertEqual(F(fast['summary']['scheduled_finish_ns_exact']),36*1000000)

    def test_copy_and_slot_lifetimes_across_wrap(self):
        for slots in (1,2,3):
            r=calculate(buffer_slots=slots,passes=2);free={};last_copy=F(0)
            for row in r['offload_copies']:
                start,end=F(row['copy_start_ns_exact']),F(row['copy_end_ns_exact'])
                use,release=F(row['consume_start_ns_exact']),F(row['consume_end_ns_exact'])
                self.assertGreaterEqual(start,last_copy)
                self.assertGreaterEqual(start,free.get(row['slot'],0))
                self.assertGreaterEqual(use,end)
                free[row['slot']]=release;last_copy=end
            self.assertEqual(sum(row['bytes'] for row in r['offload_copies']),r['summary']['total_h2d_bytes'])
        with self.assertRaises(ValueError):calculate(offloaded_layers=[36])
