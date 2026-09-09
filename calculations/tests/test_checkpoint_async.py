from pathlib import Path
from fractions import Fraction as F
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from infra_calc.topics.checkpoint_async import calculate


class CheckpointAsyncTests(unittest.TestCase):
    def test_book_durability_not_staging(self):
        args=dict(payload_bytes=112*10**9,snapshots=2,interval_ns=20*10**9)
        slow=calculate(**args);fast=calculate(**args,upload_bytes_per_second=16*10**9)
        self.assertEqual([r['exact_seconds']['durable'] for r in slow['checkpoint_save_rows']],['69/2','109/2'])
        self.assertEqual(slow['summary']['recovery_capture_exact_seconds'],'20')
        self.assertEqual(fast['summary']['recovery_capture_exact_seconds'],'40')
        self.assertEqual(slow['summary']['total_training_barrier_union_exact_seconds'],'1')
        self.assertEqual(calculate(**args,failure_ns=34500000000)['summary']['completed_durable_at_failure'],1)
        self.assertIsNone(calculate(**args,failure_ns=20500000000)['summary']['latest_recoverable_snapshot'])

    def test_backpressure_and_no_buffer_reuse_before_read(self):
        r=calculate(payload_bytes=112*10**9,buffer_slots=1)
        rows=r['checkpoint_save_rows']
        for old,new in zip(rows,rows[1:]):
            self.assertGreaterEqual(F(new['exact_seconds']['capture']),F(old['exact_seconds']['upload_end']))
        self.assertEqual(r['summary']['snapshot_buffer_live_peak_bytes'],112*10**9)
        self.assertEqual(rows[1]['exact_seconds']['capture'],'69/2')
        # Independent half-second sampling of the pause union.
        intervals=[(F(x['exact_seconds']['requested']),F(x['exact_seconds']['staging_end'])) for x in rows]
        ticks=sum(any(a<=F(t,2)<b for a,b in intervals) for t in range(400))
        self.assertEqual(F(r['summary']['total_training_barrier_union_exact_seconds']),F(ticks,2))

    def test_official_payload_and_delayed_commit(self):
        r=calculate()
        self.assertEqual(r['summary']['payload_bytes'],14*8190735360)
        self.assertEqual(F(r['summary']['upload_service_exact_seconds']),F(14*8190735360,8*10**9))
        delayed=calculate(payload_bytes=112*10**9,snapshots=2,interval_ns=20*10**9,durability_delay_ns=20*10**9)
        self.assertEqual(delayed['checkpoint_save_rows'][1]['exact_seconds']['upload_start'],'81/2')
        self.assertIsNone(delayed['summary']['latest_recoverable_snapshot'])
        for kw in ({'buffer_slots':0},{'payload_bytes':True},{'interval_ns':0}):
            with self.assertRaises(ValueError):calculate(**kw)
