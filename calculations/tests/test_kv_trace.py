"""Raw block count oracle, cancellation difference and corruption rejection."""
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from infra_calc.topics.kv_trace import calculate, read_records, recount


class KvTraceTests(unittest.TestCase):
    def test_real_pool_and_scheduled_work(self):
        records,_=read_records();r=calculate()
        self.assertEqual(r['comparison']['extra_scheduled_positions'],1805)
        self.assertTrue(r['comparison']['small_large_outputs_match'])
        self.assertTrue(r['comparison']['cancel_survivors_match'])
        for name,expected in (('small',(455,454,9993)),('large',(910,512,8188)),('cancel',(455,419,7805))):
            rows=records['results/'+name+'/blocks.jsonl'];observed=r['kv_trace_runs'][name]
            self.assertEqual((observed['total_blocks'],observed['peak_request_blocks'],observed['scheduled_token_positions']),expected)
            totals=[sum(len(q['blocks'][0]) for q in row['requests']) for row in rows]
            self.assertEqual(max(totals),observed['peak_request_blocks'])
            self.assertEqual(sum(sum(row['scheduled_tokens'].values()) for row in rows if row['event']=='schedule'),observed['scheduled_token_positions'])
        self.assertEqual(r['kv_trace_runs']['small']['preemptions'][0]['preserved_output_tokens'],270)

    def test_cancel_and_geometry(self):
        r=calculate('cancel');s=r['summary']
        self.assertEqual(s['block_bytes'],16*144*1024)
        self.assertEqual(r['cancellation']['released_blocks'],104)
        self.assertEqual(r['cancellation']['released_payload_capacity_bytes'],234*1024**2)
        self.assertGreater(r['cancellation']['release_observed_s'],r['cancellation']['api_returned_s'])
        self.assertEqual(r['kv_trace_timeline'][-1]['request_blocks'],0)
        for row in r['kv_trace_timeline']:
            self.assertEqual(row['free_blocks']+row['request_blocks']+1,455)

    def test_corrupt_pool_rejected(self):
        records,_=read_records();blocks=records['results/small/blocks.jsonl']
        blocks[1]['free_blocks']+=1
        with self.assertRaises(ValueError):recount(blocks,144*1024)
        with self.assertRaises(ValueError):calculate('unknown')
