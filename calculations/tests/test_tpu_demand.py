import unittest
from fractions import Fraction
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from infra_calc.topics.tpu_demand import calculate


class TPUDemandTests(unittest.TestCase):
    def test_three_usage_rates_and_missing_historical_counts(self):
        for minutes, total in [('1',Fraction(4,3)),('3',Fraction(2)),('6',Fraction(3))]:
            r=calculate(minutes_per_person_day=minutes)
            self.assertEqual(Fraction(r['summary']['total_conventional_capacity_exact']),total)
            self.assertIsNone(r['summary']['historical_server_count'])
            self.assertIsNone(r['tpu_capacity_candidates'][0]['added_whole_server_equivalents'])
        self.assertEqual(calculate(minutes_per_person_day='0')['summary']['total_conventional_capacity_exact'],'1')

    def test_cohort_capacity_and_increment_only_gain(self):
        # At the anchor, each of 120 normalized servers supplies one added unit.
        r=calculate(minutes_per_person_day='6',relative_population='1/2',
                    baseline_server_equivalents=120,effective_capacity_gain=4)
        base,fast=r['tpu_capacity_candidates']
        self.assertEqual(base['added_whole_server_equivalents'],120)
        self.assertEqual(fast['total_whole_server_equivalents'],150)
        self.assertNotEqual(fast['total_whole_server_equivalents'],240//4)
        rounded=calculate(minutes_per_person_day='1',baseline_server_equivalents=1000)
        self.assertEqual(rounded['tpu_capacity_candidates'][0]['total_whole_server_equivalents'],1334)
        self.assertEqual(calculate(**r['scenario']),r)

    def test_independent_factors_and_invalid_inputs(self):
        r=calculate(minutes_per_person_day='1',relative_population=2,
                    relative_work_per_audio_second='3/2',relative_peak_factor=2)
        self.assertEqual(r['summary']['incremental_conventional_capacity_exact'],'2')
        for args in [dict(minutes_per_person_day=1441),dict(relative_population=-1),
                     dict(effective_capacity_gain=0),dict(baseline_server_equivalents=True)]:
            with self.assertRaises(ValueError):calculate(**args)
