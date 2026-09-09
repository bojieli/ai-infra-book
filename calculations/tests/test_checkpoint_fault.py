import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from infra_calc.topics import checkpoint_fault as fault


class CheckpointFaultTests(unittest.TestCase):
    def test_incomplete_bytes_not_commit(self):
        r=fault.calculate();row=r['checkpoint_fault_rows'][-1]
        self.assertEqual(row['data_file_bytes'],12622659)
        self.assertFalse(row['metadata_present']);self.assertFalse(row['actual_load_succeeded'])
        self.assertIsNone(row['commit_from_call_seconds']);self.assertIsNone(row['future_observed_from_call_seconds'])
        self.assertEqual(r['summary']['completed_updates_after_recovery_point'],40)

    def test_independent_raw_clock(self):
        raw,_=fault.read_records();r=fault.calculate()
        events=[json.loads(x) for x in raw['results/fault/events.jsonl'].splitlines()]
        start=next(e['monotonic_s'] for e in events if e.get('checkpoint')=='checkpoint-2' and e['event']=='api_call')
        kill=json.loads(raw['results/outcomes.json'])['fault']['sigkill_monotonic_s']
        self.assertEqual(r['checkpoint_fault_rows'][-1]['unfinished_observation_seconds'],kill-start)
        self.assertEqual(sum(row['actual_load_succeeded'] for row in r['checkpoint_fault_rows']),3)

    def test_forged_completion_rejected(self):
        raw,sources=fault.read_records();changed=dict(raw)
        changed['results/fault/checkpoint-2/.metadata']=b'not-a-committed-checkpoint'
        with patch.object(fault,'read_records',return_value=(changed,sources)):
            with self.assertRaises(ValueError):fault.calculate()
