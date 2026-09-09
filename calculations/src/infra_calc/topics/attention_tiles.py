"""One Qwen head: declared mixed-format buffer, scanning traffic and tile work."""
from ..sources import model_config,provenance
from ..models import qwen3
from ..units import positive_int,ceil_div


def calculate(model: str = 'qwen3-8b', tokens: int = 8192,
              capacity_bytes: int = 131072, kv_blocks: list | None = None,
              kv_slots: int = 1, causal: bool = False) -> dict:
    c=model_config(model);qwen3.validate(c)
    for name,value in [('tokens',tokens),('capacity_bytes',capacity_bytes),('kv_slots',kv_slots)]:positive_int(value,name)
    if kv_slots not in (1,2):raise ValueError('kv_slots must be 1 or 2')
    if not isinstance(causal,bool):raise ValueError('causal must be boolean')
    if tokens>c['max_position_embeddings']:raise ValueError('Tokens exceed official context')
    choices=[1,64,128] if kv_blocks is None else kv_blocks
    if not isinstance(choices,list) or not choices:raise ValueError('kv_blocks must be nonempty')
    n,d=tokens,c['head_dim'];rows=[]
    for b in choices:
        positive_int(b,'KV block')
        fixed=2*b*d*kv_slots
        per_query=6*d+4*b+12
        a=min(n,(capacity_bytes-fixed)//per_query)
        if a<1:
            rows.append(dict(kv_block=b,feasible=False,query_block=None));continue
        components=dict(q_bf16=2*a*d,kv_bf16_slots=fixed,score_probability_fp32=4*a*b,
                        partial_output_fp32=4*a*d,row_statistics_fp32=12*a)
        qblocks=ceil_div(n,a);kblocks=ceil_div(n,b)
        visits=tile_pairs=kv_read=0
        for qstart in range(0,n,a):
            qend=min(qstart+a,n);height=qend-qstart
            scanned_blocks=ceil_div(qend,b) if causal else kblocks
            covered=min(n,scanned_blocks*b)
            visits+=scanned_blocks
            kv_read+=4*covered*d
            tile_pairs+=height*covered
        valid_pairs=n*(n+1)//2 if causal else n*n
        # Per-row updates skip K blocks with no visible keys; first block has no old U to rescale.
        row_updates=sum(ceil_div(i+1,b) for i in range(n)) if causal else n*kblocks
        rows.append(dict(kv_block=b,feasible=True,query_block=a,query_blocks=qblocks,kv_block_pairs=visits,
                         working_components=components,reserved_working_bytes=sum(components.values()),
                         q_read_bytes=2*n*d,o_write_bytes=2*n*d,kv_read_bytes=kv_read,
                         interface_bytes=4*n*d+kv_read,valid_matrix_flops=4*valid_pairs*d,
                         rectangular_visited_tile_matrix_flops=4*tile_pairs*d,
                         fully_padded_tile_matrix_flops=4*visits*a*b*d,
                         row_state_updates=row_updates,old_output_scale_multiplications=(row_updates-n)*d))
    feasible=[r for r in rows if r['feasible']]
    best=min(feasible,key=lambda r:r['interface_bytes']) if feasible else None
    return dict(schema_version=1,calculation='qwen-single-head-attention-tiles',model=model,
                scenario=dict(tokens=tokens,capacity_bytes=capacity_bytes,kv_blocks=choices,kv_slots=kv_slots,causal=causal),
                sources=provenance(model),attention_tile_rows=rows,
                summary=dict(head_dim=d,one_read_write_qkvo_bytes=8*n*d,
                             separate_fp32_score_and_probability_bytes=8*n*n,
                             separate_score_probability_read_write_bytes=16*n*n,
                             valid_matrix_flops=4*(n*(n+1)//2 if causal else n*n)*d,
                             feasible_candidates=len(feasible),
                             best_enumerated_kv_block=None if best is None else best['kv_block'],
                             best_enumerated_interface_bytes=None if best is None else best['interface_bytes'],
                             measured_hbm_bytes=None,predicted_kernel_seconds=None),
                assumptions=[
                    '固定Qwen3单query head及对应K/V head，head_dim来自官方配置；默认非因果完整注意力隔离分块问题，不冒充Qwen整层因果prefill。GQA跨query head复用未模拟，不能把KV接口简单乘query头数当整卡HBM。',
                    '外层保留a行Q/部分O，内层扫描b行K/V。Q/K/V及最终O为BF16，S/P与部分O和三个统计向量为FP32；K/V单槽顺序复用，S/P共用槽。预算=2ad+2bd*kv_slots+4ab+4ad+12a，取该候选最大可行整数a。',
                    'kv_slots=2为K/V同时驻留的容量变体，不免费沿用单槽a，也不假设完整预取双缓冲已经实现。容量是抽象快速缓冲，未合并某GPU的寄存器／共享内存／缓存规格。地址、对齐、临时值、流水scratch和训练LSE不在预算内。',
                    '每个Q块重新读取所需K/V，Q一次读取O一次写回。因果模式跳过全不可见K块，边界块读入实际完整行；有效因果FLOPs、被访问矩形tile工作及完整padding工作分列。',
                    '每行每个有有效key的K块更新一次状态；非首有效块无条件缩放一次旧输出，按d个乘法计。跳过不变尺度、优化指令或不同算法会改计数；块对更新次数不是主机kernel launch。',
                    '接口在工作缓冲与下一层之间，可能由L2服务，不特指HBM。最小字节仅为给定候选和排布，不代表全局下界或性能最佳；更小b的循环／缩放开销单列。',
                ])
