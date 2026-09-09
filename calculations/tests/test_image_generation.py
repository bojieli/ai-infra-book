import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from infra_calc.topics import image_generation


class ImageGenerationTests(unittest.TestCase):
    def test_packing_conservation_and_boundaries(self):
        for model, channels in [('qwen-image-2512', 16), ('flux2-klein-4b', 32)]:
            summary = image_generation.calculate(model=model)['summary']
            self.assertEqual(summary['packed_latent_shape'], [1, 4096, channels * 4])
            self.assertEqual(summary['raw_latent_elements'], channels * 128 * 128)
            self.assertEqual(summary['raw_latent_elements'], summary['packed_latent_elements'])
            # Explicit small spatial coordinate bijection for the 2x2 packing.
            coordinates = {(c, y, x) for c in range(channels) for y in range(4) for x in range(6)}
            packed = {(y // 2, x // 2, 4*c + 2*(y % 2) + x % 2) for c, y, x in coordinates}
            self.assertEqual(len(coordinates), len(packed))
            double = image_generation.calculate(model=model, height=2048)['summary']
            self.assertEqual(double['image_tokens'], 2 * summary['image_tokens'])
        for inputs in ({'height': 1023}, {'width': 1032}, {'batch': True}, {'steps': 0}, {'model': 'unknown'}):
            with self.assertRaises(ValueError):
                image_generation.calculate(**inputs)

    def test_independent_closed_form_linear_and_joint_attention(self):
        dim, image, text, batch = 3072, 4096, 128, 2
        joint = image + text
        for model, coef, blocks, input_width, text_width, mod in [
                ('qwen-image-2512', 24, 60, 64, 3584, 24*60),
                ('flux2-klein-4b', 26, 25, 128, 7680, 30)]:
            result = image_generation.calculate(model=model, text_tokens=text, batch=batch,
                                                negative_prompt_present=False, steps=1)
            # Block projection/FFN + QK/PV, then global input/output/time/AdaLN and modulation.
            block_work = batch * blocks * (coef * joint * dim**2 + 4 * joint**2 * dim)
            global_work = 2 * batch * (2 * image * input_width * dim + text * text_width * dim +
                                      256 * dim + dim**2) + 4 * batch * dim**2 + mod * batch * dim**2
            self.assertEqual(result['summary']['denoising_matrix_flops'], block_work + global_work)
            rows = result['image_generation_matrices']
            self.assertEqual(sum(r['matrix_flops'] for r in rows), block_work + global_work)
            self.assertTrue(all(r['matrix_weight_elements'] == 0 for r in rows if r['rhs_kind'] == 'activation'))
            if model.startswith('flux'):
                self.assertEqual([r['repeats'] for r in rows if 'modulation' in r['name']], [1, 1, 1, 1])
                fused = next(r for r in rows if r['name'] == 'single_qkv_and_gate_up')
                self.assertEqual(fused['rhs_mathematical_shape'], [dim, 9 * dim])

    def test_guidance_branches_steps_and_stage_exclusions(self):
        cfg = image_generation.calculate(steps=3, negative_text_tokens=32)
        plain = image_generation.calculate(steps=3, negative_prompt_present=False)
        self.assertEqual(cfg['summary']['transformer_invocations'], 6)
        self.assertEqual(plain['summary']['transformer_invocations'], 3)
        self.assertLess(cfg['summary']['denoising_matrix_flops'], 2 * plain['summary']['denoising_matrix_flops'])
        self.assertEqual(cfg['summary']['matrix_weight_elements_excluding_bias_norm'],
                         plain['summary']['matrix_weight_elements_excluding_bias_norm'])
        flux = image_generation.calculate(model='flux2-klein-4b', guidance_scale=8)
        self.assertFalse(flux['summary']['true_cfg_enabled'])
        self.assertTrue(flux['summary']['supplied_guidance_ignored'])
        self.assertEqual(flux['summary']['transformer_invocations'], 4)
        self.assertEqual(flux['image_generation_stages'][0]['pipeline_calls'], 1)
        self.assertEqual(flux['image_generation_stages'][-1]['pipeline_calls'], 1)
        latent = image_generation.calculate(output_type='latent')['summary']
        self.assertEqual(latent['vae_decode_calls'], 0)
        self.assertIsNone(latent['complete_generation_flops'])
        self.assertGreater(latent['text_encoder_matrix_flops'], 0)
        self.assertEqual(latent['vae_matrix_flops'], 0)
        self.assertIsNone(latent['encoded_image_file_bytes'])


if __name__ == '__main__':
    unittest.main()
