import unittest
from fractions import Fraction
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from infra_calc.topics.nic_budget import calculate


class NICBudgetTests(unittest.TestCase):
    def test_historical_rounding_and_idle_integer_allocation(self):
        r=calculate()
        self.assertEqual(Fraction(r['summary']['packets_per_second_exact']),Fraction(5_000_000_000,84))
        self.assertEqual(r['summary']['dedicated_cpu_cores'],[6,3])
        self.assertEqual(calculate(link_utilization='1/2')['summary']['dedicated_cpu_cores'],[3,2])
        self.assertEqual(calculate(cpu_target_utilization='1/2')['summary']['dedicated_cpu_cores'],[12,6])
        self.assertEqual(calculate(link_utilization='0')['summary']['dedicated_cpu_cores'],[0,0])

    def test_packet_count_mixture_matches_finite_wire_cohort(self):
        # Explicit four-packet cohort: 64,1518,64,1518 bytes plus each gap/preamble.
        mix=[dict(frame_bytes=64,packet_share='1/2',work_multiplier='2'),
             dict(frame_bytes=1518,packet_share='1/2',work_multiplier='1')]
        r=calculate(packet_mix=mix)
        wire=sum(n+20 for n in [64,1518,64,1518])
        cohort_seconds=Fraction(wire,5_000_000_000)
        expected_pps=4/cohort_seconds
        self.assertEqual(Fraction(r['summary']['packets_per_second_exact']),expected_pps)
        expected_busy=Fraction(6,10_000_000)/cohort_seconds
        self.assertEqual(Fraction(r['nic_cpu_candidates'][0]['busy_core_seconds_per_second_exact']),expected_busy)
        wrong=Fraction(5_000_000_000,2)*(Fraction(1,84)+Fraction(1,1538))
        self.assertNotEqual(expected_pps,wrong)
        self.assertEqual(sum(Fraction(x['packets_per_second_exact'])*x['wire_bytes'] for x in r['nic_packet_classes']),5_000_000_000)

    def test_offload_preserves_supplied_bus_limits(self):
        bus=dict(bytes_per_packet=64,effective_bytes_per_second=1_000_000_000,
                 transactions_per_packet=1,mean_transaction_seconds='1/1000000',inflight_slots=32)
        a=calculate(pcie=bus);b=calculate(pcie=bus,retained_host_work='0')
        self.assertEqual(a['pcie_budget'],b['pcie_budget'])
        self.assertEqual(b['summary']['dedicated_cpu_cores'],[0,0])
        self.assertFalse(b['pcie_budget']['offered_rate_fits_necessary_bounds'])
        self.assertEqual(b['pcie_budget']['required_integer_slots'],60)
        self.assertIsNone(b['summary']['complete_virtualization_cpu_cores'])
        self.assertEqual(calculate(**a['scenario']),a)

    def test_encapsulation_and_invalid_ambiguity(self):
        r=calculate(encapsulation_bytes=50)
        self.assertEqual(Fraction(r['summary']['packets_per_second_exact']),Fraction(5_000_000_000,134))
        for args in [dict(packet_mix=[]),dict(packet_mix=[dict(frame_bytes=64,packet_share='1/2')]),
                     dict(packet_mix=[dict(frame_bytes=63,packet_share='1')]),dict(link_utilization='2'),
                     dict(cpu_target_utilization='0'),dict(retained_host_work=True),dict(pcie={})]:
            with self.assertRaises(ValueError):calculate(**args)
