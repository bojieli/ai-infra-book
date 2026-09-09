"""Hand replay and paired-length correlation checks."""
import sys
from pathlib import Path
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from infra_calc.topics.request_trace import calculate


def row(p, g, arrival=0, prefill=5, decode=2):
    return dict(prompt_tokens=p, output_tokens=g, arrival_ns=arrival, prefill_ns=prefill, decode_ns=decode)


class RequestTraceTests(unittest.TestCase):
    def test_hand_fifo_and_kv_integral(self):
        result=calculate(workers=1, requests=[row(2,3),row(1,1,arrival=1,prefill=3)])
        a,b=result['request_rows']
        self.assertEqual((a['first_token_ns'],a['finish_ns']), (5,9))
        self.assertEqual((b['start_ns'],b['finish_ns'],b['waiting_ns']), (9,12,8))
        s=result['summary']; unit=s['kv_bytes_per_token']
        self.assertEqual(s['kv_peak_bytes'],4*unit)
        self.assertEqual(s['kv_residency_byte_ns'],27*unit)
        self.assertEqual(s['p95_latency_ns'],11)
        self.assertEqual(result['kv_timeline'][-1]['live_kv_bytes'],0)

    def test_capacity_serializes_despite_idle_worker(self):
        unit = calculate(requests=[row(1,1)])['summary']['kv_bytes_per_token']
        result = calculate(workers=2, requests=[row(2,3),row(2,3)], kv_capacity_bytes=4*unit)
        self.assertEqual([r['start_ns'] for r in result['request_rows']], [0,9])
        self.assertEqual(result['summary']['finish_ns'],18)
        self.assertEqual(result['summary']['kv_reservation_peak_bytes'],4*unit)
        self.assertEqual(result['summary']['kv_reservation_byte_ns'],72*unit)
        self.assertEqual(result['summary']['kv_residency_byte_ns'],48*unit)
        for event in result['kv_timeline']:
            self.assertLessEqual(event['live_kv_bytes'],event['reserved_kv_bytes'])
            self.assertLessEqual(event['reserved_kv_bytes'],4*unit)
        with self.assertRaises(ValueError):
            calculate(requests=[row(2,3)],kv_capacity_bytes=4*unit-1)

    def test_fifo_does_not_bypass_blocked_head(self):
        unit = calculate(requests=[row(1,1)])['summary']['kv_bytes_per_token']
        result = calculate(workers=3, requests=[row(2,3),row(2,3),row(1,1)],kv_capacity_bytes=5*unit)
        self.assertEqual([r['start_ns'] for r in result['request_rows']], [0,9,9])
        # Third request would fit at time 0, but must stay behind the second.
        ample = calculate(workers=3,requests=[row(2,3),row(2,3),row(1,1)],kv_capacity_bytes=9*unit)
        self.assertEqual([r['start_ns'] for r in ample['request_rows']], [0,0,0])
        self.assertEqual(result['summary']['decode_matrix_flops'],ample['summary']['decode_matrix_flops'])

    def test_pairing_changes_work_without_changing_marginals(self):
        same=calculate(requests=[row(2,2),row(6,6)])['summary']
        opposite=calculate(requests=[row(2,6),row(6,2)])['summary']
        self.assertEqual(same['mean_prompt_tokens'],opposite['mean_prompt_tokens'])
        self.assertEqual(same['mean_output_tokens'],opposite['mean_output_tokens'])
        self.assertEqual(same['prefill_matrix_flops'],opposite['prefill_matrix_flops'])
        self.assertGreater(same['decode_matrix_flops'],opposite['decode_matrix_flops'])

    def test_arrivals_change_waiting_not_total_work(self):
        burst=calculate(workers=1,requests=[row(3,3),row(3,3)])['summary']
        spaced=calculate(workers=1,requests=[row(3,3),row(3,3,arrival=100)])['summary']
        self.assertEqual(burst['decode_matrix_flops'],spaced['decode_matrix_flops'])
        self.assertEqual(spaced['p95_waiting_ns'],0)
        self.assertGreater(burst['p95_waiting_ns'],0)
        for args in [dict(requests=[]),dict(workers=0),dict(requests=[row(1,0)]),dict(requests=[row(999999,1)])]:
            with self.assertRaises(ValueError): calculate(**args)
