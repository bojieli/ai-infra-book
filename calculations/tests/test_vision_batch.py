import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'src'))
from infra_calc.topics import vision_batch, vl_request


class MixedImageTests(unittest.TestCase):
    def test_independent_attention_and_shared_capacity(self):
        # 256 + 576 patches: sum squares, never (sum patches)^2.
        images=[dict(height=256,width=256),dict(height=384,width=384)]
        r=vision_batch.calculate(images)
        h=1024; layers=24; p=[256,576]
        expected_attention=4*layers*h*sum(x*x for x in p)
        attention=sum(m['matrix_flops'] for image in r['per_image_encodings']
                      for m in image['encoding']['vision_encoding_matrices']
                      if m['operator'] in ('block.qk','block.pv'))
        self.assertEqual(attention,expected_attention)
        self.assertNotEqual(attention,4*layers*h*sum(p)**2)
        self.assertEqual(r['summary']['merged_positions_per_request'],208)
        self.assertEqual(r['summary']['complete_encoder_bytes_per_request'],208*2560*4*2)
        self.assertEqual(r['summary']['vision_parameter_bytes_declared_dtype'],415347712*2)

    def test_same_total_positions_different_vision_work(self):
        # 256+1024 vs 640+640 patches: equal language length, unequal vision QK/PV.
        a=vl_request.calculate(images=[dict(height=256,width=256),dict(height=512,width=512)],output_tokens=3)
        b=vl_request.calculate(images=[dict(height=320,width=512),dict(height=320,width=512)],output_tokens=3)
        self.assertEqual(a['summary']['prompt_positions'],720)
        self.assertEqual(a['summary']['language_matrix_flops'],b['summary']['language_matrix_flops'])
        delta=4*24*1024*(256**2+1024**2-2*640**2)
        self.assertEqual(a['summary']['vision_matrix_flops']-b['summary']['vision_matrix_flops'],delta)

    def test_selected_cache_hit_keeps_language_and_features(self):
        cold=[dict(height=256,width=256),dict(height=512,width=512)]
        warm=[dict(height=256,width=256),dict(height=512,width=512,cache_hit=True)]
        a=vl_request.calculate(images=cold);b=vl_request.calculate(images=warm)
        for key in ('prompt_positions','language_matrix_flops','final_kv_bytes','complete_encoder_bytes_per_request'):
            self.assertEqual(a['summary'][key],b['summary'][key])
        self.assertEqual(b['summary']['vision_matrix_flops'],a['vision_image_rows'][0]['matrix_flops'])
        self.assertEqual(b['vision_image_rows'][1]['matrix_flops'],0)
        self.assertNotIn('images_per_request',b['scenario'])
        self.assertEqual(b['summary']['vision_weight_bytes'],a['summary']['vision_weight_bytes'])

    def test_invalid_input_modes_and_cache_identity(self):
        for images in ([],{},[{}],[dict(height=256,width=256,cache_hit=1)],
                       [dict(height=256,width=256,unknown=True)]):
            with self.assertRaises(ValueError):vision_batch.calculate(images)
        with self.assertRaises(ValueError):
            vl_request.calculate(images=[dict(height=256,width=256)],images_per_request=1)


if __name__=='__main__':unittest.main()
