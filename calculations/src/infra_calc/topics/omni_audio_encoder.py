"""Qwen3-Omni input audio encoder: mel chunks to Thinker embeddings.

The declared default is the non-causal segmented varlen attention graph.
The pinned HF call does not pass its prepared block mask to encoder layers;
its unmasked eager alternative is separately identified, not called equivalent.
"""
from fractions import Fraction
from math import prod

from ..sources import model_config, provenance, read_source
from ..units import positive_int
from .omni_audio import evidence

MODEL='qwen3-omni-30b-a3b-instruct'


def encoded_length(mel_frames):
    positive_int(mel_frames,'mel_frames',allow_zero=True)
    full,tail=divmod(mel_frames,100)
    return 13*full+(tail+7)//8


def calculate(mel_lengths=None, element_bytes=2, attention_path='segmented_varlen'):
    lengths=[1000] if mel_lengths is None else mel_lengths
    if not isinstance(lengths,list) or not lengths:
        raise ValueError('mel_lengths must be a nonempty integer list')
    for length in lengths:
        positive_int(length,'mel length')
    positive_int(element_bytes,'element_bytes')
    if element_bytes not in (2,4):
        raise ValueError('Uniform operand format must use 2 or 4 bytes')
    if attention_path not in ('segmented_varlen','source_unmasked_eager'):
        raise ValueError('Unknown attention execution path')
    config=model_config(MODEL);c=config['thinker_config']['audio_config']
    if c['n_window']*2!=100 or c['scale_embedding'] or c['activation_function']!='gelu':
        raise ValueError('Unsupported source chunk or activation convention')
    # Shared research lock validates the fixed source before any implementation-derived geometry.
    source_rows=[r for r in evidence() if '/transformers/' in r['file']]
    sources=provenance(MODEL)+source_rows
    import json
    pre=json.loads(read_source(f'sources/{MODEL}/preprocessor_config.json'))
    if any(x>pre['nb_max_frames'] for x in lengths):
        raise ValueError('Mel sequence exceeds fixed processor frame limit')
    chunks=[]
    for audio,length in enumerate(lengths):
        for start in range(0,length,100):
            n=min(100,length-start)
            chunks.append(dict(audio=audio,start_frame=start,valid_frames=n,valid_embeddings=encoded_length(n)))
    count=len(chunks); padded=max(r['valid_frames'] for r in chunks)
    width=encoded_length(padded); outputs=[encoded_length(x) for x in lengths]
    max_window=width*(c['n_window_infer']//100)
    segments=[]
    for audio,total in enumerate(outputs):
        for start in range(0,total,max_window):
            segments.append(dict(audio=audio,start_embedding=start,length=min(max_window,total-start)))
    useful_pairs=sum(r['length']**2 for r in segments); tokens=sum(outputs)
    pairs=useful_pairs if attention_path=='segmented_varlen' else tokens*tokens
    ops=[]
    def add(name,kind,shape,matrix=0,scalar=0,special=None,weights=0,read=0,write=0,repeats=1,**extra):
        ops.append(dict(name=name,kind=kind,shape=shape,repeats=repeats,matrix_flops=matrix,
                        scalar_flops=scalar,special_ops=special or {},parameter_elements=weights,
                        weight_interface_bytes=weights*element_bytes,
                        activation_read_bytes=read,activation_write_bytes=write,**extra))
    # Padding is a copy/fill, not a neural multiply.
    add('mel_chunk_pad','copy',dict(input=[c['num_mel_bins'],sum(lengths)],output=[count,1,c['num_mel_bins'],padded]),
        read=sum(lengths)*c['num_mel_bins']*element_bytes,
        write=count*c['num_mel_bins']*padded*element_bytes)
    frequency=c['num_mel_bins'];time=padded;channels=1; groups=(count+c['conv_chunksize']-1)//c['conv_chunksize']
    for index in range(3):
        fout,tout=(frequency+1)//2,(time+1)//2; cout=c['downsample_hidden_size']
        cells=count*cout*fout*tout; weight=cout*channels*9+cout
        add(f'conv2d_{index+1}','conv2d',dict(input=[count,channels,frequency,time],weight=[cout,channels,3,3],output=[count,cout,fout,tout]),
            matrix=2*cells*channels*9,scalar=cells,weights=weight,
            read=count*channels*frequency*time*element_bytes,write=cells*element_bytes,
            kernel_invocations=groups,stride=[2,2],padding=[1,1],
            note='Dense convolution counts padded-zero products; groups limit simultaneous chunk batch, not temporal segment width.')
        ops[-1]['weight_interface_bytes']*=groups
        add(f'conv_gelu_{index+1}','activation',dict(elements=cells),special={'gelu':cells},
            read=cells*element_bytes,write=cells*element_bytes)
        frequency,time,channels=fout,tout,cout
    conv_tensor=count*channels*frequency*time*element_bytes
    add('concat_and_layout','copy',dict(concat=[count,channels,frequency,time],flatten=[count*time,channels*frequency]),
        read=2*conv_tensor,write=2*conv_tensor,
        note='Source concatenates convolution groups then materializes permuted layout; persistent input lists and allocator peaks separate.')
    def linear(name,rows,inputs,outs,repeats=1,bias=True):
        add(name,'linear',dict(input=[rows,inputs],weight=[outs,inputs],output=[rows,outs]),
            matrix=2*rows*inputs*outs,scalar=rows*outs if bias else 0,
            weights=inputs*outs+(outs if bias else 0),read=rows*inputs*element_bytes,
            write=rows*outs*element_bytes,repeats=repeats)
    h=c['d_model'];layers=c['encoder_layers'];heads=c['encoder_attention_heads'];d=h//heads
    linear('conv_out',count*time,channels*frequency,h,bias=False)
    add('chunk_position_add','position',dict(padded=[count,time,h]),scalar=count*time*h,
        read=(count*time*h+time*h)*element_bytes,write=count*time*h*element_bytes,
        note='Position indices restart for each CNN chunk; sinusoid table is a non-trainable buffer.')
    add('remove_padding','gather',dict(input=[count,time,h],output=[tokens,h]),
        read=tokens*h*element_bytes+count*time,write=tokens*h*element_bytes)
    def norm(name,rows,repeats=1):
        add(name,'layernorm',dict(input=[rows,h]),scalar=rows*(7*h+1),special={'rsqrt':rows},weights=2*h,
            read=rows*h*element_bytes,write=rows*h*element_bytes,repeats=repeats)
    norm('attention_norm',tokens,layers)
    for name in ('q','k','v'):
        linear(name,tokens,h,h,layers)
    add('qk','attention',dict(heads=heads,head_dim=d,positions=tokens,accounted_pairs=pairs),
        matrix=2*heads*pairs*d,read=2*tokens*h*element_bytes,write=heads*pairs*element_bytes,repeats=layers)
    add('scale_softmax','attention',dict(heads=heads,pairs=pairs),scalar=heads*(4*pairs-tokens),
        special={'exp':heads*pairs,'max_compare':heads*(pairs-tokens)},
        read=heads*pairs*element_bytes,write=heads*pairs*element_bytes,repeats=layers)
    add('pv','attention',dict(heads=heads,head_dim=d,positions=tokens,accounted_pairs=pairs),
        matrix=2*heads*pairs*d,read=(heads*pairs+tokens*h)*element_bytes,
        write=tokens*h*element_bytes,repeats=layers)
    linear('attention_output',tokens,h,h,layers)
    add('attention_residual','residual',dict(input=[tokens,h]),scalar=tokens*h,
        read=2*tokens*h*element_bytes,write=tokens*h*element_bytes,repeats=layers)
    norm('ffn_norm',tokens,layers)
    linear('ffn_fc1',tokens,h,c['encoder_ffn_dim'],layers)
    add('ffn_gelu','activation',dict(elements=tokens*c['encoder_ffn_dim']),special={'gelu':tokens*c['encoder_ffn_dim']},
        read=tokens*c['encoder_ffn_dim']*element_bytes,write=tokens*c['encoder_ffn_dim']*element_bytes,repeats=layers)
    linear('ffn_fc2',tokens,c['encoder_ffn_dim'],h,layers)
    add('ffn_residual','residual',dict(input=[tokens,h]),scalar=tokens*h,
        read=2*tokens*h*element_bytes,write=tokens*h*element_bytes,repeats=layers)
    norm('post_norm',tokens)
    linear('proj1',tokens,h,h)
    add('projection_gelu','activation',dict(elements=tokens*h),special={'gelu':tokens*h},
        read=tokens*h*element_bytes,write=tokens*h*element_bytes)
    linear('proj2_to_thinker',tokens,h,c['output_dim'])
    totals={key:sum(op[key]*op['repeats'] for op in ops) for key in
            ('matrix_flops','scalar_flops','parameter_elements','weight_interface_bytes','activation_read_bytes','activation_write_bytes')}
    totals.update(output_embeddings_per_audio=outputs,output_embedding_elements=tokens*c['output_dim'],
                  output_embedding_bytes=tokens*c['output_dim']*element_bytes,
                  padded_cnn_positions=count*time,valid_encoder_positions=tokens,
                  segmented_bidirectional_pairs=useful_pairs,source_unmasked_eager_pairs=tokens*tokens,
                  persistent_decode_kv_bytes=0,positional_buffer_elements=c['max_source_positions']*h,
                  complete_runtime_peak_bytes=None,predicted_latency_seconds=None)
    return dict(schema_version=1,calculation='omni-input-audio-encoder',model=MODEL,
                scenario=dict(mel_lengths=lengths,element_bytes=element_bytes,attention_path=attention_path),
                sources=sources,audio_encoder_chunks=chunks,audio_encoder_segments=segments,
                audio_encoder_operators=ops,summary=totals,
                chunk_execution=dict(padded_mel_width=padded,after_cnn_width=time,attention_window_positions=max_window,
                                     convolution_chunk_batch_limit=c['conv_chunksize'],convolution_groups=groups,
                                     retained_cnn_group_outputs_bytes=conv_tensor,
                                     max_single_group_output_bytes=min(count,c['conv_chunksize'])*channels*frequency*time*element_bytes),
                input_time_axis=dict(sample_rate=pre['sampling_rate'],hop_samples=pre['hop_length'],
                                     mel_frame_span_seconds_exact=[str(Fraction(n*pre['hop_length'],pre['sampling_rate'])) for n in lengths],
                                     note='Hop-based span reference only; provided mel lengths already exclude processor padding. STFT edge conventions/raw waveform length are not inferred.'),
                assumptions=[
                    'Input understanding audio encoder only, not Talker/output codec. Inputs are valid precomputed mel frames; resampling/STFT/mel filter/log normalization and raw feature masking are separate.',
                    'Every utterance is split into at most 100-frame CNN chunks, then ALL chunks in this call are padded to the largest valid chunk before batches of at most 500 chunks are convolved. Output length is 13*floor(N/100)+ceil((N%100)/8), not ceil(N/8).',
                    'Non-causal attention segments are built per original audio after padding removal; their maximum is batch-padded CNN width times 8. Thus mixed batches can alter the segmentation window of a short input. No autoregressive KV cache is retained.',
                    'Default segmented_varlen counts full bidirectional squares within cu_seqlens blocks. The locked source calls encoder layers without its prepared block mask; source_unmasked_eager therefore counts one total square and is not semantically equivalent. No backend is executed here.',
                    'All learned encoder weights, convolution/linear biases, LayerNorm scale/bias and projection to Thinker are included as logical parameter elements. Sinusoidal positions are a separate buffer. Checkpoint-header validation and mixed runtime formats are not claimed.',
                    'Matrix FMA=2; bias/LayerNorm/residual/softmax scalar work and GELU/exp/rsqrt primitive counts are separate. Conv products include source padding. Operator bytes are declared interfaces, not measured HBM or allocation peaks.',
                    'BF16-size/FP32-size uniform operands are comparison formats. Source FP16-only clipping is not executed in this declared BF16/FP32 path. Library dispatch, actual dtype conversions, mask construction, kernel padding and preprocessing remain runtime gaps.',
                ])
