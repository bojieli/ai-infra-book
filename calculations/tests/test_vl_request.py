import sys
import os
import subprocess
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from infra_calc.topics.vl_request import calculate, language_stage, text_config, SUM_FIELDS


class VLRequestTests(unittest.TestCase):
    def test_serialization_is_stable_across_hash_seeds(self):
        code='import json; from infra_calc.topics.vl_request import calculate; print(json.dumps(calculate()))'
        outputs=[]
        for seed in ('1','2'):
            env=dict(os.environ, PYTHONHASHSEED=seed,
                     PYTHONPATH=str(Path(__file__).resolve().parents[1]/'src'))
            outputs.append(subprocess.check_output([sys.executable,'-c',code],env=env))
        self.assertEqual(outputs[0],outputs[1])

    def test_all_language_matrices_parameters_and_deepstack(self):
        r=calculate(output_tokens=1);s=r['summary']
        tokens=2000;h=2560;q=4096;kv=1024;ffn=9728;layers=36;vocab=151936
        pairs=tokens*(tokens+1)//2
        projection=4*tokens*h*(q+kv)+6*tokens*h*ffn
        expected=layers*(projection+4*pairs*q)+2*h*vocab
        self.assertEqual(s['prompt_positions'],tokens)
        self.assertEqual(r['language_prefill']['summary']['matrix_flops'],expected)
        params=vocab*h+layers*(2*h*(q+kv)+3*h*ffn+2*h+2*128)+h
        self.assertEqual(s['language_parameters'],params)
        self.assertEqual(s['deepstack_language_layer_indices'],[0,1,2])
        self.assertEqual(s['deepstack_prefill_add_elements'],3*1600*h)
        self.assertEqual(s['decode_forward_calls'],0)
        self.assertEqual(s['final_kv_positions'],tokens)
        self.assertIsNone(r['language_decode_first'])
        ops={x['name']:x for x in r['language_prefill']['operators']}
        self.assertEqual(ops['q_proj']['shapes']['weight_math'],[h,q])
        self.assertEqual(ops['k_proj']['shapes']['weight_math'],[h,kv])
        self.assertEqual(ops['deepstack_prompt_clone']['repeats'],3)
        self.assertEqual(ops['image_embedding_replace']['shapes']['image_embeddings'],[1600,h])
        self.assertNotIn('rope_table',ops)
        self.assertEqual(ops['mrope_table']['shapes']['position_ids'],[3,1,tokens])

    def test_decode_affine_sum_matches_every_forward_and_kv(self):
        r=calculate(preprocessed_height=256,preprocessed_width=256,images_per_request=1,
                    text_tokens=13,output_tokens=7)
        prompt=77;calls=6
        config=text_config()
        explicit=[language_stage(config,1,prompt+i,2,2) for i in range(calls)]
        for field in SUM_FIELDS:
            self.assertEqual(r['language_decode_totals'][field],sum(x['summary'][field] for x in explicit))
        self.assertEqual(r['summary']['decode_causal_pairs'],sum(prompt+i+1 for i in range(calls)))
        self.assertEqual(r['summary']['final_kv_positions'],83)
        self.assertEqual(r['summary']['kv_bytes_per_position'],2*36*8*128*2)
        self.assertEqual(r['summary']['output_head_evaluations'],7)
        self.assertEqual(r['summary']['total_matrix_flops'],sum(x['matrix_flops'] for x in r['vl_request_stages']))
        self.assertFalse(any('deepstack' in x['name'] for x in r['language_decode_first']['operators']))

    def test_encoder_hits_do_not_shrink_language_and_context_boundary(self):
        miss=calculate(output_tokens=2)
        hit=calculate(encoder_cache_hits=4,output_tokens=2)
        self.assertEqual(hit['summary']['vision_matrix_flops'],0)
        for key in ('prompt_positions','language_matrix_flops','final_kv_bytes','complete_encoder_bytes_per_request'):
            self.assertEqual(hit['summary'][key],miss['summary'][key])
        self.assertEqual(hit['language_prefill']['summary']['matrix_flops'],miss['language_prefill']['summary']['matrix_flops'])
        fp32kv=calculate(output_tokens=2,kv_dtype='fp32')
        self.assertEqual(fp32kv['summary']['final_kv_bytes'],2*miss['summary']['final_kv_bytes'])
        self.assertEqual(fp32kv['summary']['total_matrix_flops'],miss['summary']['total_matrix_flops'])
        limit=text_config()['max_position_embeddings'];p=2000
        edge=calculate(output_tokens=limit-p+1)
        self.assertEqual(edge['summary']['final_kv_positions'],limit)
        for kwargs in [dict(output_tokens=limit-p+2),dict(output_tokens=0),dict(text_tokens=True)]:
            with self.assertRaises(ValueError):calculate(**kwargs)


if __name__=='__main__':unittest.main()
