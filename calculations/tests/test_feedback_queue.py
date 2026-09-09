"""Finite-buffer conservation and independent clipped-fluid replay."""
from fractions import Fraction
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from infra_calc.topics.feedback_queue import calculate
from infra_calc.topics.periodic_queue import calculate as periodic


class FeedbackQueueTests(unittest.TestCase):
    def test_fill_drain_and_area(self):
        r=calculate(buffer_bytes=524288);s=r['summary']
        self.assertEqual(s['dropped_exact_bytes'],'337856')
        self.assertEqual(s['peak_queue_exact_bytes'],'524288')
        self.assertEqual(Fraction(s['last_drain_exact_ns']),Fraction(362144,5))
        fill=Fraction(524288-262144,30)
        self.assertEqual(Fraction(r['queue_segments'][0]['end_exact_ns']),fill)
        area=(262144+524288)*fill/2+524288*(20000-fill)+Fraction(524288**2,20)
        self.assertEqual(Fraction(s['queue_area_exact_byte_ns']),area)
        self.assertEqual(calculate(feedback_ns=40000,buffer_bytes=524288)['summary']['dropped_exact_bytes'],'937856')
        for buffer in (None,1048576):
            row=calculate(buffer_bytes=buffer)['summary']
            self.assertEqual(row['dropped_exact_bytes'],'0')
            self.assertEqual(row['peak_queue_exact_bytes'],'862144')

    def test_finite_buffer_replay_and_conservation(self):
        for buffer in (0,1,4,10):
            for initial in (0,buffer):
                for offset in (0,2,5):
                    jobs=[dict(period_ns=7,on_ns=3,offset_ns=offset,rate_bytes_per_second=5*10**9)]
                    r=periodic(jobs=jobs,capacity_bytes_per_second=3*10**9,window_ns=35,
                               initial_queue_bytes=initial,buffer_bytes=buffer)
                    q=peak=initial;dropped=arrived=0
                    for t in range(35):
                        rate=5 if (t-offset)%7<3 else 0
                        arrived+=rate
                        raw=max(0,q+rate-3)
                        dropped+=max(0,raw-buffer);q=min(buffer,raw);peak=max(peak,q)
                    s=r['summary']
                    self.assertEqual(Fraction(s['dropped_exact_bytes']),dropped)
                    self.assertEqual(Fraction(s['peak_queue_exact_bytes']),peak)
                    self.assertEqual(Fraction(s['final_queue_exact_bytes']),q)
                    self.assertEqual(initial+arrived,Fraction(s['served_exact_bytes'])+dropped+q)
                    for row in r['queue_segments']:
                        self.assertEqual(Fraction(row['queue_start_exact_bytes'])+Fraction(row['arrived_exact_bytes']),
                                         sum(Fraction(row[key]) for key in ('queue_end_exact_bytes','served_exact_bytes','dropped_exact_bytes')))

    def test_no_drain_zero_rate_and_invalid_initial(self):
        s=calculate(reduced_bytes_per_second=50*10**9)['summary']
        self.assertEqual(s['final_queue_exact_bytes'],'862144')
        self.assertIsNone(s['last_drain_exact_ns'])
        self.assertFalse(s['after_feedback_rate_below_capacity'])
        self.assertEqual(calculate(reduced_bytes_per_second=0)['summary']['final_queue_exact_bytes'],'0')
        with self.assertRaises(ValueError):calculate(buffer_bytes=1)
