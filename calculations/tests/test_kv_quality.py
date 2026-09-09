"""Strict answer parsing, independent pool geometry and batch time denominator."""
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from infra_calc.topics.kv_quality import calculate,strict_answer,read_records,RUNS


class KVQualityTests(unittest.TestCase):
    def test_strict_answer(self):
        expected={'k0001':'123456'}
        self.assertTrue(strict_answer('{"k0001":"123456"}',expected))
        for text in ('{"k0001":"123456","k0001":"123456"}', 'Answer: {"k0001":"123456"}', '{"k0001":123456}', '{"k0001":"123456","extra":0}'):
            self.assertFalse(strict_answer(text,expected))

    def test_real_pool_geometry_and_natural_counts(self):
        results=[calculate(run) for run in RUNS]
        self.assertEqual([r['summary']['natural_correct'] for r in results],[28,26,28])
        self.assertEqual(len({r['summary']['storage_bytes'] for r in results}),1)
        for r,element_bytes in zip(results,(2,1,1)):
            s=r['summary'];self.assertEqual(s['storage_bytes'],s['blocks']*16*2*36*8*128*element_bytes)
            self.assertEqual(s['natural_output_lengths'],[46]);self.assertEqual(s['natural_length_stops'],0)
            self.assertEqual(s['distinct_tasks'],8)
        self.assertTrue(results[2]['paired_against_bf16']['fp8_qbf16']['natural_correctness_changes'])

    def test_raw_batch_windows(self):
        records,_=read_records()
        for run in RUNS:
            r=calculate(run)
            for condition in r['kv_quality_conditions']:
                batches=[b for b in records[f'results/{run}/batches.jsonl'] if b['trial']!='warm' and (b['rows'],b['concurrency'],b['mode'])==(condition['document_rows'],condition['concurrency'],condition['mode'])]
                window=sum(b['end_s']-b['start_s'] for b in batches)
                self.assertEqual(condition['batch_window_s'],window)
                self.assertEqual(condition['output_tokens_per_s'],condition['output_tokens']/window)
                if condition['mode']=='fixed':self.assertIsNone(condition['correct'])
