import sys
import unittest
from fractions import Fraction
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from infra_calc.topics.environment_lifecycle import calculate, GIB, MIB


class EnvironmentLifecycleTests(unittest.TestCase):
    def test_clone_placements_and_delta_are_distinct_pools(self):
        r=calculate(); rows=r['clone_placements']
        self.assertEqual([x['memory_only_environment_upper_bound'] for x in rows],[31,127,496,168])
        self.assertEqual([Fraction(x['total_local_bytes'],GIB) for x in rows],
                         [Fraction('200.390625'),Fraction('50.390625'),Fraction('12.890625'),Fraction('37.890625')])
        self.assertEqual(r['snapshot_budget']['total_base_plus_private_deltas_bytes'],2*GIB+100*128*MIB)
        paths={x['path']:x for x in r['creation_paths']}
        self.assertEqual(paths['cold_template']['declared_local_install_bytes'],paths['warm_template']['declared_local_install_bytes'])
        self.assertEqual(Fraction(paths['cold_template']['serial_byte_service_lower_exact_seconds'])-
                         Fraction(paths['warm_template']['serial_byte_service_lower_exact_seconds']),2)
        self.assertTrue(all(x['first_tool_complete_seconds'] is None for x in paths.values()))
        with self.assertRaises(ValueError): calculate(dirty_bytes=600*MIB)
        with self.assertRaises(ValueError): calculate(prediction_hit_probability='5/4')

    def test_prewarm_expectation_by_discrete_outcomes_and_early_cancel(self):
        r=calculate()['prewarm_budget']
        # Enumerate three hits and one miss, including independent demanded
        # preparation after the wrong prediction. Allocation starts at launch.
        wait=[1,1,1,2]; allocations=[2,2,2,4+2]; unused=[0,0,0,4]
        self.assertEqual(Fraction(r['expected_call_preparation_wait_exact_seconds']),Fraction(sum(wait),4))
        self.assertEqual(Fraction(r['expected_allocated_pretool_environment_seconds']),Fraction(sum(allocations),4))
        self.assertEqual(Fraction(r['expected_unused_environment_seconds']),Fraction(sum(unused),4))
        miss=calculate(prediction_hit_probability='0',lead_seconds='1',wrong_prediction_timeout_seconds='0')['prewarm_budget']
        self.assertEqual(miss['expected_unused_environment_seconds'],'1')
        self.assertEqual(miss['expected_call_preparation_wait_exact_seconds'],'2')
        warm=calculate(prediction_hit_probability='1',lead_seconds='4')['prewarm_budget']
        self.assertEqual(warm['expected_call_preparation_wait_exact_seconds'],'0')
        self.assertEqual(warm['expected_unused_environment_seconds'],'2')

    def test_archived_trials_are_separate_from_cloud_unknowns(self):
        r=calculate(); trials=r['measured_prewarm_trials']
        self.assertEqual(len(trials),12)
        self.assertEqual({x['policy'] for x in trials},{'resident','demand','predict-50ms','predict-fullgap'})
        for x in trials:
            self.assertEqual(x['rounds'],12)
            self.assertGreaterEqual(x['unused_allocated_lifecycle_seconds'],x['unused_ready_seconds'])
            self.assertGreater(x['sampled_rss_byte_seconds'],0)
            self.assertIsNone(x['measured_unused_physical_memory_byte_seconds'])
        self.assertFalse(r['summary']['e2b_four_path_runtime_measured'])
        # Recorded measurements cannot depend on our hypothetical preparation rate.
        self.assertEqual(trials,calculate(preparation_seconds='999')['measured_prewarm_trials'])


if __name__=='__main__': unittest.main()
