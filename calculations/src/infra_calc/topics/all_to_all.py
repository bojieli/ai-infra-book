"""Pairwise all-to-all for explicit Qwen MoE token-expert assignment counts.

One full-width vector per assignment, no destination deduplication. Dispatch and
combine transpose the traffic matrix; local assignments never enter the network.
"""
from ..sources import model_config, provenance
from ..units import positive_int


def phase(counts: list[list[int]], vector_bytes: int, bandwidth: int, startup_ns: int) -> dict:
    p = len(counts)
    sends = [sum(row[j] for j in range(p) if j != i) * vector_bytes for i, row in enumerate(counts)]
    receives = [sum(counts[i][j] for i in range(p) if i != j) * vector_bytes for j in range(p)]
    rounds = []
    for offset in range(1, p):
        edges = [dict(sender=i, receiver=(i + offset) % p,
                      assignments=counts[i][(i + offset) % p], bytes=counts[i][(i + offset) % p] * vector_bytes)
                 for i in range(p) if counts[i][(i + offset) % p]]
        if edges:
            largest = max(edge['bytes'] for edge in edges)
            rounds.append(dict(offset=offset, edges=edges, modeled_seconds=startup_ns / 1e9 + largest / bandwidth))
    return dict(send_bytes_per_rank=sends, receive_bytes_per_rank=receives,
                network_send_bytes=sum(sends), rounds=rounds,
                endpoint_service_lower_seconds=max(sends + receives) / bandwidth,
                pairwise_barrier_modeled_seconds=sum(row['modeled_seconds'] for row in rounds))


def calculate(model: str = 'qwen3-235b-a22b', tokens_per_rank: int = 64, participants: int = 8,
              routing: str = 'balanced', counts: list[list[int]] | None = None,
              bandwidth_bytes_per_second: int = 50_000_000_000, startup_ns: int = 2000) -> dict:
    for key, value in (('tokens_per_rank', tokens_per_rank), ('participants', participants),
                       ('bandwidth_bytes_per_second', bandwidth_bytes_per_second)):
        positive_int(value, key)
    positive_int(startup_ns, 'startup_ns', allow_zero=True)
    c = model_config(model)
    if c['model_type'] != 'qwen3_moe':
        raise ValueError('Assignment all-to-all requires the Qwen3 MoE full-width expert path')
    experts, topk = c['num_experts'], c['num_experts_per_tok']
    if experts % participants:
        raise ValueError('This teaching placement requires equal integer experts per rank')
    assignments = tokens_per_rank * topk
    per_destination_limit = tokens_per_rank * min(topk, experts // participants)
    if counts is None:
        if routing == 'balanced':
            q, remainder = divmod(assignments, participants)
            counts = [[q + (((j - i) % participants) < remainder) for j in range(participants)] for i in range(participants)]
        elif routing == 'hotspot':
            counts = [[assignments] + [0] * (participants - 1) for _ in range(participants)]
        else:
            raise ValueError('Routing must be balanced or hotspot')
    if not isinstance(counts, list) or len(counts) != participants:
        raise ValueError('Counts must have one row per source rank')
    for row in counts:
        if not isinstance(row, list) or len(row) != participants:
            raise ValueError('Counts must be a square source/destination matrix')
        for count in row:
            positive_int(count, 'assignment count', allow_zero=True)
            if count > per_destination_limit:
                raise ValueError('Destination exceeds distinct top-k expert capacity')
        if sum(row) != assignments:
            raise ValueError('Each source row must conserve tokens_per_rank × top_k assignments')
    vector_bytes = 2 * c['hidden_size']
    dispatch = phase(counts, vector_bytes, bandwidth_bytes_per_second, startup_ns)
    reverse = [list(row) for row in zip(*counts)]
    combine = phase(reverse, vector_bytes, bandwidth_bytes_per_second, startup_ns)
    local = sum(counts[i][i] for i in range(participants))
    return dict(schema_version=1, calculation='qwen-moe-pairwise-all-to-all', model=model,
                scenario=dict(tokens_per_rank=tokens_per_rank, participants=participants, routing=routing,
                              bandwidth_bytes_per_second=bandwidth_bytes_per_second, startup_ns=startup_ns,
                              counts=counts, expert_placement='equal contiguous groups', payload_dtype='BF16'),
                sources=provenance(model), all_to_all_phases=dict(dispatch=dispatch, combine=combine),
                summary=dict(hidden_size=c['hidden_size'], top_k=topk, experts_per_rank=experts // participants,
                             assignments_per_source=assignments, vector_payload_bytes=vector_bytes,
                             local_assignments=local, remote_assignments=participants * assignments - local,
                             dispatch_network_send_bytes=dispatch['network_send_bytes'],
                             combine_network_send_bytes=combine['network_send_bytes'],
                             dispatch_maximum_receive_bytes=max(dispatch['receive_bytes_per_rank']),
                             dispatch_endpoint_service_lower_seconds=dispatch['endpoint_service_lower_seconds'],
                             dispatch_pairwise_modeled_seconds=dispatch['pairwise_barrier_modeled_seconds'],
                             dispatch_plus_combine_modeled_seconds=dispatch['pairwise_barrier_modeled_seconds'] + combine['pairwise_barrier_modeled_seconds'],
                             measured_seconds=None),
                assumptions=[
                    'One MoE layer: each source owns tokens_per_rank tokens, each chooses top_k distinct experts. Equal contiguous expert groups are a declared placement. Counts specify assignments by source/destination rank, not observed router output.',
                    'BF16 vector width comes from official Qwen3 MoE hidden_size. Send one vector per token-expert assignment even if several selected experts share a destination. Destination token deduplication, multicast and metadata are excluded.',
                    'Diagonal assignments remain local and cause no network traffic. Combine transposes dispatch counts, returning one full-width expert output per assignment; probability weighting and final sum are compute work outside this ledger.',
                    'Pairwise offset rounds have at most one send and one receive per rank. Independent full-duplex directed links run concurrently; the next round waits for the largest transfer of the current round. Globally empty rounds are skipped.',
                    'Endpoint bandwidth lower bound uses the maximum total sent or received by any rank. Summed round maxima include barrier imbalance; equal global bytes can therefore produce different endpoint and schedule times.',
                    'No topology hop count, shared-switch contention, expert execution, pipeline overlap, pack/unpack, padding, startup implementation or measured bandwidth is claimed. Declared link conditions are teaching inputs.',
                ])
