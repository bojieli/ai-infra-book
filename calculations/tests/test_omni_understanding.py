"""Request-level position conservation, routing and first-token accounting."""
import unittest
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from infra_calc.topics.omni_understanding import calculate


class OmniUnderstandingTests(unittest.TestCase):
    def test_positions_head_and_kv(self):
        r=calculate(text_tokens=7,output_tokens=3,image_grids=[[1,4,4]],
                    video_grids=[[2,4,6]],mel_lengths=[100,1,101])
        p=7+4+12+13+1+14
        self.assertEqual(r['position_budget']['total'],p)
        self.assertEqual(r['position_budget']['audio_embeddings_per_item'],[13,1,14])
        self.assertEqual(r['summary']['decode_calls'],2)
        self.assertEqual(r['summary']['kv_bytes_per_position'],2*48*4*128*2)
        self.assertEqual(r['summary']['kv_after_last_forward_bytes'],(p+2)*98304)
        for stage,rows,pairs in [(r['thinker_prefill'],p,p*(p+1)//2),
                                (r['thinker_decode'][0],1,p+1),(r['thinker_decode'][1],1,p+2)]:
            head=next(m for m in stage['matrices'] if m['name']=='output_head')
            self.assertEqual(head['matrix_flops'],2*rows*2048*152064)
            self.assertEqual(stage['summary']['qk_matrix_flops'],2*48*32*128*pairs)
        self.assertEqual(r['deepstack_injection']['additions'],3*16*2048)
        self.assertEqual(r['summary']['delivered_feature_bytes'],(4*16+28)*2048*2)
        self.assertEqual(calculate(**r['scenario']),r)
        nodes=r['request_execution_nodes']
        self.assertEqual([n['produces_output_token'] for n in nodes if 'produces_output_token' in n],[1,2,3])
        for i,n in enumerate(nodes):self.assertEqual(n['depends_on'],[nodes[i-1]['id']] if i else [])
        for k in ('matrix_flops','accounted_scalar_flops','accounted_interface_bytes'):
            self.assertEqual(r['summary'][k],sum(n[k] for n in nodes))

    def test_cache_preserves_prefill_and_four_visual_payloads(self):
        args=dict(text_tokens=3,output_tokens=1,image_grids=[[1,4,4]],video_grids=[],mel_lengths=[100])
        miss=calculate(**args)
        hit=calculate(**args,image_cache_hits=[True],audio_cache_hits=[True])
        self.assertEqual(hit['thinker_prefill'],miss['thinker_prefill'])
        self.assertEqual(hit['deepstack_injection'],miss['deepstack_injection'])
        self.assertEqual(hit['thinker_decode'],[])
        self.assertEqual(miss['summary']['matrix_flops']-hit['summary']['matrix_flops'],
                         miss['encoders']['image']['summary']['matrix_flops']+miss['encoders']['audio']['summary']['matrix_flops'])
        cache=[n for n in hit['request_execution_nodes'] if n['id'].endswith('cache_read')]
        self.assertEqual(sum(n['accounted_interface_bytes'] for n in cache),(4*4+13)*2048*2)

    def test_expert_union_and_resident_capacity(self):
        args=dict(text_tokens=17,output_tokens=1,image_grids=[],video_grids=[],mel_lengths=[])
        a=calculate(**args);b=calculate(**args,routing='concentrated')
        self.assertEqual(a['summary']['matrix_flops'],b['summary']['matrix_flops'])
        self.assertEqual(a['thinker_prefill']['routing']['expert_union_per_layer'],128)
        self.assertEqual(b['thinker_prefill']['routing']['expert_union_per_layer'],8)
        self.assertEqual(a['summary']['logical_thinker_parameters'],30532646912)
        self.assertEqual(a['summary']['uniform_thinker_parameter_bytes'],b['summary']['uniform_thinker_parameter_bytes'])
        diff=3*48*(128-8)*2048*768*2
        self.assertEqual(a['thinker_prefill']['summary']['matrix_weight_interface_bytes']-
                         b['thinker_prefill']['summary']['matrix_weight_interface_bytes'],diff)
        fp32=calculate(**args,dtype='fp32')
        self.assertEqual(fp32['summary']['matrix_flops'],a['summary']['matrix_flops'])
        self.assertEqual(fp32['summary']['kv_after_prefill_bytes'],2*a['summary']['kv_after_prefill_bytes'])

    def test_audio_miss_batch_geometry_is_explicit(self):
        args=dict(text_tokens=1,output_tokens=1,image_grids=[],video_grids=[],mel_lengths=[100,9])
        full=calculate(**args)
        hit=calculate(**args,audio_cache_hits=[True,False])
        self.assertEqual(full['position_budget'],hit['position_budget'])
        self.assertEqual(full['audio_cache_contract']['actual_miss_chunk_execution']['attention_window_positions'],104)
        self.assertEqual(hit['audio_cache_contract']['actual_miss_chunk_execution']['attention_window_positions'],16)
        self.assertEqual(hit['audio_cache_contract']['miss_item_indices'],[1])
        self.assertEqual(hit['audio_cache_contract']['actual_miss_segments'][0]['audio'],0)

    def test_invalid_inputs(self):
        for kw in ({'text_tokens':True},{'output_tokens':0},{'image_grids':[[2,4,4]]},
                   {'audio_cache_hits':[]},{'mel_lengths':[30001],'audio_cache_hits':[True]},
                   {'text_tokens':0,'image_grids':[],'video_grids':[],'mel_lengths':[]}):
            with self.assertRaises(ValueError):calculate(**kw)

if __name__=='__main__':unittest.main()
