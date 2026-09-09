import unittest
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from infra_calc.topics import attention_input_pipeline as calculate

class PipelineTests(unittest.TestCase):
    def test_slot_retained_through_consume(self):
        x=calculate.schedule([1,1,1],[5,5,5],2,1)
        rows=x['chunks']
        self.assertEqual([r['issue_start'] for r in rows],[0,8,16])
        self.assertEqual(x['finish_tick'],24)
    def test_exact_capacity_boundary(self):
        a=calculate.calculate(capacity_bytes=16384)
        b=calculate.calculate(capacity_bytes=16383)
        self.assertEqual(a['fastest_capacity_qualified_async_tick'],1280)
        self.assertIsNone(b['fastest_capacity_qualified_async_tick'])
    def test_saturation_and_clock_accounting(self):
        x=calculate.calculate()
        rows=[r for r in x['rows'] if r['mode'].startswith('asynchronous')]
        self.assertEqual(rows[2]['timing']['finish_tick'],rows[3]['timing']['finish_tick'])
        self.assertEqual(x['smallest_enumerated_slots_matching_unlimited'],4)
        self.assertTrue(all(r['timing']['finish_tick']==r['timing']['total_compute_busy_ticks']+r['timing']['total_compute_idle_ticks'] for r in rows))
    def test_reject_invalid(self):
        for inputs in ({'tile_k':3},{'tile_k':True},{'latency_ticks':-1},{'matrix_flops_per_tick':0}):
            with self.assertRaises(ValueError):calculate.calculate(**inputs)
        with self.assertRaises(ValueError):calculate.schedule([1],[2],0,0)
        with self.assertRaises(ValueError):calculate.schedule([1],[2],0,1,3,False)
