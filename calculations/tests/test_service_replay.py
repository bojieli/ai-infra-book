"""Independent raw delivery statistics, window denominator and boundary check."""
import copy
import math
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from infra_calc.topics.service_replay import calculate,read_records,delivery_rows,RUNS


class ServiceReplayTests(unittest.TestCase):
    def test_actual_windows_and_joint_count(self):
        records,_=read_records()
        for run in RUNS:
            result=calculate(run);events=records[f'results/measured-{run}/events.jsonl']
            windows=[]
            for trial in range(3):
                group=[e for e in events if e['trial']==trial]
                windows.append(max(e['delivered_s'] for e in group if e['new_token_ids'])-min(e['submitted_s'] for e in group))
            passed=sum(row['delivered_ttft_ms']<=300 and row['delivered_e2e_ms']<=2000 and row['delivered_mean_tpot_ms']<=20 for row in result['service_requests'])
            self.assertEqual(result['summary']['summed_observation_window_s'],sum(windows))
            self.assertEqual(result['summary']['timing_goodput_requests_per_s'],passed/sum(windows))
            self.assertEqual(result['summary']['output_tokens'],2016)

    def test_threshold_equality(self):
        r=calculate()['service_requests'][0];limit=r['delivered_ttft_ms']
        yes=calculate(ttft_limit_ms=limit,e2e_limit_ms=100000,mean_tpot_limit_ms=100000)
        no=calculate(ttft_limit_ms=math.nextafter(limit,0),e2e_limit_ms=100000,mean_tpot_limit_ms=100000)
        self.assertTrue(yes['service_requests'][0]['joint_timing_pass'])
        self.assertFalse(no['service_requests'][0]['joint_timing_pass'])

    def test_reject_incomplete_and_cumulative_records(self):
        records,_=read_records();prefix='results/measured-chunk512/'
        events=copy.deepcopy(records[prefix+'events.jsonl']);inputs=records[prefix+'requests.json']
        events[0]['cumulative_tokens']+=1
        with self.assertRaises(ValueError):delivery_rows(events,inputs)
        events=copy.deepcopy(records[prefix+'events.jsonl']);events[-1]['finished']=False
        with self.assertRaises(ValueError):delivery_rows(events,inputs)
