"""Official backbone matrix identity and restoration deadline boundaries."""
from fractions import Fraction
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from infra_calc.topics.kv_restore import calculate
from infra_calc.sources import model_config


class KvRestoreTests(unittest.TestCase):
    def test_backbone_matrix_work_and_payload(self):
        c=model_config('qwen3-8b');n=1024;h=c['hidden_size'];d=c['head_dim'];q=c['num_attention_heads'];kv=c['num_key_value_heads'];f=c['intermediate_size'];layers=c['num_hidden_layers']
        linear=layers*(2*n*h*(q*d+2*kv*d)+2*n*q*d*h+6*n*h*f)
        attention=4*layers*q*d*(n*(n+1)//2)
        s=calculate()['summary']
        self.assertEqual(s['replay_backbone_matrix_flops'],linear+attention)
        self.assertEqual(s['kv_snapshot_bytes'],4*layers*kv*d*n)
        self.assertEqual(s['input_token_id_bytes'],4096)
        self.assertEqual(s['replay_new_kv_write_bytes'],s['kv_snapshot_bytes'])

    def test_deadline_and_released_capacity_area(self):
        for deadline in (0,5000000,20000000,100000000):
            r=calculate(next_use_ns=deadline);s=r['summary'];rows={row['policy']:row for row in r['restore_policies']}
            trip=Fraction(s['offload_exact_ns'])+Fraction(s['restore_exact_ns'])
            self.assertEqual(Fraction(rows['offload_prefetch']['stall_exact_ns']),max(0,trip-deadline))
            self.assertEqual(Fraction(rows['offload_prefetch']['kv_free_interval_exact_ns']),max(0,deadline-trip))
            self.assertEqual(Fraction(rows['drop_recompute']['stall_exact_ns']),max(0,50000000-deadline))
            self.assertEqual(Fraction(rows['drop_recompute']['released_byte_ns_exact']),s['kv_snapshot_bytes']*max(0,deadline-50000000))
        # Set a transfer with an integer exact round trip to test equality.
        base=calculate(offload_bandwidth=10**9,restore_bandwidth=10**9)
        deadline=int(Fraction(base['summary']['offload_exact_ns'])*2)
        equal=calculate(offload_bandwidth=10**9,restore_bandwidth=10**9,next_use_ns=deadline)
        self.assertEqual(equal['summary']['offload_return_stall_exact_ns'],'0')
        self.assertEqual(equal['restore_policies'][1]['kv_free_interval_exact_ns'],'0')

    def test_host_capacity_and_short_window(self):
        size=calculate()['summary']['kv_snapshot_bytes']
        self.assertTrue(calculate(host_capacity_bytes=size)['summary']['host_snapshot_fits'])
        r=calculate(host_capacity_bytes=size-1)
        self.assertFalse(r['restore_policies'][1]['feasible'])
        with self.assertRaises(ValueError):calculate(recompute_ns=0)
