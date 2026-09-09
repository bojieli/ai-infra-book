import json
import sys
import unittest
from fractions import Fraction
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from infra_calc.topics import environment_resources


class EnvironmentResourcesTests(unittest.TestCase):
    def test_real_process_cpu_rss_and_finite_cohort_independent_areas(self):
        result = environment_resources.calculate()
        files, _ = environment_resources.read_records('processes')
        q = lambda value: Fraction(str(value))
        self.assertEqual(result['summary']['verified_processes'], 36)
        for row in result['environment_process_runs']:
            raw = json.loads(files[f"results/case{row['run']}.json"])
            life = [(q(launch['at']), q(raw['completed'][str(launch['pid'])]['reaped']))
                    for launch in raw['launch']]
            events = sorted({q(raw['start']), q(raw['end'])} | {time for pair in life for time in pair})
            # Count live processes at each interval midpoint, independent of event-delta sweep.
            area = sum((right - left) * sum(start <= (left + right) / 2 < end for start, end in life)
                       for left, right in zip(events, events[1:]))
            window = q(raw['end']) - q(raw['start'])
            self.assertEqual(Fraction(row['average_count_recorded_decimal_exact']), area / window)
            self.assertEqual(Fraction(row['throughput_times_mean_lifetime_recorded_decimal_exact']), area / window)
            self.assertTrue(row['finite_cohort_identity_verified'])
            samples = raw['samples']
            integral = Fraction()
            for a, b in zip(samples, samples[1:]):
                # Integrate the linear interpolant using its exact midpoint value.
                midpoint_rss = Fraction(sum(p['rss'] for p in a['processes']) + sum(p['rss'] for p in b['processes']), 2)
                integral += (q(b['at']) - q(a['at'])) * midpoint_rss
            self.assertEqual(Fraction(row['sampled_rss_byte_seconds_recorded_decimal_exact']), integral)
            workers = [json.loads(w['stdout']) for w in raw['completed'].values()]
            self.assertAlmostEqual(row['recorded_process_cpu_seconds'], sum(w['cpu_total'] for w in workers))
            self.assertIsNone(row['scheduler_queue_wait_seconds'])
        selected = environment_resources.calculate(condition='cpu-stagger')
        self.assertEqual(selected['summary']['reported_runs'], 3)
        self.assertEqual(selected['summary']['reported_processes'], 12)
        self.assertEqual(selected['summary']['verified_processes'], 36)

    def test_controller_failed_task_and_separate_observation_windows(self):
        result = environment_resources.calculate(dataset='controller')
        summary = result['summary']
        files, _ = environment_resources.read_records('controller')
        rounds = [json.loads(line) for line in files['results/rounds.jsonl'].splitlines()]
        self.assertEqual(summary['rounds'], 12)
        self.assertEqual(summary['sample_count'], 186)
        self.assertFalse(summary['quality_passed'])
        self.assertEqual(summary['visible_cases_passed'], 2)
        self.assertAlmostEqual(summary['model_controller_cpu_seconds'], sum(r['model_parent_cpu_s'] for r in rounds))
        self.assertGreater(summary['sampled_rss_byte_seconds'], 0)
        self.assertAlmostEqual(summary['rss_sample_window_seconds'] + summary['rss_unobserved_prefix_seconds'] +
                               summary['rss_unobserved_suffix_seconds'], summary['observation_window_seconds'])
        self.assertAlmostEqual(summary['model_wall_seconds'] + summary['tool_wall_seconds'] +
                               summary['other_loop_wall_seconds'], summary['observation_window_seconds'])
        self.assertIsNone(summary['environment_arrival_rate_per_second'])
        self.assertIsNone(summary['scheduler_queue_wait_seconds'])
        self.assertIsNone(summary['whole_environment_memory_bytes'])
        # A supplied zero-duration lifespan contributes no occupancy.
        identity = environment_resources.finite_lifetimes([(Fraction(1), Fraction(1)), (Fraction(2), Fraction(4))], Fraction(0), Fraction(5))
        self.assertEqual(Fraction(identity['average_count_recorded_decimal_exact']), Fraction(2, 5))

    def test_semantic_corruption_and_incomplete_inputs_rejected(self):
        files, records = environment_resources.read_records('processes')
        raw = json.loads(files['results/case0.json'])
        pid = next(iter(raw['completed']))
        worker = json.loads(raw['completed'][pid]['stdout'])
        worker['memory_check'] = 0
        raw['completed'][pid]['stdout'] = json.dumps(worker)
        changed = dict(files, **{'results/case0.json': json.dumps(raw).encode()})
        with patch.object(environment_resources, 'read_records', return_value=(changed, records)):
            with self.assertRaises(ValueError):
                environment_resources.calculate()
        files, records = environment_resources.read_records('controller')
        final = json.loads(files['results/final.json'])
        validation = json.loads(final['validation']['stdout'])
        validation['passed'] = True
        final['validation']['stdout'] = json.dumps(validation)
        changed = dict(files, **{'results/final.json': json.dumps(final).encode()})
        with patch.object(environment_resources, 'read_records', return_value=(changed, records)):
            with self.assertRaises(ValueError):
                environment_resources.calculate(dataset='controller')
        for inputs in ({'dataset': 'unknown'}, {'dataset': 'controller', 'condition': 'cpu-burst'}, {'condition': 'missing'}):
            with self.assertRaises(ValueError):
                environment_resources.calculate(**inputs)
        with self.assertRaises(ValueError):
            environment_resources.sampled_rss([(Fraction(1), 10), (Fraction(1), 20)])
        with self.assertRaises(ValueError):
            environment_resources.finite_lifetimes([(Fraction(0), Fraction(2))], Fraction(1), Fraction(3))


if __name__ == '__main__':
    unittest.main()
