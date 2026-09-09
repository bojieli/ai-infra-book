"""Finite-format round trips, tie parity and exact book witnesses."""
from fractions import Fraction
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from infra_calc.topics.fusion_numerics import VALUES,round_e4m3fn,quantized_dot,calculate


class FusionNumericsTests(unittest.TestCase):
    def test_finite_values_and_nearest_even_midpoints(self):
        self.assertEqual(VALUES[1][1],Fraction(1,512))
        self.assertEqual(VALUES[-1][1],448)
        for code,value in VALUES:
            self.assertEqual(round_e4m3fn(value),value)
            self.assertEqual(round_e4m3fn(-value),-value)
        for (a,av),(b,bv) in zip(VALUES,VALUES[1:]):
            expected=av if a%2==0 else bv
            self.assertEqual(round_e4m3fn((av+bv)/2),expected)
        self.assertEqual(round_e4m3fn(1000),448)
        self.assertEqual(round_e4m3fn(Fraction(448,10)),44)

    def test_book_witness_and_permutation(self):
        first=calculate()['summary'];reverse=calculate(larger_first=True)['summary']
        self.assertEqual((first['full_row_exact'],first['prefix_exact'],first['exact_difference']),('55/56','1','1/56'))
        self.assertEqual(first['full_row_fp16'],.98193359375)
        self.assertFalse(first['equal_after_fp16'])
        self.assertEqual(reverse['full_row_exact'],reverse['prefix_exact'])
        self.assertEqual(first['lost_state_full_result'],3)
        self.assertEqual(first['lost_state_unsafe_result'],'1')
        self.assertEqual(first['sufficient_state_result'],3)

    def test_zero_blocks_and_tail(self):
        self.assertEqual(quantized_dot([0,0,0],[1,1,1],2,True),0)
        self.assertEqual(quantized_dot([0,0,1],[1,1,1],2,True),1)
        with self.assertRaises(ValueError):quantized_dot([1],[1],0)
