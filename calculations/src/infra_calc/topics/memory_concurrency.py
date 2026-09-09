"""Independent transaction window and bandwidth bounds for real KV payloads.

Interface parameters are declared teaching inputs, not inferred GPU queue specs.
Integer nanoseconds keep the ceil for required concurrency exact.
"""
from fractions import Fraction
from ..sources import provenance
from ..units import positive_int
from . import state


def calculate(model: str = 'qwen3-8b', length: int = 8192, batch: int = 1,
              transactions: int = 128, transaction_bytes: int = 128,
              latency_ns: int = 500, bandwidth_bytes_per_second: int = 10**12,
              active_transactions: int | None = None, service_interval_ns: int | None = None) -> dict:
    for name, value in (('transactions', transactions), ('transaction_bytes', transaction_bytes),
                        ('latency_ns', latency_ns), ('bandwidth_bytes_per_second', bandwidth_bytes_per_second)):
        positive_int(value, name)
    active = transactions if active_transactions is None else active_transactions
    positive_int(active, 'active_transactions')
    if active > transactions:
        raise ValueError('Active transactions cannot exceed allocated slots')
    if service_interval_ns is not None:
        positive_int(service_interval_ns, 'service_interval_ns')
    cache = state.calculate(model, length, batch)
    if model not in ('qwen3-8b', 'qwen3-32b', 'qwen3-30b-a3b', 'qwen3-235b-a22b'):
        raise ValueError('This example requires native Qwen3 full-history GQA')
    payload = cache['summary']['selected_history_payload_bytes']
    latency = latency_ns / 10**9
    exact_window = Fraction(active * transaction_bytes * 10**9, latency_ns)
    bounds = {'interface': Fraction(bandwidth_bytes_per_second), 'transaction_window': exact_window}
    if service_interval_ns is not None:
        bounds['serial_service'] = Fraction(transaction_bytes * 10**9, service_interval_ns)
    exact_throughput = min(bounds.values())
    window_bound = float(exact_window)
    throughput_bound = float(exact_throughput)
    limiters = [name for name, bound in bounds.items() if bound == exact_throughput]
    denominator = transaction_bytes * 10**9
    required = (bandwidth_bytes_per_second * latency_ns + denominator - 1) // denominator
    transfer_count = (payload + transaction_bytes - 1) // transaction_bytes
    service_bound = payload / throughput_bound
    return dict(schema_version=1, calculation='memory-concurrency', model=model,
                scenario=dict(length=length, batch=batch, transactions=transactions,
                              transaction_bytes=transaction_bytes, latency_ns=latency_ns,
                              bandwidth_bytes_per_second=bandwidth_bytes_per_second),
                sources=provenance(model),
                summary=dict(logical_kv_payload_bytes=payload,
                             allocated_window_bytes=transactions * transaction_bytes,
                             outstanding_window_bytes=active * transaction_bytes,
                             active_transactions=active,
                             throughput_bounds_exact_bytes_per_second={key: str(value) for key,value in bounds.items()},
                             effective_bandwidth_upper_exact_bytes_per_second=str(exact_throughput),
                             serial_service_can_reach_interface=(bounds.get('serial_service', Fraction(bandwidth_bytes_per_second)) >= bandwidth_bytes_per_second),
                             binding_limiters=limiters,
                             required_window_bytes=bandwidth_bytes_per_second * latency,
                             required_transactions=required,
                             transaction_limited_bytes_per_second=window_bound,
                             effective_bandwidth_upper_bytes_per_second=throughput_bound,
                             bandwidth_utilization_upper=throughput_bound / bandwidth_bytes_per_second,
                             ideal_interface_service_seconds=payload / bandwidth_bytes_per_second,
                             window_constrained_service_lower_seconds=service_bound,
                             finite_transfer_lower_seconds=max(latency, service_bound),
                             assumed_fixed_size_transfer_count=transfer_count,
                             assumed_fixed_size_payload_bytes=transfer_count * transaction_bytes,
                             limiter=limiters[0],
                             measured_bandwidth_bytes_per_second=None, predicted_decode_seconds=None),
                assumptions=[
                    'KV payload uses pinned Qwen3 configuration, BF16 and one logical visit per stored K/V record. Weight reads, new token writes, caches, repeated tile loads and other operators are excluded.',
                    'N counts independent outstanding interface transactions across the device, not batch size, threads, warps or SM count. No hardware queue capacity is inferred from the model configuration.',
                    'At the declared workload latency L, transaction rate is bounded by N/L and bandwidth by min(B,Ns/L). Required N=ceil(BL/s). B is one-direction bytes/s, L is integer ns, s is bytes per transaction.',
                    'Latency and bandwidth must describe the same interface and workload. These defaults are teaching assumptions, not H100 or Mess measurements. A pointer-chase probe is not automatically the latency of every model transaction.',
                    'Payload divided by the throughput bound is a resource service lower bound. Finite transfer also cannot finish before one assumed latency; startup, dependency chains and drain can make it longer. No exact schedule or attainable performance is claimed.',
                    'Allocated slots and active independent requests are distinct: active_transactions defaults to all slots, but source-side completion waiting may reduce it to one. An optional service_interval_ns is a sustainable serialized initiation interval (or non-pipelined service duration), not automatically a single-request latency. The combined bound is min(B, active*m/T, m/tau); tied limiters are retained. Required transaction count only satisfies the window condition, not a serial-service limit.',
                    'Transaction count rounds the whole logical payload upward as a separate fixed-size-transfer scenario; real alignment, coalescing, page walks and cache misses require execution evidence.',
                ])
