"""Pinned official DFlash checkpoint: tensor shapes and matrix/KV ledger."""
import hashlib
import json
from math import prod
from ..paths import PROJECT
from ..sources import model_config
from ..models import forward
from ..schema import Scenario
from ..units import positive_int


def calculate(cached_context=1020, new_context=4, block_size=16):
    positive_int(cached_context,'cached_context',allow_zero=True)
    positive_int(new_context,'new_context')
    positive_int(block_size,'block_size')
    if block_size < 2 or block_size > 16:
        raise ValueError('Supported block-size analysis is 2..16; checkpoint trained block size is 16')
    lock=json.loads((PROJECT/'configs/dflash.lock.json').read_text())
    loaded={}
    for row in lock['files']:
        data=(PROJECT/row['file']).read_bytes()
        if hashlib.sha256(data).hexdigest()!=row['sha256']:
            raise ValueError(f"DFlash source checksum mismatch: {row['file']}")
        loaded[row['file'].rsplit('/',1)[-1]]=data
    c=json.loads(loaded['config.json']);header=json.loads(loaded['model.safetensors.header.json'])
    h=c['hidden_size'];f=c['intermediate_size'];layers=c['num_hidden_layers']
    q=c['num_attention_heads'];kv=c['num_key_value_heads'];d=c['head_dim']
    target=model_config('qwen3-8b');selected=c['dflash_config']['target_layer_ids'];features=len(selected)
    for field in ('hidden_size','vocab_size','num_attention_heads','num_key_value_heads','head_dim'):
        if c[field]!=target[field]:raise ValueError(f'Target/draft mismatch: {field}')
    if c['num_target_layers']!=target['num_hidden_layers'] or any(i<0 or i>=target['num_hidden_layers'] for i in selected):
        raise ValueError('Target layer selection mismatch')
    expected={'fc.weight':[h,features*h],'hidden_norm.weight':[h],'norm.weight':[h]}
    for i in range(layers):
        prefix=f'layers.{i}.'
        shapes={'input_layernorm.weight':[h],'post_attention_layernorm.weight':[h],
                'self_attn.q_norm.weight':[d],'self_attn.k_norm.weight':[d],
                'self_attn.q_proj.weight':[q*d,h],'self_attn.k_proj.weight':[kv*d,h],
                'self_attn.v_proj.weight':[kv*d,h],'self_attn.o_proj.weight':[h,q*d],
                'mlp.gate_proj.weight':[f,h],'mlp.up_proj.weight':[f,h],'mlp.down_proj.weight':[h,f]}
        expected.update({prefix+k:v for k,v in shapes.items()})
    tensors={k:v for k,v in header.items() if k!='__metadata__'}
    if set(tensors)!=set(expected):raise ValueError('Unexpected checkpoint tensor names')
    for name,shape in expected.items():
        tensor=tensors[name]
        if tensor['shape']!=shape or tensor['dtype']!='BF16' or tensor['data_offsets'][1]-tensor['data_offsets'][0]!=2*prod(shape):
            raise ValueError(f'Checkpoint tensor mismatch: {name}')
    weights=sum(prod(shape) for shape in expected.values())
    rows=[]
    def gemm(name,m,k,n,count=1):
        rows.append(dict(operator=name,m=m,k=k,n=n,count=count,matrix_flops=2*m*k*n*count,
                         logical_operand_bytes_per_instance=2*(m*k+k*n+m*n)))
    gemm('target_feature_fusion',new_context,features*h,h)
    gemm('draft_q',block_size,h,q*d,layers)
    gemm('context_and_noise_kv',new_context+block_size,h,kv*d,2*layers)
    gemm('draft_o',block_size,q*d,h,layers)
    gemm('draft_gate_up',block_size,h,f,2*layers)
    gemm('draft_down',block_size,f,h,layers)
    length=cached_context+new_context+block_size
    gemm('noncausal_qk',block_size,d,length,layers*q)
    gemm('noncausal_pv',block_size,length,d,layers*q)
    gemm('shared_target_head',block_size-1,h,c['vocab_size'])
    verify=forward('qwen3-8b',Scenario(history=cached_context+new_context,tokens=block_size,output_head='all'))
    unit=2*layers*kv*d*2
    return dict(schema_version=1,calculation='dflash-work',
                scenario=dict(cached_context=cached_context,new_context=new_context,block_size=block_size),
                sources=lock['files']+verify['sources'],draft_matrices=rows,
                summary=dict(checkpoint=lock['repository'],revision=lock['revision'],
                             checkpoint_tensors=len(tensors),draft_parameters=weights,draft_weight_bytes=2*weights,
                             target_feature_layers=selected,new_target_feature_bytes=new_context*features*h*2,
                             fused_target_feature_bytes=new_context*h*2,noise_embedding_bytes=block_size*h*2,
                             shared_head_weight_bytes=h*c['vocab_size']*2,
                             draft_candidates=block_size-1,draft_matrix_flops=sum(r['matrix_flops'] for r in rows),
                             target_verify_matrix_flops=verify['summary']['matrix_flops'],
                             draft_kv_bytes_per_context_token=unit,draft_kv_peak_bytes=length*unit,
                             draft_kv_after_crop_bytes=(cached_context+new_context)*unit,
                             draft_noise_kv_discarded_bytes=block_size*unit,
                             target_verify_peak_kv_bytes=verify['summary']['kv_resident_after_bytes']),
                assumptions=[
                    '官方z-lab检查点固定revision；下载配置、源码和58个权重张量的safetensors头，未下载权重载荷、未执行远程代码或GPU推理。所有shape、BF16 dtype及payload区间长度逐项核对。',
                    '计量batch=1的一次草稿前向：cached_context为已有草稿KV，新目标特征new_context行融合后只投影K/V；block_size行噪声含已知首token，输出头只作用于后block_size-1行。',
                    '采用auto_map指定dflash.py路径，目标特征层按config显式[1,9,17,25,33]；不要改用旁置modeling_dflash.py中的默认层选择。草稿块全连接注意力，配对为block_size*(cached_context+new_context+block_size)。',
                    'embedding与lm_head复用目标权重，不属于独立草稿checkpoint参数；共享不消除head矩阵工作或权重读取。特征字节为逻辑接口载荷，同设备部署不自动等于网络流量。',
                    '矩阵表FMA=2，operand字节为每实例BF16矩阵边界尺寸；注意力分数实际dtype、融合、GQA复用、缓存和工作区另计，不将这些尺寸之和称为HBM实测。RMSNorm、RoPE、SiLU、softmax及采样的非矩阵工作未计入矩阵FLOPs。',
                    '草稿forward后crop丢弃整块噪声KV，仅留已确认目标context；下一轮重新读取目标特征。目标验证按同start历史、block_size行计算，两个KV池分列，不把单池峰值相加声称全执行驻留峰值。',
                    '块长2..16为形状扫描，不声称偏离训练块长16仍有相同接受率、质量或速度；未测草稿成本与完整采样行为。',
                ])
