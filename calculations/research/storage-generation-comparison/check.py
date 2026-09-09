"""Independent closed-form check; never imports candidate or model adapters."""
import hashlib
import json
from fractions import Fraction
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[1]
r = json.loads((HERE / 'result.json').read_text())
checks = 0

def equal(actual, expected):
    global checks
    assert actual == expected, (actual, expected)
    checks += 1

for work in r['workloads']:
    c = json.loads((PROJECT / 'configs/models' / work['model'] / 'config.json').read_text())
    H, L, V, D, Q, K = (c[k] for k in ('hidden_size', 'num_hidden_layers', 'vocab_size',
                                       'head_dim', 'num_attention_heads', 'num_key_value_heads'))
    equal(c['tie_word_embeddings'], False)
    bits, B, S = work['matrix_storage_bits'], work['batch'], work['history']
    def packed(rows, columns):
        if bits == 16:
            return 2 * rows * columns
        return rows * ((columns * bits + 7) // 8 + 2 * ((columns + 127) // 128))
    attention = L * (packed(Q * D, H) + 2 * packed(K * D, H) + packed(H, Q * D))
    norms = 2 * (L * (2 * D + 2 * H) + H)
    embeddings_and_head = 4 * V * H
    common = attention + norms + embeddings_and_head
    if c['model_type'] == 'qwen3_moe':
        E, top, F = c['num_experts'], c['num_experts_per_tok'], c['moe_intermediate_size']
        expert = L * (2 * packed(F, H) + packed(H, F))
        common += 2 * L * E * H
        active = min(E, B * top) if work['routing'] == 'balanced' else top
        resident = common + E * expert
        read = common + active * expert
        equal(sum(work['expert_counts']), B * top)
        equal(sum(x > 0 for x in work['expert_counts']), active)
    else:
        F = c['intermediate_size']
        ffn = L * (2 * packed(F, H) + packed(H, F))
        resident = read = common + ffn
    read -= 2 * V * H
    read += 2 * B * H
    unit = 4 * L * K * D
    equal(work['resident_weight_bytes'], resident)
    equal(work['payload_components_bytes']['weight_payload'] + work['payload_components_bytes']['weight_scales'], read)
    equal(work['kv_bytes_per_request'], (S + 1) * unit)
    equal(work['accounted_payload_bytes'], read + B * (S + 2) * unit)
    equal(work['resident_budget_bytes'], resident + B * (S + 1) * unit + 2**31)

workloads = {w['id']: w for w in r['workloads']}
profiles = {p['id']: p['memory'] for p in r['hardware_profiles']}
base = profiles[r['baseline_device']]
for row in r['comparisons']:
    w = workloads[row['workload']]
    selected = profiles[row['device']]
    capacity_profile = base if row['mode'] == 'bandwidth_only' else selected
    bandwidth_profile = base if row['mode'] == 'capacity_only' else selected
    # All five selected official profiles use decimal GB.
    equal(capacity_profile['capacity_unit'], 'GB')
    cap = capacity_profile['nominal_capacity'] * 10**9
    rate = Fraction(str(bandwidth_profile['bandwidth_bytes_per_second']))
    time = Fraction(w['accounted_payload_bytes']) / rate
    equal(row['capacity_bytes'], cap)
    equal(row['payload_service_seconds'], {'numerator': time.numerator, 'denominator': time.denominator})
    fits = w['resident_budget_bytes'] <= cap
    equal(row['passes_declared_capacity'], fits)
    equal(row['capacity_qualified_payload_service_seconds'], row['payload_service_seconds'] if fits else None)
    count = row['maximum_requests_for_declared_capacity']
    fixed = w['resident_weight_bytes'] + 2**31
    equal(count, max(0, (cap - fixed) // w['kv_bytes_per_request']))
    if count:
        equal(fixed + count * w['kv_bytes_per_request'] <= cap, True)
    equal(fixed + (count + 1) * w['kv_bytes_per_request'] > cap, True)

output = dict(status='passed', independent_checks=checks, workloads=len(workloads),
              comparisons=len(r['comparisons']), sha256={
                  name: hashlib.sha256((HERE / name).read_bytes()).hexdigest()
                  for name in ('calculate.py', 'result.json')})
(HERE / 'verification.json').write_text(json.dumps(output, indent=2) + '\n')
print(json.dumps(output, indent=2))
