"""Actual mixed tensor encodings from five pinned GGUF shard headers."""
import hashlib
import json
from math import prod
from fractions import Fraction
from ..paths import PROJECT
from ..gguf_header import parse
from ..sources import model_config,provenance
from ..models import qwen3_moe
from .gguf_inventory import inventory

# GGML enum ID: name, elements/block, bytes/block, raw code bits/element.
# Layouts: official ggml-common.h static_asserts, retained alongside headers.
TYPES={0:('F32',1,4,32),10:('Q2_K',256,84,2),11:('Q3_K',256,110,3),
       12:('Q4_K',256,144,4),14:('Q6_K',256,210,6)}


def calculate(variant='Q2_K'):
    if variant not in ('Q2_K','Q4_K_M'):raise ValueError('Only pinned Q2_K and Q4_K_M headers available')
    groups,sources,_=inventory();lock=json.loads((PROJECT/'configs/gguf-headers.lock.json').read_text())
    headers={}
    for entry in lock['files']:
        data=(PROJECT/entry['file']).read_bytes()
        if hashlib.sha256(data).hexdigest()!=entry['sha256']:raise ValueError('GGUF header/spec hash mismatch')
        sources.append(entry)
        if entry.get('gguf_path','').startswith(variant+'/'):headers[entry['gguf_path']]=parse(data)
    config=model_config('qwen3-235b-a22b');h=config['hidden_size'];v=config['vocab_size'];d=config['head_dim']
    q=config['num_attention_heads']*d;k=config['num_key_value_heads']*d
    e=config['num_experts'];f=config['moe_intermediate_size'];layers=config['num_hidden_layers']
    expected={'token_embd.weight':[h,v],'output.weight':[h,v],'output_norm.weight':[h]}
    for i in range(layers):
        fields={'attn_q':[h,q],'attn_k':[h,k],'attn_v':[h,k],'attn_output':[q,h],
                'attn_q_norm':[d],'attn_k_norm':[d],'attn_norm':[h],'ffn_norm':[h],
                'ffn_gate_inp':[h,e],'ffn_gate_exps':[h,f,e],'ffn_up_exps':[h,f,e],'ffn_down_exps':[f,h,e]}
        expected.update({f'blk.{i}.{name}.weight':shape for name,shape in fields.items()})
    type_rows={};tensor_rows=[];shard_rows=[];seen=set()
    for shard in groups[variant]:
        header=headers[shard['path']];meta=header['metadata'];alignment=header['alignment']
        if meta['split.no']!=shard['index']-1 or meta['split.count']!=shard['count'] or meta['split.tensors.count']!=len(expected):raise ValueError('GGUF split identity mismatch')
        if shard['index']==1:
            for key,val in {'general.architecture':'qwen3moe','qwen3moe.block_count':layers,'qwen3moe.embedding_length':h,
                            'qwen3moe.attention.head_count':config['num_attention_heads'],'qwen3moe.attention.head_count_kv':config['num_key_value_heads'],
                            'qwen3moe.expert_count':e,'qwen3moe.expert_used_count':config['num_experts_per_tok'],'qwen3moe.expert_feed_forward_length':f}.items():
                if meta.get(key)!=val:raise ValueError(f'GGUF architecture mismatch: {key}')
        cursor=0;payload=0;padding=0
        for tensor in sorted(header['tensors'],key=lambda t:t['offset']):
            name=tensor['name'];shape=tensor['shape'];offset=tensor['offset']
            if name in seen or expected.get(name)!=shape:raise ValueError(f'GGUF tensor shape/name mismatch: {name}')
            seen.add(name)
            if tensor['type_id'] not in TYPES:raise ValueError('Unsupported GGML tensor type')
            typ,block,block_bytes,bits=TYPES[tensor['type_id']]
            if shape[0]%block:raise ValueError('Quantized row is not block divisible')
            elements=prod(shape);blocks=elements//block;size=blocks*block_bytes
            codes=elements*bits//8;overhead=size-codes
            if offset<cursor or offset%alignment:raise ValueError('Overlapping or unaligned tensor data')
            padding+=offset-cursor;cursor=offset+size;payload+=size
            aggregate=type_rows.setdefault(typ,dict(type=typ,block_elements=block,block_bytes=block_bytes,
                    tensors=0,elements=0,payload_bytes=0,code_or_float_bytes=0,scale_metadata_bytes=0))
            for key,value in [('tensors',1),('elements',elements),('payload_bytes',size),('code_or_float_bytes',codes),('scale_metadata_bytes',overhead)]:aggregate[key]+=value
            tensor_rows.append(dict(shard=shard['index'],name=name,gguf_shape=shape,type=typ,elements=elements,offset=offset,payload_bytes=size,scale_metadata_bytes=overhead))
        tail=shard['file_bytes']-header['data_start_bytes']-cursor
        if tail<0 or tail>=alignment:raise ValueError('File length inconsistent with tensor layout')
        padding+=tail
        shard_rows.append(dict(path=shard['path'],file_bytes=shard['file_bytes'],header_bytes=header['header_bytes'],
                               header_alignment_bytes=header['data_start_bytes']-header['header_bytes'],
                               tensor_payload_bytes=payload,tensor_padding_bytes=padding,tensors=header['tensor_count']))
    if seen!=set(expected):raise ValueError('Incomplete model tensor set')
    parameters=sum(t['elements'] for t in tensor_rows)
    if parameters!=sum(w.parameters for w in qwen3_moe.weights(config)):raise ValueError('Original model parameter total mismatch')
    payload=sum(t['payload_bytes'] for t in type_rows.values());scale=sum(t['scale_metadata_bytes'] for t in type_rows.values())
    total=sum(s['file_bytes'] for s in shard_rows)
    if total!=payload+sum(s['header_bytes']+s['header_alignment_bytes']+s['tensor_padding_bytes'] for s in shard_rows):raise ValueError('File byte conservation failed')
    return dict(schema_version=1,calculation='gguf-layout',scenario=dict(variant=variant),sources=sources+provenance('qwen3-235b-a22b'),
                gguf_types=list(type_rows.values()),gguf_shards=shard_rows,gguf_tensors=tensor_rows,
                summary=dict(tensors=len(tensor_rows),parameters=parameters,file_bytes=total,tensor_payload_bytes=payload,
                             code_or_float_bytes=payload-scale,quantization_scale_metadata_bytes=scale,
                             file_header_and_padding_bytes=total-payload,
                             payload_bits_per_parameter_exact=str(Fraction(payload*8,parameters)),
                             file_bits_per_parameter_exact=str(Fraction(total*8,parameters)),
                             storage_types=sorted(type_rows)),
                assumptions=[
                    '对固定发布Q2_K两片／Q4_K_M三片读取文件头，保存从magic至tensor-data起点的原始字节与SHA；网络Range读取有限前缀后裁掉载荷，只保留完整头。没有下载或校验完整权重数据，不证明量化数值质量。',
                    'GGUF v3 little-endian，张量shape按GGUF内层维优先；按官方Qwen配置核对全部1131张量，包括128专家的三维合并矩阵、Router、输出头和norm。参数与原始模型相同不等于精度或输出相同。',
                    'GGML官方ggml-common.h：Q2_K每256值84bytes（64码值+20尺度／最小值元数据），Q3_K110（96+14），Q4_K144（128+16），Q6_K210（192+18）；F32每值4bytes。每个量化行必须整除block长度，不将文件名位宽套到所有张量。',
                    '按每张量实际类型计算码值／浮点载荷、块尺度元数据；再按offset核对无重叠／对齐、分片文件头与padding，逐文件字节守恒。未执行GGML解包或反量化，运行时重打包／驻留和scratch不在文件布局中。',
                ])
