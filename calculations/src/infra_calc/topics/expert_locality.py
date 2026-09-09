"""Official MoE expert reuse with explicit per-assignment activation transfers."""
from fractions import Fraction as F
from ..models import qwen3_moe
from ..sources import model_config, provenance
from ..units import positive_int


def reuse_regions(cpu_per_token, cpu_weight_read, gpu_per_token, gpu_weight_read,
                  activation_per_token, cpu_startup, copied_weight_and_startup):
    """Partition all positive integer row counts using exact affine breakpoints.

CPU = activation*m + cpu_startup + max(cpu_per_token*m, cpu_weight_read).
GPU = copied_weight_and_startup + max(gpu_per_token*m, gpu_weight_read).
No finite scan limit is used; the last interval extends to infinity.
    """
    a,b,c,d,x,y,z=map(F,(cpu_per_token,cpu_weight_read,gpu_per_token,
                        gpu_weight_read,activation_per_token,cpu_startup,
                        copied_weight_and_startup))
    if min(a,b,c,d)<=0 or min(x,y,z)<0:
        raise ValueError('Positive compute/read and nonnegative transfer costs required')
    # A branch switches just after its floor knee; exact equality is harmless.
    starts=sorted({1,max(1,int(b//a)+1),max(1,int(d//c)+1)})
    boundaries=set(starts)
    for index,lo in enumerate(starts):
        hi=starts[index+1]-1 if index+1<len(starts) else None
        cpu_slope=x+(a if a*lo>=b else 0)
        cpu_intercept=y+(0 if a*lo>=b else b)
        gpu_slope=c if c*lo>=d else 0
        gpu_intercept=z+(0 if c*lo>=d else d)
        slope=gpu_slope-cpu_slope
        intercept=gpu_intercept-cpu_intercept
        if slope:
            root=-intercept/slope
            # Include both sides and an exact integer equality as its own cell.
            for point in (int(root//1),int(root//1)+1):
                if point>=lo and (hi is None or point<=hi):boundaries.add(point)
    points=sorted(boundaries);regions=[]
    for index,lo in enumerate(points):
        hi=points[index+1]-1 if index+1<len(points) else None
        cpu=x*lo+y+max(a*lo,b)
        gpu=z+max(c*lo,d)
        winner='cpu' if cpu<gpu else 'copy-to-gpu' if gpu<cpu else 'equal'
        if regions and regions[-1]['winner']==winner:
            regions[-1]['max_tokens_per_expert']=hi
        else:
            regions.append(dict(min_tokens_per_expert=lo,max_tokens_per_expert=hi,winner=winner))
    return regions


def calculate(model='qwen3-235b-a22b',tokens=128,resident_experts=32,routing='balanced',
              counts=None,cpu_flops_per_second=2*10**12,gpu_flops_per_second=100*10**12,
              dram_bytes_per_second=200*10**9,hbm_bytes_per_second=10**12,
              link_bytes_per_second=25*10**9,startup_ns=5000):
    inputs=locals().copy()
    for name,value in inputs.items():
        if name not in ('model','routing','counts'):
            positive_int(value,name,allow_zero=name in ('resident_experts','startup_ns'))
    c=model_config(model);qwen3_moe.validate(c)
    e,k,h,f=(c[key] for key in ('num_experts','num_experts_per_tok','hidden_size','moe_intermediate_size'))
    if resident_experts>e:raise ValueError('Resident expert count exceeds model')
    histogram=qwen3_moe.routing_counts(tokens,e,k,routing,counts)
    weight=3*h*f*2
    per_task_flops=6*h*f
    rows=[]
    for expert,m in enumerate(histogram):
        rows.append(dict(expert=expert,tokens=m,gpu_resident=expert<resident_experts,
                         gate_up_shape=[m,h,f],down_shape=[m,f,h],
                         matrix_flops=m*per_task_flops,weight_read_bytes=weight if m else 0))
    remote=[row for row in rows if not row['gpu_resident']]
    active=sum(row['tokens']>0 for row in remote)
    tasks=sum(row['tokens'] for row in remote)
    weights=active*weight;flops=tasks*per_task_flops
    # No token identity in a histogram: explicitly use per-assignment dispatch.
    activations=tasks*h*2
    cpu_compute=F(flops*10**9,cpu_flops_per_second)
    cpu_read=F(weights*10**9,dram_bytes_per_second)
    gpu_compute=F(flops*10**9,gpu_flops_per_second)
    gpu_read=F(weights*10**9,hbm_bytes_per_second)
    activation_link=F(2*activations*10**9,link_bytes_per_second)+2*active*startup_ns
    weight_link=F(weights*10**9,link_bytes_per_second)+active*startup_ns
    cpu_time=activation_link+max(cpu_compute,cpu_read)
    offload_time=weight_link+max(gpu_compute,gpu_read)
    resident_time=max(gpu_compute,gpu_read)
    reuse=reuse_regions(F(per_task_flops*10**9,cpu_flops_per_second),
                        F(weight*10**9,dram_bytes_per_second),
                        F(per_task_flops*10**9,gpu_flops_per_second),
                        F(weight*10**9,hbm_bytes_per_second),
                        F(4*h*10**9,link_bytes_per_second),2*startup_ns,
                        F(weight*10**9,link_bytes_per_second)+startup_ns)
    paths=[dict(name='CPU local experts',link_bytes=2*activations,launches=2*active,
                memory_weight_bytes=weights,matrix_flops=flops,service_ns_exact=str(cpu_time)),
           dict(name='copy weights to GPU',link_bytes=weights,launches=active,
                memory_weight_bytes=weights,matrix_flops=flops,service_ns_exact=str(offload_time)),
           dict(name='GPU resident reference',link_bytes=0,launches=0,
                memory_weight_bytes=weights,matrix_flops=flops,service_ns_exact=str(resident_time))]
    return dict(schema_version=1,calculation='expert-locality',scenario=inputs,sources=provenance(model),
                summary=dict(experts=e,top_k=k,expert_bf16_weight_bytes=weight,
                             resident_expert_weight_bytes_per_layer=resident_experts*weight,
                             resident_expert_weight_bytes_all_layers=resident_experts*weight*c['num_hidden_layers'],
                             remote_active_experts=active,remote_token_expert_tasks=tasks,
                             remote_distinct_weight_bytes=weights,remote_matrix_flops=flops,
                             per_assignment_activation_roundtrip_bytes=2*activations,
                             remote_tasks_per_active_expert_exact=str(F(tasks,active)) if active else None,
                             cpu_matrix_ns_exact=str(cpu_compute),cpu_weight_read_ns_exact=str(cpu_read),
                             cpu_dominant_resource='compute' if cpu_compute>=cpu_read else 'weight-memory',
                             cpu_service_ns_exact=str(cpu_time),weight_copy_service_ns_exact=str(offload_time),
                             gpu_resident_service_ns_exact=str(resident_time),
                             cpu_lower_than_weight_copy_in_declared_model=cpu_time<offload_time,
                             extra_gpu_weights_for_all_experts_per_layer=(e-resident_experts)*weight),
                locality_experts=rows,locality_paths=paths,locality_reuse_regions=reuse,
                reuse_knees=dict(cpu_equal_compute_weight_tokens_exact=str(F(weight*cpu_flops_per_second,per_task_flops*dram_bytes_per_second)),
                                 gpu_equal_compute_weight_tokens_exact=str(F(weight*gpu_flops_per_second,per_task_flops*hbm_bytes_per_second))),
                assumptions=[
                    '复用获益区间覆盖每专家m≥1的全部整数，精确分段解两侧max的转折与等时根，末段null上界表示无穷。比较同一个非驻留专家一次BF16权重搬运和m次任务；均匀专家批可同比放大，非均匀批不能按平均m套逐专家结论。',
                    '官方Qwen MoE单层三个BF16专家矩阵，resident_experts表示ID从0开始的固定前缀集合。每层驻留字节可乘层数，但本批路由和时间仅为单层，不冒充94层实测。',
                    '路由直方图来自显式输入或教学balanced/concentrated；每批每个非空专家权重只读一次，矩阵任务按token—expert数量，不用总任务数重复搬同一权重。',
                    '只比较非驻留专家子账。GPU常驻专家可并行的工作、attention、router、归约和完整请求不在本结果；全GPU参考需要额外权重容量，未作可行性保证。',
                    'CPU每个非空专家发送一批输入并返回一批结果，激活均BF16，每个token—expert任务各算一份；直方图没有token身份，不推断跨专家去重。每方向每非空专家一次启动。',
                    '时长为明确教学路径：CPU先交接激活再计max(矩阵服务,理想权重读取)，搬权重路径先复制再计GPU同类服务；按资源聚合下界，不含各专家不均衡、padding、小矩阵效率、激活访存、格式转换、NUMA和内部依赖。',
                    '计算与带宽均为有效服务假设，不引用CPU AMX或GPU宣传值。BF16权重不代表特定KTransformers量化格式，不能据此声称CPU/GPU实际胜负。',
                ])
