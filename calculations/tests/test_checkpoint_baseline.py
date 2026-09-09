import json
from pathlib import Path
import sys
import unittest
from statistics import median
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from infra_calc.topics import checkpoint_baseline as baseline


class CheckpointBaselineTests(unittest.TestCase):
    def test_independent_paired_raw_windows(self):
        raw,_=baseline.read_records();r=baseline.calculate();differences=[]
        for trial in range(5):
            durations={}
            for mode in ('none','async'):
                record=json.loads(raw[f'results/run-v1/trial-{trial}-{mode}/raw.json'])
                start=next(x['t_s'] for x in record['events'] if x['event']=='window_start')
                end=next(x['t_s'] for x in record['events'] if x['event']=='window_end')
                durations[mode]=end-start
            differences.append(durations['async']-durations['none'])
        self.assertEqual(r['summary']['median_paired_async_minus_none_window_seconds'],median(differences))
        self.assertEqual(r['summary']['archived_evidence_files'],39)

    def test_observation_and_missing_measurements(self):
        r=baseline.calculate();m={row['mode']:row for row in r['checkpoint_baseline_modes']}
        self.assertIsNone(m['none']['api_seconds']);self.assertIsNone(m['sync']['stage_seconds'])
        self.assertGreater(m['async']['commit_from_call_seconds'],m['async']['api_seconds'])
        self.assertEqual(m['async']['commit_after_training_seconds'],0)
        self.assertEqual(m['sync']['writer_training_overlap_seconds'],0)
        self.assertEqual(r['summary']['restored_checkpoints'],10)

    def test_state_and_payload_evidence_rejected(self):
        raw,sources=baseline.read_records()
        key='results/run-v1/trial-0-async/raw.json'
        record=json.loads(raw[key]);record['final_state']['rng']='different'
        changed=dict(raw);changed[key]=json.dumps(record).encode()
        with patch.object(baseline,'read_records',return_value=(changed,sources)):
            with self.assertRaises(ValueError):baseline.calculate()
        key='results/run-v1/trial-0-async/checkpoint/__0_0.distcp'
        changed=dict(raw);changed[key]=raw[key][:-1]+bytes([raw[key][-1]^1])
        with patch.object(baseline,'read_records',return_value=(changed,sources)):
            with self.assertRaises(ValueError):baseline.calculate()
