"""Independent RMS identity, partition edges and rounding-order witness."""
import math
import sys
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from infra_calc.topics.row_reduction import calculate,partitions,normalized,sum_squares


class RowReductionTests(unittest.TestCase):
    def test_partial_storage_and_extra_input_pass(self):
        r=calculate(rows=2,splits=8);s=r['summary']
        self.assertEqual(s['partial_buffer_bytes'],64)
        self.assertEqual(s['inverse_buffer_bytes'],8)
        self.assertEqual(s['additional_interface_bytes'],2*2*4096+2*64+8+64)
        self.assertEqual(s['local_reduction_adds']+s['merge_reduction_adds'],2*(4096-1))
        self.assertEqual(s['scalar_flops'],2*4096+2*(4096-1)+4+4*4096)

    def test_partition_normalization_and_fp32_order(self):
        values=[1.,-2.,3.,-4.,5.,-6.,7.]
        expected=[x/math.sqrt(math.fsum(y*y for y in values)/7+1e-6) for x in values]
        for splits in [1,2,3,7]:
            self.assertEqual(sum(partitions(7,splits)),7)
            for a,b in zip(normalized(values,splits),expected): self.assertAlmostEqual(a,b,places=14)
        witness=[4096.]+[1.]*8
        self.assertNotEqual(sum_squares(witness,1,True),sum_squares(witness,3,True))
        self.assertEqual(sum_squares(witness,1),sum_squares(witness,3))
        with self.assertRaises(ValueError): partitions(7,8)
