import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from infra_calc.topics.image_stages import text_stage, vae_stage
from infra_calc.topics.image_generation import calculate


class ImageStagesTests(unittest.TestCase):
    def test_full_text_layers_unused_logits_and_template_work(self):
        for model, hidden, layers, qwidth, kvwidth, ffn, vocabulary, length in [
                ('qwen-image-2512', 3584, 28, 3584, 512, 18944, 152064, 42),
                ('flux2-klein-4b', 2560, 36, 4096, 1024, 9728, 151936, 8)]:
            result = text_stage(model, 'conditional', 8, 2, 2)
            params_per_layer = hidden * (2*qwidth + 2*kvwidth) + 3*hidden*ffn
            linear = 2 * 2 * length * (layers * params_per_layer + hidden*vocabulary)
            causal = sum(4 * 2 * qwidth * prefix for prefix in range(1, length+1)) * layers
            self.assertEqual(result['encoder_tokens'], length)
            self.assertEqual(result['matrix_flops'], linear + causal)
            self.assertEqual(result['unused_full_logits_bytes'], 2*length*vocabulary*2)
            self.assertEqual(result['all_returned_hidden_bytes'], (layers+1)*2*length*hidden*2)
            self.assertTrue(result['computed_logits_despite_unused'])
            self.assertEqual(next(row['repeats'] for row in result['matrices'] if row['name']=='gate'), layers)
        flux = text_stage('flux2-klein-4b', 'conditional', 8, 1, 2)
        self.assertEqual(flux['feature_layers'], [9,18,27])
        self.assertEqual(flux['encoder_layers'], 36)
        self.assertEqual(flux['temporary_returned_kv_bytes'], 0)
        qwen = text_stage('qwen-image-2512', 'conditional', 8, 1, 2)
        self.assertEqual(qwen['temporary_returned_kv_bytes'], 2*28*42*512*2)

    def test_vae_padding_by_independent_spatial_temporal_tap_enumeration(self):
        for model in ['qwen-image-2512', 'flux2-klein-4b']:
            result = vae_stage(model, 32, 48, 1, 2)
            for row in result['convolutions']:
                height, width = row['output_shape'][-2:]
                ci, co = row['input_shape'][1], row['output_shape'][1]
                kt, kh, kw = row['kernel_shape']
                taps = 0
                for y in range(height):
                    for x in range(width):
                        for t in range(kt):
                            for dy in range(kh):
                                for dx in range(kw):
                                    taps += (t - (kt-1) == 0 and 0 <= y+dy-kh//2 < height and 0 <= x+dx-kw//2 < width)
                self.assertEqual(row['nonpadding_flops'], 2*taps*ci*co)
                self.assertEqual(row['dense_kernel_flops'], 2*height*width*ci*co*kt*kh*kw)
                self.assertLessEqual(row['nonpadding_flops'], row['dense_kernel_flops'])
            self.assertEqual(result['mid_attention_positions'], 4*6)
            self.assertEqual(result['temporal_upsample_convolutions_executed'], 0)
            self.assertIsNone(result['full_runtime_peak_bytes'])
        qwen = vae_stage('qwen-image-2512', 32, 48, 1, 2)
        self.assertEqual(qwen['convolutions'][0]['input_shape'], [1, 16, 1, 4, 6])
        self.assertTrue(all(len(row['input_shape']) == 5 for row in qwen['convolutions'] if 'shortcut' in row['name']))
        self.assertTrue(all(len(row['input_shape']) == 4 for row in qwen['convolutions'] if row['name'].endswith('spatial_conv')))
        clones = [row for row in qwen['convolutions'] if row['causal_feature_cache_clone_bytes']]
        self.assertEqual(len(clones), 30)
        self.assertTrue(all('shortcut' not in row['name'] for row in clones))
        self.assertEqual(sum(row['input_tensor_bytes'] for row in clones), qwen['retained_first_frame_feature_cache_bytes'])
        self.assertEqual(vae_stage('flux2-klein-4b',32,48,1,2)['retained_first_frame_feature_cache_bytes'], 0)

    def test_step_and_cfg_scaling_do_not_reexecute_vae(self):
        one = calculate(height=32,width=32,steps=1,text_tokens=8,negative_text_tokens=2)
        seven = calculate(height=32,width=32,steps=7,text_tokens=8,negative_text_tokens=2)
        for key in ('text_encoder_matrix_flops','vae_matrix_flops','vae_first_frame_feature_cache_bytes'):
            self.assertEqual(one['summary'][key], seven['summary'][key])
        self.assertEqual(seven['summary']['denoising_matrix_flops'], 7*one['summary']['denoising_matrix_flops'])
        no_cfg = calculate(height=32,width=32,steps=1,text_tokens=8,negative_prompt_present=False)
        self.assertEqual(no_cfg['summary']['vae_matrix_flops'],one['summary']['vae_matrix_flops'])
        self.assertGreater(one['summary']['text_encoder_matrix_flops'], no_cfg['summary']['text_encoder_matrix_flops'])
        self.assertEqual(len(one['image_text_encoder_steps']),2)
        self.assertTrue(any(row['operation']=='nearest_upsample' for row in one['image_stage_nonmatrix']))
        self.assertTrue(any('conditional_prediction' in row['object'] for row in one['image_stage_lifetimes']))
        self.assertIsNone(one['summary']['complete_generation_flops'])
        self.assertIsNone(one['summary']['complete_generation_seconds'])


if __name__ == '__main__':
    unittest.main()
