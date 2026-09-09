import unittest
import calculate
class Coordinates(unittest.TestCase):
    def test_repeated_weight_reads(self):
        a=calculate.call('test',32,256,256);b=calculate.call('test',64,256,256)
        self.assertEqual(b['summary']['B_copy_payload_bytes'],2*a['summary']['B_copy_payload_bytes'])
        self.assertEqual(b['summary']['unique_B_bytes'],a['summary']['unique_B_bytes'])
    def test_strided_rectangles(self):
        r=calculate.call('test',32,256,128)['input_copy_coordinates'][1]
        self.assertEqual(r['A']['offset_bytes'],128)
        self.assertEqual(r['A']['row_bytes'],128)
        self.assertEqual(r['A']['row_stride_bytes'],256)
    def test_reject_unsupported_tail(self):
        for shape in [(1,256,128),(32,255,128),(32,256,129),(True,256,128)]:
            with self.assertRaises(ValueError):calculate.call('test',*shape)
