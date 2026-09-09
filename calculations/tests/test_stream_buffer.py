"""Independent tick simulation checks FIFO recurrence and same-tick ordering."""
from collections import deque
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from infra_calc.topics.stream_buffer import calculate, schedule


def replay(n, pi, ci, cap):
    queue = deque()
    produced, consumed = [], []
    next_produce, next_consume, tick = 4, 5, 0
    while len(consumed) < n:
        if queue and tick >= next_consume:
            queue.popleft()
            consumed.append(tick)
            next_consume = tick + ci
        if len(produced) < n and tick >= next_produce and len(queue) < cap:
            queue.append(len(produced))
            produced.append(tick)
            next_produce = tick + pi
        tick += 1
    return produced, consumed


class StreamBufferTests(unittest.TestCase):
    def test_book_capacity_and_backpressure(self):
        r=calculate();s=r['summary'];b=r['fifo_schedules']['bounded']
        self.assertEqual(s['block_bytes'],16384)
        self.assertEqual(s['original_fifo_peak_bytes'],49152)
        self.assertEqual(s['original_handoff_required_bytes'],81920)
        self.assertFalse(s['original_progress_fits'])
        self.assertEqual(b['produce_ticks'],[4,5,6,7,9])
        self.assertEqual(b['consume_ticks'],[5,7,9,11,13])
        self.assertEqual(s['producer_final_delay_ticks'],1)
        self.assertEqual(s['consumer_final_delay_ticks'],0)
        self.assertEqual(s['bounded_handoff_peak_bytes'],65536)
        unified=calculate(reorder_slots=0)
        self.assertTrue(unified['summary']['original_progress_fits'])
        self.assertEqual(unified['fifo_schedules']['original'],unified['fifo_schedules']['bounded'])

    def test_recurrence_against_tick_simulator(self):
        for n in (1,5,11):
            for pi in (1,2,5):
                for ci in (1,3,7):
                    for cap in (1,2,4):
                        r=schedule(n,4,pi,5,ci,cap)
                        p,c=replay(n,pi,ci,cap)
                        self.assertEqual(r['produce_ticks'],p)
                        self.assertEqual(r['consume_ticks'],c)
                        for event in r['timeline']:
                            self.assertGreaterEqual(event['occupied_slots'],0)
                            self.assertLessEqual(event['occupied_slots'],cap)
                        self.assertEqual(r['timeline'][-1]['occupied_slots'],0)

    def test_no_slot_and_changed_supply(self):
        self.assertIsNone(calculate(budget_bytes=32768)['fifo_schedules']['bounded'])
        self.assertEqual(calculate(produce_interval=3)['summary']['bounded_last_take_tick'],17)
        self.assertEqual(calculate(budget_bytes=49152)['summary']['bounded_last_take_tick'],13)
        for kwargs in ({'reorder_slots':-1},{'reorder_slots':True},{'blocks':0}):
            with self.assertRaises(ValueError):calculate(**kwargs)
