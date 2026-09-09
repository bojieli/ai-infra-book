import unittest
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from infra_calc.topics import matrix_vector_handoff as calculate
class HandoffTests(unittest.TestCase):
    def test_capacity_one_byte(self):
        r=calculate.calculate(capacity_bytes=49152)
        self.assertIsNotNone(r['summary']['capacity_qualified_finish_tick'])
        r=calculate.calculate(capacity_bytes=49151)
        self.assertIsNone(r['summary']['capacity_qualified_finish_tick'])
    def test_crossing_payload_conserved(self):
        staged=calculate.calculate(path='staged');direct=calculate.calculate(path='direct')
        self.assertEqual(staged['summary']['crossing_payload_bytes'],direct['summary']['crossing_payload_bytes'])
        self.assertEqual(staged['summary']['served_handoff_bytes'],2*direct['summary']['served_handoff_bytes'])
    def test_complete_row_dependency(self):
        r=calculate.calculate(group_rows=128,slots=1)
        t={e['id']:e for e in r['timeline']}
        self.assertGreaterEqual(t['g0.softmax']['start_tick'],t['g0.qk']['end_tick'])
        self.assertEqual(t['g0.qk']['duration_ticks'],512)
    def test_reject_input(self):
        for kwargs in [{'group_rows':33},{'slots':0},{'path':'vendor-fast'},{'exp_ops_per_tick':False}]:
            with self.assertRaises(ValueError):calculate.calculate(**kwargs)
