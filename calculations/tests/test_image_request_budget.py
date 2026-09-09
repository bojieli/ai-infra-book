"""Image-file byte and complete-delivery boundaries, independent formulas."""
import sys
from pathlib import Path
from fractions import Fraction as F
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from infra_calc.topics.image_request_budget import calculate


class ImageRequestTests(unittest.TestCase):
    def test_original_budget_speedup_and_connection(self):
        a=calculate(connection_seconds='1/5')['variants'][0]
        self.assertEqual(F(a['complete_final_image_seconds_exact']),F(13))
        self.assertEqual(F(a['reused_connection_final_seconds_exact']),F(64,5))
        b=calculate(model_seconds='3/100')['variants'][0]
        self.assertEqual(F(64,5)-F(b['complete_final_image_seconds_exact']),F(27,100))
        self.assertIsNone(a['preview_ready_seconds'])

    def test_compression_threshold_direction_and_local_boundary(self):
        quality='same declared information and output'
        compression=dict(transmitted_bytes=15_000_000,extra_encode_seconds='1/5',extra_decode_seconds='1/10',quality_contract=quality,comparison_authorized=True)
        for rate,win in [(200_000_000,True),(400_000_000,False),(800_000_000,False)]:
            result=calculate(upload_bits_per_second=rate,compression=compression,quality_contract=quality,local_seconds=5)
            comparison=result['compression_comparison']
            self.assertEqual(comparison['compressed_strictly_faster'],win)
            self.assertEqual(F(comparison['complete_image_saving_seconds_exact']),F(120_000_000,rate)-F(3,10))
            self.assertEqual(F(result['variants'][0]['local_comparison']['upload_equal_time_bits_per_second_exact']),F(400_000_000,7))
            self.assertEqual(F(result['variants'][1]['local_comparison']['upload_equal_time_bits_per_second_exact']),F(400_000_000,13))

    def test_unreachable_local_and_unknown_are_distinct(self):
        for local,relation in [(None,'unknown_local_time'),('4/5','no_finite_upload_rate_wins')]:
            row=calculate(local_seconds=local)['variants'][0]['local_comparison']
            self.assertEqual(row['relation'],relation)
            self.assertIsNone(row['upload_equal_time_bits_per_second_exact'])
        self.assertFalse(calculate(upload_bits_per_second='400000000/7',local_seconds=5)['variants'][0]['local_comparison']['remote_strictly_faster'])

    def test_invalid_and_unverified_quality(self):
        for args in [dict(input_bytes=True),dict(upload_bits_per_second=None),dict(model_seconds=.3),dict(output_bytes=0),dict(quality_contract=''),dict(compression={})]:
            with self.subTest(args=args),self.assertRaises(ValueError):calculate(**args)


if __name__=='__main__':unittest.main()
