"""Independent clock-tick credit and completion-consumer simulation."""
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from infra_calc.topics.completion_reclaim import calculate


class CompletionReclaimTests(unittest.TestCase):
    def test_book_and_more_slots(self):
        s=calculate()['summary']
        self.assertEqual(s['all_transfers_complete_ns'],48000)
        self.assertEqual(s['all_slots_reclaimed_ns'],80000)
        self.assertEqual(s['peak_unconsumed_completions'],8)
        self.assertEqual(s['reserved_slot_payload_bytes'],65536)
        more=calculate(slots=16)['summary']
        self.assertEqual(more['all_transfers_complete_ns'],20000)
        self.assertEqual(more['all_slots_reclaimed_ns'],80000)
        self.assertEqual(more['max_submission_delay_ns'],0)
        slow=calculate(poll_batch=1)['summary']
        self.assertEqual(slow['all_slots_reclaimed_ns'],320000)

    def test_tick_simulation(self):
        for slots in (1,3,8):
            for poll in (2,5,9):
                for batch in (1,2,4):
                    r=calculate(operations=12,slots=slots,submit_interval_ns=2,
                                transfer_latency_ns=3,poll_interval_ns=poll,poll_batch=batch)
                    submitted=[];consumed={};last=-2;peak=0
                    for time in range(1000):
                        if time and time%poll==0:
                            ready=[i for i,start in enumerate(submitted) if start+3<=time and i not in consumed]
                            for i in ready[:batch]:consumed[i]=time
                        if len(submitted)<12 and len(submitted)-len(consumed)<slots and time>=len(submitted)*2 and time-last>=2:
                            submitted.append(time);last=time
                        peak=max(peak,len(submitted)-len(consumed))
                        if len(consumed)==12:break
                    self.assertEqual(submitted,[row['submit_ns'] for row in r['completion_operations']])
                    self.assertEqual([consumed[i] for i in range(12)],[row['completion_consumed_ns'] for row in r['completion_operations']])
                    self.assertEqual(peak,r['summary']['peak_outstanding'])

    def test_slot_lifetimes_and_wait_integral(self):
        r=calculate();rows=r['completion_operations']
        for slot in range(8):
            use=[row for row in rows if row['slot']==slot]
            for left,right in zip(use,use[1:]):
                self.assertLessEqual(left['completion_consumed_ns'],right['submit_ns'])
        times=sorted({row[key] for row in rows for key in ('transfer_complete_ns','completion_consumed_ns')})
        area=sum((b-a)*sum(row['transfer_complete_ns']<=a<row['completion_consumed_ns'] for row in rows) for a,b in zip(times,times[1:]))
        self.assertEqual(area,r['summary']['total_reclaim_wait_ns'])
        for kwargs in (dict(slots=0),dict(poll_batch=0),dict(operations=0)):
            with self.assertRaises(ValueError):calculate(**kwargs)
