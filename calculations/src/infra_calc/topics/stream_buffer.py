"""Discrete FIFO handoff: consume at tick start, publish at tick end.

Slots belong only to the handoff FIFO. Producer internal state and consumer
workspaces are separate, as are the explicitly reserved layout conversion slots.
"""
from ..models import qwen3
from ..sources import model_config, provenance
from ..units import positive_int


def schedule(blocks, first_produce, produce_interval, first_consume,
             consume_interval, capacity_slots=None):
    """FIFO producer stalls propagate; consumers preserve their service spacing."""
    produced, consumed = [], []
    for i in range(blocks):
        publish = first_produce if i == 0 else produced[-1] + produce_interval
        if capacity_slots is not None and i >= capacity_slots:
            publish = max(publish, consumed[i - capacity_slots])
        take = first_consume if i == 0 else consumed[-1] + consume_interval
        # A value published at tick end is readable starting next tick.
        take = max(take, publish + 1)
        produced.append(publish)
        consumed.append(take)
    events = [(t, 1, i) for i, t in enumerate(produced)]
    events += [(t, -1, i) for i, t in enumerate(consumed)]
    occupied = peak = 0
    timeline = []
    for tick, delta, block in sorted(events):
        occupied += delta
        peak = max(peak, occupied)
        timeline.append(dict(tick=tick, event='publish' if delta > 0 else 'take',
                             block=block, occupied_slots=occupied))
    return dict(produce_ticks=produced, consume_ticks=consumed,
                peak_slots=peak, last_take_tick=consumed[-1], timeline=timeline)


def calculate(model='qwen3-8b', block_rows=64, blocks=5, first_produce=4,
              produce_interval=1, first_consume=5, consume_interval=2,
              budget_bytes=65536, reorder_slots=2):
    for name, value in [('block_rows', block_rows), ('blocks', blocks),
                        ('first_produce', first_produce), ('produce_interval', produce_interval),
                        ('first_consume', first_consume), ('consume_interval', consume_interval),
                        ('budget_bytes', budget_bytes)]:
        positive_int(value, name)
    if isinstance(reorder_slots, bool) or not isinstance(reorder_slots, int) or reorder_slots < 0:
        raise ValueError('reorder_slots must be a nonnegative integer')
    config = model_config(model)
    qwen3.validate(config)
    block_bytes = block_rows * config['head_dim'] * 2
    reorder_bytes = reorder_slots * block_bytes
    available_slots = max(0, (budget_bytes - reorder_bytes) // block_bytes)
    args = (blocks, first_produce, produce_interval, first_consume, consume_interval)
    baseline = schedule(*args)
    bounded = schedule(*args, capacity_slots=available_slots) if available_slots else None
    fifo_bytes = baseline['peak_slots'] * block_bytes
    summary = dict(block_bytes=block_bytes, total_payload_bytes=blocks*block_bytes,
                   original_fifo_peak_bytes=fifo_bytes, reorder_reserved_bytes=reorder_bytes,
                   original_handoff_required_bytes=fifo_bytes+reorder_bytes,
                   original_progress_fits=fifo_bytes+reorder_bytes <= budget_bytes,
                   fifo_available_slots=available_slots,
                   original_last_take_tick=baseline['last_take_tick'],
                   bounded_last_take_tick=bounded['last_take_tick'] if bounded else None,
                   bounded_fifo_peak_bytes=bounded['peak_slots']*block_bytes if bounded else None,
                   bounded_handoff_peak_bytes=bounded['peak_slots']*block_bytes+reorder_bytes if bounded else None,
                   producer_final_delay_ticks=bounded['produce_ticks'][-1]-baseline['produce_ticks'][-1] if bounded else None,
                   consumer_final_delay_ticks=bounded['last_take_tick']-baseline['last_take_tick'] if bounded else None,
                   actual_gpu_seconds=None)
    return dict(schema_version=1, calculation='qwen-stream-buffer', model=model,
                scenario=dict(block_rows=block_rows, blocks=blocks, first_produce=first_produce,
                              produce_interval=produce_interval, first_consume=first_consume,
                              consume_interval=consume_interval, budget_bytes=budget_bytes,
                              reorder_slots=reorder_slots),
                sources=provenance(model), summary=summary,
                fifo_schedules=dict(original=baseline, bounded=bounded),
                assumptions=[
                    'BF16块为[block_rows,官方Qwen head_dim]，默认64×128=16KiB；形状来自模型，生产／消费时间格为教学输入，不是GPU周期或实测。',
                    '单边同序FIFO，消费发生在时间格开始，生产在结束；同格先释放后写入，新发布块最早下一格消费。消费者取走即释放FIFO，后续消费工作区另计。',
                    '有限FIFO使生产发布停顿，之后的生产间隔从实际发布时刻继续；消费受数据就绪与最小消费间隔共同约束。最后取走时刻不是完整下游计算完成时间。',
                    '布局转换槽是与FIFO不别名的固定预留，默认双槽32KiB；没有模拟转换指令、任意重排网络或分支汇合。去掉重排槽假定接口已统一布局，不保证改布局没有其它成本。',
                    '预算扣除布局槽后容不下一个块时，bounded留空；本模型不实现零容量直接交接，不能据此断言所有实现均死锁。',
                ])
