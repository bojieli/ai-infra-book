"""Explicit event replay, mathematical products and recorded-sample matching."""
from collections import Counter
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from infra_calc.topics.loop_access import counts,events,calculate


class LoopAccessTests(unittest.TestCase):
    def test_tail_event_counts_and_numerical_product(self):
        m,k,n=3,5,4
        a=[i-3 for i in range(m*k)]; b=[2*i-7 for i in range(k*n)]
        reference=[sum(a[i*k+z]*b[z*n+j] for z in range(k)) for i in range(m) for j in range(n)]
        for method,tile in [('ijk',2),('ikj',2),('blocked',2),('blocked',7)]:
            seen=Counter(); output=[0]*(m*n); av=ai=None
            for operation,index in events(m,k,n,method,tile):
                seen[operation]+=1
                if operation=='a_array_reads': av=a[index];ai=index//k
                if operation=='b_array_reads': output[ai*n+index%n]+=av*b[index]
            self.assertEqual(output,reference)
            expected=counts(m,k,n,method,tile)
            for key in ['a_array_reads','b_array_reads','c_array_reads','c_update_writes','c_zeroed_elements']:
                self.assertEqual(seen[key],expected[key])
            self.assertEqual(sum(seen.values())*4,expected['source_array_bytes'])

    def test_measured_match_is_exact_and_counts_not_time_model(self):
        rows=calculate(m=127,k=257,n=65)['loop_access_rows']
        self.assertEqual(rows[0]['measured_median_us'],1398.3)
        self.assertGreater(rows[1]['source_array_bytes'],rows[0]['source_array_bytes'])
        self.assertLess(rows[1]['measured_median_us'],rows[0]['measured_median_us'])
        self.assertEqual(calculate(m=2,k=3,n=4)['summary']['candidates_with_recorded_samples'],0)
        self.assertIsNone(calculate(m=2,k=3,n=4)['loop_access_rows'][0]['measured_median_us'])
