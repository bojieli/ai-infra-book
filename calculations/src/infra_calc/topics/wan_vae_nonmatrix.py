"""Pinned Wan VAE scalar and copy boundaries, separate from contraction FLOPs.

Exact tensor-product polynomial extension of the fixed eager program's shape
counts, checked against held-out meta executions. This is a shape budget, not
an execution-time model or a claim that every logical boundary reaches HBM.
"""
import hashlib
import json
from fractions import Fraction
from ..paths import PROJECT
from ..units import positive_int


def read_trace():
    lock=json.loads((PROJECT/'configs/wan-vae-nonmatrix.lock.json').read_text())
    blobs={}
    for r in lock['sources']:
        b=(PROJECT/r['file']).read_bytes()
        if len(b)!=r['bytes'] or hashlib.sha256(b).hexdigest()!=r['sha256']:
            raise ValueError('Wan VAE nonmatrix evidence hash mismatch')
        blobs[r['role']]=b
    trace=json.loads(blobs['trace'])
    if trace['source_sha256']!=hashlib.sha256(blobs['official_source']).hexdigest():
        raise ValueError('Wan VAE nonmatrix trace source mismatch')
    return trace


def interpolate_rows(trace,t,h,w):
    """Counts are quadratic at most; first temporal chunk is a separate branch."""
    ts=(1,) if t==1 else (2,3,4)
    def weights(x,grid):
        result={}
        for a in grid:
            v=Fraction(1)
            for b in grid:
                if a!=b:v*=Fraction(x-b,a-b)
            result[a]=v
        return result
    tw,hw,ww=weights(t,ts),weights(h,(2,3,4)),weights(w,(2,3,4))
    rows={}
    for s in trace['samples']:
        st,sh,sw=s['shape']
        factor=tw.get(st,0)*hw[sh]*ww[sw]
        if not factor:continue
        for key,values in s['rows'].items():
            out=rows.setdefault(key,{k:Fraction(0) for k in values})
            for k,v in values.items():out[k]+=factor*v
    result={}
    for key,row in rows.items():
        if any(v.denominator!=1 or v<0 for v in row.values()):
            raise ValueError('VAE nonmatrix geometry interpolation is not nonnegative integral')
        if any(row.values()):result[key]={k:int(v) for k,v in row.items()}
    return result


