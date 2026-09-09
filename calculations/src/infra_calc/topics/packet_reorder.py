"""Striped payload serialization, ordered delivery and explicit loss recovery."""
from fractions import Fraction
from ..sources import model_config, provenance
from ..units import positive_int


def calculate(model='qwen3-8b', tokens=1, packet_bytes=1024,
              path_delays_ns=None, path_bytes_per_second=10**9,
              lost_packets=None, recovery_delay_ns=20000):
    """Recover declared losses once; recovery delay is supplied, not inferred."""
    delays = [1000, 9000] if path_delays_ns is None else path_delays_ns
    losses = [0] if lost_packets is None else lost_packets
    for name, value in (('tokens', tokens), ('packet_bytes', packet_bytes),
                        ('path_bytes_per_second', path_bytes_per_second)):
        positive_int(value, name)
    positive_int(recovery_delay_ns, 'recovery_delay_ns', allow_zero=True)
    if not isinstance(delays, list) or not delays:
        raise ValueError('At least one path required')
    for delay in delays:
        positive_int(delay, 'path delay', allow_zero=True)
    config = model_config(model)
    payload = tokens * config['hidden_size'] * 2
    count = (payload + packet_bytes - 1) // packet_bytes
    if count > 100000:
        raise ValueError('Too many packets; increase packet_bytes')
    if not isinstance(losses, list) or len(set(losses)) != len(losses):
        raise ValueError('Unique lost packet indices required')
    for seq in losses:
        positive_int(seq, 'lost packet', allow_zero=True)
        if seq >= count:
            raise ValueError('Lost packet index outside payload')
    sizes = [min(packet_bytes, payload - seq * packet_bytes) for seq in range(count)]
    path_free = [Fraction(0) for _ in delays]
    transmissions = []
    arrivals = []
    originals = []

    def send(seq, ready, retry):
        path = seq % len(delays)
        start = max(path_free[path], ready)
        end = start + Fraction(sizes[seq] * 10**9, path_bytes_per_second)
        path_free[path] = end
        lost = not retry and seq in losses
        arrival = end + delays[path]
        transmissions.append(dict(sequence=seq, bytes=sizes[seq], path=path, retry=retry,
                                  lost=lost, start_exact_ns=str(start), end_exact_ns=str(end),
                                  arrival_exact_ns=None if lost else str(arrival)))
        if not lost:
            arrivals.append((arrival, seq))
        return end

    for seq in range(count):
        originals.append(send(seq, Fraction(0), False))
    # Originals have priority; each path drains its original queue before retries.
    for seq in sorted(losses, key=lambda seq: (originals[seq] + recovery_delay_ns, seq)):
        send(seq, originals[seq] + recovery_delay_ns, True)

    pending = set()
    next_sequence = peak = peak_packets = 0
    delivery = []
    events = []
    area = Fraction(0)
    previous = Fraction(0)
    buffered = 0
    # All arrivals at one instant are admitted before releasing a contiguous prefix.
    # Peak is retained out-of-order state after release, excluding ingress staging.
    grouped = {}
    for time, seq in arrivals:
        grouped.setdefault(time, []).append(seq)
    for time, sequences in sorted(grouped.items()):
        area += buffered * (time - previous)
        pending.update(sequences)
        released = []
        while next_sequence in pending:
            pending.remove(next_sequence)
            released.append(next_sequence)
            delivery.append(dict(sequence=next_sequence, delivery_exact_ns=str(time)))
            next_sequence += 1
        buffered = sum(sizes[seq] for seq in pending)
        peak = max(peak, buffered)
        peak_packets = max(peak_packets, len(pending))
        events.append(dict(time_exact_ns=str(time), arrived=sorted(sequences), released=released,
                           retained_sequences=sorted(pending), retained_bytes=buffered))
        previous = time
    retry_bytes = sum(sizes[seq] for seq in losses)
    suffix_bytes = sum(sizes[min(losses):]) if losses else 0
    return dict(schema_version=1, calculation='packet-reorder',
                scenario=dict(model=model, tokens=tokens, packet_bytes=packet_bytes,
                              path_delays_ns=delays, path_bytes_per_second=path_bytes_per_second,
                              lost_packets=losses, recovery_delay_ns=recovery_delay_ns),
                sources=provenance(model), transmissions=transmissions,
                receive_events=events, delivery=delivery,
                summary=dict(payload_bytes=payload, packet_count=count,
                             retransmitted_bytes=retry_bytes, sent_bytes=payload+retry_bytes,
                             received_bytes=payload, declared_lost_bytes=retry_bytes,
                             suffix_replay_counterfactual_bytes=suffix_bytes,
                             peak_retained_reorder_bytes=peak, peak_retained_packets=peak_packets,
                             reorder_area_exact_byte_ns=str(area),
                             first_ordered_delivery_exact_ns=delivery[0]['delivery_exact_ns'],
                             completion_exact_ns=delivery[-1]['delivery_exact_ns']),
                assumptions=[
                    '官方模型hidden_size确定单个BF16 [tokens,H]载荷；报文大小、独立路径速率和延迟均为教学输入，不是网卡规格。只算payload，不含头部、ACK、编码或物理多跳流量。',
                    '按序号轮转路径，各路径独立串行发送，原始报文优先于重传。显式声明原始丢包；在其发送结束后给定recovery_delay_ns进入重传队列，每包仅重传一次且成功。此延迟不是由ACK或超时协议推导，不模拟虚假重传。',
                    '接收端无限乱序缓冲，每个同刻事件先合并到达，再释放连续前缀。保留峰值不含入口暂存；乱序payload容量与协议SRAM状态、位图、描述符大小不同。',
                    'suffix_replay_counterfactual_bytes仅为从最早丢失序号到消息末尾重发一遍的字节对照，不模拟Go-Back-N时序或宣称实际协议会这样重传。',
                    '完成时间是该消息全部按序交付时刻；没有随机分布、拥塞控制、有限窗口、接收缓冲溢出或OpenURMA版本行为校准。',
                ])
