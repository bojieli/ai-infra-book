"""Address-level port occupancy, alias and modulo-period checks."""
import math
import sys
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from infra_calc.topics.bank_mapping import calculate,service


class BankMappingTests(unittest.TestCase):
    def test_book_padding(self):
        original=calculate()['summary']; padded=calculate(stride_words=33)['summary']
        self.assertEqual((original['allocated_tile_bytes'],original['service_rounds']),(4096,32))
        self.assertEqual((padded['allocated_tile_bytes'],padded['service_rounds']),(4224,1))
        self.assertEqual(padded['padding_fraction'],.03125)
        self.assertEqual(original['lane_requested_bytes'],padded['lane_requested_bytes'])
        self.assertEqual(calculate(access='row')['summary']['service_rounds'],1)

    def test_broadcast_cannot_merge_distinct_words_in_same_bank(self):
        self.assertEqual(service([0]*32,broadcast=True)['service_rounds'],1)
        self.assertEqual(service([0]*32,broadcast=False)['service_rounds'],32)
        self.assertEqual(service([i*32 for i in range(32)],broadcast=True)['service_rounds'],32)
        self.assertEqual(service([0,0,32,64],ports=2,broadcast=True)['service_rounds'],2)

    def test_modulo_period_is_independent_reference(self):
        for stride in range(1,65):
            r=service([i*stride for i in range(32)])
            self.assertEqual(r['service_rounds'],math.gcd(stride,32))
        with self.assertRaises(ValueError): service([-1])
        with self.assertRaises(ValueError): calculate(stride_words=31)
