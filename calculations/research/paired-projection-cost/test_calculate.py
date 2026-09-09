from fractions import Fraction
import unittest
import calculate
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
