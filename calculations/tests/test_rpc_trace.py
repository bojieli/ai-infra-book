"""Archived timing partition, paired order statistics and immutable inputs."""
from pathlib import Path
from statistics import median
import sys
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from infra_calc.topics.rpc_trace import calculate, read_records


class RpcTraceTests(unittest.TestCase):
    def test_stage_partition_and_independent_order_statistics(self):
        records,_=read_records()
        raw={row['id']:row for row in records['results/client/requests.jsonl']}
        for size in (1024,65536,1048576):
            result=calculate(size)
            self.assertEqual(len(result['rpc_requests']),80)
            for row in result['rpc_requests']:
                metrics=row['metrics']
                self.assertEqual(sum(metrics[key] for key in ('encode_ns','prepare_ns','send_ns','response_wait_ns','verify_ns')),metrics['total_ns'])
                self.assertEqual(metrics['total_ns'],raw[row['id']]['end_ns']-raw[row['id']]['start_ns'])
            for group in result['rpc_groups']:
                samples=sorted(raw[row['id']]['end_ns']-raw[row['id']]['start_ns'] for row in result['rpc_requests'] if row['mode']==group['mode'])
                self.assertEqual(group['medians_ns']['total_ns'],(samples[9]+samples[10])/2)
                self.assertEqual(group['total_p95_ns'],samples[18])

    def test_pairing_and_measured_witness(self):
        result=calculate();rows={(row['mode'],row['trial']):row['metrics']['total_ns'] for row in result['rpc_requests']}
        for pair,(a,b) in zip(result['rpc_pairs'],((0,1),(1,2),(2,3))):
            expected=[rows[a,t]-rows[b,t] for t in range(20)]
            self.assertEqual(pair['saved_ns'],expected)
            self.assertEqual(pair['median_saved_ns'],median(expected))
        s=result['summary']
        self.assertEqual(s['json_client_cpu_median_ns'],9774500)
        self.assertEqual(s['binary_client_cpu_median_ns'],1084500)
        self.assertEqual(s['json_to_binary_positive_pairs'],11)
        self.assertEqual(s['json_to_binary_paired_median_saved_ns'],10093646.5)
        self.assertEqual(s['json_request_application_bytes'],[1398135])
        self.assertEqual(s['binary_request_application_bytes'],[1048593])
        self.assertNotEqual(result['rpc_pairs'][0]['median_saved_ns'],result['rpc_pairs'][0]['median_difference_ns'])

    def test_tampered_record_and_missing_payload_rejected(self):
        records,sources=read_records()
        records['results/client/requests.jsonl'][0]['payload_sha256']='bad'
        with patch('infra_calc.topics.rpc_trace.read_records',return_value=(records,sources)):
            with self.assertRaises(ValueError):calculate()
        with self.assertRaises(ValueError):calculate(123)
