"""Finite snapshot buffers, serialized staging/upload, and durable recovery points."""
from fractions import Fraction
from heapq import heappop, heappush

from ..models import qwen3, qwen3_moe
from ..sources import model_config, provenance
from ..units import positive_int
from .pipeline_schedule import peak_intervals


def calculate(model='qwen3-8b', payload_bytes=None, snapshots=6, first_capture_ns=20*10**9,
              interval_ns=10*10**9, staging_ns=500000000, upload_bytes_per_second=8*10**9,
              buffer_slots=2, durability_delay_ns=0, failure_ns=50*10**9):
    inputs = dict(model=model, payload_bytes=payload_bytes, snapshots=snapshots,
                  first_capture_ns=first_capture_ns, interval_ns=interval_ns, staging_ns=staging_ns,
                  upload_bytes_per_second=upload_bytes_per_second, buffer_slots=buffer_slots,
                  durability_delay_ns=durability_delay_ns, failure_ns=failure_ns)
    for name, value in inputs.items():
        if name not in ('model', 'payload_bytes'):
            positive_int(value, name, allow_zero=name in ('first_capture_ns','durability_delay_ns','failure_ns'))
    config = model_config(model)
    adapter = qwen3_moe if config['model_type'] == 'qwen3_moe' else qwen3
    parameters = sum(w.parameters for w in adapter.weights(config))
    size = 14*parameters if payload_bytes is None else payload_bytes
    positive_int(size, 'payload_bytes')
    interval, staging = Fraction(interval_ns,10**9), Fraction(staging_ns,10**9)
    service = Fraction(size,upload_bytes_per_second)
    durability = Fraction(durability_delay_ns,10**9)
    slots = [(Fraction(0), rank) for rank in range(buffer_slots)]
    stage_free = writer_free = Fraction(0)
    rows, lifetimes, pauses = [], [], []
    for index in range(snapshots):
        requested = Fraction(first_capture_ns,10**9)+index*interval
        slot_free, slot = heappop(slots)
        capture = max(requested, stage_free, slot_free)
        stage_end = capture+staging
        upload_start = max(stage_end,writer_free)
        upload_end = upload_start+service
        durable = upload_end+durability
        stage_free, writer_free = stage_end, upload_end
        heappush(slots,(upload_end,slot))
        lifetimes.append((capture,upload_end,size))
        # Requested checkpoints are FIFO barriers; overlapping waits are a union.
        pauses.append((requested,stage_end))
        times = dict(requested=requested,capture=capture,staging_end=stage_end,
                     upload_start=upload_start,upload_end=upload_end,durable=durable)
        rows.append(dict(snapshot=index,slot=slot,exact_seconds={k:str(v) for k,v in times.items()},
                         seconds={k:float(v) for k,v in times.items()},
                         capture_delay_exact_seconds=str(capture-requested)))
    merged = []
    for start,end in pauses:
        if merged and start<=merged[-1][1]:
            merged[-1]=(merged[-1][0],max(end,merged[-1][1]))
        else:
            merged.append((start,end))
    failure = Fraction(failure_ns,10**9)
    available = [r for r in rows if Fraction(r['exact_seconds']['durable'])<=failure]
    latest = max(available,key=lambda r:Fraction(r['exact_seconds']['capture'])) if available else None
    recovery = Fraction(latest['exact_seconds']['capture']) if latest else None
    return dict(schema_version=1,calculation='checkpoint-async',model=model,scenario=inputs,sources=provenance(model),
                checkpoint_save_rows=rows,
                checkpoint_pause_intervals=[dict(start_exact_seconds=str(a),end_exact_seconds=str(b)) for a,b in merged],
                summary=dict(official_parameters=parameters,official_14_byte_payload=14*parameters,
                             payload_bytes=size,payload_origin='official full-parameter 14-byte layout' if payload_bytes is None else 'explicit teaching payload override',
                             upload_service_exact_seconds=str(service),
                             requested_payload_bytes_per_second_exact=str(Fraction(size,1)/interval),
                             requested_upload_utilization_exact=str(service/interval),
                             requested_cadence_has_upload_slack=service<interval,
                             requested_cadence_has_staging_slack=staging<interval,
                             snapshot_buffer_reserved_bytes=buffer_slots*size,
                             snapshot_buffer_live_peak_bytes=peak_intervals(lifetimes),
                             total_training_barrier_union_exact_seconds=str(sum((b-a for a,b in merged),Fraction(0))),
                             final_durable_exact_seconds=rows[-1]['exact_seconds']['durable'],
                             completed_durable_at_failure=len(available),
                             latest_recoverable_snapshot=latest['snapshot'] if latest else None,
                             recovery_capture_exact_seconds=str(recovery) if recovery is not None else None,
                             elapsed_since_recovery_capture_exact_seconds=str(failure-recovery) if recovery is not None else None,
                             live_snapshot_buffers_at_failure=sum(start<=failure<end for start,end,_ in lifetimes)),
                assumptions=[
                    '默认官方Qwen完整参数的BF16权重＋FP32 master/m/v共14bytes/参数；payload_bytes显式覆盖用于取整8B等教学例，不更改官方参数量。未计梯度、CPU数据状态、metadata、压缩或副本。',
                    '保存请求按固定墙钟到达，FIFO且不合并。训练在请求点等待槽／stage通路，再暂停staging；实际capture为staging开始，不能把延后的快照标签仍记成原请求时间。重叠暂停取区间并集，不逐请求重复相加。',
                    '一条staging通路、一条后台upload通路，不同快照可重叠；完整缓冲从capture持有到upload读取完成，容量不足施加背压，不丢弃请求。带宽与staging时长是有效教学输入，不是设备实测或框架默认。',
                    'durability_delay为写完后的独立确认延迟，不占upload通路和已消费的快照槽；durable事件声明所有必需状态可恢复，实际StorageWriter语义必须另查，不把API返回或staging完成当持久化。',
                    'failure_ns为无故障计划上的截面；之后行仅为反事实计划，不表示故障后仍写成功。同刻durable先于故障，故使用<=；无可用快照则恢复点及回退时长为null，不假定初始快照存在。',
                    '回退量为故障到快照capture的墙钟差，不等于丢失的训练计算、token或有效进展。没有加载时间、恢复执行、故障概率及后台争用造成的训练降速，不能据此声称完整ETTR。',
                ])
