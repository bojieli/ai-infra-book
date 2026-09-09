import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import copy
import unittest
from infra_calc.topics import storage_generation_comparison as subject


class ComparisonTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.work = subject.workload('qwen3-8b', 8, 8191, 4)
        cls.device = {'id': 'declared-test', 'memory': {'nominal_capacity': 1,
                      'capacity_unit': 'GiB', 'bandwidth_bytes_per_second': 10**9}}

    def test_one_byte_capacity_boundary(self):
        # Exact integer-byte boundary; no fractional capacity rounding.
        w = dict(self.work, resident_budget_bytes=2**30)
        rows = subject.compare(w, self.device, self.device)
        self.assertTrue(all(row['passes_declared_capacity'] for row in rows))
        w['resident_budget_bytes'] += 1
        rows = subject.compare(w, self.device, self.device)
        self.assertTrue(all(row['capacity_qualified_payload_service_seconds'] is None for row in rows))
        self.assertTrue(all(row['payload_service_seconds']['numerator'] > 0 for row in rows))

    def test_independent_resource_changes(self):
        bigger = copy.deepcopy(self.device)
        bigger['memory']['nominal_capacity'] *= 2
        bigger['memory']['bandwidth_bytes_per_second'] *= 4
        rows = subject.compare(self.work, bigger, self.device)
        from fractions import Fraction
        times = [Fraction(**{'numerator': x['payload_service_seconds']['numerator'],
                             'denominator': x['payload_service_seconds']['denominator']}) for x in rows]
        self.assertEqual(times[0], 4 * times[1])
        self.assertEqual(times[1], times[2])
        self.assertEqual(rows[0]['capacity_bytes'], 2 * rows[1]['capacity_bytes'])

    def test_invalid_workloads(self):
        for args in [('qwen3-8b', True, 10, 4), ('qwen3-8b', 1, -1, 4),
                     ('qwen3-8b', 1, 10, 3), ('qwen3-32b', 1, 10, 4),
                     ('qwen3-8b', 1, 100000000, 4)]:
            with self.assertRaises(ValueError):
                subject.workload(*args)
