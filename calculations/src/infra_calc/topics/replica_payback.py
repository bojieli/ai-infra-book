"""Cold expert replication amortization for a fixed, explicitly repeated batch."""
from fractions import Fraction as F
from ..units import positive_int
from . import grouped_experts
from .graph_execution import amortization


def calculate(workload=None,batches=128,compute_flops_per_second=100*10**12,
              interface_bytes_per_second=10**12,copy_bytes_per_second=25*10**9,
              copy_startup_ns=5000,extra_budget_bytes_per_rank=64*1024**2):
    inputs=locals().copy()
    for name,value in inputs.items():
        if name!='workload':positive_int(value,name,allow_zero=name in ('copy_startup_ns','extra_budget_bytes_per_rank'))
    workload=(dict(routing='concentrated',replicas=[dict(expert=i,rank=i+1) for i in range(7)])
              if workload is None else workload)
    if not isinstance(workload,dict):raise ValueError('Workload must be grouped-experts inputs')
    candidate=grouped_experts.calculate(**workload)
    baseline=grouped_experts.calculate(**{key:value for key,value in workload.items() if key!='replicas'})
    rows=[];times={}
    for name,result in [('baseline',baseline),('replicated',candidate)]:
        times[name]=F(0)
        for rank in result['grouped_rank_rows']:
            compute=F(rank['padded_matrix_flops']*10**9,compute_flops_per_second)
            interface=F(rank['next_level_bytes']*10**9,interface_bytes_per_second)
            service=max(compute,interface)
            rows.append(dict(deployment=name,rank=rank['rank'],compute_ns_exact=str(compute),
                             interface_ns_exact=str(interface),service_ns_exact=str(service)))
            times[name]=max(times[name],service)
    s=candidate['summary']
    setup=F(s['replica_weight_bytes']*10**9,copy_bytes_per_second)+s['additional_physical_copies']*copy_startup_ns
    saving=times['baseline']-times['replicated']
    threshold=amortization(setup,saving)
    feasible=all(n<=extra_budget_bytes_per_rank for n in s['replica_weight_bytes_per_rank'])
    old=batches*times['baseline'];new=setup+batches*times['replicated']
    return dict(schema_version=1,calculation='replica-payback',sources=candidate['sources'],
                scenario={**inputs,'workload':workload},
                summary=dict(batches=batches,replica_weight_bytes=s['replica_weight_bytes'],
                             extra_weight_bytes_per_rank=s['replica_weight_bytes_per_rank'],
                             capacity_feasible=feasible,
                             over_budget_ranks=[i for i,n in enumerate(s['replica_weight_bytes_per_rank']) if n>extra_budget_bytes_per_rank],
                             serialized_copy_setup_ns_exact=str(setup),
                             baseline_batch_ns_exact=str(times['baseline']),replicated_batch_ns_exact=str(times['replicated']),
                             per_batch_saving_ns_exact=str(saving),
                             algebraic_strict_payback_batches=threshold['strictly_faster_calls'],
                             feasible_strict_payback_batches=threshold['strictly_faster_calls'] if feasible else None,
                             baseline_window_ns_exact=str(old),replicated_window_ns_exact=str(new),
                             window_saving_ns_exact=str(old-new),
                             selected_deployment='replicated' if feasible and new<old else 'baseline',
                             selected_window_ns_exact=str(min(old,new) if feasible else old)),
                replica_service_rows=rows,
                assumptions=[
                    '复用grouped-experts同一层相同批路由、tile与副本分配；重复batches次完全相同工作，不代表实际生成中历史／路由变化。非均匀副本按各rank真实汇总，不从平均专家任务套时间。',
                    '每rank服务取max(全补齐矩阵/有效计算能力,指定tile接口bytes/有效带宽)，所有rank完成取max；这是一项教学资源模型，接口不自动等于HBM，不含通信、融合、kernel启动、实际缓存和其他层。',
                    '首次新增BF16权重经一条共享串行复制资源，每物理副本一次启动；源副本保留，不把网络两端重复计字节。复制在全部批次之前完成，未假设与服务重叠，未含转换和控制协议。',
                    'extra_budget_bytes_per_rank为扣除基础模型、KV、工作区后的净可用预算；逐rank检查新增权重，即使副本未命中也占内存。未验证整个真实部署，仅验证该输入预算下的增量。',
                    '严格回本要求setup+n*new<n*old；saving≤0时无回本，容量不足时可行回本为null。代数阈值与容量可行性分列，不把预期工作下降自动当部署收益。',
                    '有效供给是教学参数，实际EPLB须使用固定模型／后端／路由的阶段记录和负载稳定窗口，不据本数值断言真实迁移收益。',
                ])
