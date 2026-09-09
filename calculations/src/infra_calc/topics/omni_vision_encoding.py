"""Omni image/video encoding of a packed miss batch, distinct from VL4.

Inputs are already processed patch grids. Cache hits still deliver final and
DeepStack features; only misses enter this packed encoder call.
"""
import ast
from fractions import Fraction
from math import prod

from ..paths import PROJECT
from ..sources import model_config, provenance
from ..units import positive_int
from .omni_audio import evidence

MODEL='qwen3-omni-30b-a3b-instruct'
DTYPE_BYTES={'bf16':2,'fp32':4}


def configuration():
    source=[r for r in evidence() if '/transformers/' in r['file']]
    config=model_config(MODEL)['thinker_config']['vision_config'].copy()
    path=next(r['file'] for r in source if r['file'].endswith('configuration_qwen3_omni_moe.py'))
    tree=ast.parse((PROJECT/path).read_text())
    cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='Qwen3OmniMoeVisionEncoderConfig')
    init=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='__init__')
    defaults={arg.arg:ast.literal_eval(value) for arg,value in zip(init.args.args[-len(init.args.defaults):],init.args.defaults)}
    config['num_position_embeddings']=config.get('num_position_embeddings',defaults['num_position_embeddings'])
    return config,source,dict(field='num_position_embeddings',value=config['num_position_embeddings'],
                              origin='explicit config' if 'num_position_embeddings' in model_config(MODEL)['thinker_config']['vision_config'] else path+'::Qwen3OmniMoeVisionEncoderConfig.__init__ default')


