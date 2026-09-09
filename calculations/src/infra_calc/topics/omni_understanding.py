"""Omni understanding request: encoders, placeholder fill, Thinker, G-1 decode.

One request with caller-tokenized text/control positions and processed media.
Encoder cache hits never imply reuse of the language model's prefix KV.
"""
import json

from ..sources import model_config, provenance, read_source
from ..units import positive_int
from . import omni_audio, omni_audio_encoder, omni_vision_encoding

MODEL='qwen3-omni-30b-a3b-instruct'


def _hits(items,hits):
    result=[False]*len(items) if hits is None else hits
    if not isinstance(result,list) or len(result)!=len(items) or any(not isinstance(x,bool) for x in result):
        raise ValueError('Each cache hit array must contain one boolean per media item')
    return result


def language_stage(config,tokens,history,width,routing):
    pairs=tokens*history+tokens*(tokens+1)//2
    stage=omni_audio.transformer('thinker',config,tokens,pairs,history+tokens,1,width,tokens)
    # One prefill call, or one decode call. Balanced selects a union up to E;
    # concentrated repeatedly uses the same k experts. Neither is a real trace.
    omni_audio.stage_execution(stage,1,tokens if routing=='balanced' else 1,width,config)
    e,k=config['num_experts'],config['num_experts_per_tok']
    q,r=divmod(tokens*k,e)
    histogram=[q+(i<r) for i in range(e)] if routing=='balanced' else [tokens if i<k else 0 for i in range(e)]
    stage['routing']=dict(policy=routing,assignments_per_layer=tokens*k,expert_union_per_layer=sum(x>0 for x in histogram),
                          tokens_per_expert_per_layer=histogram,layer_policy='Same teaching histogram at every MoE layer')
    stage['summary']['kv_new_write_bytes']=tokens*stage['summary']['kv_bytes_per_position_per_request']
    return stage


