import json
from statistics import median
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from infra_calc.topics.router_pressure import calculate,read_records


class PressureTests(unittest.TestCase):
    def test_raw_clocks_and_paired_differences(self):
        raw,_=read_records();events=[json.loads(line) for line in raw['results/raw.jsonl'].splitlines()]
        r=calculate();lookup={(e['trial'],e['policy']):e for e in events};savings=[]
        for row in r['pressure_requests']:
            e=lookup[row['trial'],row['policy']];t=e['target'];b=e['background']
            self.assertEqual(row['target_seconds'],t['end_s']-t['start_s'])
            self.assertEqual(row['pair_completion_seconds'],max(t['end_s'],b['end_s'])-b['start_s'])
        for trial in sorted({e['trial'] for e in events}):
            a=lookup[trial,'cache_first']['target'];b=lookup[trial,'queue_first']['target']
            savings.append((a['end_s']-a['start_s'])-(b['end_s']-b['start_s']))
        self.assertEqual(r['summary']['target_saved_seconds_paired_median'],median(savings))
        self.assertTrue(all(p['target_seconds_saved_by_queue_first']>0 for p in r['pressure_pairs']))
        self.assertTrue(all(p['pair_completion_seconds_added_by_queue_first']>0 for p in r['pressure_pairs']))

    def test_target_work_and_observed_hits(self):
        r=calculate();cold=set();warm=set()
        for row in r['pressure_requests']:
            if row['policy']=='cache_first':
                self.assertEqual(row['cached_tokens'],3135);self.assertGreaterEqual(row['sampled_waiting_peak'],1)
                warm.add(row['target_logical_matrix_flops'])
            else:
                self.assertEqual(row['cached_tokens'],0);self.assertEqual(row['target_saved_matrix_flops'],0)
                cold.add(row['target_logical_matrix_flops'])
        self.assertEqual(len(cold),1);self.assertEqual(len(warm),1);self.assertGreater(next(iter(cold)),next(iter(warm)))

    def test_wrong_decision_load_is_rejected(self):
        raw,sources=read_records();rows=[json.loads(line) for line in raw['results/raw.jsonl'].splitlines()]
        rows[0]['decision_load']['31191'][0]['num_reqs']=0
        raw['results/raw.jsonl']='\n'.join(json.dumps(row) for row in rows)
        with patch('infra_calc.topics.router_pressure.read_records',return_value=(raw,sources)):
            with self.assertRaisesRegex(ValueError,'Decision load'):calculate()
