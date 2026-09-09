#!/usr/bin/env python3
"""Independent integer accounting; reads JSON data only, executes no imported code."""
import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[3])
    args = parser.parse_args()
    root = args.root.resolve()
    files = {
        'config': 'references/outline-checks/2026-09-07/scaling-history/qwen3-235b-config.json',
        'capacity': 'research/2026-infra-survey/parallel-moe-ownership/inputs/capacity.json',
        'independent_tokens_communication': 'research/2026-infra-survey/parallel-moe-ownership/inputs/independent-source-communication.json',
    }
    original = {key: (root / path).read_bytes() for key, path in files.items()}
    inputs = {key: json.loads(value) for key, value in original.items()}
    c, capacity = inputs['config'], inputs['capacity']
    assert hashlib.sha256(original['config']).hexdigest() == (
        '0ecd5d6fe6f2db6739e4e36ab06b88ebe7bd013ef31b9583f43796059a2b23a4')
    h, f, layers = c['hidden_size'], c['moe_intermediate_size'], c['num_hidden_layers']
    nq, nk, dim = c['num_attention_heads'], c['num_key_value_heads'], c['head_dim']
    vocab, experts, top = c['vocab_size'], c['num_experts'], c['num_experts_per_tok']
    assert (h, f, layers, nq, nk, dim, experts, top) == (4096, 1536, 94, 64, 4, 128, 128, 8)
    tp, ep, total_ranks = 2, 4, 8
    assert not c['tie_word_embeddings'] and c['mlp_only_layers'] == []
    assert c['decoder_sparse_step'] == 1 and h % tp == f % tp == nk % tp == 0
    attn_rank = 2 * h * (nq + nk) * dim // tp
    expert_rank = 3 * h * (f // tp) * (experts // ep)
    norm_rank = 2 * h + 2 * dim
    rank_parameters = 2 * vocab * h // tp + layers * (
        attn_rank + expert_rank + h * experts + norm_rank) + h
    logical_parameters = 2 * vocab * h + layers * (
        2 * h * (nq + nk) * dim + 3 * h * f * experts + h * experts + norm_rank) + h
    assert logical_parameters == capacity['evidence']['unique_parameters']
    assert logical_parameters * 2 == capacity['evidence']['official_index_bf16_bytes']
    kv_per_position_rank = 2 * layers * (nk // tp) * dim * 2
    weight_bytes = rank_parameters * 2
    for rank in capacity['ranks']:
        bf16 = next(x for x in rank['formats'] if x['bits'] == 16)
        assert bf16['weight_bytes'] == weight_bytes
        assert bf16['kv_bytes_per_request'] == kv_per_position_rank * 8192
    tp_groups = [[2 * e, 2 * e + 1] for e in range(ep)]
    ep_groups = [[2 * e + t for e in range(ep)] for t in range(tp)]
    server = lambda rank: 'A' if rank < 4 else 'B'
    layouts = [{
        'rank': r, 'server': server(r), 'dp': 0, 'pp': 0, 'ep': r // 2, 'tp': r % 2,
        'layers_half_open': [0, layers],
        'expert_ids_half_open': [r // 2 * 32, (r // 2 + 1) * 32],
        'q_heads_half_open': [r % 2 * 32, (r % 2 + 1) * 32],
        'kv_heads_half_open': [r % 2 * 2, (r % 2 + 1) * 2],
        'expert_intermediate_half_open': [r % 2 * 768, (r % 2 + 1) * 768],
        'physical_parameters': rank_parameters, 'bf16_weight_bytes': weight_bytes,
    } for r in range(total_ranks)]

    def ring_records(groups, message, stage):
        records = []
        for group_id, group in enumerate(groups):
            size = len(group)
            assert message % size == 0
            for step in range(2 * (size - 1)):
                for i, src in enumerate(group):
                    dst = group[(i + 1) % size]
                    records.append({'stage': stage, 'group': group_id, 'round': step,
                                    'source': src, 'destination': dst,
                                    'bytes': message // size,
                                    'cross_server': server(src) != server(dst)})
        return records

    def selected(position):
        return [(8 * position + k) % experts for k in range(top)]

    # Check expert ownership and the two-stage reduction with exact integer toy values.
    proof = []
    for position in [0, 1, 3, 4, 7, 8191, 8192]:
        routes = selected(position)
        shards = [sum((1000 * position + expert + 1) * (r % 2 + 1)
                      for expert in routes if expert // 32 == r // 2) for r in range(8)]
        after_tp = [sum(shards[x] for x in tp_groups[r // 2]) for r in range(8)]
        final = [sum(after_tp[x] for x in ep_groups[r % 2]) for r in range(8)]
        expected = 3 * sum(1000 * position + expert + 1 for expert in routes)
        assert final == [expected] * 8
        proof.append({'position': position, 'routes': routes, 'rank_partial': shards,
                      'after_tp': after_tp, 'after_ep': final, 'logical_expected': expected})

    def phase(name, history, new_tokens):
        positions = range(history, history + new_tokens)
        counts = Counter(expert for pos in positions for expert in selected(pos))
        assert sum(counts.values()) == new_tokens * top
        message = new_tokens * h * 4  # Explicit FP32 reduction wire format.
        records = ring_records(tp_groups, message, 'attention_tp')
        records += ring_records(tp_groups, message, 'expert_tp')
        records += ring_records(ep_groups, message, 'expert_ep')
        pair_bytes = defaultdict(int)
        for record in records:
            pair_bytes[(record['stage'], record['source'], record['destination'])] += record['bytes']
        pairs = [{'stage': stage, 'source': src, 'destination': dst, 'bytes': size,
                  'cross_server': server(src) != server(dst)}
                 for (stage, src, dst), size in sorted(pair_bytes.items())]
        rank_rows = []
        valid_pairs = new_tokens * history + new_tokens * (new_tokens + 1) // 2
        for r in range(8):
            ids = range(r // 2 * 32, (r // 2 + 1) * 32)
            assignments = sum(counts[x] for x in ids)
            sent = {stage: sum(x['bytes'] for x in records if x['source'] == r and x['stage'] == stage)
                    for stage in ['attention_tp', 'expert_tp', 'expert_ep']}
            received = {stage: sum(x['bytes'] for x in records if x['destination'] == r and x['stage'] == stage)
                        for stage in sent}
            assert sent == received
            row = {'rank': r, 'logical_local_expert_assignments': assignments,
                   'distinct_local_experts': sum(counts[x] > 0 for x in ids),
                   'logical_local_assignment_input_bytes': assignments * h * 2,
                   'network_input_dispatch_send_bytes': 0, 'network_input_dispatch_receive_bytes': 0,
                   'expert_shard_matrix_flops_per_layer': 6 * assignments * h * (f // tp),
                   'ideal_distinct_expert_weight_read_bytes_per_layer': sum(counts[x] > 0 for x in ids) * 3 * h * (f // tp) * 2,
                   'attention_matrix_flops_per_layer': 2 * new_tokens * attn_rank + 4 * (nq // tp) * dim * valid_pairs,
                   'old_kv_bytes': history * kv_per_position_rank,
                   'new_kv_write_bytes': new_tokens * kv_per_position_rank,
                   'end_kv_bytes': (history + new_tokens) * kv_per_position_rank,
                   'ideal_decode_old_kv_read_bytes': history * kv_per_position_rank if new_tokens == 1 else None,
                   'send_bytes_per_layer': sent, 'receive_bytes_per_layer': received}
            row['weight_plus_end_kv_plus_declared_workspace_bytes'] = weight_bytes + row['end_kv_bytes'] + 2**31
            rank_rows.append(row)
        # Two TP shards compute each logical expert assignment; their intermediate widths are disjoint.
        assert sum(x['logical_local_expert_assignments'] for x in rank_rows) == new_tokens * top * tp
        assert sum(x['expert_shard_matrix_flops_per_layer'] for x in rank_rows) == 6 * new_tokens * top * h * f
        logical_attention = 2 * new_tokens * attn_rank * tp + 4 * nq * dim * valid_pairs
        assert sum(x['attention_matrix_flops_per_layer'] for x in rank_rows) == logical_attention * ep
        assert sum(x['end_kv_bytes'] for x in rank_rows) == (history + new_tokens) * 2 * layers * nk * dim * 2 * ep
        cross = sum(x['bytes'] for x in records if x['cross_server'])
        assert cross == 6 * message
        for stage, per_rank in [('attention_tp', message), ('expert_tp', message), ('expert_ep', 3 * message // 2)]:
            assert all(row['send_bytes_per_layer'][stage] == per_rank for row in rank_rows)
        return {'name': name, 'history_positions': history, 'new_positions': new_tokens,
                'cohort_requests': 1, 'logical_assignments_per_layer': new_tokens * top,
                'kv_scope': 'Full 94-layer retained state and known interface bytes, not per layer or measured HBM',
                'per_expert_counts': [counts[e] for e in range(experts)], 'ranks': rank_rows,
                'wire_dtype': 'FP32', 'reduction_input_bytes': message,
                'collective_messages': records, 'source_destination_totals': pairs,
                'network_send_per_layer_bytes': sum(x['bytes'] for x in records),
                'cross_server_send_per_layer_bytes': cross,
                'cross_server_each_direction_per_layer_bytes': cross // 2,
                'cross_server_send_94_layers_bytes': cross * layers,
                'modeled_seconds': None, 'measured_seconds': None}

    out = {'scope': 'One BF16 Qwen3-235B teaching layout, DP1 TP2 EP4 PP1; replicated attention cohort',
           'sources': {key: {'file': files[key], 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}
                       for key, data in original.items()},
           'weights': {'logical_parameters': logical_parameters, 'logical_bf16_bytes': logical_parameters * 2,
                       'physical_bf16_bytes': weight_bytes * 8, 'per_rank_parameters': rank_parameters,
                       'per_rank_weight_bytes': weight_bytes},
           'capacity_bytes_per_rank': 80000000000, 'declared_workspace_bytes_per_rank': 2**31,
           'layout': layouts, 'tp_groups': tp_groups, 'ep_groups': ep_groups,
           'routing_rule': 'expert(position,k)=(8*position+k)%128, k=0..7; same all layers; teaching only',
           'phases': [phase('prefill_8192_from_empty', 0, 8192), phase('first_decode_after_prefill', 8192, 1)],
           'integer_reduction_proof': proof,
           'checks': {'capacity_summary_matches_all_8_existing_ranks': True,
                      'logical_parameter_count_matches_existing_evidence': True,
                      'expert_flops_preserved_across_tp_shards': True,
                      'attention_matrix_work_replicates_4_times_across_ep': True,
                      'kv_replicates_4_times_across_ep': True,
                      'send_receive_and_physical_edges_conserved': True,
                      'integer_reduction_recovers_one_logical_result_on_every_rank': True},
           'limitations': ['Not a vLLM/SGLang default implementation or measured result.',
                           'Exact integer proof does not establish BF16/FP32 bitwise equivalence.',
                           'No input dispatch is needed only because attention/hidden states and routing replicate across EP.',
                           'Fixed full-shape rings include zero contributions; no data-dependent collective skipping.',
                           'Per-layer network covers attention output TP, expert TP and expert EP reductions only.',
                           'Embedding, head, sampling, token/routing setup, protocol overhead and physical routing beyond server cut omitted.',
                           'Prefill KV HBM reads, full temporary peaks and actual collective overlap not predicted.']}
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
