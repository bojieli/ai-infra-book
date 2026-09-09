"""One-row RMSNorm versus three-pass split reduction at an explicit interface."""
import math
import struct
from ..sources import model_config, provenance
from ..models import qwen3
from ..units import positive_int


def partitions(width, splits):
    positive_int(width,'width'); positive_int(splits,'splits')
    if splits>width: raise ValueError('Cannot create empty reduction partitions')
    q,r=divmod(width,splits)
    return [q+(i<r) for i in range(splits)]


def sum_squares(values, splits=1, fp32=False):
    """Small numerical witness; explicit sequential reduction inside partitions."""
    sizes=partitions(len(values),splits)
    rnd=(lambda x: struct.unpack('f',struct.pack('f',x))[0]) if fp32 else (lambda x:x)
    partials=[]; offset=0
    for size in sizes:
        terms=[rnd(rnd(x)*rnd(x)) for x in values[offset:offset+size]]
        total=terms[0]
        for term in terms[1:]: total=rnd(total+term)
        partials.append(total); offset+=size
    total=partials[0]
    for part in partials[1:]: total=rnd(total+part)
    return total


def normalized(values, splits=1, epsilon=1e-6):
    inv=1/math.sqrt(sum_squares(values,splits)/len(values)+epsilon)
    return [x*inv for x in values]


def calculate(model: str = 'qwen3-8b', rows: int = 1, splits: int = 8,
              width_multiplier: int = 1) -> dict:
    c=model_config(model); qwen3.validate(c)
    positive_int(rows,'rows'); positive_int(width_multiplier,'width_multiplier')
    width=c['hidden_size']*width_multiplier
    sizes=partitions(width,splits)
    common=dict(squares=rows*width,reduction_adds=rows*(width-1),
                mean_and_epsilon=2*rows,normalize_and_affine=2*rows*width,rsqrt=rows)
    fused=dict(name='one_group_per_row',groups=rows,launches=1,
               input_read_bytes=2*rows*width,weight_read_bytes=2*rows*width,
               output_write_bytes=2*rows*width,partial_write_bytes=0,partial_read_bytes=0,
               inverse_write_bytes=0,inverse_read_bytes=0,declared_auxiliary_bytes=0)
    split=dict(name='three_pass_split',groups=rows*(2*splits+1),launches=3,
               input_read_bytes=4*rows*width,weight_read_bytes=2*rows*width,
               output_write_bytes=2*rows*width,partial_write_bytes=4*rows*splits,
               partial_read_bytes=4*rows*splits,inverse_write_bytes=4*rows,
               inverse_read_bytes=4*rows*splits,declared_auxiliary_bytes=4*rows*(splits+1))
    fields=['input_read_bytes','weight_read_bytes','output_write_bytes','partial_write_bytes',
            'partial_read_bytes','inverse_write_bytes','inverse_read_bytes']
    for item in [fused,split]: item['interface_bytes']=sum(item[key] for key in fields)
    return dict(schema_version=1,calculation='qwen-rmsnorm-split-reduction',model=model,
                scenario=dict(rows=rows,splits=splits,width_multiplier=width_multiplier),sources=provenance(model),
                reduction_variants=[fused,split],partition_widths=sizes,arithmetic=common,
                summary=dict(width=width,official_hidden_size=c['hidden_size'],
                             scalar_flops=rows*(4*width+1),rsqrt_calls=rows,
                             first_pass_groups=rows*splits,second_pass_groups=rows,apply_groups=rows*splits,
                             local_reduction_adds=rows*(width-splits),merge_reduction_adds=rows*(splits-1),
                             partial_buffer_bytes=4*rows*splits,inverse_buffer_bytes=4*rows,
                             fused_interface_bytes=fused['interface_bytes'],split_interface_bytes=split['interface_bytes'],
                             additional_interface_bytes=split['interface_bytes']-fused['interface_bytes'],
                             fused_retained_fp32_row_bytes=4*width,
                             split_max_partition_fp32_bytes=4*max(sizes),predicted_seconds=None),
                assumptions=[
                    '使用官方 Qwen3 Dense hidden_size 的单个 RMSNorm；width_multiplier>1 是加宽归约的教学变体，不是实际 Qwen 配置。行数是本次调用规模，不将结果自动乘层数。',
                    '一组一行路径保留输入的 FP32 行值，计算 sum(x²)/D+epsilon、rsqrt、归一化及 affine；输入／gamma／输出均按 BF16 接口。这里是数学及载荷计数，转换与具体融合精度另算。',
                    '拆分路径有三个 kernel：M*S 个组写 FP32 partial；M 个组合并并写 FP32 inverse；M*S 个组重读输入并应用 inverse/gamma。每个 apply 组读一次 inverse。均匀整数划分保留尾部，不创建空分片。',
                    '归约加法分为 M*(D-S) 与 M*(S-1)，总数仍 M*(D-1)，但浮点顺序变化可能改变结果。特殊 rsqrt 独立列出；增加组数不保证加速。',
                    '接口假定 gamma 每行读取，不假定跨行缓存；局部 inverse 在组内复用。partial 与 inverse 独立分配并在第二阶段共存，辅助字节不包含输入输出或完整峰值；FP32 行保留量不是实际寄存器分配。',
                    '下一层可能是 L2 等，不把逻辑重读直接称 HBM 流量；launch、同步、容量、线程布局及真实 kernel 时间待校准。Python 小例仅展示归约代数与显式 FP32 舍入，不模拟 GPU 指令。',
                ])
