"""Publication dependencies and state-machine sampling at visibility boundaries."""
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from infra_calc.topics.operation_ordering import calculate, stale_read


class OperationOrderingTests(unittest.TestCase):
    def test_schedule_formulas_and_dependencies(self):
        for recovery in (0,80000,200000):
            r=calculate(recovery_ns=recovery)
            s=r['summary'];publication=20000+recovery+2000
            self.assertEqual(s['each_data_transfer_bytes'],8192)
            self.assertEqual(s['strict_all_done_ns'],publication+10000)
            self.assertEqual(s['dependency_all_done_ns'],max(publication,10000))
            self.assertEqual(s['dependency_independent_done_ns'],10000)
            for scheduled in r['request_schedules'].values():
                rows={row['id']:row for row in scheduled['tasks']}
                self.assertGreaterEqual(rows['publish_notification']['start_ns'],rows['recover_and_make_visible']['end_ns'])
                for row in rows.values():
                    for predecessor in row['scheduled_predecessors']:
                        self.assertGreaterEqual(row['start_ns'],rows[predecessor]['end_ns'])
        shared=calculate(shared_resource=True)['summary']
        self.assertEqual(shared['all_done_saved_ns'],0)
        self.assertEqual(shared['dependency_independent_done_ns'],112000)

    def test_sampling_with_independent_register_events(self):
        for sample in (0,1999,2000,2001,4000):
            r=stale_read(speculative_read_ns=sample)
            data=0;observed=None
            events=[(2000,0,'write'),(sample,1,'read')]
            for time,priority,kind in sorted(events):
                if kind=='write':data=1
                else:observed=data
            self.assertEqual(r['response_order_only_data'],observed)
            self.assertEqual(r['response_order_only_valid'],observed==1)
            self.assertEqual(r['repaired_read_bytes'],8+(4 if observed==0 else 0))
            self.assertEqual(r['repaired_data'],1)
            if not observed:
                self.assertEqual(r['repaired_delivery_ns'],6000)
            else:
                self.assertEqual(r['repaired_delivery_ns'],5000)

    def test_response_delay_does_not_fix_stale_value(self):
        r=stale_read(response_ns=100000)
        self.assertFalse(r['response_order_only_valid'])
        self.assertEqual(r['repaired_delivery_ns'],100000)
        self.assertEqual(r['source_ordered_delivery_ns'],6000)
        with self.assertRaises(ValueError):stale_read(flag_visible_ns=1000)
        with self.assertRaises(ValueError):stale_read(speculative_read_ns=5000)
