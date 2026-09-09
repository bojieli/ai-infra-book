"""Book schedule totals, strict crossover and physical-vs-logical weight ledger."""
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from infra_calc.topics.microbatch_overlap import calculate


class MicrobatchOverlapTests(unittest.TestCase):
    def test_book_constants(self):
        s=calculate()['summary']
        self.assertEqual(s['ffn_parameters'],150994944)
        self.assertEqual(s['matrix_flops'],77309411328)
        self.assertEqual(s['split_matrix_flops'],s['matrix_flops'])
        self.assertEqual(s['unique_weight_bytes'],288*2**20)
        self.assertEqual(s['split_cold_weight_read_bytes'],576*2**20)
        self.assertEqual([s[k] for k in ('full_finish_ns','split_serial_finish_ns','ideal_finish_ns','paired_finish_ns')],[1200000,1360000,1160000,1280000])
        self.assertEqual(s['split_compute_service_increase_ns'],160000)

    def test_strict_window_threshold(self):
        threshold=calculate()['summary']['joint_window_strict_upper_bound_ns']
        self.assertEqual(threshold,520000)
        for offset in (-1,0,1):
            r=calculate(joint_window_ns=threshold+offset)['summary']
            self.assertEqual(r['paired_beats_full'],offset<0)
        r=calculate(full_n_ns=1,full_c_ns=1)['summary']
        self.assertFalse(r['positive_joint_window_can_win'])
        self.assertFalse(r['paired_beats_full'])

    def test_uneven_work_and_explicit_dependencies(self):
        r=calculate(tokens=257,first_tokens=100,split_n_ns=[150000,250000],split_c_ns=[400000,600000])
        self.assertEqual([x['tokens'] for x in r['microbatch_rows']],[100,157])
        self.assertEqual(sum(x['matrix_flops'] for x in r['microbatch_rows']),6*257*4096*12288)
        ideal=r['request_schedules']['split_ideal']
        self.assertEqual(ideal['finish_ns'],150000+max(400000,250000)+600000)
        paired=r['request_schedules']['split_paired']
        self.assertEqual(paired['finish_ns'],150000+600000+600000)
        for schedule in r['request_schedules'].values():
            by_id={t['id']:t for t in schedule['tasks']}
            for task in schedule['tasks']:
                for dep in task['scheduled_predecessors']:
                    self.assertGreaterEqual(task['start_ns'],by_id[dep]['end_ns'])
        with self.assertRaises(ValueError):calculate(first_tokens=256)
        with self.assertRaises(ValueError):calculate(split_n_ns=[1])
