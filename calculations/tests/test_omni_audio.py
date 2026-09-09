"""Audio time-axis checks from independent decode call enumeration."""
import unittest
from fractions import Fraction
from infra_calc.topics.omni_audio import calculate, omni_wave_length
from infra_calc.sources import model_config


class OmniAudioTests(unittest.TestCase):
    def test_omni_code_predictor_invocations_and_attention(self):
        r=calculate(frames=3,batch=2)
        p=r['audio_stages'][2]
        positions=[2]+[1]*14
        visited=0;pairs=0
        for count in positions:
            for _ in range(count):
                visited+=1;pairs+=visited
        self.assertEqual(visited,16)
        self.assertEqual(p['summary']['processed_rows'],2*3*visited)
        self.assertEqual(p['summary']['valid_attention_pairs_all_invocations'],2*3*pairs)
        head=next(x for x in p['matrices'] if x['name']=='output_head')
        self.assertEqual(head['rows_per_layer'],96)
        self.assertEqual(head['stored_copies_per_layer'],15)
        self.assertEqual(r['audio_codebook_loops']['predictor_calls'],45)
        self.assertEqual(p['summary']['kv_retained_logical_bytes'],2*5*8*128*2*2*16)
        talker=r['audio_stages'][1]
        self.assertIn('shared_expert_output_gate',{x['name'] for x in talker['matrices']})

    def test_fish_priming_is_real_work_and_rate_is_rational(self):
        r=calculate(model='fish-audio-s2-pro',frames=4)
        fast=r['audio_stages'][1]
        self.assertEqual(fast['summary']['processed_rows'],40)
        self.assertEqual(fast['summary']['valid_attention_pairs_all_invocations'],4*sum(range(1,11)))
        self.assertEqual(r['audio_codebook_loops']['fast_discarded_priming_heads'],4)
        self.assertEqual(r['audio_codebook_loops']['fast_sampled_residual_heads'],36)
        self.assertEqual(Fraction(r['audio_codec_timing']['nominal_frames_per_second_exact']),Fraction(44100,2048))
        self.assertEqual(r['audio_codec_timing']['source_output_samples'],4*2048)
        q=next(x for x in fast['matrices'] if x['name']=='q')
        self.assertEqual((q['input_width'],q['output_width']),(2560,4096))
        self.assertEqual(r['audio_bridges']['fast_project_in_matrix_flops'],0)

    def test_omni_transposed_convolution_crop_not_nominal_hop(self):
        c=model_config('qwen3-omni-30b-a3b-instruct')['code2wav_config']
        for frames in (1,12,72,73):
            length=frames
            for stride,kernel in [(2,2),(2,2),(8,16),(5,10),(4,8),(3,6)]:
                # Enumerate contributed output coordinates before the two-sided crop.
                coordinates={i*stride+j for i in range(length) for j in range(kernel)}
                low=kernel-stride;high=max(coordinates)+1-low
                length=sum(low<=x<high for x in coordinates)
            got=omni_wave_length(frames,c)
            self.assertEqual(got['output_samples'],length)
            self.assertEqual(length,1920*frames-555)
        r=calculate(frames=73)
        codec=r['audio_stages'][-1]
        self.assertEqual(codec['summary']['valid_attention_pairs_all_invocations'],sum(range(1,73))+72)
        self.assertEqual(codec['summary']['kv_retained_logical_bytes'],0)
        with self.assertRaises(ValueError):
            calculate(frames=0)
        with self.assertRaises(ValueError):
            calculate(element_bytes=1)

    def test_unfolded_dependencies_work_conservation_and_rates(self):
        r=calculate(frames=2,text_tokens=3,effective_matrix_flops_per_second=10**12)
        nodes=r['audio_execution_dag']['nodes']
        positions={n['id']:i for i,n in enumerate(nodes)}
        for i,n in enumerate(nodes):
            self.assertEqual(n['depends_on'],[nodes[i-1]['id']] if i else [])
        self.assertLess(positions['frame_0_code_14'],positions['frame_1_primary'])
        self.assertLess(positions['frame_1_code_14'],positions['codec_code_embedding_lookup'])
        self.assertEqual(nodes[-1]['id'],'return_float32_wave')
        codec=r['audio_codec_operations']
        self.assertEqual(sum(n['matrix_flops'] for n in nodes),
                         r['summary']['accounted_transformer_and_bridge_matrix_flops']+codec['summary']['matrix_flops'])
        supply=r['audio_supply']
        self.assertEqual(Fraction(supply['accounted_serial_critical_path_lower_bound_seconds_exact']),
                         Fraction(sum(n['matrix_flops'] for n in nodes),10**12))
        self.assertIsNone(supply['first_audio_latency_seconds'])
        self.assertEqual(Fraction(supply['required_matrix_flops_per_second_exact']),
                         Fraction(sum(n['matrix_flops'] for n in nodes))*24000/codec['output_samples_per_request'])

    def test_codec_source_interfaces_and_transposed_contribution_work(self):
        r=calculate(frames=1)
        ops={op['name']:op for op in r['audio_codec_operations']['operators']}
        first=ops['upsample_0']
        self.assertEqual(first['matrix_flops'],2*1*1024*1024*2)
        self.assertEqual(first['output_elements'],2*1024)
        embed=ops['code_embedding_lookup']
        self.assertEqual(embed['weight_interface_bytes'],16*1024*2)
        self.assertEqual(embed['activation_read_bytes'],16*8)
        self.assertEqual(ops['code_embedding_mean']['scalar_flops'],16*1024)
        snake=ops['output_snake']
        self.assertEqual(snake['special_ops']['sin'],1365*96)
        self.assertEqual(snake['special_ops']['exp'],2*96)
        self.assertEqual(ops['output_conv']['matrix_flops'],2*1365*96*7)
        self.assertEqual(r['audio_codec_operations']['output_samples_per_request'],1365)

    def test_interface_weight_visits_and_lifetime_do_not_multiply_frames(self):
        a=calculate(model='fish-audio-s2-pro',frames=1)
        b=calculate(model='fish-audio-s2-pro',frames=3)
        fast_a=a['audio_stages'][1];fast_b=b['audio_stages'][1]
        self.assertEqual(fast_a['state_lifecycle']['retained_bytes'],fast_b['state_lifecycle']['retained_bytes'])
        self.assertEqual(fast_b['summary']['matrix_weight_interface_bytes'],3*fast_a['summary']['matrix_weight_interface_bytes'])
        self.assertEqual(sum(n.get('output_discarded',False) for n in b['audio_execution_dag']['nodes']),3)
        rates=calculate(model='fish-audio-s2-pro',frames=1,effective_matrix_flops_per_second=1000,
                        effective_interface_bytes_per_second=100)
        node=rates['audio_execution_dag']['nodes'][0]
        self.assertEqual(Fraction(node['conditional_service_lower_bound_seconds_exact']),
                         max(Fraction(node['matrix_flops'],1000),Fraction(node['accounted_interface_bytes'],100)))
        for kwargs in [dict(effective_matrix_flops_per_second=0),dict(effective_scalar_flops_per_second='nan'),
                       dict(effective_interface_bytes_per_second=True),dict(frames=301)]:
            with self.assertRaises(ValueError):
                calculate(**kwargs)

    def test_fish_codec_rvq_and_exact_right_crop(self):
        from infra_calc.topics.omni_audio import fish_codec_config
        c=fish_codec_config()
        self.assertEqual(c['num_quantizers'],10)
        self.assertEqual(c['post_transformer']['num_hidden_layers'],8)
        for frames in (1,3,129):
            r=calculate(model='fish-audio-s2-pro',frames=frames)
            codec=r['audio_codec_operations'];ops={x['name']:x for x in codec['operators']}
            length=frames
            for stride,kernel in [(2,2),(2,2),(8,16),(8,16),(4,8),(2,4)]:
                # Independent ConvTranspose final coordinate and source right crop.
                last_coordinate=(length-1)*stride+(kernel-1)
                length=last_coordinate+1-(kernel-stride)
            self.assertEqual(codec['output_samples_per_request'],length)
            self.assertEqual(length,2048*frames)
            self.assertEqual(ops['residual_index_clamp']['special_ops']['integer_max_compare'],9*frames)
            self.assertEqual(ops['semantic_book_0_lookup']['weight_interface_bytes'],frames*8*2)
            self.assertEqual(ops['residual_book_8_out_proj']['matrix_flops'],2*frames*8*1024)
            self.assertEqual(ops['rvq_post_transformer']['transformer']['summary']['valid_attention_pairs_all_invocations'],
                             sum(min(i,128) for i in range(1,frames+1)))
            self.assertEqual(len([op for op in codec['operators'] if op['kind']=='transformer']),1)
            self.assertIn('wave_tanh',ops)
            self.assertNotIn('exp',ops['output_snake']['special_ops'])
            self.assertTrue(any(op['kind']=='weight_normalization' for op in codec['operators']))
            self.assertEqual(codec['persistent_decode_module_buffers']['post_module_causal_mask_bool_bytes'],1024**3)

    def test_fish_prompt_prefill_produces_first_code_without_extra_slow_step(self):
        r=calculate(model='fish-audio-s2-pro',frames=2,fish_prompt_tokens=8,audio_history=0)
        slow=r['audio_stages'][0]
        self.assertEqual(slow['summary']['processed_rows'],9)
        self.assertEqual(slow['summary']['valid_attention_pairs_all_invocations'],sum(range(1,10)))
        head=next(x for x in slow['matrices'] if x['name']=='output_head')
        self.assertEqual(head['rows_per_layer'],2)
        self.assertEqual(slow['summary']['special_ops']['rsqrt'],2*36*9+2+36*9*40)
        nodes={n['id']:n for n in r['audio_execution_dag']['nodes']}
        self.assertEqual(nodes['frame_0_primary']['processed_rows'],8)
        self.assertEqual(nodes['frame_1_primary']['processed_rows'],1)
        self.assertTrue(nodes['frame_0_slow_input_mask']['text_only_prompt'])
        self.assertGreater(nodes['frame_0_slow_input_lookup']['accounted_interface_bytes'],0)
        self.assertTrue(nodes['frame_0_fast_embedding_9']['output_unused'])
        self.assertEqual(len([n for n in nodes.values() if n['kind']=='transformer' and n['id'].endswith('_primary')]),2)
        with self.assertRaises(ValueError):
            calculate(fish_prompt_tokens=1)

    def test_fish_codec_supply_includes_whole_decoder_and_prompt(self):
        r=calculate(model='fish-audio-s2-pro',frames=3,fish_prompt_tokens=5,
                    effective_matrix_flops_per_second=10**12)
        expected=r['summary']['accounted_transformer_and_bridge_matrix_flops']+r['audio_codec_operations']['summary']['matrix_flops']
        self.assertEqual(r['audio_supply']['accounted_work_totals']['matrix_flops'],expected)
        self.assertEqual(Fraction(r['audio_supply']['accounted_serial_critical_path_lower_bound_seconds_exact']),
                         Fraction(expected,10**12))
        self.assertEqual(Fraction(r['audio_supply']['duration_basis_seconds_exact']),Fraction(3*2048,44100))
        nodes=r['audio_execution_dag']['nodes']
        self.assertEqual(nodes[-1]['id'],'codec_wave_tanh')
