import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from infra_calc.topics.cache_fault import calculate,read_records


class CacheFaultTests(unittest.TestCase):
    def test_censored_request_is_not_a_completion(self):
        r=calculate();wait=r['fault_policy_rows'][0]
        self.assertFalse(wait['completed']);self.assertIsNone(wait['completion_seconds'])
        self.assertIsNone(wait['cached_tokens']);self.assertIsNone(wait['completed_fallback_prefill_matrix_flops'])
        self.assertGreater(wait['incomplete_observation_lower_seconds'],60)
        self.assertEqual(r['summary']['completed_requests'],2)

    def test_raw_event_timing_and_work(self):
        raw,_=read_records()
        for row in calculate()['fault_policy_rows'][1:]:
            events=[json.loads(line) for line in raw[row['policy']+'/results/lifecycle.jsonl'].decode().splitlines()]
            start=next(e['time_s'] for e in events if e['event']=='request_start')
            end=next(e['time_s'] for e in events if e['event']=='request_return')
            self.assertEqual(row['completion_seconds'],end-start)
            self.assertLess(row['exception_after_request_seconds'],end-start)
            self.assertEqual(row['cached_tokens'],0)
            self.assertTrue(row['corrupt_file_reported_unchanged'])

    def test_no_observed_exception_is_rejected(self):
        raw,sources=read_records();name='timeout/results/storage.jsonl'
        events=[json.loads(line) for line in raw[name].decode().splitlines()]
        raw[name]='\n'.join(json.dumps(e) for e in events if e['event']!='exception').encode()
        with patch('infra_calc.topics.cache_fault.read_records',return_value=(raw,sources)):
            with self.assertRaisesRegex(ValueError,'short-read'):calculate()