def calculate(grid_thw=None,cache_hits=None,dtype='bf16',seconds_per_grid=None):
    grids=[[1,40,40]] if grid_thw is None else grid_thw
    if not isinstance(grids,list) or not grids:
        raise ValueError('grid_thw must be a nonempty list of [temporal,height,width] patch grids')
    for grid in grids:
        if not isinstance(grid,list) or len(grid)!=3:
            raise ValueError('Each grid is a three-integer list')
        for value in grid:positive_int(value,'grid dimension')
    hits=[False]*len(grids) if cache_hits is None else cache_hits
    if not isinstance(hits,list) or len(hits)!=len(grids) or any(not isinstance(x,bool) for x in hits):
        raise ValueError('cache_hits must provide one boolean per item')
    if dtype not in DTYPE_BYTES:raise ValueError('dtype must be bf16 or fp32')
    times=[None]*len(grids) if seconds_per_grid is None else seconds_per_grid
    if not isinstance(times,list) or len(times)!=len(grids):raise ValueError('seconds_per_grid must align with items')
    deltas=[]
    for time in times:
        if time is None:deltas.append(None);continue
        if isinstance(time,bool):raise ValueError('Positive rational seconds required')
        try:delta=Fraction(str(time))
        except (ValueError,ZeroDivisionError) as error:raise ValueError('Positive rational seconds required') from error
        if delta<=0:raise ValueError('Positive rational seconds required')
        deltas.append(delta)
    c,source,default=configuration();h=c['hidden_size'];f=c['intermediate_size'];out=c['out_hidden_size']
    depth=c['depth'];heads=c['num_heads'];d=h//heads;s=c['spatial_merge_size'];merge=s*s;b=DTYPE_BYTES[dtype]
    if h%heads or d%4:raise ValueError('Unsupported rotary head dimensions')
    if any(gh%s or gw%s for _,gh,gw in grids):raise ValueError('Spatial patch grid must divide into merge groups')
    active=[g for g,hit in zip(grids,hits) if not hit];p=sum(prod(g) for g in active);m=p//merge
    spatial=sum(gh*gw for _,gh,gw in active);max_hw=max((max(gh,gw) for _,gh,gw in active),default=0)
    rows=[];scalars=[]
    def scalar(name,cells,flops=0,special=None,reads=0,writes=0,repeats=1,read_bytes=None,write_bytes=None):
        scalars.append(dict(name=name,elements=cells,repeats=repeats,scalar_flops=flops*repeats,
                            special_ops={k:v*repeats for k,v in (special or {}).items()},
                            interface_read_bytes=(reads*b if read_bytes is None else read_bytes)*repeats,
                            interface_write_bytes=(writes*b if write_bytes is None else write_bytes)*repeats))
    def gemm(name,n,k,o,repeats=1,bias=True,learned=True):
        rows.append(dict(name=name,input_shape=[n,k],weight_shape=[k,o],output_shape=[n,o],repeats=repeats,
                         matrix_flops=2*n*k*o*repeats,
                         learned_parameters=(k*o+(o if bias else 0))*repeats if learned else 0,
                         interface_read_bytes=((n*k+(k*o if learned or n else 0))*b*repeats if n else 0),
                         interface_write_bytes=n*o*b*repeats))
        if bias:scalar(name+'_bias',n*o,n*o,reads=n*o+(o if n else 0),writes=n*o,repeats=repeats)
    def norm(name,n,width,repeats=1):
        scalar(name,n*width,n*(7*width+1),{'rsqrt':n},n*width+(2*width if n else 0),n*width,repeats)
    patch_inner=c['in_channels']*c['temporal_patch_size']*c['patch_size']**2
    gemm('patch_embedding',p,patch_inner,h)
    # Official Omni weight_tensor follows embedding dtype, unlike the VL4 reference.
    scalar('position_interpolate',spatial*h,7*spatial*h,reads=4*spatial*h+4*spatial,writes=spatial*h)
    scalar('position_temporal_repeat_layout',p*h,reads=p*h,writes=p*h)
    scalar('position_add',p*h,p*h,reads=2*p*h,writes=p*h)
    scalar('rope_frequency_outer',max_hw*d//4,max_hw*d//4,
           read_bytes=(max_hw+d//4)*4 if p else 0,write_bytes=max_hw*d//4*4)
    scalar('rope_gather_duplicate_trig',p*d,special={'cos':p*d,'sin':p*d},
           read_bytes=p*2*8+p*d//2*4,write_bytes=2*p*d*4)
    norm('block_norm1',p,h,depth)
    gemm('block_qkv',p,h,3*h,depth)
    scalar('block_rope_qk',2*p*h,6*p*h,{'sign_negation':p*h},
           read_bytes=(4*p*h+2*p*d)*4,write_bytes=2*p*h*4,repeats=depth)
    attention_pairs=0
    for index,((t,gh,gw),hit) in enumerate(zip(grids,hits)):
        if hit:continue
        n=gh*gw;repeat=t*heads*depth;attention_pairs+=t*n*n
        gemm(f'item_{index}_qk',n,d,n,repeat,False,False)
        scalar(f'item_{index}_scale_softmax',n*n,4*n*n-n,{'exp':n*n,'max_compare':n*(n-1)},n*n,n*n,repeat)
        gemm(f'item_{index}_pv',n,n,d,repeat,False,False)
    gemm('block_attention_output',p,h,h,depth)
    scalar('block_residual1',p*h,p*h,reads=2*p*h,writes=p*h,repeats=depth)
    norm('block_norm2',p,h,depth)
    gemm('block_mlp_up',p,h,f,depth)
    scalar('block_gelu_tanh',p*f,8*p*f,{'tanh':p*f},p*f,p*f,depth)
    gemm('block_mlp_down',p,f,h,depth)
    scalar('block_residual2',p*h,p*h,reads=2*p*h,writes=p*h,repeats=depth)
    for branch in ['final']+['deepstack_'+str(i) for i in c['deepstack_visual_indexes']]:
        norm(branch+'_norm',p if branch=='final' else m,h if branch=='final' else merge*h)
        gemm(branch+'_up',m,merge*h,merge*h)
        scalar(branch+'_gelu_erf',m*merge*h,4*m*merge*h,{'erf':m*merge*h},m*merge*h,m*merge*h)
        gemm(branch+'_out',m,merge*h,out)
    all_positions=sum(prod(g)//merge for g in grids);components=1+len(c['deepstack_visual_indexes'])
    items=[];time_scale=model_config(MODEL)['thinker_config']['position_id_per_seconds']
    for index,(grid,hit,delta) in enumerate(zip(grids,hits,deltas)):
        t,gh,gw=grid;positions=prod(grid)//merge
        items.append(dict(index=index,grid_thw=grid,cache_hit=hit,premerge_patches=prod(grid),
                          merged_positions=positions,attention_pairs_executed=0 if hit else t*(gh*gw)**2,
                          feature_components=components,feature_bytes=components*positions*out*b,
                          temporal_position_ids=None if delta is None else [int(i*delta*time_scale) for i in range(t)],
                          temporal_position_note='Thinker time scale times explicit seconds; does not change vision attention or patch count.'))
    learned=sum(r['learned_parameters'] for r in rows)+c['num_position_embeddings']*h+4*h*depth+2*h+len(c['deepstack_visual_indexes'])*2*merge*h
    total_matrix=sum(r['matrix_flops'] for r in rows);total_scalar=sum(r['scalar_flops'] for r in scalars)
    return dict(schema_version=1,calculation='omni-vision-encoding',model=MODEL,
                scenario=dict(grid_thw=grids,cache_hits=hits,dtype=dtype,seconds_per_grid=times),
                sources=provenance(MODEL)+source,omni_vision_items=items,omni_vision_matrices=rows,
                omni_vision_scalars=scalars,official_default=default,
                summary=dict(encoder_items_executed=len(active),encoder_cache_hits=sum(hits),
                             executed_patches=p,executed_merged_positions=m,delivered_visual_positions=all_positions,
                             executed_bidirectional_pairs=attention_pairs,matrix_flops=total_matrix,scalar_flops=total_scalar,
                             logical_vision_parameters=learned,parameter_bytes_declared_dtype=learned*b,
                             complete_encoder_feature_bytes=components*all_positions*out*b,
                             feature_components=components,component_width=out,
                             interface_read_bytes=sum(r['interface_read_bytes'] for r in rows+scalars),
                             interface_write_bytes=sum(r['interface_write_bytes'] for r in rows+scalars),
                             persistent_decode_kv_bytes=0,complete_runtime_peak_bytes=None,predicted_latency_seconds=None),
                deepstack_delivery=dict(visual_encoder_layers=c['deepstack_visual_indexes'],thinker_destination_layers=[0,1,2],
                                        injected_feature_bytes=3*all_positions*out*b,
                                        injection_adds=3*all_positions*out,
                                        injection_gather_clone_add_scatter_interface_bytes=3*all_positions*out*b*9,
                                        note='Separate consumer-side source gather→clone→add→scatter: 9 operand transfers per element; excluded from encoder totals. Final features fill the original visual positions; DeepStack does not multiply their count.'),
                assumptions=[
                    'Already processed patch grids only. Static image temporal duplication is in the 1536-element patch contraction; no raw image decode/resize/normalization or frame sampling is counted.',
                    'Miss items form one packed encoder call: projections consume total patches and share one weight read per matrix/layer; attention remains independent for each temporal spatial block. Cache-hit items skip encoding but still deliver all four feature components and participate in Thinker injection.',
                    '27 layers, width1152, FFN4304, 16 heads of72, final and three DeepStack mergers of width4608 to2048 follow official Omni config. Position table2304 follows the locked config class default, not VL4 substitution.',
                    'Spatial learned positions are interpolated once per spatial grid then repeated over time. Interpolation weights/sums use embedding dtype in this source; rotary table and Q/K rotary arithmetic use FP32 interfaces. They must not be copied from the VL4 FP32 interpolation byte convention.',
                    'FA2 cu_seqlens and the explicit non-FA2 split both prohibit attention across temporal blocks/items. Total pairs=sum(T*(Hgrid*Wgrid)^2), never the square of total packed tokens.',
                    'Scalar formulas declare LayerNorm/GELU/softmax arithmetic; special functions are separate primitive counts. Index construction, interpolation coefficient arithmetic, inv_freq initialization, casts/backend fusion and sampling metadata processing are not claimed as complete runtime instructions.',
                    'Cache hits are caller-verified identities, not inferred from equal dimensions. Declared interfaces are not measured HBM or residency peaks. Logical parameters include bias/norm/position tensors but have not been checked against checkpoint headers.',
                ])
