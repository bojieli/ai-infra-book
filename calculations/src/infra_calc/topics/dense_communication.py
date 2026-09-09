"""Communication-only path for the declared vocabulary-parallel Dense placement.

Includes input embedding reduction, per-layer output reductions, PP activation,
full-logit all-gather, and selected-token feedback. No compute/queue time is added.
"""
from ..sources import model_config, provenance
from ..units import positive_int
from . import dense_placement


def calculate(model: str = 'qwen3-8b', tp: int = 8, pp: int = 1, dp: int = 1,
              batch_per_replica: int = 1, tokens: int = 1,
              bandwidth_bytes_per_second: int = 50_000_000_000, startup_ns: int = 2000,
              logit_element_bytes: int = 4) -> dict:
    for name, value in (('bandwidth_bytes_per_second', bandwidth_bytes_per_second), ('logit_element_bytes', logit_element_bytes)):
        positive_int(value, name)
    positive_int(startup_ns, 'startup_ns', allow_zero=True)
    placement = dense_placement.calculate(model, tp, pp, dp, batch_per_replica, 0, tokens)
    c = model_config(model)
    activation = 2 * batch_per_replica * tokens * c['hidden_size']
    logits = logit_element_bytes * batch_per_replica * c['vocab_size']
    token_ids = 4 * batch_per_replica
    alpha = startup_ns / 1e9
    operations = []

    def add(name, stage, rounds, network_bytes, bottleneck_bytes, note, layer=None):
        operations.append(dict(name=name, stage=stage, layer=layer, rounds=rounds,
                               network_send_bytes_per_replica=network_bytes,
                               critical_resource_bytes=bottleneck_bytes,
                               startup_seconds=rounds * alpha,
                               bandwidth_seconds=bottleneck_bytes / bandwidth_bytes_per_second,
                               modeled_seconds=rounds * alpha + bottleneck_bytes / bandwidth_bytes_per_second,
                               notes=note))

    def all_reduce(name, stage, layer=None):
        # Actual placement ensures whole heads and hence integral BF16 chunks.
        if activation % tp:
            raise ValueError('Ring activation chunks must be integral bytes')
        per_rank = 2 * (tp - 1) * (activation // tp)
        add(name, stage, 2 * (tp - 1), tp * per_rank, per_rank,
            'Full hidden activation M, ring RS+AG, independent directed edges.', layer)

    all_reduce('vocabulary_embedding_reduce', 0)
    representatives = sorted((row for row in placement['placement_cards'] if row['replica'] == 0 and row['tp_rank'] == 0),
                             key=lambda row: row['stage'])
    for card in representatives:
        stage = card['stage']
        for layer in card['layer_ids']:
            all_reduce('attention_output_reduce', stage, layer)
            all_reduce('ffn_output_reduce', stage, layer)
        if stage < pp - 1:
            add('pipeline_hidden_transfer', stage, 1, tp * activation, activation,
                'Each TP rank sends full replicated hidden to matching next-stage rank; links assumed independent.')
    if logits % tp:
        raise ValueError('Vocabulary shards require integral logit bytes')
    shard = logits // tp
    add('last_position_logits_all_gather', pp - 1, tp - 1, tp * (tp - 1) * shard, (tp - 1) * shard,
        'Each last-stage TP rank starts with B×V/TP logits and gathers full B×V. Wire element size is explicit.')
    if pp > 1:
        add('selected_token_to_first_stage', pp - 1, 1, token_ids, token_ids,
            'After local sampling on last-stage rank 0, send selected int32 token IDs to first-stage rank 0.')
    broadcast_rounds = (tp - 1).bit_length()
    add('selected_token_first_stage_broadcast', 0, broadcast_rounds, (tp - 1) * token_ids, broadcast_rounds * token_ids,
        'Unsegmented binomial broadcast of int32 IDs inside first-stage TP group; other stages receive hidden activations.')
    total = sum(row['network_send_bytes_per_replica'] for row in operations)
    stage_bytes = [sum(row['network_send_bytes_per_replica'] for row in operations if row['stage'] == stage) for stage in range(pp)]
    return dict(schema_version=1, calculation='qwen-dense-communication-path', model=model,
                scenario=dict(tp=tp, pp=pp, dp=dp, batch_per_replica=batch_per_replica, tokens=tokens,
                              bandwidth_bytes_per_second=bandwidth_bytes_per_second, startup_ns=startup_ns,
                              logit_element_bytes=logit_element_bytes),
                sources=provenance(model), communication_operations=operations,
                summary=dict(activation_bytes=activation, full_last_position_logit_bytes=logits,
                             vocabulary_logit_shard_bytes=shard, selected_token_id_bytes=token_ids,
                             nonempty_communication_operations=sum(row['network_send_bytes_per_replica'] > 0 for row in operations),
                             network_send_bytes_per_replica=total, network_send_bytes_all_replicas=dp * total,
                             operation_stage_accounted_bytes=stage_bytes,
                             serial_communication_path_seconds=sum(row['modeled_seconds'] for row in operations),
                             startup_seconds=sum(row['startup_seconds'] for row in operations),
                             bandwidth_seconds=sum(row['bandwidth_seconds'] for row in operations),
                             predicted_iteration_seconds=None),
                assumptions=[
                    'One forward plus selected-token feedback for the next call. Input vocabulary embedding shards produce masked partial hidden vectors and need an all-reduce, in addition to two output reductions per decoder layer.',
                    'Hidden states are replicated across TP ranks at PP boundaries; matching-rank sends are explicit and not deduplicated. The basic placement is inherited from dense-placement, not inferred from aggregate device memory.',
                    'Only last-position vocabulary logits are gathered, regardless of input token count. Default four-byte wire logits are a scenario choice, not a claim about every framework output dtype. All-gather is the declared sampling strategy, not the only distributed sampling algorithm.',
                    'Sampling computation is excluded. Last-stage rank 0 sends int32 IDs to first-stage rank 0 when PP>1; first-stage TP broadcasts them. Scheduler metadata, RNG coordination, masks and position control messages are not included.',
                    'Operations lie on the declared serial dependency path for one microbatch. Summed communication models omit compute, overlap, queueing and pipeline bubbles, so no full iteration time is reported.',
                    'All links in each collective/PP boundary are assumed independent with the same effective one-direction bandwidth and startup. Shared fabric resources and physical hops require the separate traffic mapper.',
                    'DP duplicates bytes across independent replicas but does not multiply this per-replica path time. Global shared-network throughput cannot be inferred without mapping those replicas.',
                    'Norm statistics use local complete hidden/head vectors in this placement and require no extra cross-rank normalization reduction. Other sequence-parallel layouts would change that communication graph.',
                ])
