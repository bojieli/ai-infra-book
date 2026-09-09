"""Book fluid backlog, wraparound demand and independent per-tick replay."""
from fractions import Fraction
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from infra_calc.topics.periodic_queue import calculate


class PeriodicQueueTests(unittest.TestCase):
    def test_book_peak_area_and_offset(self):
        r=calculate();s=r['summary']
        self.assertEqual(s['peak_queue_exact_bytes'],'600000000')
        self.assertEqual(s['compatibility_exact'],'22/25')
        self.assertEqual(s['peak_queue_virtual_wait_exact_ns'],'12000000')
        self.assertEqual(s['last_drain_exact_ns'],'32000000')
        self.assertEqual(s['mean_queue_bytes'],96000000)
        jobs=r['scenario']['jobs'];jobs[1]['offset_ns']=20000000
        staggered=calculate(jobs=jobs)['summary']
        self.assertEqual(staggered['peak_queue_bytes'],0)
        self.assertEqual(staggered['compatibility'],1)
        jobs[1]['offset_ns']=15000000
        self.assertEqual(calculate(jobs=jobs)['summary']['peak_queue_bytes'],150000000)

    def test_wrap_and_multiple_periods_by_ticks(self):
        for offset in (0,2,5,12):
            jobs=[dict(period_ns=7,on_ns=3,offset_ns=offset,rate_bytes_per_second=5*10**9),
                  dict(period_ns=5,on_ns=1,offset_ns=0,rate_bytes_per_second=2*10**9)]
            r=calculate(jobs=jobs,capacity_bytes_per_second=3*10**9)
            self.assertEqual(r['scenario']['window_ns'],35)
            q=peak=arrivals=excess=0
            for t in range(35):
                rate=sum(j['rate_bytes_per_second']//10**9 for j in jobs if (t-j['offset_ns'])%j['period_ns']<j['on_ns'])
                arrivals+=rate;excess+=max(0,rate-3)
                q=max(0,q+rate-3);peak=max(peak,q)
            s=r['summary']
            self.assertEqual(Fraction(s['final_queue_exact_bytes']),q)
            self.assertEqual(Fraction(s['peak_queue_exact_bytes']),peak)
            self.assertEqual(Fraction(s['arrived_exact_bytes']),arrivals)
            self.assertEqual(Fraction(s['excess_demand_exact_bytes']),excess)
            self.assertEqual(Fraction(s['served_exact_bytes'])+q,arrivals)
            for row in r['queue_segments']:
                served=Fraction(row['served_exact_bytes'])
                self.assertGreaterEqual(served,0)
                self.assertLessEqual(served,3*(Fraction(row['end_exact_ns'])-Fraction(row['start_exact_ns'])))

    def test_overload_and_rejection(self):
        jobs=[dict(period_ns=10,on_ns=10,offset_ns=0,rate_bytes_per_second=150*10**9)]
        s=calculate(jobs=jobs)['summary']
        self.assertEqual(s['compatibility'],-1)
        self.assertEqual(s['final_queue_bytes'],1000)
        self.assertEqual(s['stop_arrivals_final_drain_exact_ns'],'20')
        with self.assertRaises(ValueError):calculate(jobs=[dict(jobs[0],on_ns=11)])
        with self.assertRaises(ValueError):calculate(capacity_bytes_per_second=0)
