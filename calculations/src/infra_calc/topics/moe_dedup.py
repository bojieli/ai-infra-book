"""Token-identity-aware MoE dispatch deduplication and destination combine.

Identical source/destination assignment histograms can have different savings.
Only explicit per-token expert selections establish the destination union.
"""
from collections import Counter
from ..sources import model_config, provenance
from ..units import positive_int
from .all_to_all import phase


def calculate(model: str = 'qwen3-235b-a22b', tokens_per_rank: int = 64, participants: int = 8,
              pattern: str = 'clustered', routes: list | None = None, combine_element_bytes: int = 4,
              bandwidth_bytes_per_second: int = 50_000_000_000, startup_ns: int = 2000) -> dict:
    for name, value in (('tokens_per_rank', tokens_per_rank), ('participants', participants),
                        ('combine_element_bytes', combine_element_bytes), ('bandwidth_bytes_per_second', bandwidth_bytes_per_second)):
        positive_int(value, name)
    positive_int(startup_ns, 'startup_ns', allow_zero=True)
    c = model_config(model)
    if c['model_type'] != 'qwen3_moe':
        raise ValueError('Destination dedup adapter requires Qwen3 MoE')
    e, k, h = c['num_experts'], c['num_experts_per_tok'], c['hidden_size']
    if e % participants:
        raise ValueError('Equal expert groups require experts divisible by participants')
    group = e // participants
    if routes is None:
        if pattern not in ('clustered', 'spread'):
            raise ValueError('Pattern must be clustered or spread')
        routes = []
        for source in range(participants):
            rows = []
            for token in range(tokens_per_rank):
                if pattern == 'clustered':
                    chosen = [(((source + token) % participants) * group + j) % e for j in range(k)]
                else:
                    chosen = [((source + token + j) % participants) * group + (token + j // participants) % group for j in range(k)]
                rows.append(chosen)
            routes.append(rows)
    if not isinstance(routes, list) or len(routes) != participants:
        raise ValueError('Routes require one token list per source rank')
    assignments = [[0] * participants for _ in range(participants)]
    unique = [[0] * participants for _ in range(participants)]
    local_reduction = [0] * participants
    origin_reduction = [0] * participants
    records = []
    for source, tokens in enumerate(routes):
        if not isinstance(tokens, list) or len(tokens) != tokens_per_rank:
            raise ValueError('Each source must provide tokens_per_rank expert lists')
        for token, chosen in enumerate(tokens):
            if not isinstance(chosen, list) or len(chosen) != k:
                raise ValueError('Each token requires exactly top_k expert IDs')
            for expert in chosen:
                positive_int(expert, 'expert ID', allow_zero=True)
                if expert >= e:
                    raise ValueError('Expert ID outside official configuration')
            if len(set(chosen)) != k:
                raise ValueError('Top-k selections must contain distinct experts')
            destinations = Counter(expert // group for expert in chosen)
            for destination, count in destinations.items():
                assignments[source][destination] += count
                unique[source][destination] += 1
                local_reduction[destination] += (count - 1) * h
            origin_reduction[source] += (len(destinations) - 1) * h
            records.append(dict(source=source, token=token, experts=chosen, destination_counts=dict(destinations)))
    def transpose(matrix):
        return [list(row) for row in zip(*matrix)]
    variants = {}
    for name, matrix in (('per_assignment', assignments), ('per_destination', unique)):
        dispatch = phase(matrix, 2 * h, bandwidth_bytes_per_second, startup_ns)
        combine = phase(transpose(matrix), combine_element_bytes * h, bandwidth_bytes_per_second, startup_ns)
        variants[name] = dict(dispatch=dispatch, combine=combine)
    a, d = variants['per_assignment'], variants['per_destination']
    baseline_adds = participants * tokens_per_rank * (k - 1) * h
    if sum(local_reduction) + sum(origin_reduction) != baseline_adds:
        raise ValueError('Destination/source combination does not conserve reduction additions')
    return dict(schema_version=1, calculation='qwen-moe-destination-dedup', model=model,
                scenario=dict(tokens_per_rank=tokens_per_rank, participants=participants, pattern=pattern,
                              combine_element_bytes=combine_element_bytes, bandwidth_bytes_per_second=bandwidth_bytes_per_second,
                              startup_ns=startup_ns, routes=routes),
                sources=provenance(model), token_routes=records,
                assignment_counts=assignments, destination_token_counts=unique, dedup_variants=variants,
                reduction_placement=dict(destination_adds_per_rank=local_reduction, source_adds_per_rank=origin_reduction),
                summary=dict(per_assignment_dispatch_bytes=a['dispatch']['network_send_bytes'],
                             deduplicated_dispatch_bytes=d['dispatch']['network_send_bytes'],
                             per_assignment_combine_bytes=a['combine']['network_send_bytes'],
                             destination_combined_return_bytes=d['combine']['network_send_bytes'],
                             dispatch_saved_bytes=a['dispatch']['network_send_bytes'] - d['dispatch']['network_send_bytes'],
                             combine_saved_bytes=a['combine']['network_send_bytes'] - d['combine']['network_send_bytes'],
                             original_source_reduction_adds=baseline_adds,
                             destination_reduction_adds=sum(local_reduction), remaining_source_reduction_adds=sum(origin_reduction),
                             assignment_pairwise_seconds=a['dispatch']['pairwise_barrier_modeled_seconds'] + a['combine']['pairwise_barrier_modeled_seconds'],
                             dedup_pairwise_seconds=d['dispatch']['pairwise_barrier_modeled_seconds'] + d['combine']['pairwise_barrier_modeled_seconds'],
                             metadata_bytes=None, measured_seconds=None),
                assumptions=[
                    'One layer, equal contiguous expert placement. Explicit token identities are (source rank, token index); top-k expert IDs are unique and checked against official Qwen3 MoE configuration.',
                    'Dispatch sends a BF16 token once per destination rank, then that rank reuses it for its selected experts. This does not reduce expert GEMM rows or the number of token-expert computations.',
                    'Combine assumes routing weights are applied to each expert output before summing experts on the destination; return one partial per token/destination. The final source sums destination partials. Total scalar additions are conserved but their placement changes.',
                    'Default return elements are four-byte scenario values for both baseline and destination-combined paths; dispatch is two bytes. This is not a claim about the pinned inference backend wire dtype.',
                    'Reassociation preserves exact-real algebra but need not preserve floating-point bits. Numerical quality, rounding, execution placement and output compatibility need backend checks.',
                    'Counts alone cannot determine deduplication: clustered and spread routes can have the same assignment histogram but different token destination unions. Synthetic patterns are controlled examples, not measured model routing.',
                    'Diagonal local work never enters network phases. Metadata, probability transport, pack/unpack, buffers, multicast fabric and additional dependencies are excluded; modeled phase sums are not end-to-end speedups.',
                ])