def calculate(text_tokens=128,output_tokens=32,image_grids=None,video_grids=None,mel_lengths=None,
              image_cache_hits=None,video_cache_hits=None,audio_cache_hits=None,dtype='bf16',routing='balanced'):
    positive_int(text_tokens,'text_tokens',allow_zero=True);positive_int(output_tokens,'output_tokens')
    if dtype not in omni_vision_encoding.DTYPE_BYTES:raise ValueError('dtype must be bf16 or fp32')
    if routing not in ('balanced','concentrated'):raise ValueError('Unknown expert routing policy')
    images=[[1,40,40]] if image_grids is None else image_grids
    videos=[] if video_grids is None else video_grids
    audios=[1000] if mel_lengths is None else mel_lengths
    for label,items in [('images',images),('videos',videos),('audios',audios)]:
        if not isinstance(items,list):raise ValueError(label+' must be a list')
    if any(not isinstance(g,list) or len(g)!=3 or g[0]!=1 for g in images):
        raise ValueError('Static image grids must have temporal dimension 1')
    ih,vh,ah=_hits(images,image_cache_hits),_hits(videos,video_cache_hits),_hits(audios,audio_cache_hits)
    width=omni_vision_encoding.DTYPE_BYTES[dtype]
    image_result=omni_vision_encoding.calculate(images,ih,dtype) if images else None
    video_result=omni_vision_encoding.calculate(videos,vh,dtype) if videos else None
    audio_positions=[omni_audio_encoder.encoded_length(n) for n in audios]
    for n in audios:positive_int(n,'mel length')
    # Validate all media even when a hit skips execution.
    max_frames=json.loads(read_source(f'sources/{MODEL}/preprocessor_config.json'))['nb_max_frames']
    if any(n>max_frames for n in audios):raise ValueError('Audio exceeds pinned processor frame limit')
    audio_misses=[n for n,hit in zip(audios,ah) if not hit]
    audio_result=omni_audio_encoder.calculate(audio_misses,width) if audio_misses else None
    ip=image_result['summary']['delivered_visual_positions'] if image_result else 0
    vp=video_result['summary']['delivered_visual_positions'] if video_result else 0
    ap=sum(audio_positions);prompt=text_tokens+ip+vp+ap
    if not prompt:raise ValueError('Request requires at least one prompt position')
    c=model_config(MODEL)['thinker_config']['text_config'];h=c['hidden_size'];l=c['num_hidden_layers']
    if prompt+output_tokens-1>c['max_position_embeddings']:raise ValueError('Consumed positions exceed Thinker context limit')
    if c['shared_expert_intermediate_size'] or c['attention_bias'] or c['mlp_only_layers']:
        raise ValueError('Unsupported Thinker mixture or projection structure')
    prefill=language_stage(c,prompt,0,width,routing)
    decode=[language_stage(c,1,prompt+i,width,routing) for i in range(output_tokens-1)]
    # Sources deduplicated by actual locked file; no encoder run is required to
    # prove a cache payload geometry, but config/implementation remains cited.
    source_rows=provenance(MODEL)+[r for r in omni_audio.evidence() if '/transformers/' in r['file']]
    for result in (image_result,video_result,audio_result):
        if result:source_rows+=result['sources']
    sources=list({r['file']:r for r in source_rows}.values())
    nodes=[]
    def node(name,matrix=0,scalar=0,interface=0,**extra):
        nodes.append(dict(id=name,depends_on=[nodes[-1]['id']] if nodes else [],matrix_flops=matrix,
                          accounted_scalar_flops=scalar,accounted_interface_bytes=interface,**extra))
    node('prompt_embedding_lookup',interface=prompt*(8+2*h*width),
         positions=prompt,note='Lookup includes media placeholders, later replaced. No language prefix cache is assumed.')
    for label,result,count,hits,position_counts in [
        ('audio',audio_result,ap,ah,audio_positions),
        ('image',image_result,ip,ih,[r['merged_positions'] for r in image_result['omni_vision_items']] if image_result else []),
        ('video',video_result,vp,vh,[r['merged_positions'] for r in video_result['omni_vision_items']] if video_result else [])]:
        if result:
            z=result['summary']
            if label=='audio':
                interface=sum(z[k] for k in ('weight_interface_bytes','activation_read_bytes','activation_write_bytes'))
            else:interface=z['interface_read_bytes']+z['interface_write_bytes']
            node(label+'_encoder',z['matrix_flops'],z['scalar_flops'],interface)
        hit_positions=sum(n for n,hit in zip(position_counts,hits) if hit)
        if hit_positions:
            node(label+'_feature_cache_read',interface=hit_positions*h*width*(1 if label=='audio' else 4),
                 note='Declared cached-feature payload read; storage/network implementation and latency are unknown.')
        if count:
            node(label+'_placeholder_replace',interface=(2*prompt+count)*h*width+prompt,
                 feature_positions=count,note='Source out-of-place masked_scatter reads old prompt plus features and writes the whole prompt; position-bool mask shared across hidden columns.')
    visual=ip+vp
    if ip and vp:
        node('joint_deepstack_pack',interface=3*visual*h*width*3+3*prompt,
             note='Three zero-initialized joint feature arrays filled from image/video branches; mask/index implementation not fully modeled.')
    # DeepStack additions occur within first three Thinker layers; their scalar
    # work and interfaces are separate to avoid modifying the shared MoE ledger.
    deepstack=dict(branches=3 if visual else 0,visual_positions=visual,
                   consumer_layers=[0,1,2] if visual else [],additions=3*visual*h,
                   gather_clone_add_scatter_interface_bytes=9*3*visual*h*width,
                   injected_only_during_prefill=True)
    def language_node(name,stage,first=False):
        z=stage['summary']
        node(name,z['matrix_flops'],z['accounted_scalar_flops']+(deepstack['additions'] if first else 0),
             z['accounted_interface_bytes']+z['kv_new_write_bytes']+
             (deepstack['gather_clone_add_scatter_interface_bytes'] if first else width*h*2+8),
             kv_after_bytes=z['kv_retained_logical_bytes'],
             produces_output_token=1 if first else int(name.rsplit('_',1)[1])+2,
             output_head_rows=prompt if first else 1,
             note='Pinned Thinker source projects all incoming hidden rows; prefill head work is not reduced to last position.')
    language_node('thinker_prefill',prefill,True)
    for index,stage in enumerate(decode):language_node(f'thinker_decode_{index}',stage)
    unit=prefill['summary']['kv_bytes_per_position_per_request']
    heads,kv,d,e,f=(c[k] for k in ('num_attention_heads','num_key_value_heads','head_dim','num_experts','moe_intermediate_size'))
    parameters=2*c['vocab_size']*h+h+l*(h*(2*heads+2*kv)*d+2*d+2*h+h*e+3*h*f*e)
    totals={key:sum(n[key] for n in nodes) for key in ('matrix_flops','accounted_scalar_flops','accounted_interface_bytes')}
    return dict(schema_version=1,calculation='omni-understanding-request',model=MODEL,
                scenario=dict(text_tokens=text_tokens,output_tokens=output_tokens,image_grids=images,video_grids=videos,
                              mel_lengths=audios,image_cache_hits=ih,video_cache_hits=vh,audio_cache_hits=ah,dtype=dtype,routing=routing),
                sources=sources,encoders=dict(image=image_result,video=video_result,audio=audio_result),
                thinker_prefill=prefill,thinker_decode=decode,request_execution_nodes=nodes,deepstack_injection=deepstack,
                audio_cache_contract=dict(
                    miss_item_indices=[i for i,hit in enumerate(ah) if not hit],
                    actual_miss_chunk_execution=audio_result['chunk_execution'] if audio_result else None,
                    actual_miss_segments=audio_result['audio_encoder_segments'] if audio_result else [],
                    segment_audio_index_scope='Indices address the compact miss batch, mapped by miss_item_indices.',
                    required_cache_identity=['model/source revision','processed mel content','dtype','attention execution path',
                                             'batch padded CNN width and resulting segmentation window'],
                    validity='Caller asserts cache identity matches the intended encoder execution. Equal embedding counts do not prove equal features. Removing hits may change the padded width/attention segmentation of short miss items; this ledger reports their actual miss batch, not equivalence to an uncached full batch.'),
                position_budget=dict(text_and_controls=text_tokens,image=ip,video=vp,audio=ap,total=prompt,
                                     audio_embeddings_per_item=audio_positions,
                                     placement='Counts of caller-packed positions; modality ordering/mRoPE values are not invented from counts.'),
                summary={**totals,'prompt_positions':prompt,'output_tokens':output_tokens,'decode_calls':output_tokens-1,
                         'consumed_positions':prompt+output_tokens-1,'kv_bytes_per_position':unit,
                         'kv_after_prefill_bytes':prompt*unit,'kv_after_last_forward_bytes':(prompt+output_tokens-1)*unit,
                         'logical_thinker_parameters':parameters,'uniform_thinker_parameter_bytes':parameters*width,
                         'delivered_feature_bytes':((ip+vp)*4+ap)*h*width,
                         'first_output_latency_seconds':None,'request_latency_seconds':None,'complete_runtime_peak_bytes':None},
                assumptions=[
                    'One understanding request generating text, not Talker/codec audio output. text_tokens includes all caller-tokenized control/delimiter/template positions; processed patch grids and valid mel lengths are explicit. No tokenizer, raw media preparation or language prefix-cache hit is inferred.',
                    'Audio, image and video features replace existing placeholders; they are not appended a second time. Image and video encoder calls stay separate as in the pinned wrapper. Encoder feature-cache hits remove their encoder work, never their placeholder positions or Thinker prefill.',
                    'Thinker uses its actual 48-layer GQA/top-8 of128 MoE structure; no 6ND or advertised active-parameter scaling. Balanced/concentrated expert histograms are declared conditional inputs at every layer. Matrix work is sum of selected expert rows; resident capacity includes all experts.',
                    'Source lm_head processes all prompt rows. Prefill produces output token one; exactly G-1 one-token forwards produce the rest. Last returned token is not consumed, so final KV has P+G-1 positions.',
                    'DeepStack image/video features are combined when both exist and injected after Thinker layers0/1/2 during prefill only. Add/gather/clone/scatter counted once here, not in both encoder and language totals.',
                    'The dependency chain follows the declared serial source path; kernel concurrency, modality parallel serving and cache transport schedules require separate measured/input evidence. Totals are accounted matrices/scalars/interfaces; special primitives, router dispatch internals, sampling, mRoPE index construction and complete runtime allocation remain gaps.',
                    'Thinker attention matrices count valid causal query/key pairs. Dense masked eager kernels may perform additional masked products; no physical kernel work is asserted. Input-audio execution uses the declared segmented varlen path and its source-specific boundaries.',
                    'Logical Thinker parameter count is config/source derived, not checkpoint-header verified. Uniform operands/KV dtype is a comparison convention; no timing is fabricated from peak compute or this interface sum.',
                ])
