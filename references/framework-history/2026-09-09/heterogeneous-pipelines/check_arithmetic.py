#!/usr/bin/env python3
"""Independent teaching arithmetic only; never imports archived framework code."""
from pathlib import Path
import hashlib
import itertools
import json

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
config_path = ROOT / 'references/outline-checks/2026-09-07/scaling-history/qwen3-8b-config.json'
config = json.loads(config_path.read_text())
assert (config['num_hidden_layers'], config['hidden_size'], config['num_key_value_heads'], config['head_dim']) == (36, 4096, 8, 128)


def mincut(cross_capacity):
    # Every capacity is processed tokens/s for one fixed phase/shape profile.
    edges = [('s', 'A', 10000), ('s', 'C', 4000), ('A', 'B', 20000),
             ('C', 'D', 20000), ('A', 'D', cross_capacity),
             ('B', 't', 6000), ('D', 't', 8000)]
    values = []
    for bits in itertools.product([False, True], repeat=4):
        side = {'s'} | {n for n, include in zip(['A', 'C', 'B', 'D'], bits) if include}
        values.append(sum(c for a, b, c in edges if a in side and b not in side))
    bound = min(values)
    # Explicit feasible routes give the matching lower bound in this flow model.
    routes = {'A-B': 6000, 'C-D': 4000, 'A-D': min(cross_capacity, 4000)}
    assert routes['A-B'] + routes['A-D'] <= 10000
    assert routes['C-D'] + routes['A-D'] <= 8000
    assert sum(routes.values()) == bound == min(14000, 10000 + cross_capacity)
    return dict(cross_capacity=cross_capacity, min_cut=bound, feasible_routes=routes)


hidden = config['hidden_size'] * 2
payload = hidden * 2  # BF16 hidden_states + residual; TP=1, no auxiliary speculative tensors.
stage_kv = 2 * 18 * config['num_key_value_heads'] * config['head_dim'] * 2
link_bytes = 32768000  # Assumed effective one-way 31.25 MiB/s payload budget.
result = dict(
    scope='Own exact integer arithmetic and enumeration of 16 cuts; no downloaded code, model, GPU, simulator or cloud execution.',
    config=dict(file=str(config_path.relative_to(ROOT)), sha256=hashlib.sha256(config_path.read_bytes()).hexdigest()),
    assumptions=['36 layers split 18+18, TP=1, BF16 activations and GQA KV; no auxiliary speculative states.',
                 'Weights and workspace already fit per device; 4 GiB is the separate remaining KV budget.',
                 'Node service rates and link budgets are illustrative fixed-profile inputs, not card specifications or measured performance.',
                 'Network flow ignores pipeline fill/drain, request queues and KV constraints; check these separately before deployment.',
                 'No reuse of a prefill service rate for decode or a changed batch/context.'],
    logical_hidden_bytes_per_token=hidden,
    inspected_pp_tensor_bytes_per_token=payload,
    prefill_8192_pp_tensor_bytes=8192*payload,
    per_stage_kv_bytes_per_history_token=stage_kv,
    kv_capacity_cases=[dict(context=length, per_sequence_bytes=stage_kv*length,
                           capacity_only_sequences=(4*2**30)//(stage_kv*length)) for length in [8192, 16384]],
    flow_sweep=[mincut(c) for c in [0, 1000, 2000, 4000, 8000]],
    payload_sensitivity=dict(effective_link_bytes_per_second=link_bytes,
                            correct_cross_tokens_per_second=link_bytes//payload,
                            one_tensor_cross_tokens_per_second=link_bytes//hidden,
                            correct_flow_bound=mincut(link_bytes//payload)['min_cut'],
                            one_tensor_flow_bound=mincut(link_bytes//hidden)['min_cut']),
    latency_filter=dict(assumed_cross_link_propagation_ms=80, one_pass_budget_ms=50,
                        cross_edge_excluded=True, remaining_flow_bound=mincut(0)['min_cut'],
                        caveat='Removing this edge does not prove other paths meet the budget: compute and queue delays remain.'))
assert hidden == 8192 and payload == 16384 and stage_kv == 73728
assert result['prefill_8192_pp_tensor_bytes'] == 128*2**20
assert [x['capacity_only_sequences'] for x in result['kv_capacity_cases']] == [7, 3]
(HERE/'arithmetic.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
print('Passed: Qwen3 PP tensor payload, KV capacity and independently enumerated flow bounds.')
