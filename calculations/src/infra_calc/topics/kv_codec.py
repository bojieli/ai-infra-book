"""Official GQA and GGML q8_0/q4_0 storage; explicit conversion break-even."""
import hashlib
import json
from fractions import Fraction
from math import ceil
from ..paths import PROJECT
from ..sources import model_config,provenance
from ..units import positive_int


def calculate(model='qwen3-8b',length=8192,batch=1,bandwidth_bytes_per_second=10**12,
              decode_fixed_ns=100000,decode_ns_per_value='1/1000',append_encode_ns=20000):
    for name,value in [('length',length),('batch',batch),('bandwidth_bytes_per_second',bandwidth_bytes_per_second),
                       ('decode_fixed_ns',decode_fixed_ns),('append_encode_ns',append_encode_ns)]:
        positive_int(value,name,allow_zero=name in ('decode_fixed_ns','append_encode_ns'))
    if isinstance(decode_ns_per_value,bool) or not isinstance(decode_ns_per_value,(int,str)):
        raise ValueError('Use exact integer or fraction string for conversion cost')
    rate=Fraction(decode_ns_per_value)
    if rate<0:raise ValueError('Conversion cost cannot be negative')
    c=model_config(model)
    if c['model_type'] not in ('qwen3','qwen3_moe') or c.get('use_sliding_window'):raise ValueError('Full GQA Qwen state required')
    if length>c['max_position_embeddings']:raise ValueError('Context exceeds official limit')
    d=c['head_dim']
    if d%32:raise ValueError('This GGML layout requires each head row divisible by 32')
    sources=provenance(model)
    for row in json.loads((PROJECT/'configs/gguf-headers.lock.json').read_text())['files']:
        if row['file'].endswith(('ggml-common.h','ggml.h')):
            if hashlib.sha256((PROJECT/row['file']).read_bytes()).hexdigest()!=row['sha256']:raise ValueError('GGML source hash mismatch')
            sources.append(row)
    head_rows=batch*2*c['num_hidden_layers']*c['num_key_value_heads']
    values_per_position=head_rows*d
    base_unit=2*values_per_position;base_history=length*base_unit
    base_traffic=base_history+base_unit
    ns_per_byte=Fraction(10**9,bandwidth_bytes_per_second)
    base_ns=base_traffic*ns_per_byte
    rows=[]
    for name,block_bytes,code_bytes in [('BF16',64,64),('Q8_0',34,32),('Q4_0',18,16)]:
        unit=head_rows*(d//32)*block_bytes;history=length*unit
        scales=head_rows*(d//32)*(block_bytes-code_bytes)*length
        conversion=Fraction(0) if name=='BF16' else decode_fixed_ns+rate*values_per_position*length+append_encode_ns
        traffic=history+unit
        fused_ns=traffic*ns_per_byte+conversion
        # Separate-buffer implementation writes decoded BF16 history then
        # attention reads it again. Serialized service ledger, no overlap claim.
        extra=0 if name=='BF16' else 2*base_history
        materialized_ns=(traffic+extra)*ns_per_byte+conversion
        saved_per_position=(base_unit-unit)*ns_per_byte
        slope=saved_per_position-rate*values_per_position if name!='BF16' else Fraction(0)
        intercept=saved_per_position-decode_fixed_ns-append_encode_ns
        crossing=None;winning_min=None;winning_max=None
        if name!='BF16':
            if slope>0:
                crossing=max(1,(-intercept)//slope+1);winning_min=int(crossing)
            elif slope==0 and intercept>0:
                crossing=1;winning_min=1
            elif slope<0:
                upper=ceil(intercept/(-slope))-1
                if upper>=1:winning_min=1;winning_max=upper
        rows.append(dict(format=name,values_per_block=32,bytes_per_block=block_bytes,
                         history_resident_bytes=history,history_code_bytes=history-scales,
                         history_scale_bytes=scales,next_token_append_bytes=unit,
                         saved_history_bytes=base_history-history,
                         fused_declared_traffic_bytes=traffic,materialized_declared_traffic_bytes=traffic+extra,
                         materialized_extra_history_buffer_bytes=0 if name=='BF16' else base_history,
                         conversion_ns_exact=str(conversion),baseline_ns_exact=str(base_ns),
                         fused_ns_exact=str(fused_ns),materialized_ns_exact=str(materialized_ns),
                         fused_saving_ns_exact=str(base_ns-fused_ns),fused_wins=fused_ns<base_ns,
                         materialized_wins=materialized_ns<base_ns,
                         strict_fused_crossover_length=int(crossing) if crossing is not None else None,
                         winning_length_min=winning_min,winning_length_max=winning_max,
                         crossover_within_model_context=crossing is not None and crossing<=c['max_position_embeddings']))
    return dict(schema_version=1,calculation='kv-codec',scenario=dict(model=model,length=length,batch=batch,
                bandwidth_bytes_per_second=bandwidth_bytes_per_second,decode_fixed_ns=decode_fixed_ns,
                decode_ns_per_value=str(rate),append_encode_ns=append_encode_ns),sources=sources,kv_codec_rows=rows,
                summary=dict(values_per_cached_position=values_per_position,bf16_history_bytes=base_history,
                             bf16_next_token_append_bytes=base_unit,baseline_read_append_ns_exact=str(base_ns)),
                assumptions=[
                    '官方Qwen full GQA，每token每K/V head一行head_dim值；Q8_0每32值32码值bytes+2bytes FP16 scale，Q4_0每32值16码值bytes+2bytes scale，来源为固定GGML官方结构体。BF16是容量基线，不是Q8/Q4输出类型。',
                    '存储与执行分开：假定量化KV恢复后仍按原Attention精度使用，不套INT8/FP4 Tensor峰值。量化误差、质量、实际后端支持及内核算术尚未验证。',
                    '查询读取length条已有KV并编码／写入一个新位置；baseline按BF16旧读+新增写。融合路径不把完整解码KV写回外存；物化路径另加BF16历史写一次／读一次及一份临时历史buffer。',
                    '带宽和decode_fixed_ns、decode_ns_per_value、append_encode_ns均是显式教学输入，转换成本采用独立串行服务账；append_encode_ns是整个batch一次新增编码成本，不随history增长。不能当作GPU实测或声称转换与访存无重叠。',
                    '只比较KV读／写与转换子账，未包含目标矩阵、softmax、分页、对齐、索引、数据布局重打包及工作区其它部分。转换固定成本与每值成本可替换，交叉点仅对当前线性子账成立。',
                ])
