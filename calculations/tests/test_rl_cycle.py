"""Explicit call enumeration and cohort conservation for RL matrix accounting."""
import sys
from pathlib import Path
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from infra_calc.topics.rl_cycle import calculate
from infra_calc.models import forward
from infra_calc.schema import Scenario


class RLCycleTests(unittest.TestCase):
    def test_generation_matches_each_actual_call(self):
        for model in ('qwen3-8b', 'qwen3-235b-a22b'):
            for g in (1, 2, 7):
                s = calculate(model=model, prompts=2, samples_per_prompt=2, prompt_tokens=3,
                              output_tokens=g, accepted_samples=2)['summary']
                expected = forward(model, Scenario(batch=4, tokens=3))['summary']['matrix_flops']
                for step in range(g - 1):
                    expected += forward(model, Scenario(batch=4, tokens=1, history=3 + step))['summary']['matrix_flops']
                self.assertEqual(s['rollout_matrix_flops'], expected)
                self.assertEqual(s['supervised_tokens_per_epoch'], 2 * g)
                self.assertEqual(s['training_input_tokens_per_epoch'], 2 * (3 + g - 1))

    def test_fixed_accepted_cohort_rejected_work_is_retained(self):
        base = calculate(prompts=2, samples_per_prompt=2, accepted_samples=2)
        lower = calculate(prompts=4, samples_per_prompt=2, accepted_samples=2)
        for a, b in zip(base['rl_stages'], lower['rl_stages']):
            self.assertEqual(b['matrix_flops'], a['matrix_flops'] * (1 if a['name']=='policy_update' else 2))
        self.assertGreater(lower['summary']['matrix_flops_per_accepted_sample'], base['summary']['matrix_flops_per_accepted_sample'])

    def test_passes_and_snapshot_are_separate(self):
        r = calculate(reference_passes=0, teacher_passes=2, update_epochs=3, rollout_replicas=4)
        base = calculate()
        self.assertEqual(r['rl_stages'][2]['matrix_flops'], 0)
        self.assertEqual(r['rl_stages'][3]['matrix_flops'], 2 * base['rl_stages'][2]['matrix_flops'])
        self.assertEqual(r['rl_stages'][4]['matrix_flops'], 3 * base['rl_stages'][4]['matrix_flops'])
        self.assertEqual(r['summary']['independent_unicast_weight_sync_bytes'], 4 * r['summary']['bf16_weight_snapshot_bytes'])
        self.assertIsNone(r['summary']['predicted_cycle_seconds'])
        with self.assertRaises(ValueError):
            calculate(accepted_samples=33)
        with self.assertRaises(ValueError):
            calculate(reference_passes=-1)
