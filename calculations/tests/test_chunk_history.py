"""Raw event sample identity, token-pair partition and damaged trace rejection."""
import copy
from fractions import Fraction
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from infra_calc.topics.chunk_history import calculate,read_records,recount


class ChunkHistoryTests(unittest.TestCase):
    def test_raw_samples_and_paired_statistics(self):
        raw=read_records()[0]['results/run-v1/raw.json'];result=calculate();pairs=[]
        for record in raw['records']:
            steps=[s for s in record['steps'][0] if s['total_scheduled_tokens']]
            pairs.append(steps[-1]['event_ms']/steps[0]['event_ms'])
        self.assertEqual(result['summary']['paired_last_first_median'],sorted(pairs)[5])
        self.assertEqual(result['paired_last_first_ratios'],pairs)
        self.assertEqual(sum(len(r['samples_ms']) for r in result['chunk_history_rows']),176)
        for row in result['chunk_history_rows']:
            self.assertEqual(row['median_ms'],sorted(row['samples_ms'])[5])
        self.assertEqual(result['summary']['empty_execute_calls'],11)

    def test_causal_pair_partition_and_work_ratio(self):
        r=calculate();rows=r['chunk_history_rows']
        for row in rows:
            h=row['history_tokens']
            self.assertEqual(row['causal_pairs'],sum(h+i+1 for i in range(512)))
        self.assertEqual(sum(row['causal_pairs'] for row in rows),8192*8193//2)
        s=r['summary']
        self.assertEqual(sum(row['backbone_matrix_flops'] for row in rows),s['full_prefill_backbone_matrix_flops'])
        self.assertGreater(Fraction(s['causal_pair_ratio_exact']),30)
        self.assertLess(Fraction(s['backbone_matrix_ratio_exact']),Fraction(4,3))

    def test_corrupt_history_and_request_rejected(self):
        raw=read_records()[0]['results/run-v1/raw.json']
        damaged=copy.deepcopy(raw);step=damaged['records'][0]['steps'][0][0]
        rid=next(iter(step['prior_scheduled_tokens']));step['prior_scheduled_tokens'][rid]=512
        with self.assertRaises(ValueError):recount(damaged)
        damaged=copy.deepcopy(raw);damaged['records'][0]['output']['cached_tokens']=512
        with self.assertRaises(ValueError):recount(damaged)
