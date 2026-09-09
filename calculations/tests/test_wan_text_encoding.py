import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from infra_calc.topics.wan_text_encoding import calculate
from infra_calc.topics.video_generation import calculate as video


class WanTextEncodingTests(unittest.TestCase):
    def test_full_encoder_matrix_and_parameter_sum(self):
        r=calculate();p=512;h=4096;f=10240;layers=24
        expected=layers*(8*p*h*h+6*p*h*f+4*p*p*h)
        self.assertEqual(r['matrix_flops_per_encoder_call'],expected)
        self.assertEqual(r['matrix_flops'],2*expected)
        params=256384*h+layers*(4*h*h+3*h*f+2*h+32*64)+h
        self.assertEqual(r['learned_encoder_parameters'],params)
        self.assertEqual(r['declared_weight_bytes'],2*params)
        self.assertEqual(r['scalar_reference_counts_per_call']['attention_scale_multiply'],0)

    def test_padding_masks_dont_shrink_executed_gemms(self):
        a=calculate(positive_tokens=1,negative_tokens=2);b=calculate(positive_tokens=512,negative_tokens=512)
        self.assertEqual(a['matrix_flops'],b['matrix_flops'])
        self.assertEqual(a['output_valid_hidden_bytes'],3*4096*2)
        self.assertEqual(b['output_valid_hidden_bytes'],1024*4096*2)
        self.assertEqual(a['branches'][0]['dense_attention_pairs_per_head'],512**2)
        self.assertEqual(a['branches'][0]['valid_unpadded_pairs_per_head'],1)
        for args in [dict(positive_tokens=513),dict(padded_tokens=256),dict(negative_tokens=0),dict(dtype_bytes=3),dict(dtype_bytes=True)]:
            with self.assertRaises(ValueError):calculate(**args)

    def test_preforward_cost_once_independent_of_denoise_nfe(self):
        args=dict(model='wan2.2-ti2v-5b',frames=121,text_tokens=512)
        a=video(**args,steps=1,evaluations_per_step=1);b=video(**args,steps=2,evaluations_per_step=2)
        self.assertEqual(a['wan_text_encoding']['matrix_flops'],b['wan_text_encoding']['matrix_flops'])
        self.assertEqual(b['summary']['matrix_core_flops'],4*a['summary']['matrix_core_flops'])
        self.assertEqual(a['summary']['matrix_core_plus_text_encoder_flops'],a['summary']['matrix_core_flops']+a['wan_text_encoding']['matrix_flops'])


if __name__=='__main__':unittest.main()
