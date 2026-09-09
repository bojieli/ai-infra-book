"""Explicit feedback delay and post-feedback offered rate over a finite fluid buffer."""
from fractions import Fraction
from ..units import positive_int
from .periodic_queue import calculate as periodic_queue


def calculate(offered_bytes_per_second=80*10**9,capacity_bytes_per_second=50*10**9,
              reduced_bytes_per_second=40*10**9,feedback_ns=20000,after_feedback_ns=100000,
              initial_queue_bytes=262144,buffer_bytes=1048576):
    inputs=locals().copy()
    for name,value in inputs.items():
        if name=='buffer_bytes' and value is None:continue
        positive_int(value,name,allow_zero=name in ('initial_queue_bytes','buffer_bytes','reduced_bytes_per_second'))
    window=feedback_ns+after_feedback_ns
    jobs=[dict(period_ns=window,on_ns=feedback_ns,offset_ns=0,rate_bytes_per_second=offered_bytes_per_second)]
    if reduced_bytes_per_second:
        jobs.append(dict(period_ns=window,on_ns=after_feedback_ns,offset_ns=feedback_ns,rate_bytes_per_second=reduced_bytes_per_second))
    result=periodic_queue(jobs=jobs,capacity_bytes_per_second=capacity_bytes_per_second,
                          window_ns=window,initial_queue_bytes=initial_queue_bytes,buffer_bytes=buffer_bytes)
    at_feedback=next(row for row in result['queue_segments'] if Fraction(row['end_exact_ns'])==feedback_ns)
    unbounded=max(Fraction(0),initial_queue_bytes+Fraction((offered_bytes_per_second-capacity_bytes_per_second)*feedback_ns,10**9))
    result['calculation']='feedback-fluid-queue';result['scenario']=inputs
    result['summary'].update(feedback_applied_ns=feedback_ns,
                             unbounded_queue_at_feedback_exact_bytes=str(unbounded),
                             bounded_queue_at_feedback_exact_bytes=at_feedback['queue_end_exact_bytes'],
                             after_feedback_rate_below_capacity=reduced_bytes_per_second<capacity_bytes_per_second)
    result['assumptions'][0]='反馈教学例：到达80GB/s、出口50GB/s，20us后明确降低到40GB/s，再观察100us；默认初始256KiB、缓冲1MiB。反馈时间与速率是输入，不是DCQCN/PFC算法生成或硬件实测。'
    result['assumptions'][1]='观察起点积压明确给定；反馈时刻切换到给定速率，观察窗口结束后不自动重复反馈周期。'
    result['assumptions'].append('只观察一次反馈和指定后续窗口，不模拟多轮控制、ECN阈值、PFC暂停、丢弃数据重传或任务完成。减到出口速率只停止增长，不自动清空已有积压；减到出口以下才有余量排空。')
    return result
