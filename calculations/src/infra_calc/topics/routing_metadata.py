"""Logical routed-expert ID payload, identity fields and supply requirements."""
from fractions import Fraction
from ..sources import provenance
from ..units import positive_int
from .experts import geometry


ENCODINGS={'uint8':(1,255),'uint16':(2,65535),'int32':(4,2**31-1)}


def calculate(model='qwen3-30b-a3b', tokens=8192, encoding='uint16',
              token_rate_per_second=1000000, retained_copies=1,
              bandwidth_bytes_per_second=10**9, header_bytes=128):
    for name,value in (('tokens',tokens),('token_rate_per_second',token_rate_per_second),
                       ('retained_copies',retained_copies),('bandwidth_bytes_per_second',bandwidth_bytes_per_second)):
        positive_int(value,name)
    positive_int(header_bytes,'header_bytes',allow_zero=True)
    if encoding not in ENCODINGS:raise ValueError('Choose uint8, uint16 or int32 expert IDs')
    g=geometry(model);width,maximum=ENCODINGS[encoding]
    if g['experts']-1>maximum:raise ValueError('Expert IDs exceed selected encoding range')
    layers=len(g['moe_layers']);entries=tokens*layers*g['top_k'];ids=entries*width
    # A declared portable teaching layout: sequence ID, token position and weight version.
    identity=tokens*(8+8+8)
    mask=(tokens+7)//8
    payload=header_bytes+identity+mask+ids
    alternatives=[]
    for name,(size,limit) in ENCODINGS.items():
        fits=g['experts']-1<=limit
        alternatives.append(dict(encoding=name,bytes_per_id=size,max_id=limit,can_represent_all_experts=fits,
                                 routed_id_bytes=entries*size if fits else None))
    per_token=Fraction(payload,tokens)
    required=per_token*token_rate_per_second
    return dict(schema_version=1,calculation='routing-metadata',model=model,
                scenario=dict(model=model,tokens=tokens,encoding=encoding,token_rate_per_second=token_rate_per_second,
                              retained_copies=retained_copies,bandwidth_bytes_per_second=bandwidth_bytes_per_second,header_bytes=header_bytes),
                sources=provenance(model),routing_metadata_encodings=alternatives,
                routing_metadata_components=dict(routed_ids_bytes=ids,token_identity_bytes=identity,validity_bitset_bytes=mask,stream_header_bytes=header_bytes),
                summary=dict(moe_layers=layers,moe_layer_ids=g['moe_layers'],routed_experts=g['experts'],top_k=g['top_k'],
                             dense_layer_count=len(g['dense_layers']),shared_experts_per_layer=g['shared'],hash_routed_layers=len(g['hash_layers']),
                             id_entries=entries,routed_id_bytes=ids,complete_declared_payload_bytes=payload,
                             minimum_unsigned_bits_per_id=(g['experts']-1).bit_length(),
                             retained_payload_bytes=retained_copies*payload,
                             average_declared_bytes_per_token_exact=str(per_token),
                             required_transport_bytes_per_second_exact=str(required),
                             transport_has_strict_slack=required<bandwidth_bytes_per_second,
                             one_payload_transfer_exact_seconds=str(Fraction(payload,bandwidth_bytes_per_second))),
                assumptions=[
                    '复用官方专家几何：仅主模型MoE层的逻辑routed专家ID，shared专家无top-k选择所以不另写ID；K3排除首个dense层，V4包含hash路由层的选中ID，MTP/草稿分支不计。只证明元数据几何，不表示框架支持该模型的R3训练。',
                    '路由ID张量形状[tokens,MoE层数,top-k]，ID从0开始，uint8上限255恰好支持256专家，不能用于384/896专家；int32为非负有符号整数范围。bit_length仅信息位数参考，实际字节编码不自动位打包。',
                    '教学记录每token另存uint64 sequence ID、position和weight version各8bytes；有效位图ceil(tokens/8)，stream header默认128bytes为输入预算，不声称实际NeMo/vLLM格式。固定model revision及layer顺序须由stream header/外部schema绑定，128bytes不证明任意元数据都可装下。',
                    'tokens为明确记录位置数，包括caller选择保留的前缀；多轮共享、packing重排、缺失路由、不同模型/权重版本需要身份验证，本模块不根据相同文本去重，也不自动把KV命中当路由日志命中。',
                    'retained_copies是物理保留完整副本数，只乘存储，不自动乘一次传输；每秒供给按同长度记录批次的平均bytes/token乘token_rate，header/bitset尾部随批次重新计量。带宽为有效单向教学输入，不是硬件峰值。',
                    '没有路由分数、概率、logprob、梯度或KV载荷，不能据此声称省掉router/专家计算或保证训练质量。供给等于带宽不标有余量；未计通信启动、排队、压缩或持久化协议。',
                ])
