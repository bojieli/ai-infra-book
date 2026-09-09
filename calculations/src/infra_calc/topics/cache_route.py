"""Queue/cache-ready dependencies and stale-hit risk for one fixed request."""
from fractions import Fraction as F
from ..models import forward
from ..schema import Scenario
from ..units import positive_int
from .state import calculate as state_calculate
from .pd_pool import exact_rate


def calculate(model='qwen3-8b',prefix_tokens=8192,suffix_tokens=256,
              queue_a_ns=250000000,queue_b_ns=20000000,full_compute_ns=180000000,
              warm_compute_ns=10000000,lookup_ns=10000000,
              remote_bytes_per_second=5*10**9,host_gpu_bytes_per_second=25*10**9,
              hit_probability='9/10',slo_ns=220000000,retrieval_after_queue=False,
              requests_per_second=16):
    inputs=locals().copy()
    for name,value in inputs.items():
        if name not in ('model','hit_probability','retrieval_after_queue'):
            positive_int(value,name,allow_zero=name in ('queue_a_ns','queue_b_ns','lookup_ns','requests_per_second'))
    if not isinstance(retrieval_after_queue,bool):raise ValueError('retrieval_after_queue must be boolean')
    if warm_compute_ns>=full_compute_ns:raise ValueError('This scenario requires a positive cache computation saving')
    p=exact_rate(hit_probability,'hit_probability',True)
    if p>1:raise ValueError('Hit probability exceeds one')
    state=state_calculate(model,prefix_tokens)
    size=state['summary']['resident_bytes']
    cold=forward(model,Scenario(tokens=prefix_tokens+suffix_tokens,output_head='last'))
    warm=forward(model,Scenario(history=prefix_tokens,tokens=suffix_tokens,output_head='last'))
    h2d=F(size*10**9,host_gpu_bytes_per_second)
    network=F(size*10**9,remote_bytes_per_second)
    remote_ready=lookup_ns+network+h2d
    def finish(queue,ready):
        return queue+ready+warm_compute_ns if retrieval_after_queue else max(F(queue),ready)+warm_compute_ns
    a_hit=F(queue_a_ns+warm_compute_ns)
    a_miss=F(queue_a_ns+full_compute_ns)
    b_cold=F(queue_b_ns+full_compute_ns)
    remote=finish(queue_b_ns,remote_ready)
    cpu=finish(queue_a_ns,h2d)
    mean=p*a_hit+(1-p)*a_miss
    p99=a_hit if p>=F(99,100) else a_miss
    passes=(p if a_hit<=slo_ns else 0)+(1-p if a_miss<=slo_ns else 0)
    # Remote path must have completed by the remaining compute-saving window.
    window=(b_cold-warm_compute_ns-queue_b_ns if retrieval_after_queue else b_cold-warm_compute_ns)
    residual=window-lookup_ns-h2d
    threshold=F(size*10**9)/residual if residual>0 else None
    prob_threshold=(a_miss-b_cold)/(a_miss-a_hit)
    rows=[dict(path='A valid HBM',queue_ns=queue_a_ns,ready_ns_exact='0',finish_ns_exact=str(a_hit)),
          dict(path='B recompute',queue_ns=queue_b_ns,ready_ns_exact='0',finish_ns_exact=str(b_cold)),
          dict(path='B remote through host',queue_ns=queue_b_ns,ready_ns_exact=str(remote_ready),finish_ns_exact=str(remote)),
          dict(path='A CPU copy survives',queue_ns=queue_a_ns,ready_ns_exact=str(h2d),finish_ns_exact=str(cpu))]
    return dict(schema_version=1,calculation='cache-route',scenario=inputs,sources=cold['sources'],
                summary=dict(prefix_state_bytes=size,cold_matrix_flops=cold['summary']['matrix_flops'],
                             warm_matrix_flops=warm['summary']['matrix_flops'],
                             saved_matrix_flops=cold['summary']['matrix_flops']-warm['summary']['matrix_flops'],
                             remote_transfer_ns_exact=str(network),host_gpu_transfer_ns_exact=str(h2d),
                             remote_equal_recompute_bytes_per_second_exact=str(threshold) if threshold else None,
                             remote_payload_demand_bytes_per_second=size*requests_per_second,
                             remote_payload_demand_strictly_below_bandwidth=size*requests_per_second<remote_bytes_per_second,
                             a_valid_hit_ns_exact=str(a_hit),a_all_tiers_miss_ns_exact=str(a_miss),
                             a_expected_ns_exact=str(mean),a_p99_ns_exact=str(p99),
                             a_slo_pass_probability_exact=str(passes),
                             a_mean_better_than_b=mean<b_cold,
                             a_p99_passes_slo=p99<=slo_ns,
                             strict_mean_hit_probability_threshold_exact=str(prob_threshold),
                             fastest_known_valid_path=min(rows,key=lambda row:F(row['finish_ns_exact']))['path']),
                cache_route_paths=rows,
                assumptions=[
                    '同一官方Qwen前缀和新suffix的矩阵工作独立复算；full/warm计算时间是教学输入，不由FLOPs比例外推。只预测首token，不是完整生成或任务质量。',
                    '远端整份状态先到host，再经H2D到GPU，lookup和两段复制串行；默认可与GPU队列等待重叠，完成为max(queue,ready)+warm。retrieval_after_queue则等待queue后才开始取回，不能混用两种依赖。',
                    'ready字段是取回自身耗时；默认从到达起算，after_queue时从GPU可执行时刻起算。HBM已命中与CPU副本仍在是分别声明的有效状态，不把GPU淘汰当作全部失效。',
                    'A失效概率采用两点分布：有效HBM命中或全部层级失效重算，无额外失败探测成本。p是校准输入而非框架评分；排队与淘汰相关性、部分前缀命中及事件恢复未模拟。',
                    'p99按最小累计概率达到99%的值，等号保留。平均优于B不保证尾延迟SLO；概率阈值为未裁剪代数值，须与0≤p≤1共同判断。',
                    '带宽和请求率是有效服务教学假设；共享链路仅检查payload需求，未建队列。单请求有利不保证持续服务，需求严格低于带宽也不证明SLO。',
                ])
