"""Nominal 70B decode sensitivity with independently specified storage/compute.

This chapter-one model uses 2NB matrix work, not a real architecture adapter.
"""
from math import ceil
from .. import hardware
from ..sources import records
from ..units import positive_int, positive_number


def calculate(batch: int = 1, parameters: int = 70_000_000_000, weight_bits: int = 8,
              kv_history_bytes_per_request: int = 0, kv_append_bytes_per_request: int = 0,
              workspace_bytes: int = 0, metadata_bytes: int = 0,
              compute_multiplier: float = 1.0, bandwidth_multiplier: float = 1.0) -> dict:
    for key, value in (('batch', batch), ('parameters', parameters), ('weight_bits', weight_bits)):
        positive_int(value, key)
    if weight_bits not in (4, 8, 16):
        raise ValueError('Teaching weight storage supports 4/8/16 bits')
    for key, value in (('kv_history_bytes_per_request', kv_history_bytes_per_request),
                       ('kv_append_bytes_per_request', kv_append_bytes_per_request),
                       ('workspace_bytes', workspace_bytes), ('metadata_bytes', metadata_bytes)):
        positive_int(value, key, allow_zero=True)
    for key, value in (('compute_multiplier', compute_multiplier), ('bandwidth_multiplier', bandwidth_multiplier)):
        positive_number(value, key)
    device = hardware.select_device('h100-sxm')
    peak = hardware.select_peak(device, 'BF16', 'FP32', 'tensor', 'dense')
    compute = peak['tera_ops_per_second'] * 10**12 * compute_multiplier
    bandwidth = device['memory']['bandwidth_bytes_per_second'] * bandwidth_multiplier
    capacity = int(device['memory']['nominal_capacity'] * 10**9)
    weights = (parameters * weight_bits + 7) // 8
    shared_read = weights + metadata_bytes
    per_request = kv_history_bytes_per_request + kv_append_bytes_per_request
    traffic = shared_read + batch * per_request
    resident = traffic + workspace_bytes
    flops = 2 * parameters * batch
    compute_seconds, memory_seconds = flops / compute, traffic / bandwidth
    denominator = 2 * parameters * bandwidth / compute - per_request
    crossover = max(1, ceil(shared_read / denominator)) if denominator > 0 else None
    fits = resident <= capacity
    bound = max(compute_seconds, memory_seconds) if fits else None
    return dict(schema_version=1, calculation='nominal-decode-budget', model='nominal-70b-teaching-model',
                scenario=dict(batch=batch, parameters=parameters, weight_bits=weight_bits,
                              kv_history_bytes_per_request=kv_history_bytes_per_request,
                              kv_append_bytes_per_request=kv_append_bytes_per_request,
                              workspace_bytes=workspace_bytes, metadata_bytes=metadata_bytes,
                              compute_multiplier=compute_multiplier, bandwidth_multiplier=bandwidth_multiplier,
                              device='h100-sxm', compute_input='BF16', accumulator='FP32', sparsity='dense'),
                sources=[{key: row[key] for key in ('file', 'url', 'revision', 'sha256')}
                         for row in records() if row.get('id') in device['source_ids']],
                selected_peak=peak,
                summary=dict(matrix_flops=flops, weight_payload_bytes=weights, declared_read_write_bytes=traffic,
                             declared_resident_bytes=resident, nominal_capacity_bytes=capacity,
                             fits_declared_budget=fits, arithmetic_intensity_flops_per_byte=flops / traffic,
                             compute_service_seconds=compute_seconds, memory_service_seconds=memory_seconds,
                             resource_lower_bound_seconds=bound,
                             capacity_feasible_throughput_upper_tokens_per_second=batch / bound if bound else None,
                             compute_memory_crossover_batch=crossover,
                             crossover_fits_declared_capacity=(shared_read + crossover * per_request + workspace_bytes <= capacity) if crossover else False,
                             dominant_resource='compute' if compute_seconds >= memory_seconds else 'memory',
                             measured_decode_seconds=None),
                assumptions=[
                    'Nominal N parameters use approximate 2NB dense matrix FLOPs; no actual architecture, attention correction or output-head distinction is inferred. Qwen actual operators remain in forward/projection-bound.',
                    'Official H100 SXM BF16 input/FP32 accumulator/dense Tensor peak is selected strictly. Storage may be 4/8 bits; assumed dequantized BF16 operands use this peak, not INT8 TOPS or native FP4 peak. Conversion work and buffers require additional accounting.',
                    'Weights and supplied metadata are read once and reused across the batch. Each request reads its declared history and writes its append once. KV values are explicit teaching bytes, not borrowed from a different model configuration.',
                    'Resident budget includes declared weights/metadata, end-of-step KV and workspace. Device nominal GB is converted using 10^9; reserved runtime space must be represented in workspace. Zero extras mean excluded, not proven absent.',
                    'Compute and memory service can overlap only as a lower-bound assumption: take max, not sum. Failed capacity leaves a runnable resource bound and throughput null, while component arithmetic remains visible.',
                    'Multipliers are hypothetical resource changes relative to the official profile, not other hardware SKUs. Crossover solves shared_bytes + B*KV_bytes = B*2N*bandwidth/compute; no positive denominator means this model never becomes compute dominated.',
                    'No kernel padding, launch, communication, non-matrix arithmetic, quality impact or measured efficiency is included. This is the initial chapter-one estimate, not complete model/token latency.',
                ])
