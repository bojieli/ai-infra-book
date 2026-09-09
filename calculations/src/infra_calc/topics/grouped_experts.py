"""Per-expert GEMM tiles and rank imbalance under a declared expert placement."""
from fractions import Fraction
from ..models import qwen3_moe
from ..sources import model_config, provenance
from ..units import positive_int
from .gemm_tiles import account


def calculate(model='qwen3-235b-a22b',tokens=128,participants=8,routing='balanced',
              placement='contiguous',counts=None,tile_m=64,tile_k=32,tile_n=128,replicas=None):
    inputs=locals().copy()
    for name,value in inputs.items():
        if name not in ('model','routing','placement','counts','replicas'):positive_int(value,name)
    c=model_config(model);qwen3_moe.validate(c)
    e,h,f=(c[key] for key in ('num_experts','hidden_size','moe_intermediate_size'))
    if e%participants:raise ValueError('Equal expert groups require divisible expert count')
    if placement not in ('contiguous','striped'):raise ValueError('Placement must be contiguous or striped')
    hist=qwen3_moe.routing_counts(tokens,e,c['num_experts_per_tok'],routing,counts)
    ranks=[dict(rank=i,active_experts=0,token_expert_tasks=0,valid_matrix_flops=0,
                padded_matrix_flops=0,weight_read_bytes=0,next_level_bytes=0,output_tiles=0)
           for i in range(participants)]
    owners={expert:[expert//(e//participants) if placement=='contiguous' else expert%participants]
            for expert in range(e)}
    replicas=[] if replicas is None else replicas
    if not isinstance(replicas,list):raise ValueError('Replicas must be a list of expert/rank records')
    extra_bytes=[0]*participants
    for replica in replicas:
        if not isinstance(replica,dict) or set(replica)!={'expert','rank'}:
            raise ValueError('Each replica requires expert and rank')
        expert,rank=replica['expert'],replica['rank']
        positive_int(expert,'replica expert',allow_zero=True);positive_int(rank,'replica rank',allow_zero=True)
        if expert>=e or rank>=participants:raise ValueError('Replica outside model or rank range')
        if rank in owners[expert]:raise ValueError('Duplicate physical expert on rank')
        owners[expert].append(rank);extra_bytes[rank]+=3*h*f*2
    experts=[];rerouted=0
    for expert,m in enumerate(hist):
        # Deterministic balanced splitting, remainder to earlier copies.
        quotient,remainder=divmod(m,len(owners[expert]))
        for copy_index,rank in enumerate(owners[expert]):
            physical_m=quotient+(copy_index<remainder)
            if copy_index:rerouted+=physical_m
            kernels=[]
            if physical_m:
                for name,k,n in [('gate',h,f),('up',h,f),('down',f,h)]:
                    kernels.append(dict(name=name,shape=[physical_m,k,n],**account(physical_m,k,n,tile_m,tile_k,tile_n)))
            row=dict(expert=expert,rank=rank,physical_copy=copy_index,tokens=physical_m,
                     padded_token_rows=((physical_m+tile_m-1)//tile_m)*tile_m if physical_m else 0,
                     kernels=kernels)
            experts.append(row)
            aggregate=ranks[rank]
            aggregate['active_experts']+=bool(physical_m)
            aggregate['token_expert_tasks']+=physical_m
            for kernel in kernels:
                aggregate['valid_matrix_flops']+=kernel['valid_matrix_flops']
                aggregate['padded_matrix_flops']+=kernel['fully_padded_matrix_flops']
                aggregate['weight_read_bytes']+=kernel['b_read_bytes']
                aggregate['next_level_bytes']+=kernel['next_level_bytes']
                aggregate['output_tiles']+=kernel['output_tiles']
    valid=sum(r['valid_matrix_flops'] for r in ranks)
    padded=sum(r['padded_matrix_flops'] for r in ranks)
    max_valid=max(r['valid_matrix_flops'] for r in ranks)
    max_padded=max(r['padded_matrix_flops'] for r in ranks)
    active=sum(bool(m) for m in hist)
    distinct_weights=active*3*h*f*2
    baseline=calculate(**{key:value for key,value in inputs.items() if key!='replicas'})['summary'] if replicas else None
    kv_unit=2*c['num_hidden_layers']*c['num_key_value_heads']*c['head_dim']*2
    return dict(schema_version=1,calculation='grouped-experts',scenario=inputs,sources=provenance(model),
                summary=dict(experts=e,active_experts=active,token_expert_tasks=sum(hist),
                             additional_physical_copies=len(replicas),
                             rerouted_token_expert_tasks=rerouted,
                             replica_weight_bytes=sum(extra_bytes),
                             replica_weight_bytes_per_rank=extra_bytes,
                             equivalent_full_model_kv_tokens_per_rank_floor=[n//kv_unit for n in extra_bytes],
                             baseline_max_rank_padded_flops=baseline['max_rank_padded_flops'] if baseline else max_padded,
                             max_rank_padded_flops_reduction=(baseline['max_rank_padded_flops']-max_padded) if baseline else 0,
                             added_padded_flops=padded-baseline['padded_matrix_flops'] if baseline else 0,
                             padded_token_rows=sum(r['padded_token_rows'] for r in experts),
                             valid_matrix_flops=valid,padded_matrix_flops=padded,
                             padding_work_ratio_exact=str(Fraction(padded,valid)),
                             max_rank_valid_flops=max_valid,max_rank_padded_flops=max_padded,
                             valid_rank_imbalance_exact=str(Fraction(max_valid*participants,valid)),
                             padded_rank_imbalance_exact=str(Fraction(max_padded*participants,padded)),
                             distinct_expert_weight_bytes=distinct_weights,
                             tile_schedule_weight_read_bytes=sum(r['weight_read_bytes'] for r in ranks),
                             tile_schedule_next_level_bytes=sum(r['next_level_bytes'] for r in ranks),
                             extra_weight_tile_reads_bytes=sum(r['weight_read_bytes'] for r in ranks)-distinct_weights),
                grouped_expert_rows=experts,grouped_rank_rows=ranks,
                assumptions=[
                    '官方Qwen MoE单层gate/up/down矩阵，BF16操作数与FP32 tile累加器。逻辑任务按官方top-k路由直方图，集中／均衡为教学输入，placement只改变专家归属不改变逻辑路由。',
                    '每个非空专家独立对M/K/N向上补齐指定tile，空专家不启动；完全执行padded tile给矩阵工作上界，真实kernel可跳过部分无效指令，不能当实测issued FLOPs。',
                    '复用gemm_tiles的output-stationary载荷：每输出tile跨K保留累加器，输出tile之间不保留输入，边界读取只计有效元素。权重随M块重读，A随N块重读；不把补齐FLOPs比例乘到有效字节上。',
                    '这是选定工作缓冲与下一层之间的访存模型，不自动等于HBM。gate/up分别读输入，中间结果物化，激活非线性、路由、dispatch/combine、数据重排、融合与缓存复用不在本子账。',
                    '基础placement等量放专家；replicas额外指定相同逻辑专家的rank副本，任务按商和余数均分，余数给原副本优先，每个任务仅执行一次。保留原权重，空闲新副本仍占容量；不是修改top-k。',
                    '新增权重按单层每物理副本计，KV等价仅将每rank新增容量除以官方全模型BF16 GQA每token容量取整，假定对照保存未切分完整KV，不证明实际EP布局或剩余容量。',
                    'rerouted任务仅表示从基础owner分给新副本的assignment；没有token源rank或身份，不能推断实际网络增减、去重或迁移时间。最忙工作减少也不保证速度提高，未计设备速度、kernel调度和通信。',
                ])
