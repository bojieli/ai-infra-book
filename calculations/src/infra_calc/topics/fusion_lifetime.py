"""Pointwise-chain materialization and owner-released tensor lifetimes.

A boundary means a full next-level tensor, not merely a kernel dependency.
No in-place aliasing, recomputation, allocator pool or tile scratch is inferred.
"""
from ..sources import model_config, provenance
from ..models import qwen3
from ..units import positive_int


def ledger(sizes, operations, boundaries):
    """Group a linear operator chain and allocate output before freeing inputs."""
    n=len(operations)
    if not isinstance(boundaries,list) or len(set(boundaries))!=len(boundaries):
        raise ValueError('boundaries must be a list without duplicates')
    for end in boundaries:
        positive_int(end,'boundary',allow_zero=True)
        if end>=n-1: raise ValueError('Boundary must follow a nonfinal operator')
    ends=sorted(boundaries)+[n-1]
    produced={op['output'] for op in operations}
    external={name for op in operations for name in op['inputs'] if name not in produced}
    live=set(external)
    groups=[]; start=0
    for end in ends:
        group=operations[start:end+1]
        internal={op['output'] for op in group}
        inputs={name for op in group for name in op['inputs'] if name not in internal}
        groups.append(dict(operators=[op['name'] for op in group],inputs=sorted(inputs),output=group[-1]['output']))
        start=end+1
    stages=[];peak=sum(sizes[t] for t in live)
    for index,group in enumerate(groups):
        if not set(group['inputs'])<=live: raise ValueError('Consumer input is not materialized')
        live.add(group['output'])
        during=sum(sizes[t] for t in live);peak=max(peak,during)
        read=sum(sizes[t] for t in group['inputs']);write=sizes[group['output']]
        future={t for later in groups[index+1:] for t in later['inputs']}
        final=operations[-1]['output']
        released=sorted(t for t in live if t not in future and t!=final)
        stages.append(dict(stage=index,**group,read_bytes=read,write_bytes=write,
                           live_during=sorted(live),live_bytes=during,released_after=released))
        live.difference_update(released)
    return dict(stages=stages,interface_bytes=sum(s['read_bytes']+s['write_bytes'] for s in stages),
                declared_tensor_peak_bytes=peak,final_live=sorted(live))


def calculate(model: str = 'qwen3-8b', tokens: int = 1024,
              layout_copy: bool = False) -> dict:
    c=model_config(model);qwen3.validate(c);positive_int(tokens,'tokens')
    if not isinstance(layout_copy,bool): raise ValueError('layout_copy must be boolean')
    if tokens>c['max_position_embeddings']: raise ValueError('Tokens exceed official config')
    elements=tokens*c['intermediate_size'];x=2*elements
    sizes=dict(gate=x,up=x,silu=x,product=x,quantized=elements)
    operations=[dict(name='silu',inputs=['gate'],output='silu'),
                dict(name='multiply',inputs=['silu','up'],output='product')]
    quant_input='product'
    if layout_copy:
        sizes['reordered']=x
        operations.append(dict(name='layout_permute',inputs=['product'],output='reordered'))
        quant_input='reordered'
    operations.append(dict(name='fixed_scale_cast',inputs=[quant_input],output='quantized'))
    variants=[]
    for mask in range(1<<(len(operations)-1)):
        cuts=[i for i in range(len(operations)-1) if mask&(1<<i)]
        result=ledger(sizes,operations,cuts)
        variants.append(dict(boundaries=cuts,**result))
    unfused=variants[-1];fused=variants[0]
    for row in variants: row['saved_interface_bytes']=unfused['interface_bytes']-row['interface_bytes']
    return dict(schema_version=1,calculation='qwen-pointwise-fusion-lifetimes',model=model,
                scenario=dict(tokens=tokens,layout_copy=layout_copy),sources=provenance(model),
                tensor_sizes=sizes,chain_operations=operations,fusion_variants=variants,
                summary=dict(elements=elements,bf16_intermediate_bytes=x,
                             standalone_layout_read_write_bytes=2*x if layout_copy else 0,
                             contiguous_partitions=len(variants),
                             separate_interface_bytes=unfused['interface_bytes'],
                             fused_interface_bytes=fused['interface_bytes'],
                             saved_interface_bytes=unfused['interface_bytes']-fused['interface_bytes'],
                             separate_tensor_peak_bytes=unfused['declared_tensor_peak_bytes'],
                             fused_tensor_peak_bytes=fused['declared_tensor_peak_bytes'],
                             actual_device_peak_bytes=None,predicted_seconds=None),
                assumptions=[
                    '从官方 Qwen3 单层 FFN 的 gate/up 输出尺寸 M×F 开始，不包含两个投影或 down GEMM；输入与SiLU／乘法中间量BF16，最终声明1-byte量化存储。固定尺度视为已给定的标量，不包含动态amax／scale构建或元数据。',
                    '枚举链上所有连续分组，边界表示完整张量物化。分组内部逐元素计算、保留原中间舍入语义而不写全张量；这是可消除物化的条件模型，不断言特定后端已融合或能保持相同指令。',
                    '可选layout_permute为元素双射的物理重排，独立执行读写各一份BF16张量；融合时假设生产者直接按目标索引写出，无需中间全张量。未计地址计算／合并访问损失／tile和真实布局限制。',
                    '所有外部gate/up起初已存在，所有权允许在最后消费组结束释放。每组先分配独立输出，再释放不再使用的输入，无in-place别名；阶段内活跃张量联合大小决定声明峰值，不把各张量容量直接相加。',
                    '统计主张量接口载荷，不含固定标量、权重、allocator保留池、临时FP32寄存器／共享内存和同步。融合增加的局部scratch未推断，因此声明张量峰值不等于实际设备峰值。',
                    '每取消一个只跨单边界的中间张量X，少一次写回和读取2X；多个消费者或重计算会改变这个关系。本例无跨输出tile重读，量化融入GEMM的重读反例另算。',
                ])
