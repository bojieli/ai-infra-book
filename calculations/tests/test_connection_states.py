"""Independent group partitions, sparse activity and state-budget boundaries."""
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from infra_calc.topics.connection_states import calculate


class ConnectionStateTests(unittest.TestCase):
    def test_book_and_isolation(self):
        s=calculate()['summary']
        self.assertEqual(s['active_relations'],8192)
        self.assertEqual(s['coupled_total_bytes'],8929280)
        self.assertEqual(s['shared_total_bytes'],671744)
        self.assertTrue(s['shared_fits_budget'])
        isolated=calculate(isolation_classes=8)['summary']
        self.assertEqual(isolated['shared_transport_count'],1024)
        self.assertEqual(isolated['shared_total_bytes'],1589248)
        self.assertFalse(isolated['shared_fits_budget'])
        dedicated=calculate(isolation_classes=64)['summary']
        self.assertEqual(dedicated['saved_bytes'],0)
        self.assertTrue(calculate(budget_bytes=671744)['summary']['shared_fits_budget'])
        self.assertFalse(calculate(budget_bytes=671743)['summary']['shared_fits_budget'])

    def test_sparse_partition_by_independent_equivalence(self):
        for classes in (1,2,3,8):
            relations=[dict(thread=t,peer=p) for t in range(5) for p in range(4) if (t+p)%3==0]
            result=calculate(threads=5,peers=4,isolation_classes=classes,relations=relations)
            remaining={(r['thread'],r['peer']) for r in relations}
            expected=[]
            while remaining:
                t,p=next(iter(remaining))
                group={(u,v) for u,v in remaining if v==p and (u-t)%classes==0}
                expected.append(group);remaining-=group
            actual=[{(t,row['peer']) for t in row['threads']} for row in result['transport_groups']]
            self.assertEqual({frozenset(g) for g in actual},{frozenset(g) for g in expected})
            s=result['summary']
            self.assertEqual(s['active_relations'],sum(len(group) for group in actual))
            self.assertEqual(s['saved_bytes'],(len(relations)-len(actual))*1024)

    def test_empty_hotspot_and_validation(self):
        empty=calculate(relations=[])['summary']
        self.assertEqual(empty['shared_total_bytes'],64*256)
        self.assertEqual(empty['active_local_endpoints'],0)
        hot=calculate(relations=[dict(thread=t,peer=0) for t in range(64)])['summary']
        self.assertEqual(hot['shared_transport_count'],1)
        self.assertEqual(hot['shared_total_bytes'],21504)
        for relations in ([dict(thread=64,peer=0)],[dict(thread=0,peer=0)]*2):
            with self.assertRaises(ValueError):calculate(relations=relations)
