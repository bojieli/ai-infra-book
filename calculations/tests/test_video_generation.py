"""Independent frame-rule and operator accounting checks against pinned sources."""
import ast
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from infra_calc.paths import PROJECT
from infra_calc.topics.video_generation import calculate, h3_frame_geometry


class VideoGenerationTests(unittest.TestCase):
    def test_h3_exact_official_frame_helpers_and_stereo(self):
        path=PROJECT/'research/generative-video-analysis/huggingface--diffusers/src/diffusers/modular_pipelines/minimax_h3/modular_pipeline.py'
        tree=ast.parse(path.read_text())
        names={'align_num_frames','video_latent_num_frames','audio_latent_num_frames'}
        subset=ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names],type_ignores=[])
        namespace={'MINIMAX_H3_FPS':24,'MINIMAX_H3_AUDIO_LATENTS_PER_SECOND':40}
        exec(compile(subset,str(path),'exec'),namespace)
        for requested in range(1,361):
            aligned=namespace['align_num_frames'](requested,17,5)
            latent=namespace['video_latent_num_frames'](aligned,17,5)
            self.assertEqual(h3_frame_geometry(requested),(aligned,latent))
        result=calculate()
        self.assertEqual(result['summary']['resolved_frames'],124)
        self.assertEqual(result['summary']['latent_frames'],37)
        stage=result['video_generation_stages'][0]
        self.assertEqual(stage['target_audio_tokens'],2*namespace['audio_latent_num_frames'](124))
        self.assertEqual(stage['target_video_tokens'],37*24*42)
        self.assertNotEqual(37,(124-1)//4+1)

    def test_h3_distinct_projection_widths_all_row_heads_and_cache(self):
        result=calculate(height=64,width=96,frames=5,text_tokens=7,steps=2,evaluations_per_step=3,
                         regeneration_height=128,regeneration_width=192,regeneration_steps=1,
                         unique_timestep_values=4)
        first,second=result['video_generation_stages']
        h,a,f,L=5376,7168,14336,50
        t=7;v=2*2*3;audio=2*round(5/24*40);s=t+v+audio
        # 3 QKV+O, SwiGLU gate/up/down, two full attention matrix products.
        blocks=L*(8*s*h*a+6*s*h*f+4*s*s*a)
        refiner=2*(8*t*h*a+6*t*h*f+4*t*t*a)
        io=2*v*96*h+2*audio*32*h+2*t*5120*h+2*s*h*(96+32)
        self.assertEqual(first['matrix_core_flops_per_evaluation'],blocks+refiner+io)
        self.assertEqual(first['matrix_core_flops_all_evaluations'],6*(blocks+refiner+io))
        self.assertEqual(second['reference_video_tokens'],v)
        self.assertEqual(second['target_video_tokens'],4*v)
        qkv=next(r for r in first['operators'] if r['operator']=='joint.qkv')
        self.assertEqual(qkv['b_shape'],[h,a])
        output=next(r for r in first['operators'] if r['operator']=='video_output_all_rows')
        self.assertEqual(output['a_shape'][0],s)
        cache=result['summary']['block_modulation_cache']
        self.assertEqual(cache['block_modulation_weight_parameters'],50*(2688+1)*18*5376)
        self.assertEqual(cache['cache_table_bf16_bytes'],4*50*18*5376*2)
        self.assertEqual(result['summary']['matrix_core_flops'],sum(x['matrix_core_flops_all_evaluations'] for x in (first,second)))

    def test_wan_default_has_two_guidance_forwards(self):
        args=dict(model='wan2.2-ti2v-5b',frames=5,height=64,width=96,text_tokens=512,steps=3)
        default=calculate(**args)
        single=calculate(**args,evaluations_per_step=1)
        self.assertEqual(default['scenario']['evaluations_per_step'],2)
        self.assertEqual(default['summary']['matrix_core_flops'],2*single['summary']['matrix_core_flops'])
        self.assertEqual(default['wan_text_encoding'],single['wan_text_encoding'])
        self.assertEqual(default['wan_vae_decode'],single['wan_vae_decode'])

    def test_wan_context_padding_cross_attention_and_rejections(self):
        r=calculate(model='wan2.2-ti2v-5b',frames=121,height=64,width=96,text_tokens=512,steps=1)
        stage=r['video_generation_stages'][0];s=31*2*3;h=3072;f=14336;t=512;L=30
        self_attn=8*s*h*h+4*s*s*h
        cross=4*s*h*h+4*t*h*h+4*s*t*h
        ffn=4*s*h*f
        io=2*s*192*h+2*t*4096*h+2*t*h*h+2*s*h*192
        self.assertEqual(stage['matrix_core_flops_per_evaluation'],L*(self_attn+cross+ffn)+io)
        self.assertEqual(stage['target_audio_tokens'],0)
        self.assertIsNone(r['summary']['block_modulation_cache'])
        for args in [dict(model='wan2.2-ti2v-5b',frames=120,text_tokens=512),
                     dict(model='wan2.2-ti2v-5b',frames=121,text_tokens=256),
                     dict(height=720),dict(regeneration_height=2048),dict(frames=True)]:
            with self.assertRaises(ValueError): calculate(**args)


if __name__=='__main__':unittest.main()
