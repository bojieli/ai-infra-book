"""Experiment 4-3: fixed weight/KV payloads under independent resource changes.

Candidate integration module. Uses the public, source-checked model adapters.
Run from the repository root with Python 3; no model execution is required.
"""
import argparse
from fractions import Fraction
import json
from pathlib import Path
import re
import sys

PROJECT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT / 'src'))
from infra_calc import hardware
from infra_calc.sources import model_config, records
from infra_calc.topics import capacity_scan
from infra_calc.models import qwen3_moe

DEVICES = ('a100-80gb-sxm', 'h100-sxm', 'h200-sxm', 'b200-sxm',
           'm2-max-38gpu-96gb')


def fraction(value):
    return {'numerator': value.numerator, 'denominator': value.denominator}


def workload(model, batch, history, bits, routing='balanced'):
    """One synchronized decode forward, with history positions before append.

Read each selected expert once per layer across the batch. Distinct current
input token IDs are declared, so embedding lookup reads B rows, not V rows.
Current K/V operand reads are counted separately from their append writes.
"""
    if model not in ('qwen3-8b', 'qwen3-235b-a22b'):
        raise ValueError('Only the two pinned experiment 4-3 models are supported')
    for value in (batch, history):
        if type(value) is not int or value < 1:
            raise ValueError('Batch and prior history must be positive integers')
    if bits not in (16, 8, 4) or type(bits) is not int:
        raise ValueError('Storage width must be 16, 8 or 4')
    if routing not in ('balanced', 'concentrated'):
        raise ValueError('Unknown declared routing policy')
    config = model_config(model)
    if batch > config['vocab_size']:
        raise ValueError('Distinct embedding IDs require batch <= vocabulary')
    capacity = capacity_scan.calculate(model, history + 1)
    storage = next(row for row in capacity['storage_formats'] if row['matrix_bits'] == bits)
    counts = (qwen3_moe.routing_counts(batch, config['num_experts'],
              config['num_experts_per_tok'], routing)
              if config['model_type'] == 'qwen3_moe' else None)
    tensors = []
    for tensor in storage['tensors']:
        match = re.search(r'\.experts\.(\d+)\.', tensor['name'])
        selected = match is None or counts[int(match.group(1))] > 0
        # All expert tensors remain resident even when no token selects them.
        payload = tensor['payload_bytes'] if selected else 0
        metadata = tensor['scale_bytes'] if selected else 0
        if tensor['name'] == 'model.embed_tokens.weight':
            payload = batch * config['hidden_size'] * 2
        tensors.append(dict(tensor, selected=selected,
                            step_payload_read_bytes=payload,
                            step_metadata_read_bytes=metadata))
    kv_unit = 4 * config['num_hidden_layers'] * config['num_key_value_heads'] * config['head_dim']
    parts = dict(weight_payload=sum(t['step_payload_read_bytes'] for t in tensors),
                 weight_scales=sum(t['step_metadata_read_bytes'] for t in tensors),
                 prior_kv_read=batch * history * kv_unit,
                 current_kv_operand_read=batch * kv_unit,
                 kv_append_write=batch * kv_unit)
    weights = storage['total_weight_bytes']
    workspace = capacity['scenario']['workspace_bytes']
    return dict(id=f'{model}-b{batch}-h{history}-w{bits}-{routing}',
                model=model, batch=batch, history=history, matrix_storage_bits=bits,
                routing=routing, expert_counts=counts, sources=capacity['sources'],
                tensors=tensors, resident_weight_bytes=weights,
                kv_bytes_per_request=(history + 1) * kv_unit,
                kv_resident_bytes=batch * (history + 1) * kv_unit,
                declared_workspace_bytes=workspace,
                resident_budget_bytes=weights + batch * (history + 1) * kv_unit + workspace,
                payload_components_bytes=parts, accounted_payload_bytes=sum(parts.values()))


def compare(work, device, baseline):
    """Change capacity alone, bandwidth alone, or the actual published pair."""
    def memory(profile):
        value = profile['memory']
        if value['capacity_unit'] not in ('GB', 'GiB'):
            raise ValueError('Unsupported memory unit')
        scale = 10**9 if value['capacity_unit'] == 'GB' else 2**30
        return int(value['nominal_capacity'] * scale), Fraction(str(value['bandwidth_bytes_per_second']))
    capacity, bandwidth = memory(device)
    base_capacity, base_bandwidth = memory(baseline)
    rows = []
    for mode, cap, rate in (('capacity_only', capacity, base_bandwidth),
                           ('bandwidth_only', base_capacity, bandwidth),
                           ('published_pair', capacity, bandwidth)):
        fits = work['resident_budget_bytes'] <= cap
        service = Fraction(work['accounted_payload_bytes'], 1) / rate
        free = cap - work['resident_weight_bytes'] - work['declared_workspace_bytes']
        rows.append(dict(workload=work['id'], device=device['id'], mode=mode,
                         capacity_bytes=cap, bandwidth_bytes_per_second=fraction(rate),
                         passes_declared_capacity=fits,
                         maximum_requests_for_declared_capacity=max(0, free // work['kv_bytes_per_request']),
                         payload_service_seconds=fraction(service),
                         capacity_qualified_payload_service_seconds=fraction(service) if fits else None,
                         measured_hbm_bytes=None, measured_decode_seconds=None))
    return rows


def calculate():
    catalog = {row['id']: row for row in hardware.catalog()['devices']}
    profiles = [catalog[name] for name in DEVICES]
    source_ids = {source for profile in profiles for source in profile['source_ids']}
    work, comparisons = [], []
    for model in ('qwen3-8b', 'qwen3-235b-a22b'):
        policies = ('balanced', 'concentrated') if '235b' in model else ('balanced',)
        for batch in (1, 8, 32):
            for history in (8191, 32767):
                for bits in (16, 8, 4):
                    for policy in policies:
                        row = workload(model, batch, history, bits, policy)
                        work.append(row)
                        for profile in profiles:
                            comparisons.extend(compare(row, profile, catalog['h100-sxm']))
    return dict(schema_version=1, calculation='storage-generation-comparison',
                baseline_device='h100-sxm', hardware_profiles=profiles,
                hardware_sources=[r for r in records() if r.get('id') in source_ids],
                workloads=work, comparisons=comparisons,
                assumptions=[
                    'One device, all weights resident; no implicit TP, offload or expert eviction.',
                    'History is before the current forward. Final retained positions are 8192 or 32768.',
                    'Low-bit storage is the public declared grouped format, not a verified quantized checkpoint or a quality claim. KV and embedding/head remain BF16.',
                    'Workspace is an explicit 2 GiB reserve, not an estimate of complete runtime or conversion buffers. Capacity success is conditional.',
                    'Selected weights/scales are read once per layer and reused across this batch. Expert routing is declared, not measured. All experts remain in resident bytes.',
                    'Prior KV read, current KV operand read and current append write are distinct logical interfaces. Internal forwarding may avoid current-record HBM reads.',
                    'Payload excludes activation intermediates, temporary conversion traffic, cache effects and runtime traffic. Payload/bandwidth is a conditional service budget for these interfaces, not full latency or an unconditional HBM lower bound.',
                    'Nominal memory capacity and peak bandwidth retain official scope. Apple memory is shared with CPU/OS; no ANE or undisclosed FLOPs enter this comparison.',
                    'Capacity-only and bandwidth-only rows are hypothetical changes around H100 SXM, not additional products.',
                ])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.write_text(json.dumps(calculate(), ensure_ascii=False, indent=2) + '\n')
