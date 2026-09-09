"""Wan2.2 VAE decoder contractions from actual meta-device execution geometry."""
import hashlib
import json
from math import prod

from ..paths import PROJECT
from ..units import positive_int
from .wan_vae_nonmatrix import calculate as calculate_nonmatrix


def read_trace():
    records=json.loads((PROJECT/'configs/video-generation.lock.json').read_text())['sources']
    names={'wan-vae-decode-meta.json','capture_wan_vae_shapes.py','wan/modules/vae2_2.py'}
    selected={r['upstream_file']:r for r in records if r['upstream_file'] in names}
    if set(selected)!=names:raise ValueError('VAE shape trace requires all original/capture sources')
    data={}
    for key,r in selected.items():
        b=(PROJECT/r['file']).read_bytes()
        if len(b)!=r['bytes'] or hashlib.sha256(b).hexdigest()!=r['sha256']:
            raise ValueError('Wan VAE source/capture hash mismatch')
        data[key]=b
    trace=json.loads(data['wan-vae-decode-meta.json'])
    if trace['source_sha256']!=selected['wan/modules/vae2_2.py']['sha256']:
        raise ValueError('VAE trace was produced from a different implementation')
    return trace


def axis_nonpadding_pairs(length,output,kernel,stride,dilation,padding_before):
    """Count valid output/kernel pairs, excluding external padding coordinates."""
    total=0
    for tap in range(kernel):
        first=max(0,-((tap*dilation-padding_before)//stride))
        last=min(output-1,(length-1+padding_before-tap*dilation)//stride)
        total+=max(0,last-first+1)
    return total


def calculate(latent_frames=31,latent_height=48,latent_width=84,dtype_bytes=4):
    for key,value in locals().copy().items():positive_int(value,key)
    if dtype_bytes not in (2,4):raise ValueError('VAE boundary storage must be 2 or 4 bytes per floating-point element')
    trace=read_trace();events=[]
    def scale_shape(shape,initial=False):
        result=list(shape)
        if result[-2]%2 or result[-1]%3:raise ValueError('Trace spatial axes do not scale integrally')
        result[-2]=result[-2]//2*latent_height;result[-1]=result[-1]//3*latent_width
        if initial:result[2]=latent_frames
        return result
    for raw in trace['events']:
        chunk=raw['chunk']
        repeats=1 if chunk<1 else (min(1,latent_frames-1) if chunk==1 else max(0,latent_frames-2))
        if not repeats:continue
        phase={-1:'all_latents_projection',0:'first_chunk',1:'second_chunk',2:'steady_chunk'}[chunk]
        if raw['kind']=='attention':
            b,heads,_,dim=raw['q_shape'];tokens=latent_height*latent_width
            flops=4*b*heads*tokens*tokens*dim
            events.append(dict(name=raw['name'],phase=phase,kind='attention',repeats=repeats,
                q_shape=[b,heads,tokens,dim],k_shape=[b,heads,tokens,dim],v_shape=[b,heads,tokens,dim],
                causal=False,matrix_flops_per_occurrence=flops,
                matrix_flops=flops*repeats,external_padding_excluded_flops=flops*repeats,
                logical_operand_bytes=(4*b*heads*tokens*dim+2*b*heads*tokens*tokens)*dtype_bytes*repeats))
            continue
        inp=scale_shape(raw['input_shape'],chunk==-1);out=scale_shape(raw['output_shape'],chunk==-1)
        cache=scale_shape(raw['cache_shape']) if raw['cache_shape'] is not None else None
        kernel=raw['kernel'];ndim=len(kernel);stride=raw['stride'];dilation=raw['dilation']
        spatial=list(inp[2:]);cache_frames=cache[2] if cache else 0
        if raw['causal_padding'] is not None:
            w0,w1,h0,h1,t0,t1=raw['causal_padding']
            before=[t0-cache_frames,h0,w0];after=[t1,h1,w1]
            spatial[0]+=cache_frames
        else:
            before=list(raw['padding']);after=list(raw['padding'])
        expected=[(size+left+right-dil*(k-1)-1)//st+1
                  for size,left,right,dil,k,st in zip(spatial,before,after,dilation,kernel,stride)]
        if expected!=out[2:]:raise ValueError('Archived VAE convolution output violates its padding/stride geometry')
        full=2*prod(out)*raw['weight_shape'][1]*prod(kernel)
        valid=prod(axis_nonpadding_pairs(size,o,k,st,dil,pad)
                   for size,o,k,st,dil,pad in zip(spatial,out[2:],kernel,stride,dilation,before))
        no_pad=2*inp[0]*out[1]*raw['weight_shape'][1]*valid
        events.append(dict(name=raw['name'],phase=phase,kind=raw['kind'],repeats=repeats,
            input_shape=inp,cache_shape=cache,output_shape=out,weight_shape=raw['weight_shape'],
            kernel=kernel,stride=stride,padding_before=before,padding_after=after,
            matrix_flops_per_occurrence=full,matrix_flops=full*repeats,
            external_padding_excluded_flops=no_pad*repeats,
            bias_adds=prod(out)*repeats if raw['bias'] else 0,
            logical_operand_bytes=(prod(inp)+(prod(cache) if cache else 0)+prod(raw['weight_shape'])
                +(out[1] if raw['bias'] else 0)+prod(out))*dtype_bytes*repeats))
    total=sum(r['matrix_flops'] for r in events)
    return dict(nonmatrix_work=calculate_nonmatrix(latent_frames,latent_height,latent_width,dtype_bytes),status='matrix_contractions_accounted',latent_shape=[1,48,latent_frames,latent_height,latent_width],
        output_video_shape=[1,3,4*(latent_frames-1)+1,16*latent_height,16*latent_width],
        decoder_evaluations=1,temporal_decoder_chunk_calls=latent_frames,
        matrix_flops=total,external_padding_excluded_flops=sum(r['external_padding_excluded_flops'] for r in events),
        convolution_bias_adds=sum(r.get('bias_adds',0) for r in events),
        decoder_learned_parameters=trace['decoder_parameters'],declared_decoder_weight_bytes=trace['decoder_parameters']*dtype_bytes,
        logical_operand_bytes=sum(r['logical_operand_bytes'] for r in events),operators=events,
        assumptions=[
            '固定官方Wan2.2_VAE无权重meta execution获取完整decode卷积/空间attention形状；不是实测GPU运行。原件与capture代码/hash锁定，首块/第二块/cache稳定块分别计数，不能把每块简单视为四帧。',
            '此处是TI2V5B无输入图像分支的输出VAE decode一次；未添加无发生的输入图像VAE encode。3D causal temporal padding、cache拼接与2D spatial padding进入输出几何；最终unpatchify空间2倍已计输出尺寸。',
            'matrix_flops按卷积完整kernel乘加，含外部padding零位；另给排除外部F.pad位置的诊断值，cache tensor内部可能已有零，不把诊断值称真实非零计算。稀疏值不能自动免去dense卷积work。',
            'VAE中AttentionBlock虽注释causal，实际sdpa调用没有is_causal=True，按每latent帧完整空间attention计；不是跨输出视频所有帧做一次全attention。',
            '覆盖所有decode Conv2d/CausalConv3d与QK/PV矩阵，bias add另列；RMS/SiLU/nearest上采样、残差、latent反标准化、clamp、cat/copy另见nonmatrix_work；实际VAE工作区与kernel耗时仍未给定。不可把此矩阵和当完整端到端时间。',
            'dtype_bytes仅声明存储；官方wrapper默认float32，实际checkpoint混合精度未下载验证。decoder参数不含未执行encoder，模型可能整体常驻而额外占内存；逻辑bytes不含所有cache复制与padding缓冲，不是峰值显存。',
        ])
