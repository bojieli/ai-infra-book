"""Declared independent matrix/vector workers: operator barrier versus tile readiness."""
from fractions import Fraction
from ..sources import model_config,provenance
from ..models import qwen3
from ..units import positive_int
from .pipeline_schedule import peak_intervals


def calculate(model='qwen3-8b',tokens=512,tile_rows=64,
              matrix_flops_per_second=200*10**12,activation_elements_per_second=20*10**9,
              host_launch_ns=5000,task_dispatch_ns=500,event_publish_ns=200):
    inputs=locals().copy()
    for name,value in inputs.items():
        if name!='model':positive_int(value,name,allow_zero=name in ('host_launch_ns','task_dispatch_ns','event_publish_ns'))
    config=model_config(model);qwen3.validate(config)
    if tokens>config['max_position_embeddings']:raise ValueError('Tokens exceed pinned context')
    h,f=config['hidden_size'],config['intermediate_size']
    launch=Fraction(host_launch_ns)
    task_cost=Fraction(task_dispatch_ns+event_publish_ns)
    matrix_total=Fraction(2*tokens*h*f*10**9,matrix_flops_per_second)
    vector_total=Fraction(tokens*f*10**9,activation_elements_per_second)
    # Coarse kernels serialize the complete producer before the consumer.
    barrier_finish=2*launch+matrix_total+vector_total
    matrix_free=vector_free=launch
    rows=[];intermediate=[]
    for index,start in enumerate(range(0,tokens,tile_rows)):
        m=min(tile_rows,tokens-start)
        matrix_work=Fraction(2*m*h*f*10**9,matrix_flops_per_second)
        vector_work=Fraction(m*f*10**9,activation_elements_per_second)
        producer_start=matrix_free
        producer_done=producer_start+task_cost+matrix_work
        consumer_start=max(vector_free,producer_done)
        consumer_done=consumer_start+task_cost+vector_work
        matrix_free=producer_done;vector_free=consumer_done
        size=2*m*f
        intermediate.append((producer_start,consumer_done,size))
        times=dict(producer_start=producer_start,producer_ready=producer_done,
                   consumer_start=consumer_start,consumer_done=consumer_done)
        rows.append(dict(tile=index,rows=m,row_start=start,intermediate_bytes=size,
                         matrix_flops=2*m*h*f,activation_elements=m*f,
                         exact_ns={k:str(v) for k,v in times.items()},
                         nanoseconds={k:float(v) for k,v in times.items()}))
    n=len(rows);finish=vector_free
    return dict(schema_version=1,calculation='qwen-persistent-tasks',model=model,
                scenario={k:v for k,v in inputs.items() if k!='model'},sources=provenance(model),
                persistent_tiles=rows,
                summary=dict(tiles=n,matrix_flops=2*tokens*h*f,activation_elements=tokens*f,
                             coarse_host_launches=2,persistent_host_launches=1,
                             persistent_device_tasks=2*n,completion_event_publications=2*n,
                             intertask_dependency_edges=n,event_poll_iterations=None,
                             task_dispatch_total_ns=2*n*task_dispatch_ns,event_publish_total_ns=2*n*event_publish_ns,
                             intermediate_total_bytes=2*tokens*f,
                             intermediate_write_read_bytes=4*tokens*f,
                             persistent_intermediate_live_peak_bytes=peak_intervals(intermediate),
                             barrier_finish_exact_ns=str(barrier_finish),barrier_finish_ns=float(barrier_finish),
                             persistent_finish_exact_ns=str(finish),persistent_finish_ns=float(finish),
                             hypothetical_speedup=float(barrier_finish/finish),actual_gpu_seconds=None),
                assumptions=[
                    '官方Qwen Dense单支up投影[M,H]×[H,F]接SiLU，按行切块无跨块归约；不是完整FFN，也不把down投影所需全K依赖忽略。SiLU按元素服务率输入，不将其冒充矩阵FLOPs。',
                    '生产为一条串行矩阵worker，消费为一条串行向量worker，声明资源独立且可并行。默认200TFLOP/s、20G元素/s、host launch5us、设备任务分派0.5us和完成事件发布0.2us均为教学输入，未借用官方峰值或MPK实测。',
                    '粗粒度两次主机launch，完整生产结束才启动消费；persistent一次launch，每块两个设备任务、各一次完成事件发布和一条生产到消费依赖。等待由ready时间满足，轮询次数、原子争用和事件表字节未假造。',
                    '每任务分派及事件发布占用其worker，与同worker后续工作串行；不同worker可重叠，因此元数据总服务量不直接全部加到关键路径。尾块按实际行数重新算工作，但仍各支付一次固定任务开销。',
                    '中间块从生产任务开始保留至消费完成，报告实际同时存活上界；本表未施加有限槽预算，不保证某个片上池可容纳。没有消除中间张量读写，输入／最终输出／权重／队列及库scratch另算。',
                    '实际GPU若矩阵／向量争用同一SM、带宽或寄存器，必须另给并发服务率及可驻留证据。单次主机提交不等于只做一次设备工作，本模型不声称实现了MPK。',
                ])
