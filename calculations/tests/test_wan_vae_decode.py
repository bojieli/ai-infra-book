import json
import sys
import unittest
from math import prod
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from infra_calc.paths import PROJECT
from infra_calc.topics.wan_vae_decode import calculate,axis_nonpadding_pairs
from infra_calc.topics.video_generation import calculate as video


class WanVAEDecodeTests(unittest.TestCase):
    def test_full_contraction_sum_matches_independent_meta_execution(self):
        raw=json.loads((PROJECT/'research/generative-video-analysis/wan-vae-decode-validation.json').read_text())
        r=calculate(5,3,4)
        self.assertEqual(r['output_video_shape'],raw['output_shape'])
        total=0;bias=0
        for row in raw['events']:
            if row['kind']=='attention':
                b,heads,n,d=row['q_shape'];total+=4*b*heads*n*n*d
            else:
                total+=2*prod(row['output_shape'])*prod(row['weight_shape'][1:])
                if row['bias']:bias+=prod(row['output_shape'])
        self.assertEqual(r['matrix_flops'],total)
        self.assertEqual(r['convolution_bias_adds'],bias)
        self.assertEqual(r['decoder_learned_parameters'],raw['decoder_parameters'])
        # All cached steady occurrences contribute, no last-chunk truncation.
        self.assertEqual(r['temporal_decoder_chunk_calls'],5)

    def test_spatial_temporal_padding_pairs_by_coordinate_enumeration(self):
        for length in range(1,7):
            for kernel in (1,3):
                for stride in (1,2):
                    for padding in (0,1,2):
                        output=max(0,(length+padding-(kernel-1)-1)//stride+1)
                        brute=sum(0<=i*stride+k-padding<length for i in range(output) for k in range(kernel))
                        self.assertEqual(axis_nonpadding_pairs(length,output,kernel,stride,1,padding),brute)
        first=calculate(1,2,3);two=calculate(2,2,3);three=calculate(3,2,3)
        self.assertEqual(first['output_video_shape'][2],1)
        self.assertEqual(two['output_video_shape'][2],5)
        self.assertEqual(three['output_video_shape'][2],9)
        self.assertLess(three['external_padding_excluded_flops'],three['matrix_flops'])
        phases={r['phase'] for r in first['operators']}
        self.assertEqual(phases,{'all_latents_projection','first_chunk'})
        self.assertFalse(any(r.get('causal') for r in three['operators'] if r['kind']=='attention'))

    def test_vae_runs_once_and_old_core_remains_separate(self):
        args=dict(model='wan2.2-ti2v-5b',frames=121,text_tokens=512)
        a=video(**args,steps=1);b=video(**args,steps=2)
        self.assertEqual(a['wan_vae_decode']['matrix_flops'],b['wan_vae_decode']['matrix_flops'])
        self.assertEqual(b['summary']['matrix_core_flops'],2*a['summary']['matrix_core_flops'])
        self.assertEqual(a['summary']['matrix_core_plus_text_and_vae_flops'],a['summary']['matrix_core_flops']+a['wan_text_encoding']['matrix_flops']+a['wan_vae_decode']['matrix_flops'])
        with self.assertRaises(ValueError):calculate(dtype_bytes=3)


if __name__=='__main__':unittest.main()
