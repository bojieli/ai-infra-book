import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from infra_calc.topics.vision_encoding import calculate
from infra_calc.topics.multimodal_cache import calculate as cache_geometry


class VisionEncodingTests(unittest.TestCase):
    def test_independent_complete_matrix_and_parameter_sum(self):
        r=calculate(images_per_request=1);s=r['summary']
        p=1600;m=400;h=1024;f=4096;out=2560;depth=24;merged=4096
        patch=2*p*1536*h
        block=8*p*h*h+4*p*p*h+4*p*h*f
        mergers=4*(2*m*merged*merged+2*m*merged*out)
        self.assertEqual(s['matrix_flops_per_image'],patch+depth*block+mergers)
        # Independent model state enumeration: all Linear/Conv biases, both norms,
        # learned position embedding, and differing pre/post-shuffle norm widths.
        block_params=4*h*h+2*h*f+(3*h+h+f+h)+4*h
        final_params=merged*merged+merged+merged*out+out+2*h
        deep_params=merged*merged+merged+merged*out+out+2*merged
        params=1536*h+h+2304*h+depth*block_params+final_params+3*deep_params
        self.assertEqual(s['complete_vision_learned_parameters'],params)
        self.assertEqual(s['complete_encoder_bytes_per_image'],cache_geometry(images_per_request=1)['summary']['complete_encoder_bytes_per_image'])
        self.assertEqual(s['patch_input_shape'],[1600,1536])

    def test_norm_scalar_reference_and_merger_shapes(self):
        r=calculate(preprocessed_height=256,preprocessed_width=256,images_per_request=1)
        rows={x['operator']:x for x in r['vision_encoding_scalars']}
        final=rows['merger_final.norm'];deep=rows['merger_deepstack_5.norm']
        self.assertEqual(final['shape'],[256,1024]);self.assertEqual(deep['shape'],[64,4096])
        # Enumerate the two reductions and affine/normalization for each row.
        for row in (final,deep):
            n,d=row['shape'];adds=muls=roots=0
            for _ in range(n):
                adds+=(d-1)+d+(d-1)+1+d
                muls+=1+d+1+d+d
                roots+=1
            self.assertEqual(row['counts'],dict(add=adds,multiply=muls,rsqrt=roots))
        self.assertIn('erf',rows['merger_final.gelu_exact']['counts'])
        self.assertIn('tanh',rows['block.gelu_tanh']['counts'])
        matrices={x['operator']:x for x in r['vision_encoding_matrices']}
        self.assertEqual(matrices['block.qk']['copies'],24*16)
        self.assertEqual(matrices['block.qk']['b_shape'],[64,256])

    def test_independent_images_cache_hits_and_precision(self):
        one=calculate(images_per_request=1)['summary']
        four=calculate(images_per_request=4)['summary']
        hits=calculate(images_per_request=4,encoder_cache_hits=3)['summary']
        allhits=calculate(images_per_request=4,encoder_cache_hits=4)['summary']
        fp32=calculate(images_per_request=1,dtype='fp32')['summary']
        self.assertEqual(four['matrix_flops_per_request'],4*one['matrix_flops_per_request'])
        self.assertEqual(hits['matrix_flops_per_request'],one['matrix_flops_per_request'])
        self.assertEqual(allhits['matrix_flops_per_request'],0)
        self.assertEqual(allhits['complete_encoder_bytes_per_request'],four['complete_encoder_bytes_per_request'])
        self.assertEqual(fp32['matrix_flops_per_request'],one['matrix_flops_per_request'])
        self.assertGreater(fp32['semantic_read_bytes_per_image'],one['semantic_read_bytes_per_image'])
        self.assertLess(fp32['semantic_read_bytes_per_image'],2*one['semantic_read_bytes_per_image'])
        self.assertEqual(fp32['vision_parameter_bytes_declared_dtype'],2*one['vision_parameter_bytes_declared_dtype'])
        for kwargs in [dict(encoder_cache_hits=5),dict(encoder_cache_hits=True),dict(preprocessed_height=641)]:
            with self.assertRaises(ValueError):calculate(**kwargs)


if __name__=='__main__':unittest.main()
