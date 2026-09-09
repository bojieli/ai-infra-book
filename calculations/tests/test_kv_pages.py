"""Reference multiplicities, branch length isolation and safe cancellation."""
from collections import Counter
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from infra_calc.topics.kv_pages import calculate


class KvPagesTests(unittest.TestCase):
    def test_book_and_model_geometry(self):
        r=calculate();s=r['summary'];unit=144*1024
        self.assertEqual(s['kv_bytes_per_token'],unit)
        self.assertEqual(s['page_bytes'],16*unit)
        self.assertEqual(s['final_allocated_page_bytes'],64*unit)
        self.assertEqual(s['final_logical_request_bytes'],51*unit)
        self.assertEqual(s['final_unique_live_bytes'],35*unit)
        self.assertEqual(s['final_unused_page_bytes'],29*unit)
        self.assertEqual(s['total_copied_valid_bytes'],2*unit)
        self.assertEqual(calculate(model='qwen3-235b-a22b')['summary']['kv_bytes_per_token'],188*1024)

    def test_reference_and_length_oracles(self):
        for length in (0,1,15,16,17,31,32):
            events=[dict(op='create',id='a',tokens=length),dict(op='fork',parent='a',id='b'),
                    dict(op='append',id='a',tokens=1),dict(op='append',id='b',tokens=17),
                    dict(op='cancel',id='a'),dict(op='cancel',id='b')]
            r=calculate(events=events);expected={}
            for event,row in zip(events,r['kv_page_events']):
                name=event['id']
                if event['op']=='create':expected[name]=event['tokens']
                elif event['op']=='fork':expected[name]=expected[event['parent']]
                elif event['op']=='append':expected[name]+=event['tokens']
                else:del expected[name]
                self.assertEqual(row['request_lengths'],expected)
                counts=Counter(p for table in row['page_tables'].values() for p in table)
                self.assertEqual(counts,{p['id']:p['references'] for p in row['pages']})
                used={p['id']:p['used_tokens'] for p in row['pages']}
                for table in row['page_tables'].values():
                    self.assertTrue(all(used[p]==16 for p in table[:-1]))
                self.assertEqual(row['unused_page_bytes']+row['unique_live_bytes'],row['allocated_page_bytes'])
            self.assertEqual(r['summary']['final_allocated_page_bytes'],0)
            self.assertEqual(r['kv_page_events'][-1]['pages'],[])
            if length%16==0:self.assertEqual(r['summary']['total_copied_valid_bytes'],0)

    def test_shared_tail_copy_and_invalid_lifecycle(self):
        events=[dict(op='create',id='a',tokens=3),dict(op='fork',id='b',parent='a'),dict(op='append',id='b',tokens=1)]
        r=calculate(events=events)
        before,after=r['kv_page_events'][1:]
        self.assertEqual(before['page_tables']['a'],before['page_tables']['b'])
        self.assertNotEqual(after['page_tables']['a'],after['page_tables']['b'])
        self.assertEqual(after['request_lengths'],{'a':3,'b':4})
        self.assertEqual(after['copied_valid_bytes'],3*144*1024)
        for bad in ([dict(op='cancel',id='missing')],[dict(op='create',id='a',tokens=65)]):
            with self.assertRaises(ValueError):calculate(events=bad)