def calculate(latent_frames=31,latent_height=48,latent_width=84,dtype_bytes=4):
    for key,value in locals().copy().items():positive_int(value,key)
    if dtype_bytes not in (2,4):raise ValueError('dtype_bytes must be 2 or 4')
    if min(latent_height,latent_width)<2:
        return dict(status='unavailable_degenerate_spatial_layout',operators=[],assumptions=['单一latent空间轴可能改变contiguous/copy分支，未外推已锁定的非退化layout trace。'])
    trace=read_trace();rows=interpolate_rows(trace,latent_frames,latent_height,latent_width)
    operators=[];excluded=[];unclassified=[]
    scalar={'aten.add.Tensor','aten.mul.Tensor','aten.mul.Scalar','aten.div.Tensor','aten.div.Scalar'}
    copies={'aten.clone.default','aten.cat.default','aten.constant_pad_nd.default','aten.upsample_nearest2d.vec','aten._upsample_nearest_exact2d.default','aten._to_copy.default','aten.copy_.default','aten.stack.default'}
    aliases={'aten.view.default','aten._unsafe_view.default','aten.permute.default','aten.slice.Tensor','aten.select.int','aten.unsqueeze.default','aten.squeeze.dim','aten.expand.default','aten.detach.default','aten.split.Tensor','aten.split_with_sizes.default','aten.alias.default','aten.as_strided.default','aten.transpose.int'}
    allocation={'aten.empty.memory_format','aten.empty_strided.default','aten.empty_like.default','aten.new_empty.default'}
    for key,r in sorted(rows.items()):
        op,line=key.split('|');n=r['output_elements'];i=r['input_elements']
        stage={0:'output_wrapper',58:'rms_normalization',68:'nearest_spatial_upsample',38:'causal_cache_concat',40:'causal_padding',121:'temporal_cache_clone',125:'temporal_cache_concat',135:'temporal_cache_concat',137:'temporal_cache_zero_fill',149:'temporal_channel_shuffle',219:'residual_cache_clone',222:'residual_cache_concat',234:'residual_silu',235:'residual_add',264:'attention_qkv_layout',267:'attention_normalization',277:'attention_residual',307:'output_unpatchify',391:'shortcut_repeat',402:'shortcut_layout',490:'upsample_shortcut_clone',495:'upsample_residual_add',675:'decoder_cache_clone',677:'decoder_cache_concat',708:'decoder_head_cache_clone',722:'decoder_head_silu',815:'latent_destandardization',836:'growing_output_concat'}.get(int(line),'official_decode')
        row=dict(stage=stage,operator=op,official_source_line=int(line),calls=r['calls'],input_elements=i,output_elements=n,
                 scalar_arithmetic_ops=0,comparisons=0,exp_evaluations=0,sqrt_evaluations=0,
                 logical_read_bytes=i*dtype_bytes,logical_write_bytes=n*dtype_bytes)
        if op in scalar:row['scalar_arithmetic_ops']=n;row['kind']='elementwise'
        elif op=='aten.linalg_vector_norm.default':
            row.update(kind='l2_norm',scalar_arithmetic_ops=2*r['reduction_input_elements']-n,sqrt_evaluations=n)
        elif op=='aten.clamp_min.default':row.update(kind='normalization_epsilon_clamp',comparisons=n)
        elif op=='aten.clamp_.default':row.update(kind='output_clamp',comparisons=2*n)
        elif op=='aten.silu.default':row.update(kind='silu',scalar_arithmetic_ops=4*n,exp_evaluations=n)
        elif op=='aten._safe_softmax.default':
            ar=latent_frames*latent_height*latent_width
            row.update(kind='stable_softmax_reference',scalar_arithmetic_ops=3*n-ar,comparisons=n-ar,exp_evaluations=n)
        elif op in copies:
            row['kind']='copy_or_gather'
            if 'upsample' in op:row['logical_read_bytes']=n*dtype_bytes
        elif op=='aten.zeros_like.default':row.update(kind='zero_fill',logical_read_bytes=0)
        elif op in aliases or op in allocation:
            excluded.append(dict(operator=op,official_source_line=int(line),calls=r['calls'],reason='view/metadata/allocation; no payload work charged'));continue
        elif op in ('aten.convolution.default','aten.bmm.default') or 'scaled_dot_product' in op:
            excluded.append(dict(operator=op,official_source_line=int(line),calls=r['calls'],reason='contraction already in matrix ledger; eager SDPA scalar primitives are separately recorded'));continue
        else:
            unclassified.append(dict(operator=op,official_source_line=int(line),**r));continue
        operators.append(row)
    fields=('scalar_arithmetic_ops','comparisons','exp_evaluations','sqrt_evaluations','logical_read_bytes','logical_write_bytes')
    return dict(status='known_scalar_and_copy_boundaries_accounted' if not unclassified else 'unclassified_dispatch_operations',
        sources=json.loads((PROJECT/'configs/wan-vae-nonmatrix.lock.json').read_text())['sources'],
        shape_proof=dict(method='fixed eager program polynomial shape counts, not runtime fit',basis_samples=len(trace['samples']),held_out_executions=len(trace['validation']),temporal_branches=['T=1','T>=2'],spatial_domain='integer latent H>=2 and W>=2',degree_per_axis=2,torch_version=trace['torch_version']),
        scalar_dtype='FP32 official wrapper/meta path; 2-byte declaration is storage sensitivity only',
        operators=operators,summary={k:sum(r[k] for r in operators) for k in fields},
        excluded_dispatch=excluded,unclassified_dispatch=unclassified,
        assumptions=[
            '固定官方eager源码的无权重meta dispatcher trace；RMS包含平方/求和/sqrt、epsilon clamp、divide、scale/gamma与源码中的加零；SiLU采用四个基本算术加一次exp的参考分解。',
            '每个源码行的primitive按调用次数分账；cat含逐块增长的完整输出拼接，clone含cache与contiguous实质复制，nearest按输出gather读写；view/空分配不算payload复制。',
            '固定非退化空间layout下已知element计数在T/H/W各至多二次：padding仿射、attention平方、增长cat为等差和。首帧分支独立，以36组精确整数shape trace重建，并用3组未参与重建的官方执行核验；不是性能拟合。',
            'primitive逻辑读写可含多个中间边界，不是实际HBM流量/峰值显存；矩阵原有logical_operand_bytes亦有交叠，两个账的bytes不可直接相加当唯一搬运量。',
            '输出反标准化与float32 clamp覆盖；2-byte仅缩放逻辑存储，不推断实际混合精度cast或autocast kernel。SDPA实际两个Q/K缩放primitive分别保留，softmax按无mask稳定参考分解，不能把这些scalar/exp等价折算Tensor FLOPs或耗时。',
        ])
