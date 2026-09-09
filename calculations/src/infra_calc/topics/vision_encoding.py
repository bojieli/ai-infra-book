"""Qwen3-VL image encoder matrix/scalar work, separate from language prefill."""
import hashlib
import json

from ..paths import PROJECT
from ..sources import model_config
from ..units import positive_int
from . import multimodal_cache


def read_implementation():
    records = json.loads((PROJECT/'configs/vision-encoding.lock.json').read_text())
    for row in records:
        data=(PROJECT/row['file']).read_bytes()
        if len(data)!=row['bytes'] or hashlib.sha256(data).hexdigest()!=row['sha256']:
            raise ValueError('Vision implementation hash mismatch: '+row['file'])
    return records


def calculate(preprocessed_height=640, preprocessed_width=640, images_per_request=4,
              encoder_cache_hits=0, dtype='bf16'):
    """Encode each miss once; cache hits skip encoder work, not feature delivery.

    Scalar work uses an explicit reference arithmetic decomposition, with special
    functions counted separately. Semantic tensor reads/writes do not predict
    actual HBM traffic, fusion, temporary memory, or CPU preprocessing latency.
    """
    inputs=locals().copy()
    positive_int(encoder_cache_hits,'encoder_cache_hits',allow_zero=True)
    positive_int(images_per_request,'images_per_request')
    if encoder_cache_hits>images_per_request:
        raise ValueError('Encoder cache hits cannot exceed image count')
    geo=multimodal_cache.calculate(preprocessed_height=preprocessed_height,
        preprocessed_width=preprocessed_width,images_per_request=images_per_request,text_tokens=0,dtype=dtype)
    source=read_implementation()
    cfg=model_config(multimodal_cache.MODEL)['vision_config']
    p=geo['summary']['pre_merge_patch_count'];m=geo['summary']['image_visual_positions']
    h=cfg['hidden_size'];f=cfg['intermediate_size'];o=cfg['out_hidden_size']
    heads=cfg['num_heads'];d=h//heads;layers=cfg['depth'];merge=cfg['spatial_merge_size']**2
    width=multimodal_cache.DTYPE_BYTES[dtype];merged=h*merge
    matrices=[];scalars=[]
    def scalar(name,stage,shape,copies,counts,reads,writes,parameters=0):
        scalars.append(dict(operator=name,stage=stage,shape=shape,copies=copies,
            counts={k:v*copies for k,v in counts.items()},
            semantic_read_bytes=reads*width*copies,semantic_write_bytes=writes*width*copies,
            learned_parameters=parameters*copies))
    def gemm(name,stage,rows,inner,cols,copies=1,bias=True,learned=True):
        matrices.append(dict(operator=name,stage=stage,a_shape=[rows,inner],
            b_shape=[inner,cols],output_shape=[rows,cols],copies=copies,
            matrix_flops=2*rows*inner*cols*copies,
            semantic_read_bytes=(rows*inner+inner*cols)*width*copies,
            semantic_write_bytes=rows*cols*width*copies,
            learned_parameters=(inner*cols+(cols if bias else 0))*copies if learned else 0))
        if bias:
            scalar(name+'.bias',stage,[rows,cols],copies,{'add':rows*cols},rows*cols+cols,rows*cols)
    def layernorm(name,stage,rows,cols,copies=1):
        scalar(name,stage,[rows,cols],copies,
               {'add':rows*(4*cols-1),'multiply':rows*(3*cols+2),'rsqrt':rows},
               rows*cols+2*cols,rows*cols,2*cols)
    def gelu(name,stage,elements,copies,tanh):
        scalar(name,stage,[elements],copies,
               {'multiply':(6 if tanh else 3)*elements,'add':(2 if tanh else 1)*elements,
                'tanh' if tanh else 'erf':elements},elements,elements)

    # Nonoverlapping Conv3d is exactly this flattened patch contraction.
    patch_inner=cfg['in_channels']*cfg['temporal_patch_size']*cfg['patch_size']**2
    gemm('patch_embedding','patch_embedding',p,patch_inner,h)
    # Four learned-grid neighbors per patch, weighted sum then addition to patch embedding.
    scalar('learned_position_interpolation','position_embedding',[p,h],1,
           {'multiply':4*p*h,'add':3*p*h},4*p*h+4*p,p*h,
           cfg['num_position_embeddings']*h)
    # Interpolation weights and their promoted weighted sum are float32.
    scalars[-1]['semantic_read_bytes']=4*p*h*width+4*p*4
    scalars[-1]['semantic_write_bytes']=p*h*4
    scalar('position_add','position_embedding',[p,h],1,{'add':p*h},2*p*h,p*h)
    # Shared rotary table: 2 axes * head_dim/4 values before duplication across halves.
    angles=p*d//2
    scalar('rotary_table','position_embedding',[2,p,d//4],1,
           {'multiply':3*angles,'cos':angles,'sin':angles},2*p+d//4,2*p*d)
    scalars[-1]['semantic_read_bytes']=(2*p+d//4)*4
    scalars[-1]['semantic_write_bytes']=2*p*d*4

    layernorm('block.norm1','vision_blocks',p,h,layers)
    gemm('block.qkv','vision_blocks',p,h,3*h,layers)
    scalar('block.rope_qk','vision_blocks',[2,p,h],layers,
           {'multiply':4*p*h,'add':2*p*h,'negate':p*h},4*p*h+2*p*d,2*p*h)
    # Explicit .float() rotary arithmetic; cast copy operations are excluded.
    scalars[-1]['semantic_read_bytes']=(4*p*h+2*p*d)*4*layers
    scalars[-1]['semantic_write_bytes']=2*p*h*4*layers
    gemm('block.qk','vision_blocks',p,d,p,heads*layers,bias=False,learned=False)
    score=heads*p*p
    scalar('block.score_scale','vision_blocks',[heads,p,p],layers,{'multiply':score},score,score)
    scalar('block.softmax','vision_blocks',[heads,p,p],layers,
           {'comparison':heads*p*(p-1),'subtract':score,'exp':score,
            'add':heads*p*(p-1),'divide':score},score,score)
    gemm('block.pv','vision_blocks',p,p,d,heads*layers,bias=False,learned=False)
    gemm('block.attention_output','vision_blocks',p,h,h,layers)
    scalar('block.residual1','vision_blocks',[p,h],layers,{'add':p*h},2*p*h,p*h)
    layernorm('block.norm2','vision_blocks',p,h,layers)
    gemm('block.mlp_up','vision_blocks',p,h,f,layers)
    gelu('block.gelu_tanh','vision_blocks',p*f,layers,True)
    gemm('block.mlp_down','vision_blocks',p,f,h,layers)
    scalar('block.residual2','vision_blocks',[p,h],layers,{'add':p*h},2*p*h,p*h)

    merger_names=['final']+['deepstack_'+str(i) for i in cfg['deepstack_visual_indexes']]
    for name in merger_names:
        stage='merger_'+name
        if name=='final':layernorm(stage+'.norm',stage,p,h)
        else:layernorm(stage+'.norm',stage,m,merged)
        gemm(stage+'.up',stage,m,merged,merged)
        gelu(stage+'.gelu_exact',stage,m*merged,1,False)
        gemm(stage+'.out',stage,m,merged,o)

    scalar_counts={}
    for row in scalars:
        for key,value in row['counts'].items():scalar_counts[key]=scalar_counts.get(key,0)+value
    misses=images_per_request-encoder_cache_hits
    per_image=sum(r['matrix_flops'] for r in matrices)
    parameter_count=sum(r['learned_parameters'] for r in matrices+scalars)
    stages=[]
    for stage in dict.fromkeys(r['stage'] for r in matrices+scalars):
        mr=[r for r in matrices if r['stage']==stage];sr=[r for r in scalars if r['stage']==stage]
        counts={}
        for row in sr:
            for key,val in row['counts'].items():counts[key]=counts.get(key,0)+val
        stages.append(dict(stage=stage,encoder_executions=misses,
            matrix_flops_per_image=sum(r['matrix_flops'] for r in mr),
            matrix_flops_per_request=sum(r['matrix_flops'] for r in mr)*misses,
            scalar_counts_per_image=counts,
            semantic_read_bytes_per_image=sum(r['semantic_read_bytes'] for r in mr+sr),
            semantic_write_bytes_per_image=sum(r['semantic_write_bytes'] for r in mr+sr)))
    return dict(schema_version=1,calculation='vision-encoding',model=multimodal_cache.MODEL,
        scenario=inputs,sources=geo['sources']+source,vision_encoding_matrices=matrices,
        vision_encoding_scalars=scalars,vision_encoding_stages=stages,
        summary=dict(preprocessed_grid_thw=geo['summary']['preprocessed_grid_thw'],
            patches_per_image=p,merged_positions_per_image=m,vision_layers=layers,
            encoder_executions_per_request=misses,encoder_cache_hits=encoder_cache_hits,
            patch_input_shape=[p,patch_inner],patch_input_bytes_per_image=p*patch_inner*width,
            matrix_flops_per_image=per_image,matrix_flops_per_request=per_image*misses,
            scalar_counts_per_image=scalar_counts,
            scalar_counts_per_request={k:v*misses for k,v in scalar_counts.items()},
            complete_vision_learned_parameters=parameter_count,
            vision_parameter_bytes_declared_dtype=parameter_count*width,
            one_image_one_layer_materialized_score_bytes=heads*p*p*width,
            complete_encoder_bytes_per_image=geo['summary']['complete_encoder_bytes_per_image'],
            complete_encoder_bytes_per_request=geo['summary']['complete_encoder_bytes_per_request'],
            final_and_deepstack_components=geo['multimodal_encoder_components'],
            semantic_read_bytes_per_image=sum(r['semantic_read_bytes'] for r in matrices+scalars),
            semantic_write_bytes_per_image=sum(r['semantic_write_bytes'] for r in matrices+scalars)),
        assumptions=[
            '输入为已预处理静态图，复用multimodal_cache官方patch/merge/面积校验；不计JPEG/PNG解码、resize、像素标准化、CPU调度。temporal patch复制已体现在1536输入宽，不把静态图token翻倍。',
            '逐图独立非因果视觉attention；N张同尺寸图的QK/PV为N×P²，不是(NP)²。24个视觉block、final merger和3个DeepStack分别计一次，完全不包含语言prefill或语言KV写入，避免与语言预算重复。',
            '矩阵按2MNK统计，bias和所有列出的norm/activation/softmax/RoPE/残差单列；exp/tanh/erf/rsqrt等调用数不等同一个FLOP。LayerNorm为明确两遍参考算术分解，实际kernel可融合/改变归约次序。',
            '逻辑tensor读写表示逐算子语义操作数，参数可重复读；不是HBM访存实测。dtype控制声明模型边界操作数存储字节；位置插值权重/输出与RoPE显式FP32操作数按4B保留。LayerNorm/softmax内部FP32中间量、casts与实际工作区另计，不据此套统一低精度峰值。',
            'learned position四邻点加权与rotary table主体已计；位置index/grid构造、插值权重计算、rope inv_freq初始化和数据搬运未计，故scalar清单是声明参考工作而非所有系统指令。',
            'final norm在[P,1024]上执行，DeepStack norm在[P/4,4096]上执行；merger使用erf GELU，block使用tanh GELU。DeepStack扩展EC特征维，不增加语言图像位置数。',
            'encoder_cache_hits为整数已验证命中图数；命中跳过所有视觉工作，但仍返回所有图EC字节。缓存查找/读取/身份校验和E/PD传输不在本编码工作内，没有据此推断命中延迟或吞吐。',
            '参数数目包含patch/position embedding/全部block与merger的Linear bias和LayerNorm affine，不含非持久rope buffer、语言模型；假设所选dtype统一保存参数，实际checkpoint混合精度及并行复制需要另核。',
        ])
