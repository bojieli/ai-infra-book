"""Exact fluid queue under external periodic demand; no congestion-control model."""
from collections import defaultdict
from fractions import Fraction
from math import lcm
from ..units import positive_int


def calculate(jobs=None,capacity_bytes_per_second=50*10**9,window_ns=None,
              initial_queue_bytes=0,buffer_bytes=None):
    jobs=jobs if jobs is not None else [dict(period_ns=100000000,on_ns=20000000,offset_ns=0,rate_bytes_per_second=40*10**9) for _ in range(2)]
    if not isinstance(jobs,list) or not jobs:raise ValueError('At least one periodic demand required')
    positive_int(capacity_bytes_per_second,'capacity_bytes_per_second')
    positive_int(initial_queue_bytes,'initial_queue_bytes',allow_zero=True)
    if buffer_bytes is not None:
        positive_int(buffer_bytes,'buffer_bytes',allow_zero=True)
        if initial_queue_bytes>buffer_bytes:raise ValueError('Initial queue exceeds buffer')
    for job in jobs:
        for name in ('period_ns','on_ns','rate_bytes_per_second'):positive_int(job[name],name)
        positive_int(job['offset_ns'],'offset_ns',allow_zero=True)
        if job['on_ns']>job['period_ns']:raise ValueError('on_ns cannot exceed period')
    window_ns=lcm(*(job['period_ns'] for job in jobs)) if window_ns is None else window_ns
    positive_int(window_ns,'window_ns')
    if sum(window_ns//j['period_ns']+2 for j in jobs)>100000:
        raise ValueError('Too many pulse intervals; select a shorter observation window')
    changes=defaultdict(int);changes[0]=0;changes[window_ns]=0
    for job in jobs:
        period=job['period_ns'];offset=job['offset_ns']%period
        for index in range(-1,(window_ns-offset)//period+1):
            start=index*period+offset;end=start+job['on_ns']
            a,b=max(0,start),min(window_ns,end)
            if a<b:
                changes[a]+=job['rate_bytes_per_second'];changes[b]-=job['rate_bytes_per_second']
    queue=peak=Fraction(initial_queue_bytes)
    arrived=served=excess=area=dropped=Fraction(0)
    rate=peak_rate=0;segments=[];last_drain=None
    points=sorted(changes)
    for start,end in zip(points,points[1:]):
        rate+=changes[start];peak_rate=max(peak_rate,rate)
        arrival_slope=Fraction(rate,10**9)
        net_slope=Fraction(rate-capacity_bytes_per_second,10**9)
        boundaries=[Fraction(start),Fraction(end)]
        if queue>0 and net_slope<0:
            drain=Fraction(start)+queue/(-net_slope)
            if start<drain<end:boundaries.insert(1,drain)
        if buffer_bytes is not None and queue<buffer_bytes and net_slope>0:
            fill=Fraction(start)+(buffer_bytes-queue)/net_slope
            if start<fill<end:boundaries.insert(1,fill)
        for a,b in zip(boundaries,boundaries[1:]):
            duration=b-a;before=queue
            queue=max(Fraction(0),before+net_slope*duration)
            loss=max(Fraction(0),queue-buffer_bytes) if buffer_bytes is not None else Fraction(0)
            queue-=loss
            dropped+=loss
            input_bytes=arrival_slope*duration
            output_bytes=before+input_bytes-queue-loss
            arrived+=input_bytes;served+=output_bytes
            excess+=max(Fraction(0),net_slope)*duration
            area+=(before+queue)*duration/2
            peak=max(peak,queue)
            if before>0 and queue==0:last_drain=b
            segments.append(dict(start_exact_ns=str(a),end_exact_ns=str(b),
                                 start_ns=float(a),end_ns=float(b),arrival_bytes_per_second=rate,
                                 queue_start_exact_bytes=str(before),queue_end_exact_bytes=str(queue),
                                 queue_start_bytes=float(before),queue_end_bytes=float(queue),
                                 arrived_exact_bytes=str(input_bytes),served_exact_bytes=str(output_bytes),
                                 dropped_exact_bytes=str(loss)))
    compatibility=1-excess/Fraction(capacity_bytes_per_second*window_ns,10**9)
    return dict(schema_version=1,calculation='periodic-fluid-queue',
                scenario=dict(jobs=jobs,capacity_bytes_per_second=capacity_bytes_per_second,window_ns=window_ns,
                              initial_queue_bytes=initial_queue_bytes,buffer_bytes=buffer_bytes),
                sources=[],queue_segments=segments,
                summary=dict(average_offered_bytes_per_second=float(arrived*10**9/window_ns),
                             peak_offered_bytes_per_second=peak_rate,arrived_exact_bytes=str(arrived),
                             served_exact_bytes=str(served),excess_demand_exact_bytes=str(excess),
                             dropped_exact_bytes=str(dropped),dropped_bytes=float(dropped),
                             peak_queue_exact_bytes=str(peak),peak_queue_bytes=float(peak),
                             final_queue_exact_bytes=str(queue),final_queue_bytes=float(queue),
                             queue_area_exact_byte_ns=str(area),mean_queue_bytes=float(area/window_ns),
                             compatibility_exact=str(compatibility),compatibility=float(compatibility),
                             last_drain_exact_ns=str(last_drain) if last_drain is not None else None,
                             stop_arrivals_final_drain_exact_ns=str(queue*10**9/capacity_bytes_per_second),
                             peak_queue_virtual_wait_exact_ns=str(peak*10**9/capacity_bytes_per_second),
                             actual_switch_queue_bytes=None,actual_job_completion_ns=None),
                assumptions=[
                    '默认两作业周期100ms、持续20ms、各40GB/s，共用50GB/s；均为外生教学到达速率，不是官方网卡规格或CASSINI实测。默认观察窗口为周期最小公倍数。',
                    '每个周期的on区间按半开区间处理，offset按周期取模，跨窗口起点的脉冲尾部会纳入；观察起点队列由initial_queue_bytes明确给定，默认零，不冒称周期稳态。',
                    '流体队列q=max(0,q+(arrival-capacity)*dt)，有积压时满速服务，无积压时不凭空发送。有限buffer_bytes将队列截断，多余流体字节记为丢弃；精确有理数在区间内部插入排空／填满时刻，再积分队列面积。该丢弃是流体近似，不是包级队列或拥塞控制实现。',
                    'excess_demand是正超额速率积分，peak_queue是带排空过程的实际分析积压，二者一般不同。compatibility=1-excess/(capacity*window)，可为负，不是概率。',
                    '末尾排空时间假设观察结束后停止所有新输入；周期流继续时不能直接使用。peak_queue/capacity只是流体FIFO虚拟等待上界口径，不是实际请求或训练步耗时。',
                    '不模拟DCQCN/PFC、通信依赖或GPU反馈改变发送时刻，不将600MB教学积压写成真实交换机队列；稳定错峰还需实际漂移与反馈校准。',
                ])
