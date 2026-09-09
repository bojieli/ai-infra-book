"""Window, serial service and exact simultaneous limiter checks."""
from fractions import Fraction
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from infra_calc.topics.memory_concurrency import calculate


class RemoteWindowTests(unittest.TestCase):
    def test_book_constraints(self):
        base=dict(transaction_bytes=256,latency_ns=2000,bandwidth_bytes_per_second=40*10**9)
        window=calculate(**base)['summary']
        self.assertEqual(window['required_transactions'],313)
        self.assertEqual(window['effective_bandwidth_upper_exact_bytes_per_second'],'16384000000')
        serial=calculate(**base,service_interval_ns=100)['summary']
        self.assertEqual(serial['effective_bandwidth_upper_exact_bytes_per_second'],'2560000000')
        self.assertFalse(serial['serial_service_can_reach_interface'])
        wait=calculate(**base,service_interval_ns=100,active_transactions=1)['summary']
        self.assertEqual(wait['effective_bandwidth_upper_exact_bytes_per_second'],'128000000')
        self.assertEqual(wait['allocated_window_bytes'],32768)
        self.assertEqual(wait['outstanding_window_bytes'],256)
        enlarged=calculate(**base,transactions=313,service_interval_ns=100)['summary']
        self.assertEqual(enlarged['effective_bandwidth_upper_bytes_per_second'],2560000000)
        fast=calculate(**base,transactions=313,service_interval_ns=6)['summary']
        self.assertEqual(fast['effective_bandwidth_upper_bytes_per_second'],40*10**9)

    def test_exact_rates_and_ties(self):
        s=calculate(transaction_bytes=3,transactions=2,latency_ns=7,
                    bandwidth_bytes_per_second=10**9,service_interval_ns=5)['summary']
        self.assertEqual(Fraction(s['throughput_bounds_exact_bytes_per_second']['transaction_window']),Fraction(6*10**9,7))
        tied=calculate(transaction_bytes=1,transactions=2,latency_ns=2,
                       bandwidth_bytes_per_second=10**9,service_interval_ns=1)['summary']
        self.assertEqual(set(tied['binding_limiters']),{'interface','transaction_window','serial_service'})
        with self.assertRaises(ValueError):calculate(active_transactions=129)
        with self.assertRaises(ValueError):calculate(service_interval_ns=0)
