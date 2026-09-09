"""Atomic page admission, COW headroom and model-specific page geometry."""
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from infra_calc.topics.kv_pages import calculate


class KvPageCapacityTests(unittest.TestCase):
    def test_reject_is_atomic_and_fork_needs_no_page(self):
        page=16*144*1024
        result=calculate(capacity_bytes=2*page)
        rows=result['kv_page_events']
        self.assertTrue(rows[1]['accepted']);self.assertTrue(rows[2]['accepted'])
        self.assertEqual(result['summary']['rejected_events'],2)
        for index in (3,4):
            row=rows[index];before=rows[index-1]
            self.assertFalse(row['accepted'])
            for key in ('page_tables','pages','request_lengths','allocated_page_bytes'):
                self.assertEqual(row[key],before[key])
            self.assertEqual(row['copied_valid_bytes'],0)
            self.assertEqual(row['freed_page_ids'],[])
        self.assertEqual(rows[3]['additional_pages_required'],1)
        self.assertEqual(rows[4]['additional_pages_required'],2)

    def test_cancel_removes_cow_requirement(self):
        events=[dict(op='create',id='a',tokens=17),dict(op='fork',id='b',parent='a'),
                dict(op='append',id='b',tokens=1),dict(op='cancel',id='a'),dict(op='append',id='b',tokens=1)]
        result=calculate(events=events,capacity_bytes=2*16*144*1024)
        rows=result['kv_page_events']
        self.assertFalse(rows[2]['accepted'])
        self.assertEqual(rows[3]['freed_page_ids'],[])
        self.assertTrue(rows[4]['accepted'])
        self.assertEqual(rows[4]['additional_pages_required'],0)
        self.assertEqual(rows[4]['request_lengths'],{'b':18})
        self.assertEqual(result['summary']['total_copied_valid_bytes'],0)

    def test_preflight_matches_unbounded_growth(self):
        page=16*144*1024
        for length in (1,15,16,17,31,32):
            for added in (1,15,16,17):
                base=[dict(op='create',id='a',tokens=length),dict(op='fork',id='b',parent='a')]
                event=dict(op='append',id='b',tokens=added)
                unbounded=calculate(events=base+[event])['kv_page_events']
                needed=(unbounded[-1]['allocated_page_bytes']-unbounded[-2]['allocated_page_bytes'])//page
                self.assertEqual(unbounded[-1]['additional_pages_required'],needed)
                exact=unbounded[-1]['allocated_page_bytes']
                self.assertTrue(calculate(events=base+[event],capacity_bytes=exact)['kv_page_events'][-1]['accepted'])
                self.assertFalse(calculate(events=base+[event],capacity_bytes=exact-1)['kv_page_events'][-1]['accepted'])
        qwen=calculate(model='qwen3-235b-a22b',capacity_bytes=2*page,events=[dict(op='create',id='a',tokens=17)])
        self.assertEqual(qwen['summary']['capacity_pages'],1)
        self.assertEqual(qwen['summary']['rejected_events'],1)
        self.assertEqual(qwen['kv_page_events'][0]['request_lengths'],{})
