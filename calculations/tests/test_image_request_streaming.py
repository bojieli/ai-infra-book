"""Hand-checked block service and separate preview/final delivery."""
import sys
from pathlib import Path
import unittest
from fractions import Fraction as F
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from infra_calc.topics.image_request_streaming import calculate,default_chunks


class ImageStreamingTests(unittest.TestCase):
    def test_same_work_and_barrier_removal(self):
        whole=calculate();blocks=calculate(mode='independent_blocks',independent_blocks_authorized=True)
        self.assertEqual(F(whole['summary']['complete_final_image_seconds_exact']),F(64,5))
        self.assertEqual(F(blocks['summary']['complete_final_image_seconds_exact']),F(309,25))
        for r in [whole,blocks]:
            self.assertEqual(r['summary']['input_file_bytes'],30_000_000)
            self.assertEqual(r['summary']['total_downlink_bytes'],5_000_000)
            self.assertEqual(sum(F(e['duration_seconds_exact']) for e in r['events'] if e['id'].startswith('process.')),F(3,10))
            self.assertIsNone(r['summary']['preview_ready_seconds_exact'])

    def test_preview_extra_cost_and_delivery_not_interchangeable(self):
        preview=dict(after_processed_chunk=0,bytes=500_000,encode_seconds='1/20',quality_contract='partial lower quality preview')
        for mode,expected_preview,expected_final in [('whole_image',F(1229,100),F(257,20)),('independent_blocks',F(108,25),F(309,25))]:
            r=calculate(mode=mode,independent_blocks_authorized=True,preview=preview)['summary']
            self.assertEqual(F(r['preview_ready_seconds_exact']),expected_preview)
            self.assertEqual(F(r['complete_final_image_seconds_exact']),expected_final)
            self.assertEqual(r['total_downlink_bytes'],5_500_000)
            self.assertFalse(r['preview_is_complete_final_image'])

    def test_propagation_does_not_reserve_links(self):
        r=calculate(mode='independent_blocks',independent_blocks_authorized=True,forward_propagation_seconds=10)
        byid={e['id']:e for e in r['events']}
        self.assertEqual(F(byid['upload.1']['start_seconds_exact']),F(4))
        self.assertEqual(F(byid['input_arrival.0']['end_seconds_exact']),F(14))
        for resource in ['uplink','server','downlink','client']:
            rows=sorted((e for e in r['events'] if e['resource']==resource),key=lambda e:F(e['start_seconds_exact']))
            self.assertTrue(all(F(a['end_seconds_exact'])<=F(b['start_seconds_exact']) for a,b in zip(rows,rows[1:])))

    def test_no_implicit_block_independence(self):
        with self.assertRaises(ValueError):calculate(mode='independent_blocks')
        chunks=default_chunks();chunks[0]['required_inputs']=[0,1]
        with self.assertRaises(ValueError):calculate(chunks=chunks,mode='independent_blocks',independent_blocks_authorized=True)
        for args in [dict(upload_bits_per_second=0),dict(forward_propagation_seconds=.1),dict(chunks=[]),dict(preview={})]:
            with self.subTest(args=args),self.assertRaises(ValueError):calculate(**args)


if __name__=='__main__':unittest.main()
