"""Finite outstanding credits held until periodic completion consumption."""
from heapq import heappop, heappush
from ..sources import model_config, provenance
from ..units import positive_int
from .pipeline_schedule import peak_intervals


def calculate(model='qwen3-8b',tokens=1,operations=16,slots=8,
              submit_interval_ns=1000,transfer_latency_ns=5000,
              poll_interval_ns=20000,poll_batch=4,completion_entry_bytes=64):
    inputs=locals().copy()
    for name,value in inputs.items():
        if name!='model':positive_int(value,name)
    if operations>100000 or slots>100000:
        raise ValueError('Limit operations and slots to 100000')
    config=model_config(model)
    payload=2*tokens*config['hidden_size']
    free=[(0,index) for index in range(slots)]
    last_submit=-submit_interval_ns
    last_poll=0;used_at_poll=0
    rows=[]
    for index in range(operations):
        available,slot=heappop(free)
        offered=index*submit_interval_ns
        submit=max(offered,last_submit+submit_interval_ns,available)
        complete=submit+transfer_latency_ns
        eligible=max(poll_interval_ns,((complete+poll_interval_ns-1)//poll_interval_ns)*poll_interval_ns)
        consume=max(eligible,last_poll)
        if consume>last_poll:
            used_at_poll=0
        elif used_at_poll==poll_batch:
            consume+=poll_interval_ns
            used_at_poll=0
        used_at_poll+=1;last_poll=consume;last_submit=submit
        heappush(free,(consume,slot))
        rows.append(dict(operation=index,slot=slot,offered_ns=offered,submit_ns=submit,
                         transfer_complete_ns=complete,completion_consumed_ns=consume,
                         submission_delay_ns=submit-offered,reclaim_wait_ns=consume-complete))
    outstanding=[(row['submit_ns'],row['completion_consumed_ns'],1) for row in rows]
    completed=[(row['transfer_complete_ns'],row['completion_consumed_ns'],1) for row in rows]
    in_flight=[(row['submit_ns'],row['transfer_complete_ns'],1) for row in rows]
    return dict(schema_version=1,calculation='completion-reclaim',scenario=inputs,
                sources=provenance(model),completion_operations=rows,
                summary=dict(payload_bytes_per_operation=payload,total_payload_bytes=payload*operations,
                             reserved_slot_payload_bytes=slots*payload,
                             peak_outstanding=peak_intervals(outstanding),
                             peak_in_flight=peak_intervals(in_flight),
                             peak_unconsumed_completions=peak_intervals(completed),
                             peak_retained_completion_bytes=peak_intervals(completed)*completion_entry_bytes,
                             last_submit_ns=rows[-1]['submit_ns'],
                             all_transfers_complete_ns=rows[-1]['transfer_complete_ns'],
                             all_slots_reclaimed_ns=rows[-1]['completion_consumed_ns'],
                             total_submission_delay_ns=sum(row['submission_delay_ns'] for row in rows),
                             total_reclaim_wait_ns=sum(row['reclaim_wait_ns'] for row in rows),
                             max_submission_delay_ns=max(row['submission_delay_ns'] for row in rows)),
                assumptions=[
                    '每操作载荷为官方BF16 [tokens,H]；间隔、固定传输延迟、轮询周期、每次消费条数及64-byte完成项均为教学输入，不是NIC/QP规格或测量。',
                    '本模型一个credit同时覆盖提交后在途与已完成未消费阶段，消费完成项后才回收。不是所有真实队列都采用此生命周期；传输完成不代表本例槽位可复用。固定延迟使完成顺序等于提交顺序。',
                    '最早在poll_interval_ns时轮询，之后固定周期，每次至多poll_batch条，FIFO消费。传输在同刻完成可先被轮询消费，再用释放槽位提交；半开区间峰值不包含同刻入口瞬态。',
                    '轮询消费本身视为瞬时，每次条数限制表示给定服务预算；提交有最小间隔。各操作传输可并行，不另建共享带宽、CQ独立容量、丢弃、地址转换或异常恢复。',
                    'slots*payload是预留缓冲预算；完成项为独立元数据，不与payload混淆。各操作等待之和是操作时间积分，不能相加到墙钟；传输完毕和全部回收时刻分列。',
                ])
