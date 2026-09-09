from fractions import Fraction
import unittest
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from infra_calc.topics import paired_projection_cost as calculate
class CostTests(unittest.TestCase):
    def test_exact_rate_boundary(self):
        baseline=calculate.calculate()['rows'][0]
        ratio=Fraction(**baseline['rtx_over_mac_rate_tie_ratio'])
        tied=calculate.calculate({'mps':1,'cuda':str(ratio)})['rows'][0]
        self.assertEqual(tied['lower_declared_cost'],['mps','cuda'])
        lower=calculate.calculate({'mps':1,'cuda':str(ratio-Fraction(1,1000))})['rows'][0]
        upper=calculate.calculate({'mps':1,'cuda':str(ratio+Fraction(1,1000))})['rows'][0]
        self.assertEqual(lower['lower_declared_cost'],['cuda'])
        self.assertEqual(upper['lower_declared_cost'],['mps'])
    def test_unknown_is_not_zero(self):
        for row in calculate.calculate()['rows']:
            self.assertIsNone(row['cost_per_call_proxy'])
            self.assertIsNone(row['joules_per_call_proxy'])
            self.assertIsNone(row['measured_task_energy_joules'])
    def test_reject_incomplete_or_bad_rates(self):
        for values in [{'mps':1},{'mps':True,'cuda':2},{'mps':0,'cuda':2},{'mps':1,'cuda':'NaN'}]:
            with self.assertRaises(ValueError):calculate.calculate(hourly_cost_units=values)

    def test_corrupted_archived_inputs_rejected(self):
        import json
        import tempfile
        from unittest.mock import patch
        record=json.loads((calculate.ROOT/'configs/paired-projection-cost.lock.json').read_text())
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            lock=root/'configs/paired-projection-cost.lock.json'
            lock.parent.mkdir(parents=True)
            lock.write_text(json.dumps(record))
            for row in record:
                path=root/row['file'];path.parent.mkdir(parents=True,exist_ok=True)
                path.write_bytes((calculate.ROOT/row['file']).read_bytes())
            for row in record:
                path=root/row['file'];old=path.read_bytes();path.write_bytes(old+b'changed')
                with patch.object(calculate,'ROOT',root),self.assertRaises(ValueError):calculate.calculate()
                path.write_bytes(old)
