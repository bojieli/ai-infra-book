"""FIFO request replay with explicit service durations and official Qwen shapes.

Each worker owns one request until completion. KV reservation events describe
this policy only; durations are inputs, never inferred from FLOPs or GPU peaks.
"""
import heapq
from collections import defaultdict
from ..models import forward
from ..schema import Scenario
from ..sources import model_config, provenance
from ..units import positive_int


def percentile95(values):
    return sorted(values)[(95 * len(values) + 99) // 100 - 1]


def calculate(model: str = 'qwen3-8b', requests: list | None = None, workers: int = 2,
              kv_capacity_bytes: int | None = None) -> dict:
    positive_int(workers, 'workers')
    if kv_capacity_bytes is not None:
        positive_int(kv_capacity_bytes, 'kv_capacity_bytes')
    if requests is None:
        requests = [dict(arrival_ns=i * 500000, prompt_tokens=1024, output_tokens=128,
                         prefill_ns=1000000, decode_ns=1000000) for i in range(4)]
    if not isinstance(requests, list) or not requests:
        raise ValueError('requests must be a nonempty list')
    required = {'arrival_ns', 'prompt_tokens', 'output_tokens', 'prefill_ns', 'decode_ns'}
    for row in requests:
        if set(row) != required:
            raise ValueError('Each request needs arrival_ns, prompt_tokens, output_tokens, prefill_ns, decode_ns')
        for name, value in row.items():
            positive_int(value, name, allow_zero=name == 'arrival_ns')
    c = model_config(model)
    # Validate supported Qwen architecture before accessing shared cache geometry.
    forward(model, Scenario(tokens=1))
    kv_token = 4 * c['num_hidden_layers'] * c['num_key_value_heads'] * c['head_dim']
    pool = [(0, w) for w in range(workers)]
    heapq.heapify(pool)
    events = defaultdict(int)
    reservations = defaultdict(int)
    active_reservations = []
    reserved = 0
    last_admission = 0
    rows = []
    for index, request in sorted(enumerate(requests), key=lambda item: (item[1]['arrival_ns'], item[0])):
        p, g = request['prompt_tokens'], request['output_tokens']
        if p + g - 1 > c['max_position_embeddings']:
            raise ValueError('Prompt plus consumed output exceeds official context limit')
        free, worker = heapq.heappop(pool)
        start = max(free, request['arrival_ns'], last_admission)
        reservation = (p + g - 1) * kv_token
        if kv_capacity_bytes is not None:
            if reservation > kv_capacity_bytes:
                raise ValueError(f'Request {index} cannot fit the declared KV capacity even alone')
            while active_reservations and active_reservations[0][0] <= start:
                _, released = heapq.heappop(active_reservations)
                reserved -= released
            # Strict FIFO: later smaller requests cannot bypass this head.
            while reserved + reservation > kv_capacity_bytes:
                start = active_reservations[0][0]
                while active_reservations and active_reservations[0][0] <= start:
                    _, released = heapq.heappop(active_reservations)
                    reserved -= released
            reserved += reservation
        last_admission = start
        first = start + request['prefill_ns']
        finish = first + (g - 1) * request['decode_ns']
        heapq.heappush(pool, (finish, worker))
        if kv_capacity_bytes is not None:
            heapq.heappush(active_reservations, (finish, reservation))
            reservations[start] += reservation
            reservations[finish] -= reservation
        prefill = forward(model, Scenario(tokens=p))['summary']['matrix_flops']
        decode = 0
        if g > 1:
            low = forward(model, Scenario(tokens=1, history=p))['summary']['matrix_flops']
            high = forward(model, Scenario(tokens=1, history=p + g - 2))['summary']['matrix_flops']
            decode = (g - 1) * (low + high) // 2
        # Reserve prompt slots at start, and one slot at each decode start.
        events[start] += p * kv_token
        for j in range(g - 1):
            events[first + j * request['decode_ns']] += kv_token
        events[finish] -= (p + g - 1) * kv_token
        rows.append(dict(request=index, worker=worker, **request, start_ns=start,
                         first_token_ns=first, finish_ns=finish,
                         waiting_ns=start - request['arrival_ns'],
                         ttft_ns=first - request['arrival_ns'],
                         latency_ns=finish - request['arrival_ns'],
                         prefill_matrix_flops=prefill, decode_matrix_flops=decode,
                         final_kv_bytes=reservation,
                         admission_reserved_bytes=reservation if kv_capacity_bytes is not None else None))
    current = peak = area = 0
    reserved_current = reserved_peak = reserved_area = 0
    previous = min(events)
    timeline = []
    for time, delta in sorted(events.items()):
        area += current * (time - previous)
        reserved_area += reserved_current * (time - previous)
        reserved_current += reservations.get(time, 0)
        reserved_peak = max(reserved_peak, reserved_current)
        current += delta
        if kv_capacity_bytes is not None and not current <= reserved_current <= kv_capacity_bytes:
            raise ValueError("Live KV exceeds reservation or capacity")
        if current < 0:
            raise ValueError('KV event accounting underflow')
        peak = max(peak, current)
        timeline.append(dict(time_ns=time, live_kv_bytes=current,
                             reserved_kv_bytes=reserved_current if kv_capacity_bytes is not None else None))
        previous = time
    if current:
        raise ValueError('KV allocations not released')
    n = len(rows)
    return dict(schema_version=1, calculation='qwen-fifo-request-trace', model=model,
                scenario=dict(workers=workers, requests=requests, kv_capacity_bytes=kv_capacity_bytes), sources=provenance(model),
                request_rows=rows, kv_timeline=timeline,
                summary=dict(requests=n, mean_prompt_tokens=sum(r['prompt_tokens'] for r in rows)/n,
                             mean_output_tokens=sum(r['output_tokens'] for r in rows)/n,
                             p95_prompt_tokens=percentile95([r['prompt_tokens'] for r in rows]),
                             p95_output_tokens=percentile95([r['output_tokens'] for r in rows]),
                             prefill_matrix_flops=sum(r['prefill_matrix_flops'] for r in rows),
                             decode_matrix_flops=sum(r['decode_matrix_flops'] for r in rows),
                             mean_waiting_ns=sum(r['waiting_ns'] for r in rows)/n,
                             p95_waiting_ns=percentile95([r['waiting_ns'] for r in rows]),
                             p95_ttft_ns=percentile95([r['ttft_ns'] for r in rows]),
                             p95_latency_ns=percentile95([r['latency_ns'] for r in rows]),
                             finish_ns=max(r['finish_ns'] for r in rows),
                             kv_bytes_per_token=kv_token, kv_peak_bytes=peak,
                             kv_residency_byte_ns=area,
                             kv_reservation_peak_bytes=reserved_peak if kv_capacity_bytes is not None else None,
                             kv_reservation_byte_ns=reserved_area if kv_capacity_bytes is not None else None,
                             complete_device_peak_bytes=None),
                assumptions=[
                    'kv_capacity_bytes 仅为这些 worker 共用的逻辑 KV 预算，不含权重、激活或工作区，也不声明物理 KV 池可跨设备免费共享。有限模式在准入时预留 P+G−1 个槽直到完成；G 是本情景声明的输出上限且实际生成恰好达到它，不能把已观察未来长度当成部署时已知信息。',
                    '同时满足 worker 空闲和 KV 预留可放才准入。单请求超过 KV 预算直接拒绝输入，不制造永不完成的队列。预留峰值／面积与活跃峰值／面积分列；逐时刻检查活跃量不超过预留量、预留量不超过预算。',
                    '请求记录保留成对输入／输出长度和到达时刻；同刻按输入顺序 FIFO。每个 worker 独占处理一条请求直到完成，无连续 batching、抢占、优先级、缓存共享。可选 KV 容量采用整请求上限预留的 FIFO 准入，后来的小请求不越过队头。',
                    'prefill_ns 与 decode_ns 为显式服务输入，默认仅教学数值，不由矩阵 FLOPs 或官方峰值预测。多个 worker 假设独立服务资源；共享设备争用需要重新校准，不代表同卡并发免费。',
                    '每条请求使用官方 Qwen 配置、B=1、last 输出头；prefill 产生首 token，仅执行 G−1 次 decode。历史相关注意力按首尾等差求和，MoE 使用 balanced 情景；矩阵账与输入服务耗时独立输出。',
                    'KV 按 BF16 K/V 逻辑载荷，每请求开始即预留 P 个 prompt 槽，每次 decode 开始再预留一个槽，最后输出不再喂回。完成即释放，同刻释放可供新请求复用；这是活跃槽口径，不是分页粒度或完整显存峰值。',
                    'p95 使用 nearest-rank ceil(0.95*n)，小样本时可能就是最大值。TTFT 从到达至首输出，latency 至最后输出；等待与服务分列。KV 面积为存活字节乘纳秒，不能当 HBM 读写流量。',
                ])
