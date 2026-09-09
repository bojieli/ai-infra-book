"""Exact rational host-prepare / H2D / consume schedule with separate slot pools."""
from fractions import Fraction
from heapq import heappop,heappush
from ..sources import model_config,provenance
from ..models import qwen3
from ..units import positive_int
from .pipeline_schedule import peak_intervals


def calculate(model: str = 'qwen3-8b', tokens: int = 8192, blocks: int = 8,
              host_slots: int = 2, device_slots: int = 2,
              prepare_ns: int = 1000000, consume_ns: int = 4000000,
              bandwidth_bytes_per_second: int = 24*2**30) -> dict:
    for name,value in [('tokens',tokens),('blocks',blocks),('host_slots',host_slots),('device_slots',device_slots),
                       ('prepare_ns',prepare_ns),('consume_ns',consume_ns),('bandwidth_bytes_per_second',bandwidth_bytes_per_second)]:
        positive_int(value,name)
    c=model_config(model);qwen3.validate(c)
    if tokens>c['max_position_embeddings']:raise ValueError('Tokens exceed pinned context')
    size=2*tokens*c['hidden_size']
    prep=Fraction(prepare_ns,10**9);compute=Fraction(consume_ns,10**9)
    transfer=Fraction(size,bandwidth_bytes_per_second)
    host=[(Fraction(0),slot) for slot in range(host_slots)]
    device=[(Fraction(0),slot) for slot in range(device_slots)]
    prep_free=copy_free=compute_free=Fraction(0)
    rows=[];host_intervals=[];device_intervals=[]
    for block in range(blocks):
        host_free,hs=heappop(host)
        p0=max(prep_free,host_free);p1=p0+prep;prep_free=p1
        device_free,ds=heappop(device)
        d0=max(p1,copy_free,device_free);d1=d0+transfer;copy_free=d1
        c0=max(d1,compute_free);c1=c0+compute;compute_free=c1
        heappush(host,(d1,hs));heappush(device,(c1,ds))
        host_intervals.append((p0,d1,size));device_intervals.append((d0,c1,size))
        times=dict(prepare_start=p0,prepare_end=p1,copy_start=d0,copy_end=d1,consume_start=c0,consume_end=c1)
        rows.append(dict(block=block,host_slot=hs,device_slot=ds,
                         seconds={key:float(value) for key,value in times.items()},
                         exact_seconds={key:str(value) for key,value in times.items()}))
    serial=blocks*(prep+transfer+compute)
    ideal=prep+transfer+compute+(blocks-1)*max(prep,transfer,compute)
    return dict(schema_version=1,calculation='qwen-activation-host-transfer',model=model,
                scenario=dict(tokens=tokens,blocks=blocks,host_slots=host_slots,device_slots=device_slots,
                              prepare_ns=prepare_ns,consume_ns=consume_ns,bandwidth_bytes_per_second=bandwidth_bytes_per_second),
                sources=provenance(model),transfer_blocks=rows,
                summary=dict(block_bytes=size,total_h2d_bytes=blocks*size,
                             copy_seconds=float(transfer),copy_exact_seconds=str(transfer),
                             serial_seconds=float(serial),ideal_unconstrained_pipeline_seconds=float(ideal),
                             scheduled_finish_seconds=float(compute_free),scheduled_finish_exact_seconds=str(compute_free),
                             host_reserved_pool_bytes=host_slots*size,device_reserved_pool_bytes=device_slots*size,
                             host_live_peak_bytes=peak_intervals(host_intervals),device_live_peak_bytes=peak_intervals(device_intervals),
                             combined_live_peak_bytes=peak_intervals(host_intervals+device_intervals),
                             hypothetical_speedup=float(serial/compute_free),actual_gpu_seconds=None),
                assumptions=[
                    '对象为固定Qwen3 Dense的[tokens,hidden_size] BF16激活；不是全模型激活峰值。默认每块64MiB，准备1ms、单向有效H2D24GiB/s、消费4ms，均为教学供给，未引用硬件峰值或实测。',
                    '准备、H2D和消费各有一条串行通路，不同块可跨阶段重叠；同块消费必须等复制结束。主机槽从准备开始占用至DMA读完，设备槽从复制开始占用至消费结束。分别追踪槽编号和可复用时间。',
                    'FIFO提交，使用最早释放槽。服务时间按Fraction精确递推，JSON同时保存有理数秒和浮点显示，避免把每块复制时长先舍入后累加。',
                    '串行与无限缓冲流水公式仅是声明独立资源的对照；有限池可能使实际调度更长。增加slot不等于链路带宽增加，未模拟共享内存带宽争用、copy-engine限制变化或调度开销。',
                    '准备已包含本例必需的主机复制；初次分配／锁页、pageable staging、D2H与其它工作区另计。池预留与实际同时存活峰值分列，同刻释放后复用，不把两侧池当同一设备显存。',
                    '不由non_blocking或Async名称推断完成／重叠；本表时序是显式依赖模型，真实API事件与并发服务条件必须另测。',
                ])
