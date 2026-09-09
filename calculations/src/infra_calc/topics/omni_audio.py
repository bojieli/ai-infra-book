"""Audio autoregressive stage geometry and codebook time axes.

Config-derived transformer matrices, declared scalar work, operator interfaces
and unfolded codebook dependencies. Omni codec convolutions are included;
Fish RVQ/decoder and Omni codec are accounted; complete request preparation
and runtime implementation costs remain explicit gaps.
"""
import hashlib
import ast
import re
import json
from fractions import Fraction
from math import prod

from ..paths import PROJECT
from ..sources import model_config, provenance
from ..units import positive_int

RESEARCH = 'research/generative-audio-analysis'


def evidence() -> list[dict]:
    rows = json.loads((PROJECT / RESEARCH / 'sources.lock.json').read_text())['sources']
    result = []
    for row in rows:
        path = f"{RESEARCH}/{row['file']}"
        data = (PROJECT / path).read_bytes()
        if len(data) != row['bytes'] or hashlib.sha256(data).hexdigest() != row['sha256']:
            raise ValueError(f'Audio implementation evidence mismatch: {path}')
        result.append({**row, 'file': path})
    return result


def transformer(name, c, rows, pairs, retained_positions, batch, element_bytes,
                output_rows=0, head_copies=1):
    """One architecture's matrix subtotal; row/pair totals include all invocations."""
    h, layers, heads, kv = (c[k] for k in ('hidden_size','num_hidden_layers','num_attention_heads','num_key_value_heads'))
    d = c.get('head_dim', h // heads)
    matrices = []
    def add(label, inputs, outputs, row_count, stored=1, repetitions=layers):
        matrices.append(dict(name=label, input_width=inputs, output_width=outputs,
                             rows_per_layer=row_count, repeats=repetitions,
                             stored_copies_per_layer=stored,
                             matrix_parameters=repetitions*stored*inputs*outputs,
                             matrix_flops=2*repetitions*row_count*inputs*outputs))
    for label,i,o in [('q',h,heads*d),('k',h,kv*d),('v',h,kv*d),('o',heads*d,h)]:
        add(label,i,o,rows)
    if c.get('num_experts',1)>1:
        e,k,f=c['num_experts'],c['num_experts_per_tok'],c['moe_intermediate_size']
        add('router',h,e,rows)
        for label,i,o in [('expert_gate',h,f),('expert_up',h,f),('expert_down',f,h)]:
            add(label,i,o,rows*k,e)
        shared=c.get('shared_expert_intermediate_size',0)
        if shared:
            for label,i,o in [('shared_gate',h,shared),('shared_up',h,shared),('shared_down',shared,h)]:
                add(label,i,o,rows)
            add('shared_expert_output_gate',h,1,rows)
    else:
        f=c['intermediate_size']
        for label,i,o in [('ffn_gate',h,f),('ffn_up',h,f),('ffn_down',f,h)]:
            add(label,i,o,rows)
    if output_rows:
        add('output_head',h,c['vocab_size'],output_rows,head_copies,1)
    qk=2*layers*heads*pairs*d
    return dict(name=name, matrices=matrices,
                summary=dict(projection_and_ffn_matrix_flops=sum(r['matrix_flops'] for r in matrices),
                             qk_matrix_flops=qk,pv_matrix_flops=qk,
                             matrix_flops=sum(r['matrix_flops'] for r in matrices)+2*qk,
                             matrix_weight_elements=sum(r['matrix_parameters'] for r in matrices),
                             kv_bytes_per_position_per_request=2*layers*kv*d*element_bytes,
                             kv_retained_logical_bytes=2*layers*kv*d*element_bytes*batch*retained_positions,
                             processed_rows=rows,valid_attention_pairs_all_invocations=pairs))


def fish_config(c):
    return dict(hidden_size=c['dim'],num_hidden_layers=c['n_layer'],num_attention_heads=c['n_head'],
                num_key_value_heads=c['n_local_heads'],head_dim=c['head_dim'],
                intermediate_size=c['intermediate_size'],vocab_size=c['vocab_size'],
                attention_qk_norm=c['attention_qk_norm'])


def omni_wave_length(frames: int, c: dict) -> dict:
    """Exact tensor lengths of the pinned code's ConvTranspose and two-sided crop."""
    positive_int(frames,'frames')
    length=frames; stages=[]
    for stride,kernel in [(r,r) for r in c['upsampling_ratios']]+[(r,2*r) for r in c['upsample_rates']]:
        raw=(length-1)*stride+kernel
        crop=kernel-stride
        after=raw-2*crop
        stages.append(dict(input_length=length,stride=stride,kernel=kernel,raw_length=raw,
                           crop_each_side=crop,output_length=after))
        length=after
    return dict(stages=stages,output_samples=length,nominal_samples=frames*prod(c['upsampling_ratios']+c['upsample_rates']))


def calculate(model: str = 'qwen3-omni-30b-a3b-instruct', frames: int = 12,
              batch: int = 1, text_tokens: int = 16, text_history: int = 128,
              audio_history: int = 32, element_bytes: int = 2,
              effective_matrix_flops_per_second=None, effective_interface_bytes_per_second=None,
              effective_scalar_flops_per_second=None, fish_prompt_tokens: int = 0) -> dict:
    for key,value in [('frames',frames),('batch',batch),('text_tokens',text_tokens),('element_bytes',element_bytes)]:
        positive_int(value,key)
    for key,value in [('text_history',text_history),('audio_history',audio_history)]:
        positive_int(value,key,allow_zero=True)
    if element_bytes not in (2,4):
        raise ValueError('KV comparison precision must be BF16/FP16-sized or FP32-sized')
    if model not in ('qwen3-omni-30b-a3b-instruct','fish-audio-s2-pro'):
        raise ValueError('Unsupported audio model')
    positive_int(fish_prompt_tokens,'fish_prompt_tokens',allow_zero=True)
    if fish_prompt_tokens and model!='fish-audio-s2-pro':
        raise ValueError('fish_prompt_tokens applies only to Fish')
    sources=evidence()+provenance(model)
    c=model_config(model)
    stages=[]
    if model.startswith('qwen3-omni'):
        thinker,talker,predictor=c['thinker_config']['text_config'],c['talker_config']['text_config'],c['talker_config']['code_predictor_config']
        if text_history+text_tokens>thinker['max_position_embeddings'] or audio_history+frames>talker['max_position_embeddings']:
            raise ValueError('Text/talker positions exceed configured context')
        groups=c['talker_config']['num_code_groups']
        # Each independent predictor generate: two-position prefill + G-2 decode calls.
        predictor_rows=groups
        stages.append(transformer('thinker_text',thinker,batch*text_tokens,
                                  batch*(text_tokens*text_history+text_tokens*(text_tokens+1)//2),
                                  text_history+text_tokens,batch,element_bytes,batch*text_tokens))
        stages.append(transformer('talker_temporal',talker,batch*frames,
                                  batch*(frames*audio_history+frames*(frames+1)//2),
                                  audio_history+frames,batch,element_bytes,batch*frames))
        stages.append(transformer('code_predictor_reset_each_frame',predictor,batch*frames*predictor_rows,
                                  batch*frames*predictor_rows*(predictor_rows+1)//2,
                                  predictor_rows,batch,element_bytes,batch*frames*predictor_rows,groups-1))
        wav=c['code2wav_config'];window=wav['sliding_window']
        stages.append(transformer('code2wav_pre_transformer',wav,batch*frames,
                                  batch*sum(min(i,window) for i in range(1,frames+1)),0,batch,element_bytes))
        # Resize MLPs separately transform Thinker token embeddings and accepted hidden states.
        resize_rows=batch*text_tokens
        resize_flops=2*resize_rows*(c['talker_config']['thinker_hidden_size']*talker['intermediate_size']+
                                    talker['intermediate_size']*talker['hidden_size'])
        bridges=dict(text_projection_matrix_flops=resize_flops,hidden_projection_matrix_flops=resize_flops,
                     projected_rows_each=resize_rows,
                     assumption='Two ResizeMLPs on the declared text token rows; prompt/control projection rows beyond these are excluded.')
        wave=omni_wave_length(frames,wav)
        timing=dict(sample_rate=24000,nominal_samples_per_frame=1920,nominal_frames_per_second_exact='25/2',
                    source_output_samples=wave['output_samples'],nominal_output_samples=wave['nominal_samples'],
                    source_output_seconds_exact=str(Fraction(wave['output_samples'],24000)),
                    nominal_output_seconds_exact=str(Fraction(wave['nominal_samples'],24000)),
                    crop_length_discrepancy_samples=wave['nominal_samples']-wave['output_samples'],
                    convtranspose_lengths=wave['stages'],code2wav_chunk_calls=1)
        loops=dict(primary_audio_codes=frames,residual_codes=frames*(groups-1),
                   predictor_calls=frames*(groups-1),predictor_processed_positions=frames*groups,
                   predictor_prefill_positions=2,predictor_single_position_calls_per_frame=groups-2,
                   predictor_cache_reset_per_frame=True)
    else:
        slow,fast=fish_config(c['text_config']),fish_config(c['audio_decoder_config'])
        if audio_history+frames+max(fish_prompt_tokens-1,0)>c['text_config']['max_seq_len']:
            raise ValueError('Slow AR positions exceed configured context')
        groups=c['audio_decoder_config']['num_codebooks']
        slow_positions=frames+max(fish_prompt_tokens-1,0)
        slow_pairs=slow_positions*audio_history+slow_positions*(slow_positions+1)//2
        slow['_final_norm_rows']=batch*frames
        stages.append(transformer('slow_ar',slow,batch*slow_positions,batch*slow_pairs,
                                  audio_history+slow_positions,batch,element_bytes,batch*frames))
        stages.append(transformer('fast_ar_reset_each_frame',fast,batch*frames*groups,
                                  batch*frames*groups*(groups+1)//2,groups,batch,element_bytes,batch*frames*groups))
        bridges=dict(fast_project_in_matrix_flops=0,
                     assumption='Official dimensions equal 2560: fast_project_in is Identity. Slow text/reference-audio prompt prefill is already represented by audio_history and not charged in this continuation.')
        timing=dict(sample_rate=44100,nominal_samples_per_frame=2048,
                    nominal_frames_per_second_exact=str(Fraction(44100,2048)),
                    nominal_output_samples=frames*2048,
                    nominal_output_seconds_exact=str(Fraction(frames*2048,44100)),
                    source_output_samples=None,
                    evidence='DAC encoder rates 2*4*8*8, RVQ downsample factors 2*2. Decoder source length and work are added in audio_codec_operations.')
        loops=dict(primary_audio_codes=frames,residual_codes=frames*(groups-1),
                   fast_calls=frames*groups,fast_discarded_priming_heads=frames,
                   fast_sampled_residual_heads=frames*(groups-1),fast_cache_reset_per_frame=True)
    execution = execution_ledger(model,c,stages,bridges,frames,batch,text_tokens,text_history,
                                 audio_history,element_bytes,effective_matrix_flops_per_second,
                                 effective_interface_bytes_per_second,effective_scalar_flops_per_second,fish_prompt_tokens)
    if model=='fish-audio-s2-pro':
        samples=execution['audio_codec_operations']['output_samples_per_request']
        timing.update(source_output_samples=samples,source_output_seconds_exact=str(Fraction(samples,44100)),
                      evidence='Locked Fish right-only ConvTranspose crops preserve each stride; source decoder produces exactly 2048*frames samples.')
    matrix=sum(stage['summary']['matrix_flops'] for stage in stages)+sum(value for key,value in bridges.items() if key.endswith('_matrix_flops'))
    return dict(schema_version=1,calculation='audio-generation-matrix-and-codebook-ledger',model=model,
                scenario=dict(frames=frames,batch=batch,text_tokens=text_tokens,text_history=text_history,
                              audio_history=audio_history,kv_element_bytes=element_bytes,operand_element_bytes=element_bytes,fish_prompt_tokens=fish_prompt_tokens),sources=sources,
                **execution, audio_stages=stages,audio_codebook_loops=loops,audio_codec_timing=timing,audio_bridges=bridges,
                summary=dict(accounted_transformer_and_bridge_matrix_flops=matrix,
                             full_model_parameters=None,full_generation_flops=None,
                             full_codec_flops=None,predicted_latency_seconds=None),
                assumptions=[
                    'The legacy stage matrix subtotal is preserved; audio_supply includes the unfolded stages and added Omni codec graph. This is not a runnable-model/full-request total. Matrix weight elements exclude embeddings, norms and biases and do not replace complete model parameters. element_bytes is a uniform operand/KV comparison precision, not an assertion of every runtime dtype.',
                    'Transformer causal work uses valid pairs; logical KV uses explicit bytes per element, not a claim about backend accumulation, cache allocation, FP8 support or HBM. MoE uses top-k selected row totals; resident expert matrix count uses all experts.',
                    'Text-token and acoustic-frame axes are independent. Omni code predictor is reset each frame, 2-token prefill then 14 singleton calls: 15 residual outputs but 16 processed positions and 16 output-head rows. Fish primes fast AR once with slow hidden and discards its logits, then executes 9 sampled residual steps: 10 fast calls, not 9.',
                    'Omni Talker includes shared SwiGLU and its scalar output gate projection. ResizeMLP matrix work is counted for the declared text rows; actual special-token packing, speaker/tts prompts and termination are not simulated.',
                    'Omni code2wav pre-transformer uses a 72-position causal window. Its ConvTranspose crop formula is audited separately: both pinned v4.57.1 and inspected current official source crop kernel-stride from both ends. For this config each whole chunk yields 1920*frames-555 samples, unlike nominal 1920*frames; this is source geometry, not a measured waveform or corrected implementation.',
                    'Fish codec uses 44100/(512*4)=21.533203125 frames/s, not exactly 21. The official codec YAML has one semantic codebook of 4096 and nine residual codebooks of 1024, while Fast AR logits have width 4096; logits vocabulary width must not be silently changed to codec size. The locked RVQ.decode clamps residual indices to 1023 and semantic indices to 4095; integer clamp and lookup are included separately.',
                    'Updated execution ledger adds declared Transformer scalar work, full Omni non-transformer codec conv/Snake/ConvNeXt operations, operator interfaces and ordered frame/codebook DAG. Missing remain uncounted token preparation and sampling, multi-chunk execution, complete runtime conversions/allocator/placement and measured latency/quality. No marketing parameter label is used as an exact parameter count.',
                ])


def omni_codec_operators(frames, batch, c, element_bytes=2, codec_kind="omni"):
    """Shared codec primitives with explicit conv/crop interfaces.

    Conv1d work includes left zero-padding products; transposed convolution
    counts all pre-crop input/kernel contributions, not only retained samples.
    """
    fish = codec_kind == "fish"
    ops=[]; h=c['hidden_size']; length=frames
    def op(name,kind,inputs,outputs,weight=0,matrix=0,scalar=0,special=None,**extra):
        ops.append(dict(name=name,kind=kind,input_elements=inputs,output_elements=outputs,
                        weight_elements=weight,matrix_flops=matrix,scalar_flops=scalar,
                        special_ops=special or {},weight_interface_bytes=weight*element_bytes,
                        activation_read_bytes=inputs*element_bytes,
                        activation_write_bytes=outputs*element_bytes,**extra))
    if not fish:
        code_cells=batch*frames*c['num_quantizers']
        op('code_embedding_lookup','embedding',0,code_cells*h,weight=code_cells*h,
           resident_embedding_elements=c['codebook_size']*c['num_quantizers']*h,
           special={'integer_offset_add':code_cells})
        ops[-1]['activation_read_bytes']=code_cells*8
        op('code_embedding_mean','embedding',code_cells*h,batch*frames*h,scalar=code_cells*h,
           note='Explicit embedding output consumed by mean: 15 adds and one division per hidden element.')
    def normalize_weight(name,weights,channels):
        op(name+'_weight_norm','weight_normalization',weights+channels,weights,scalar=3*weights,
           special={'sqrt':channels},
           note='Declared g*v/||v|| per dim-0 group; source weight_norm is not removed by the inference loader.')
    def conv(name,ci,co,kernel,groups=1,dilation=1):
        if fish and name.startswith(('decoder_','output_conv')):
            normalize_weight(name,ci*co*kernel//groups,co)
        count=batch*length*co
        op(name,'causal_conv1d',batch*length*ci,count,ci*co*kernel//groups+co,
           2*batch*length*co*(ci//groups)*kernel,count,
           input_length=length,output_length=length,kernel=kernel,dilation=dilation,groups=groups,
           note='Length-preserving causal padding. Matrix work includes padded-zero products; bias counted separately.')
    def transpose(name,ci,co,kernel,stride):
        nonlocal length
        raw=(length-1)*stride+kernel; crop=kernel-stride; after=raw-(crop if fish else 2*crop)
        if fish and name.startswith('decoder_'):
            normalize_weight(name,ci*co*kernel,ci)
        op(name,'conv_transpose1d',batch*length*ci,batch*raw*co,ci*co*kernel+co,
           2*batch*length*ci*co*kernel,batch*raw*co,input_length=length,
           output_length_before_crop=raw,retained_length=after,kernel=kernel,stride=stride,
           note='Full source ConvTranspose before two-sided crop; scattered contribution multiply/add count.')
        op(name+'_crop_contiguous','copy',batch*after*co,batch*after*co,
           crop_each_side=crop if not fish else None,crop_left=0 if fish else crop,crop_right=crop,
           note='Retained slice materialized by contiguous(); Fish trims only right, Omni both sides.')
        length=after
    def snake(name,channels):
        cells=batch*length*channels
        op(name,'snake1d' if fish else 'snake_beta',cells,cells,channels if fish else 2*channels,scalar=4*cells+2*channels,
           special={'sin':cells} if fish else {'sin':cells,'exp':2*channels},
           note='Fish uses alpha directly (no exp); Omni exponentiates alpha/beta. Both apply reciprocal, sin-square, scale and residual add.')
    if fish:
        for group,books in [('semantic',1),('residual',c['num_quantizers']-1)]:
            count=batch*frames*books
            op(group+'_index_clamp','index',0,0,special={'integer_max_compare':count})
            ops[-1]['activation_read_bytes']=ops[-1]['activation_write_bytes']=count*8
            for index in range(books):
                prefix=f'{group}_book_{index}'
                cells=batch*frames*c['codebook_dim']
                op(prefix+'_lookup','embedding',0,cells,weight=cells)
                ops[-1]['activation_read_bytes']=batch*frames*8
                normalize_weight(prefix+'_out_proj',c['codebook_dim']*h,h)
                op(prefix+'_out_proj','conv1d',cells,batch*frames*h,c['codebook_dim']*h+h,
                   matrix=2*batch*frames*c['codebook_dim']*h,scalar=batch*frames*h)
                op(prefix+'_accumulate','reduce',batch*frames*h*(1 if index==0 else 2),batch*frames*h,
                   scalar=batch*frames*h,note='Source begins z_q=0.0, including the first scalar-zero add.')
            op(group+'_unused_latent_cat','copy',count*c['codebook_dim'],count*c['codebook_dim'])
        op('semantic_residual_add','residual',2*batch*frames*h,batch*frames*h,scalar=batch*frames*h)
        tc=c['post_transformer']
        st=transformer('fish_codec_post',tc,batch*frames,batch*sum(min(i,128) for i in range(1,frames+1)),0,batch,element_bytes)
        stage_execution(st,1,batch,element_bytes,tc)
        z=st['summary']
        op('rvq_post_transformer','transformer',batch*frames*h,batch*frames*h,
           matrix=z['matrix_flops'],scalar=z['accounted_scalar_flops'],special=z['special_ops'],transformer=st)
        ops[-1]['weight_interface_bytes']=z['matrix_weight_interface_bytes']
        ops[-1]['activation_read_bytes']=z['accounted_interface_bytes']-z['matrix_weight_interface_bytes']
        ops[-1]['activation_write_bytes']=0
    for index,factor in enumerate(c['upsampling_ratios']):
        prefix=f'upsample_{index}'
        transpose(prefix,h,h,factor,factor)
        conv(prefix+'_depthwise',h,h,7,groups=h)
        cells=batch*length*h
        op(prefix+'_layernorm','normalization',cells,cells,2*h,
           scalar=batch*length*(7*h+1),special={'rsqrt':batch*length})
        op(prefix+'_pointwise1','linear',cells,4*cells,h*4*h+4*h,
           matrix=2*batch*length*h*4*h,scalar=4*cells)
        op(prefix+'_gelu','activation',4*cells,4*cells,special={'gelu':4*cells})
        op(prefix+'_pointwise2','linear',4*cells,cells,4*h*h+h,
           matrix=2*batch*length*4*h*h,scalar=cells)
        op(prefix+'_gamma_residual','residual',2*cells,cells,h,scalar=2*cells)
    conv('decoder_input',h,c['decoder_dim'],7)
    for index,rate in enumerate(c['upsample_rates']):
        ci=c['decoder_dim']//2**index; co=ci//2
        snake(f'decoder_{index}_snake',ci)
        transpose(f'decoder_{index}_upsample',ci,co,2*rate,rate)
        for dilation in (1,3,9):
            prefix=f'decoder_{index}_residual_d{dilation}'
            snake(prefix+'_snake1',co);conv(prefix+'_conv1',co,co,7,dilation=dilation)
            snake(prefix+'_snake2',co);conv(prefix+'_conv2',co,co,1)
            cells=batch*length*co
            op(prefix+'_add','residual',2*cells,cells,scalar=cells)
    final_channels=c['decoder_dim']//2**len(c['upsample_rates'])
    snake('output_snake',final_channels);conv('output_conv',final_channels,1,7)
    op('wave_tanh' if fish else 'wave_clamp','activation',batch*length,batch*length,
       special={'tanh':batch*length} if fish else {'compare':2*batch*length})
    totals={key:sum(row[key] for row in ops) for key in ('matrix_flops','scalar_flops','weight_interface_bytes','activation_read_bytes','activation_write_bytes')}
    totals['interface_bytes']=sum(totals[key] for key in ('weight_interface_bytes','activation_read_bytes','activation_write_bytes'))
    return dict(operators=ops,summary=totals,output_samples_per_request=length,
                coverage='Ordered decoder graph under declared conv arithmetic/operator interfaces; Fish includes RVQ post-transformer, Omni pre-transformer is outside this helper. Special primitives separate; not measured kernel work.')


def stage_execution(stage, invocations, batch, element_bytes, config):
    """Add operator interface accounting without treating resident MoE as reads."""
    summary=stage['summary'];rows=summary['processed_rows']; matrices=stage['matrices']
    e=config.get('num_experts',1);k=config.get('num_experts_per_tok',1)
    for row in matrices:
        expert=row['name'].startswith('expert_')
        # Conditional balanced routing per invocation; one expert read per visited expert.
        visited=min(e,batch*k) if expert else 1
        row['weight_read_invocations']=invocations*visited
        row['weight_interface_bytes']=row['input_width']*row['output_width']*row['repeats']*invocations*visited*element_bytes
        row['activation_read_bytes']=row['rows_per_layer']*row['input_width']*row['repeats']*element_bytes
        row['activation_write_bytes']=row['rows_per_layer']*row['output_width']*row['repeats']*element_bytes
    h=config['hidden_size'];l=config['num_hidden_layers'];heads=config['num_attention_heads'];kv=config['num_key_value_heads'];d=config.get('head_dim',h//heads)
    # Logical per-query KV operands with KV-head reuse across GQA heads; prefill
    # query reuse across positions is not assumed in this declared interface.
    pairs=summary['valid_attention_pairs_all_invocations']
    attention_bytes=l*element_bytes*(2*rows*heads*d+2*pairs*kv*d+2*pairs*heads)
    final_norm_rows=config.get('_final_norm_rows',rows)
    norm_scalar=(2*l*rows+final_norm_rows)*(4*h+1)
    norm_special={'rsqrt':2*l*rows+final_norm_rows}
    qk_norm=config.get('attention_qk_norm',stage['name']!='code2wav_pre_transformer')
    if qk_norm:
        norm_scalar+=l*rows*(heads+kv)*(4*d+1)
        norm_special['rsqrt']+=l*rows*(heads+kv)
    # Two residuals, all SwiGLU/SiLU rows, router stable softmax and routed mixing.
    scalar=norm_scalar+2*l*rows*h+3*l*rows*(heads+kv)*d
    special={**norm_special,'rope_sign_negation':l*rows*(heads+kv)*d//2,
             'attention_exp':l*heads*pairs,'attention_max_compare':l*heads*(pairs-rows)}
    scalar+=l*heads*(4*pairs-rows)
    if e>1:
        f=config['moe_intermediate_size'];shared=config.get('shared_expert_intermediate_size',0)
        scalar+=l*rows*(2*k*f+2*shared+(3*e-1)+(2*k-1)+h*(2*k-1))
        special['sigmoid']=l*rows*(k*f+shared)
        special['router_exp']=l*rows*e;special['router_max_compare']=l*rows*(e-1)
        if shared:
            scalar+=2*l*rows*h;special['sigmoid']+=l*rows
    else:
        scalar+=2*l*rows*config['intermediate_size']
        special['sigmoid']=l*rows*config['intermediate_size']
    if config.get('_layer_scale'):
        scalar+=2*l*rows*h
    # Declared logical interfaces of norms, residuals, RoPE, stable softmax and
    # SwiGLU. Internal dtype casts/reductions are not inferred as HBM transfers.
    nonmatrix_bytes=element_bytes*((2*l+1)*(2*rows*h+invocations*h)+6*l*rows*h
                                  +l*(2*rows*(heads+kv)*d+2*rows*d)+2*l*heads*pairs)
    nonmatrix_bytes-=2*(rows-final_norm_rows)*h*element_bytes
    if qk_norm:
        nonmatrix_bytes+=element_bytes*l*(2*rows*(heads+kv)*d+2*d*invocations)
    ffn_cells=l*rows*(k*config['moe_intermediate_size']+config.get('shared_expert_intermediate_size',0)) if e>1 else l*rows*config['intermediate_size']
    nonmatrix_bytes+=element_bytes*5*ffn_cells
    if config.get('_layer_scale'):
        nonmatrix_bytes+=element_bytes*(4*l*rows*h+2*l*h*invocations)
    summary.update(invocations=invocations,accounted_scalar_flops=scalar,special_ops=special,
                   matrix_weight_interface_bytes=sum(r['weight_interface_bytes'] for r in matrices),
                   matrix_activation_read_bytes=sum(r['activation_read_bytes'] for r in matrices),
                   matrix_activation_write_bytes=sum(r['activation_write_bytes'] for r in matrices),
                   attention_logical_interface_bytes=attention_bytes,
                   accounted_nonmatrix_interface_bytes=nonmatrix_bytes)
    summary['accounted_interface_bytes']=sum(summary[key] for key in ('matrix_weight_interface_bytes','matrix_activation_read_bytes','matrix_activation_write_bytes','attention_logical_interface_bytes','accounted_nonmatrix_interface_bytes'))
    stage['state_lifecycle']=dict(scope='one acoustic frame' if 'reset_each_frame' in stage['name'] else 'request',
                                  retained_bytes=summary['kv_retained_logical_bytes'],
                                  release='after each frame' if 'reset_each_frame' in stage['name'] else 'after stage/request',
                                  bytes_scope='logical KV only; weights, eager temporaries, output tokens and allocator not included')
    stage['interface_assumptions']=['Each selected matrix weight read once per invocation, conditional balanced MoE visits min(E,B*top_k); no cross-call caching assumed.', 'Attention KV interfaces reuse each KV head across GQA query heads but conservatively account each valid query/history pair; these are not measured HBM bytes.', 'Norm/residual/RoPE/softmax/SwiGLU interfaces use declared mathematical primitives; remaining router gather/scatter, sampling, dtype conversion and allocator traffic remain unaccounted.']
    return stage


def execution_ledger(model,c,stages,bridges,frames,batch,text_tokens,text_history,
                     audio_history,element_bytes,matrix_rate,interface_rate,scalar_rate,fish_prompt_tokens=0):
    """Unfold sequential frame/codebook dependencies, with conditional lower bounds.

    Existing inputs describe a continuation, not an unaccounted prompt's cost.
    A single source codec chunk is covered; larger chunks are rejected rather
    than silently skipping the reference's repeated left context.
    """
    rates={}
    for key,value in [('matrix',matrix_rate),('interface',interface_rate),('scalar',scalar_rate)]:
        if value is None:
            rates[key]=None
        else:
            if isinstance(value,bool):
                raise ValueError('Effective rates must be positive numbers')
            try:
                rate=Fraction(str(value))
            except (ValueError,ZeroDivisionError) as error:
                raise ValueError('Effective rates must be finite positive numbers') from error
            if rate<=0:
                raise ValueError('Effective rates must be positive')
            rates[key]=rate
    omni=model.startswith('qwen3-omni')
    if omni and frames>300:
        raise ValueError('This execution ledger covers one reference codec chunk (at most 300 frames); overlap needs its own total')
    configs=([c['thinker_config']['text_config'],c['talker_config']['text_config'],
              c['talker_config']['code_predictor_config'],c['code2wav_config']] if omni else
             [fish_config(c['text_config']),fish_config(c['audio_decoder_config'])])
    if omni:
        configs[-1]={**configs[-1], 'attention_qk_norm':False, '_layer_scale':True}
    groups=c['talker_config']['num_code_groups'] if omni else c['audio_decoder_config']['num_codebooks']
    if not omni:
        configs[0]['_final_norm_rows']=batch*frames
    invocation_counts=[text_tokens,frames,frames*(groups-1),1] if omni else [frames,frames*groups]
    for stage,config,invocations in zip(stages,configs,invocation_counts):
        stage_execution(stage,invocations,batch,element_bytes,config)
    nodes=[]
    def add(name,kind,matrix,interface,scalar,**extra):
        bounds=[]
        for work,key in [(matrix,'matrix'),(interface,'interface'),(scalar,'scalar')]:
            if rates[key] is not None:
                bounds.append(Fraction(work)/rates[key])
        lower=max(bounds) if bounds else None
        nodes.append(dict(id=name,kind=kind,depends_on=[nodes[-1]['id']] if nodes else [],
                          matrix_flops=matrix,accounted_interface_bytes=interface,accounted_scalar_flops=scalar,
                          conditional_service_lower_bound_seconds_exact=str(lower) if lower is not None else None,
                          **extra))
    def add_transformer(name,config,rows,pairs,retained,calls,head_rows,**extra):
        # Per-call output head selected once; parameter replicas irrelevant to execution.
        if not omni and name.endswith('_primary'):
            config={**config,'_final_norm_rows':head_rows}
        st=transformer(name,config,rows,pairs,retained,batch,element_bytes,head_rows)
        stage_execution(st,calls,batch,element_bytes,config)
        z=st['summary']
        add(name,'transformer',z['matrix_flops'],z['accounted_interface_bytes'],z['accounted_scalar_flops'],
            processed_rows=rows,valid_attention_pairs=pairs,kv_live_after_bytes=z['kv_retained_logical_bytes'],
            invocation_count=calls,**extra)
    if omni:
        for position in range(text_tokens):
            add_transformer(f'thinker_t{position}',configs[0],batch,batch*(text_history+position+1),
                            text_history+position+1,1,batch,loop_axis='text token')
        tc=c['talker_config'];h=tc['thinker_hidden_size'];f=configs[1]['intermediate_size'];out=configs[1]['hidden_size']
        m=batch*text_tokens
        for label in ['text_projection','hidden_projection']:
            # Two independent biased Linear calls; their intermediate has both a write and a read.
            size=element_bytes*(h*f+f*out+f+out+m*(h+4*f+out))
            add(label,'resize_mlp',bridges[label+'_matrix_flops'],size,m*(f+out),
                special_ops={'silu':m*f},projected_rows=m)
        temporal,inner=configs[1:3]
    else:
        temporal,inner=configs
    for frame in range(frames):
        positions=fish_prompt_tokens if not omni and frame==0 and fish_prompt_tokens else 1
        before=audio_history+frame+(max(fish_prompt_tokens-1,0) if not omni and frame>0 else 0)
        if not omni:
            m=batch*positions; h=temporal['hidden_size']; g=groups; prefix=f'frame_{frame}_slow_input'
            add(prefix+'_lookup','embedding',0,m*(g+1)*(h*element_bytes*2+8),0,
                special_ops={'integer_offset_add':m*g},input_positions=positions,
                note='All ten codebook lookups execute even for masked text-only prompt positions; plus the text/semantic token embedding.')
            add(prefix+'_stack_reduce','reduction',0,element_bytes*m*h*(3*g+1),m*h*(g-1))
            text_only=bool(frame==0 and fish_prompt_tokens)
            add(prefix+'_mask','index',0,(m*h*element_bytes if text_only else 0),0,
                special_ops={'integer_compare':2*m,'boolean_not':m},text_only_prompt=text_only)
            add(prefix+'_merge_scale','elementwise',0,element_bytes*m*h*8,2*m*h,
                note='Embedding merge, division by sqrt(11), and where; division is evaluated even on text-only positions.')
        add_transformer(f'frame_{frame}_primary',temporal,batch*positions,
                        batch*(positions*before+positions*(positions+1)//2),
                        before+positions,1,batch,loop_axis='acoustic frame',frame=frame,
                        prompt_prefill=bool(not omni and frame==0 and fish_prompt_tokens))
        # Whole code-predictor generation is reset. The first Omni call consumes two positions.
        for code in range(groups-1 if omni else groups):
            row_count=2 if omni and code==0 else 1
            retained=code+2 if omni else code+1
            pair_count=3 if omni and code==0 else retained
            add_transformer(f'frame_{frame}_code_{code}',inner,batch*row_count,batch*pair_count,
                            retained,1,batch*row_count,loop_axis='codebook within frame',frame=frame,
                            cache_reset=code==0,cache_release_after=code==(groups-2 if omni else groups-1),
                            output_discarded=(not omni and code==0))
            if not omni:
                add(f'frame_{frame}_fast_embedding_{code}','embedding',0,
                    batch*(8+2*inner['hidden_size']*element_bytes),0,
                    output_unused=code==groups-1,
                    note='Source performs the next-code embedding even after the final residual sample.')
    codec=None
    if omni:
        wav=configs[-1]
        # Embedding mean logically precedes codec pre-transformer; remaining codec ops follow it.
        codec=omni_codec_operators(frames,batch,wav,element_bytes)
        for first in codec['operators'][:2]:
            add('codec_'+first['name'],'codec_embedding',first['matrix_flops'],
                first['weight_interface_bytes']+first['activation_read_bytes']+first['activation_write_bytes'],first['scalar_flops'])
        add_transformer('codec_pre_transformer',wav,batch*frames,
                        batch*sum(min(i,wav['sliding_window']) for i in range(1,frames+1)),0,1,0,
                        loop_axis='one codec chunk',cross_call_kv=False)
        for op in codec['operators'][2:]:
            add('codec_'+op['name'],op['kind'],op['matrix_flops'],
                op['weight_interface_bytes']+op['activation_read_bytes']+op['activation_write_bytes'],op['scalar_flops'],
                special_ops=op['special_ops'])
        samples=codec['output_samples_per_request']*batch
        add('return_float32_wave','cast',0,samples*(element_bytes+4),0,special_ops={'cast_elements':samples})
        duration=Fraction(codec['output_samples_per_request'],24000)
    else:
        fc=fish_codec_config()
        codec=omni_codec_operators(frames,batch,fc,element_bytes,codec_kind='fish')
        for row in codec['operators']:
            add('codec_'+row['name'],row['kind'],row['matrix_flops'],
                row['weight_interface_bytes']+row['activation_read_bytes']+row['activation_write_bytes'],
                row['scalar_flops'],special_ops=row['special_ops'])
        duration=Fraction(codec['output_samples_per_request'],fc['sample_rate'])
        codec['source_notes']=['Only RVQ post_module executes in decode. Encoder/pre_module and nearest-neighbor search do not execute.',
                               'DecoderBlock constructs the configured transformer but omits it from self.block; do not charge the YAML [4,0,0,0] transformer layers.',
                               'Weight normalization remains attached in the locked inference loader. Descript dependency is pinned here for accounting; Fish pyproject leaves its version unpinned.']
        codec['persistent_decode_module_buffers']=dict(post_module_causal_mask_bool_bytes=32768**2,
               post_module_rope_bf16_bytes=327680*fc['post_transformer']['head_dim']*2,
               logical_cross_call_kv_bytes=0,
               note='Source constructor buffers, not an allocator peak. Full instantiated codec also includes unused encoder/pre-module buffers; not summed here.')
    totals={key:sum(n[key] for n in nodes) for key in ('matrix_flops','accounted_interface_bytes','accounted_scalar_flops')}
    lower=sum((Fraction(n['conditional_service_lower_bound_seconds_exact']) for n in nodes),Fraction()) if any(v is not None for v in rates.values()) else None
    return dict(audio_execution_dag=dict(nodes=nodes,loop_counts=dict(text_tokens=text_tokens if omni else None,
                              acoustic_frames=frames,inner_calls_per_frame=groups-1 if omni else groups),
                              scheduling='Unfolded single-request source-order chain; independent requests may share a service pool.',
                              first_external_audio='Pinned Omni wrapper returns after all codec work; Fish external transport not covered.',
                              ignored_dependencies='Prompt/control preparation, sampling and device transport still add real dependencies.'),
                audio_codec_operations=codec,
                audio_supply=dict(effective_rates={key:str(value) if value is not None else None for key,value in rates.items()},
                                  accounted_work_totals=totals,
                                  accounted_serial_critical_path_lower_bound_seconds_exact=str(lower) if lower is not None else None,
                                  full_request_latency_seconds=None,first_audio_latency_seconds=None,
                                  prompt_scope='Fish optional already-tokenized text-only prompt included; text/audio tokenizer and reference-audio encoder excluded.',
                                  duration_basis_seconds_exact=str(duration),
                                  required_matrix_flops_per_second_exact=str(Fraction(totals['matrix_flops'],1)/duration),
                                  required_accounted_interface_bytes_per_second_exact=str(Fraction(totals['accounted_interface_bytes'],1)/duration),
                                  required_accounted_scalar_flops_per_second_exact=str(Fraction(totals['accounted_scalar_flops'],1)/duration),
                                  interpretation='Necessary average aggregate supply to emit this batch within one request audio duration; not sufficient for latency. Node max(F/P,bytes/BW,scalar/S) uses only supplied rates and declared interfaces, permits within-node overlap, and excludes special-op/launch costs. Sum follows strict node dependencies.'),
                audio_state_lifetimes=[dict(stage=st['name'],**st['state_lifecycle']) for st in stages])


def fish_codec_config():
    """Read the small fixed YAML scalar/list fields without a YAML dependency.

    Reject conflicting duplicate keys rather than interpreting a generic YAML
    document. Configuration/source digests are verified by evidence().
    """
    raw=(PROJECT/RESEARCH/'fish/fish_speech/configs/modded_dac_vq.yaml').read_text()
    def value(key):
        matches=re.findall(r'^\s*'+re.escape(key)+r':\s*([^#\n]+)',raw,re.M)
        values=[ast.literal_eval(x.strip()) for x in matches]
        if not values or any(x!=values[0] for x in values):
            raise ValueError(f'Unsupported missing/ambiguous Fish codec YAML field {key}')
        return values[0]
    h=value('input_dim');heads=value('n_head')
    return dict(hidden_size=h,codebook_dim=value('codebook_dim'),
                codebook_size=value('codebook_size'),semantic_codebook_size=value('semantic_codebook_size'),
                num_quantizers=1+value('n_codebooks'),decoder_dim=value('decoder_dim'),
                upsample_rates=value('decoder_rates'),upsampling_ratios=list(reversed(value('downsample_factor'))),
                sample_rate=value('sample_rate'),encoder_rates=value('encoder_rates'),
                post_transformer=dict(hidden_size=h,num_hidden_layers=value('n_layer'),
                                      num_attention_heads=heads,num_key_value_heads=heads,head_dim=value('head_dim'),
                                      intermediate_size=value('intermediate_size'),attention_qk_norm=False,
                                      _layer_scale=True),
                ignored_decoder_transformer_layers=value('decoder_transformer_layers'))
