from fractions import Fraction as F
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from infra_calc.topics.cache_route import calculate


class CacheRouteTests(unittest.TestCase):
    def test_book_dependencies_and_bandwidth_boundary(self):
        r=calculate();s=r['summary'];size=36*2*8*128*2*8192
        self.assertEqual(s['prefix_state_bytes'],size)
        remote=next(row for row in r['cache_route_paths'] if row['path'].startswith('B remote'))
        self.assertEqual(F(remote['finish_ns_exact']),10**7+F(size,5)+F(size,25)+10**7)
        threshold=F(s['remote_equal_recompute_bytes_per_second_exact'])
        for bandwidth in (int(threshold),int(threshold)+1):
            r=calculate(remote_bytes_per_second=bandwidth)
            value=F(r['cache_route_paths'][2]['finish_ns_exact'])
            self.assertEqual(value<200000000,bandwidth>threshold)
        self.assertEqual(s['remote_payload_demand_bytes_per_second'],19327352832)

    def test_stale_mean_quantile_and_equality(self):
        s=calculate(queue_a_ns=80000000)['summary']
        self.assertEqual(F(s['a_expected_ns_exact']),107000000)
        self.assertEqual(F(s['a_p99_ns_exact']),260000000)
        self.assertEqual(F(s['strict_mean_hit_probability_threshold_exact']),F(6,17))
        self.assertTrue(s['a_mean_better_than_b']);self.assertFalse(s['a_p99_passes_slo'])
        tie=calculate(queue_a_ns=80000000,hit_probability='6/17')['summary']
        self.assertFalse(tie['a_mean_better_than_b'])
        self.assertEqual(F(calculate(queue_a_ns=80000000,hit_probability='99/100')['summary']['a_p99_ns_exact']),90000000)

    def test_cpu_copy_overlap_is_a_dependency_choice(self):
        overlap=calculate(queue_a_ns=80000000)['cache_route_paths'][3]
        serial=calculate(queue_a_ns=80000000,retrieval_after_queue=True)['cache_route_paths'][3]
        self.assertEqual(F(overlap['finish_ns_exact']),90000000)
        self.assertEqual(F(serial['finish_ns_exact']),90000000+F(1207959552,25))
        with self.assertRaises(ValueError):calculate(hit_probability='101/100')
