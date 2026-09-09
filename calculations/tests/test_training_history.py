"""Independent fixed-value checks and adversarial fixtures; no repo writes."""
from copy import deepcopy
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from infra_calc.topics.training_history import calculate, verify_archives
from infra_calc.paths import PROJECT




class HistoricalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = calculate(PROJECT)
        cls.rows = {r['input']['id']: r for r in cls.result['training_history_rows']}

    def test_fixed_proxy_values(self):
        expected = {
            'llama1-7b': (40200000000000000000000, Fraction(10000, 67)),
            'llama2-7b': (84000000000000000000000, Fraction(2000, 7)),
            'llama31-8b': (720000000000000000000000, Fraction(1875)),
            'qwen25-7b-proxy': (756000000000000000000000, Fraction(18000, 7)),
            'qwen3-8b-proxy': (1728000000000000000000000, Fraction(4500)),
            'llama31-405b': (37908000000000000000000000, Fraction(1040, 27)),
            'deepseek-v3-pretraining': (3285600000000000000000000, Fraction(400)),
            'deepseek-v4-flash': (2496000000000000000000000, Fraction(32000, 13)),
            'deepseek-v4-pro': (9702000000000000000000000, Fraction(33000, 49)),
        }
        for identifier, (flops, ratio) in expected.items():
            with self.subTest(model=identifier):
                self.assertEqual(self.rows[identifier]['proxy_flops'], flops)
                self.assertEqual(Fraction(self.rows[identifier]['tokens_per_parameter_exact']), ratio)
        self.assertEqual(Fraction(self.rows['llama31-405b']['proxy_to_reported_flops_ratio_exact']), Fraction(9477, 9500))

    def test_duration_interpretations(self):
        expected = {'llama1-65b': 20.800008138020832,
                    'deepseek-v3-pretraining': 54.19921875,
                    'llama31-405b': 78.43017578125}
        for identifier, days in expected.items():
            duration = self.rows[identifier]['duration']
            self.assertAlmostEqual(duration['conditional_constant_count_days'], days)
            self.assertIsNone(duration['measured_calendar_days'])
        maximum = self.rows['llama31-405b']['duration']
        self.assertEqual(maximum['interpretation'], 'lower_bound_using_reported_maximum')
        self.assertEqual(maximum['conditional_calendar_lower_bound_days_exact'], maximum['conditional_constant_count_days_exact'])
        self.assertIsNone(maximum['calendar_lower_bound_days_exact'])
        self.assertIsNone(self.rows['llama1-65b']['duration']['calendar_lower_bound_days_exact'])
        self.assertEqual(self.rows['llama1-65b']['input']['gpu_hours'], 1022362)

    def test_unknowns_and_no_mfu(self):
        row = self.rows['qwen35-397b']
        self.assertIsNone(row['proxy_flops'])
        self.assertIsNone(row['tokens_per_parameter_exact'])
        for row in self.rows.values():
            self.assertIsNone(row['mfu'])
            if row['input']['gpu_hours'] is None or row['input']['gpu_count'] is None:
                self.assertIsNone(row['duration']['conditional_constant_count_days'])
        self.assertIsNone(self.rows['qwen3-8b-proxy']['input']['gpu_hours'])

    def test_stage_scopes(self):
        deepseek, qwen = self.result['stage_reports']
        self.assertEqual(deepseek['summed_gpu_hours_exact'], '2788000')
        self.assertTrue(deepseek['reported_total_matches'])
        self.assertEqual(qwen['aggregation'], 'alternatives')
        self.assertIsNone(qwen['summed_gpu_hours_exact'])
        self.assertEqual(qwen['input']['alternatives'], {'reinforcement_learning': 17920, 'on_policy_distillation': 1800})

    def test_growth_and_scenario_intervals(self):
        result = calculate(PROJECT, comparisons=[{'baseline': 'llama1-7b', 'target': 'qwen3-8b-proxy'}],
                           duration_scenarios=[{'model': 'llama2-7b', 'min_constant_gpu_count': 256, 'max_constant_gpu_count': 1024},
                                               {'model': 'qwen3-8b-proxy', 'min_constant_gpu_count': 256, 'max_constant_gpu_count': 1024}])
        self.assertEqual(result['comparisons'][0]['training_tokens_growth_exact'], '36')
        self.assertEqual(Fraction(result['comparisons'][0]['proxy_flops_growth_exact']), Fraction(2880, 67))
        self.assertEqual(result['duration_scenarios'][0]['conditional_days_min_exact'], '15/2')
        self.assertEqual(result['duration_scenarios'][0]['conditional_days_max_exact'], '30')
        self.assertIsNone(result['duration_scenarios'][1]['conditional_days_min_exact'])

    def test_lifecycle_exact_and_missing(self):
        spec = dict(model='llama1-7b', currency='scenario-units', service_unit='request', scope='synthetic test',
                    training_price_per_gpu_hour='1/3', service_usage=300, service_price_per_unit='1/10', other_cost=0)
        result = calculate(PROJECT, lifecycle=[spec])['lifecycle'][0]
        self.assertEqual(result['scoped_lifecycle_cost_exact'], '82522/3')
        self.assertEqual(result['input'], spec)
        for missing in ('training_price_per_gpu_hour', 'service_usage', 'service_price_per_unit', 'other_cost'):
            changed = {**spec, missing: None}
            self.assertIsNone(calculate(PROJECT, lifecycle=[changed])['lifecycle'][0]['scoped_lifecycle_cost_exact'])
        self.assertIsNone(calculate(PROJECT, lifecycle=[{**spec, 'model': 'qwen3-8b-proxy', 'training_price_per_gpu_hour': 0}])['lifecycle'][0]['training_cost_exact'])

    def test_all_archives_and_catalog_preserved(self):
        self.assertEqual(self.result['summary'], {'models': 13, 'verified_archives': 16})
        self.assertEqual(self.result['catalog'], json.loads((PROJECT / 'configs/training-history.json').read_text()))
        self.assertEqual(len(self.result['sources']), 16)
        json.dumps(self.result, allow_nan=False)


class FixtureTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parent)
        self.addCleanup(self.temp.cleanup)
        self.project = Path(self.temp.name)
        (self.project / 'configs').mkdir()
        (self.project / 'evidence.txt').write_bytes(b'fixed official evidence fixture')
        self.lock = [dict(id='fixture', file='evidence.txt', url='https://example.invalid/fixture',
                          revision='test only', bytes=31,
                          sha256=hashlib.sha256(b'fixed official evidence fixture').hexdigest())]
        self.catalog = dict(snapshot='test', future={'keep': [None]}, models=[dict(
            id='test', source_id='fixture', parameter_proxy=2, parameter_proxy_kind='nominal_dense_proxy',
            training_tokens=3, gpu_hours=48, gpu_count=2, gpu_count_role='reported_configuration',
            scope_notes='retain', unknown={'nested': None})], stage_reports=[])
        self.write()

    def write(self):
        (self.project / 'configs/training-history.json').write_text(json.dumps(self.catalog))
        (self.project / 'configs/training-history.lock.json').write_text(json.dumps(self.lock))

    def test_preserve_unknown_fields_without_mutation(self):
        original = deepcopy(self.catalog)
        result = calculate(self.project)
        self.assertEqual(result['catalog'], original)
        self.assertEqual(result['training_history_rows'][0]['input'], original['models'][0])
        self.assertEqual(result['training_history_rows'][0]['proxy_flops'], 36)
        self.assertEqual(self.catalog, original)

    def test_hash_size_missing_and_unlinked_fail_closed(self):
        (self.project / 'evidence.txt').write_bytes(b'altered')
        with self.assertRaises(ValueError): calculate(self.project)
        (self.project / 'evidence.txt').write_bytes(b'fixed official evidence fixture')
        self.lock[0]['bytes'] = 32
        self.write()
        with self.assertRaises(ValueError): calculate(self.project)
        self.lock[0]['bytes'] = 31
        self.catalog['models'][0]['source_id'] = 'absent'
        self.write()
        with self.assertRaises(ValueError): calculate(self.project)
        (self.project / 'evidence.txt').unlink()
        with self.assertRaises(FileNotFoundError): verify_archives(self.project, self.lock)

    def test_bad_model_inputs(self):
        original = deepcopy(self.catalog['models'][0])
        for field, value in [('parameter_proxy', 0), ('training_tokens', True), ('gpu_hours', -1),
                             ('gpu_count', '3/2'), ('gpu_count_role', 'available_cluster'),
                             ('parameter_proxy_kind', 'total_moe'), ('gpu_hours', 1.5)]:
            self.catalog['models'][0] = {**original, field: value}
            self.write()
            with self.subTest(field=field, value=value), self.assertRaises(ValueError): calculate(self.project)

    def test_stage_missing_mismatch_and_mixed_branches(self):
        self.catalog['stage_reports'] = [dict(model='test', source_id='fixture', parts={'a': 2, 'b': None}, reported_total=3)]
        self.write()
        self.assertIsNone(calculate(self.project)['stage_reports'][0]['summed_gpu_hours_exact'])
        self.catalog['stage_reports'][0]['parts']['b'] = 2
        self.write()
        self.assertFalse(calculate(self.project)['stage_reports'][0]['reported_total_matches'])
        self.catalog['stage_reports'][0]['alternatives'] = {'x': 2}
        self.write()
        with self.assertRaises(ValueError): calculate(self.project)

    def test_bad_scenarios(self):
        for spec in [dict(model='absent', min_constant_gpu_count=1, max_constant_gpu_count=2),
                     dict(model='test', min_constant_gpu_count=3, max_constant_gpu_count=2),
                     dict(model='test', min_constant_gpu_count=0, max_constant_gpu_count=2)]:
            with self.assertRaises(ValueError): calculate(self.project, duration_scenarios=[spec])
        with self.assertRaises(ValueError): calculate(self.project, comparisons=[{'baseline': 'test', 'target': 'absent'}])
        with self.assertRaises(ValueError): calculate(self.project, lifecycle=[{'model': 'test'}])


if __name__ == '__main__':
    unittest.main()
