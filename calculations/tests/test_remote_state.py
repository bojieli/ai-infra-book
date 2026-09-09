"""Frozen KV shape, exact amortization boundary and capacity feasibility."""
from fractions import Fraction
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from infra_calc.topics.remote_state import calculate
from infra_calc.sources import model_config


class RemoteStateTests(unittest.TestCase):
    def test_shape_and_independent_serial_costs(self):
        c=model_config('qwen3-8b');size=2*c['num_hidden_layers']*c['num_key_value_heads']*c['head_dim']*2*1024
        s=calculate()['summary']
        self.assertEqual(size,144*1024**2)
        self.assertEqual(s['snapshot_payload_bytes'],size)
        remote=5000+Fraction(size*10**9,40*10**9)
        setup=10000+Fraction(size*10**9,25*10**9)+Fraction(size*10**9,10**12)
        local=1000+Fraction(size*10**9,10**12)
        self.assertEqual(Fraction(s['direct_total_exact_ns']),4*remote)
        self.assertEqual(Fraction(s['staged_total_exact_ns']),setup+4*local)
        self.assertEqual(s['direct_network_bytes'],4*size)
        self.assertEqual(s['staged_network_bytes'],size)
        self.assertEqual(s['staged_local_read_bytes'],4*size)

    def test_amortization_and_capacity_edges(self):
        s=calculate()['summary'];threshold=s['strict_reuses_to_amortize']
        self.assertEqual(threshold,2)
        self.assertEqual(calculate(reuses=threshold-1)['summary']['selected_policy'],'direct')
        self.assertEqual(calculate(reuses=threshold)['summary']['selected_policy'],'stage')
        size=s['snapshot_payload_bytes']
        self.assertTrue(calculate(available_local_bytes=size)['summary']['staged_fits_local_capacity'])
        limited=calculate(available_local_bytes=size-1)['summary']
        self.assertFalse(limited['staged_fits_local_capacity'])
        self.assertEqual(limited['selected_policy'],'direct')
        self.assertEqual(limited['selected_total_exact_ns'],limited['direct_total_exact_ns'])

    def test_window_limit_and_no_payback(self):
        window=calculate(reuses=1,active_transactions=128)['summary']
        self.assertEqual(window['remote_effective_upper_exact_bytes_per_second'],'16384000000')
        self.assertEqual(window['selected_policy'],'stage')
        slow=calculate(local_bandwidth=10**9)['summary']
        self.assertIsNone(slow['strict_reuses_to_amortize'])
        self.assertEqual(slow['selected_policy'],'direct')
        with self.assertRaises(ValueError):calculate(reuses=0)
