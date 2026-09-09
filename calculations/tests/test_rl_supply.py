"""Shared-resource, service-wave and bottleneck-transfer checks."""
import sys
from pathlib import Path
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from infra_calc.topics.rl_supply import calculate, teaching_supply


class RLSupplyTests(unittest.TestCase):
    def test_shared_pool_sums_instead_of_max_stage(self):
        supply = teaching_supply()
        for stage in supply['matrix'].values():
            stage['pool'] = 'shared'
        supply['verifier']['pool'] = 'shared'
        supply['synchronization']['pool'] = 'shared'
        result = calculate(supply=supply)
        s = result['summary']
        self.assertAlmostEqual(s['ideal_pipeline_interval_lower_seconds'], s['serial_component_batch_seconds'])
        self.assertGreater(s['ideal_pipeline_interval_lower_seconds'], max(r['service_seconds'] for r in result['service_stages']))

    def test_finite_verifier_wave_and_steady_demand(self):
        result = calculate(cycle=dict(prompts=3, samples_per_prompt=3, accepted_samples=3))
        row = next(r for r in result['service_stages'] if r['stage']=='verification')
        self.assertAlmostEqual(row['service_seconds'], 9 * .05 / 8)
        self.assertAlmostEqual(row['isolated_batch_seconds'], .1)

    def test_speedup_moves_limit_and_preserves_other_demands(self):
        base = calculate()
        faster = calculate(pool_speedups={'actor':2})
        self.assertEqual(base['summary']['limiting_pools'], ['actor'])
        self.assertEqual(faster['summary']['limiting_pools'], ['learner'])
        for pool, value in base['pool_service_seconds'].items():
            self.assertEqual(faster['pool_service_seconds'][pool], value / (2 if pool=='actor' else 1))
        with self.assertRaises(ValueError):
            calculate(pool_speedups={'unknown':2})
        with self.assertRaises(ValueError):
            calculate(pool_speedups={'actor':0})
