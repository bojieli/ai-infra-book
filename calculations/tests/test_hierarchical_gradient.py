"""Independent size, directional traffic and necessary-budget checks."""
from fractions import Fraction
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from infra_calc.topics import hierarchical_gradient as gradient


class HierarchicalGradientTests(unittest.TestCase):
    def test_real_parameter_and_algorithm_conservation(self):
        elements = 12288 * 4096
        for dtype, width in [('FP32', 4), ('BF16', 2)]:
            payload = elements * width
            for algorithm, remote_factor, rounds in [
                ('flat_contiguous', Fraction(7, 2), 14),
                ('flat_interleaved', 14, 14), ('hierarchical', 2, 8)
            ]:
                result = gradient.calculate(gradient_dtype=dtype, algorithm=algorithm)
                self.assertEqual(result['gradient']['bytes_per_rank'], payload)
                summary = result['summary']
                self.assertEqual(summary['network_send_bytes'], 14 * payload)
                self.assertEqual(summary['remote_send_bytes'], remote_factor * payload)
                self.assertEqual(summary['reduction_scalar_adds'], 7 * elements)
                self.assertEqual(summary['rounds'], rounds)
                self.assertIsNone(summary['actual_training_deadline_feasible'])

    def test_two_nics_cannot_exceed_server_shared_egress(self):
        payload = 12288 * 4096 * 4
        result = gradient.calculate(nics_per_server=2)
        # Six local rounds M/4 on 200 GB/s, two remote rounds M/2
        # on a fixed 40 GB/s server exit; eight declared launches.
        expected = 6 * Fraction(payload, 4 * 200_000_000_000)
        expected += 2 * Fraction(payload, 2 * 40_000_000_000)
        expected += Fraction(8 * 2000, 10**9)
        self.assertEqual(Fraction(result['summary']['serial_barrier_lower_seconds_exact']), expected)
        resources = {r['resource']: r for r in result['resources']}
        self.assertEqual(resources['server0.egress']['bytes'], payload)
        for nic in (0, 1):
            self.assertEqual(resources[f'server0.nic{nic}.tx']['bytes'], payload // 2)
            self.assertEqual(resources[f'server1.nic{nic}.rx']['bytes'], payload // 2)

    def test_receiver_can_determine_bound_and_budget_is_only_necessary(self):
        payload = 12288 * 4096 * 4
        arguments = {'bandwidth_overrides': {'server1.nic0.rx': 1_000_000_000}}
        result = gradient.calculate(**arguments)
        expected = Fraction(6 * payload, 4 * 200_000_000_000)
        expected += Fraction(payload, 1_000_000_000) + Fraction(16000, 10**9)
        self.assertEqual(Fraction(result['summary']['serial_barrier_lower_seconds_exact']), expected)
        ns = expected * 10**9
        floor = ns.numerator // ns.denominator
        for budget, allowed in [(floor, ns.denominator == 1), (floor + 1, True)]:
            summary = gradient.calculate(**arguments, budget_ns=budget)['summary']
            self.assertEqual(summary['necessary_budget_not_excluded'], allowed)
            self.assertIsNone(summary['actual_training_deadline_feasible'])

    def test_invalid_inputs_do_not_get_unlimited_resources(self):
        cases = [dict(nics_per_server=True), dict(nics_per_server=3),
                 dict(gradient_dtype='FP8'), dict(startup_ns=-1), dict(budget_ns=True),
                 dict(bandwidth_overrides={'unknown': 10}),
                 dict(bandwidth_overrides={'server0.egress': 0}),
                 dict(bandwidth_overrides={'server0.egress': None})]
        for arguments in cases:
            with self.subTest(arguments=arguments), self.assertRaises(ValueError):
                gradient.calculate(**arguments)


if __name__ == '__main__':
    unittest.main()
