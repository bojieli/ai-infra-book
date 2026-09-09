import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from infra_calc.topics.image_generation import calculate


def indexed(result, key):
    return {r['operation']:r for r in result[key]}


class ImageSetupTests(unittest.TestCase):
    def test_qwen_cache_scope_and_constructor_exclusion(self):
        cold=calculate(height=32,width=48,batch=2,text_tokens=8,negative_text_tokens=3,steps=3)
        warm=calculate(height=32,width=48,batch=2,text_tokens=8,negative_text_tokens=3,steps=3,qwen_shape_cache_warm=True)
        data=indexed(cold,'image_setup_data_operations'); wd=indexed(warm,'image_setup_data_operations')
        # Different text lengths do not change the image-only cache key. Outer cat
        # remains outside the decorated helper, including when the cache is warm.
        cache=data['qwen_image_rope_cache_and_forward']
        self.assertEqual((cache['cold_unique_keys'],cache['cache_hits']),(1,5))
        self.assertEqual(wd['qwen_image_rope_cache_and_forward']['cache_hits'],6)
        self.assertEqual(cache['outer_image_concat_output_bytes'],6*6*64*8)
        self.assertEqual(wd['qwen_cached_image_frequency_build']['logical_output_bytes'],0)
        ops=indexed(cold,'image_setup_operations')
        self.assertEqual(ops['qwen_rope_constructor_tables']['special_calls']['polar'],2*4096*64)
        self.assertFalse(any(r['operation']=='qwen_rope_constructor_tables' for r in cold['image_reference_operations']))
        timestep=ops['timestep_sinusoidal_features']
        self.assertEqual(timestep['special_calls'],dict(log=6,exp=6*128,sin=6*2*128,cos=6*2*128))
        # Frequency multiply/divide, scalar negate, outer multiply and explicit scale.
        self.assertEqual(timestep['ordinary_arithmetic_ops'],6*(128+128+1+256+256))
        with self.assertRaises(ValueError):
            calculate(qwen_shape_cache_warm=1)

    def test_flux_positions_shared_across_batch_but_text_rope_is_batched(self):
        result=calculate(model='flux2-klein-4b',height=32,width=48,batch=3,text_tokens=8,steps=2)
        ops=indexed(result,'image_setup_operations'); data=indexed(result,'image_setup_data_operations')
        # DiT drops batch axis of IDs; encoder RoPE retains batch.
        self.assertEqual(ops['flux_rope_conditional']['special_calls']['sin'],2*(6+8)*64)
        self.assertEqual(ops['text_conditional_rope_forward']['special_calls']['sin'],2*3*8*64)
        self.assertEqual(data['flux_input_position_ids']['text_cartesian_product_and_stack_elements'],2*3*8*4)
        cast=data['flux_repeated_cos_sin_cast']
        self.assertEqual(cast['conversion_elements'],2*2*(6+8)*128)
        self.assertEqual(cast['logical_input_bytes'],cast['conversion_elements']*8)
        self.assertEqual(cast['logical_output_bytes'],cast['conversion_elements']*4)
        self.assertIsNone(cast['actual_device_transfer_bytes'])

    def test_scheduler_setup_is_once_and_typed_casts_are_not_flops(self):
        result=calculate(height=32,width=32,text_tokens=8,steps=3,dtype='fp32')
        ops=indexed(result,'image_setup_operations'); data=indexed(result,'image_setup_data_operations')
        self.assertEqual(ops['scheduler_exponential_shift']['ordinary_arithmetic_ops'],3*4)
        self.assertEqual(ops['scheduler_exponential_shift']['special_calls'],dict(exp=2,pow=3))
        self.assertEqual(ops['scheduler_terminal_stretch']['ordinary_arithmetic_ops'],3*3+2)
        self.assertEqual(data['scheduler_append_terminal_zero']['output_elements'],4)
        self.assertIsNone(data['scheduler_linspace']['ordinary_arithmetic_ops'])
        self.assertEqual(data['euler_sample_upcast']['conversion_elements'],0)
        self.assertEqual(data['euler_sample_upcast']['logical_output_bytes'],0)
        self.assertEqual(data['initial_noise']['normal_samples'],16*4*4)
        self.assertFalse(result['summary']['complete_nonmatrix_coverage'])
        flux=calculate(model='flux2-klein-4b',height=1056,width=1056,text_tokens=8,steps=1,output_type='latent')
        fo=indexed(flux,'image_setup_operations')
        self.assertEqual(fo['scheduler_mu']['ordinary_arithmetic_ops'],2)
        self.assertNotIn('scheduler_terminal_stretch',fo)


if __name__=='__main__': unittest.main()
