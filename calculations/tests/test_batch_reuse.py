"""Independent batch/serial traffic and exact crossover/capacity boundaries."""
from fractions import Fraction as F
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from infra_calc.topics.batch_reuse import calculate
from infra_calc.models import forward
from infra_calc.schema import Scenario


class BatchReuseTests(unittest.TestCase):
    def test_actual_batch_work_and_saved_traffic(self):
        r=calculate()
        for row in r['batch_reuse_rows']:
            b=row['batch']
            actual=forward('qwen3-8b',Scenario(batch=b,tokens=1,history=2048))
            self.assertEqual(row['matrix_flops'],actual['summary']['matrix_flops'])
            self.assertEqual(row['serial_declared_traffic_bytes']-row['declared_traffic_bytes'],row['saved_weight_read_bytes'])
            self.assertEqual(row['kv_history_read_bytes'],b*2048*147456)
        self.assertEqual(r['selected_peak']['accumulator_precision'],'FP32')
        self.assertEqual(r['selected_peak']['sparsity'],'dense')

    def test_capacity_and_kv_crossover_neighbors(self):
        for device in ('rtx4090','h100-sxm'):
            for history in (2048,8192):
                s=calculate(device=device,history=history)['summary'];cap=s['declared_capacity_max_batch']
                r=calculate(device=device,history=history,batches=[cap,cap+1])
                self.assertTrue(r['batch_reuse_rows'][0]['capacity_feasible'])
                self.assertFalse(r['batch_reuse_rows'][1]['capacity_feasible'])
                self.assertIsNone(r['batch_reuse_rows'][1]['runnable_lower_ns_exact'])
                k=s['kv_history_equals_weights_batch'];unit=s['per_request_history_read_bytes'];w=s['shared_decode_weight_read_bytes']
                self.assertLess((k-1)*unit,w);self.assertGreaterEqual(k*unit,w)
                self.assertIsNone(s['compute_memory_crossover_batch'])

    def test_compute_crossover_without_history(self):
        s=calculate(history=0)['summary'];cross=s['compute_memory_crossover_batch']
        self.assertIsNotNone(cross)
        r=calculate(history=0,batches=[cross-1,cross])
        before,after=r['batch_reuse_rows']
        self.assertLess(F(before['compute_lower_ns_exact']),F(before['memory_lower_ns_exact']))
        self.assertGreaterEqual(F(after['compute_lower_ns_exact']),F(after['memory_lower_ns_exact']))
        self.assertIsNone(s['kv_history_equals_weights_batch'])
        with self.assertRaises(ValueError):calculate(batches=[1,1])
