"""Unsegmented binomial reduce plus reverse-tree broadcast, rooted at rank 0.

This is a declared algorithm, not NCCL's double-tree implementation. Every edge
carries the full tensor; each round is a barrier before the next round starts.
"""
from ..sources import model_config, provenance
from ..units import positive_int


def schedule(participants: int, payload_bytes: int) -> list[dict]:
    positive_int(participants, 'participants')
    positive_int(payload_bytes, 'payload_bytes')
    reduction = []
    stride = 1
    while stride < participants:
        edges = [dict(sender=base + stride, receiver=base, bytes=payload_bytes)
                 for base in range(0, participants, 2 * stride) if base + stride < participants]
        reduction.append(dict(phase='reduce', step=len(reduction), edges=edges))
        stride *= 2
    broadcast = [dict(phase='broadcast', step=i,
                      edges=[dict(sender=edge['receiver'], receiver=edge['sender'], bytes=payload_bytes)
                             for edge in row['edges']]) for i, row in enumerate(reversed(reduction))]
    return reduction + broadcast


def calculate(model: str = 'qwen3-8b', batch: int = 1, tokens: int = 1,
              participants: int = 8, bandwidth_bytes_per_second: int = 50_000_000_000,
              startup_ns: int = 2000) -> dict:
    for key, value in (('batch', batch), ('tokens', tokens), ('participants', participants),
                       ('bandwidth_bytes_per_second', bandwidth_bytes_per_second)):
        positive_int(value, key)
    positive_int(startup_ns, 'startup_ns', allow_zero=True)
    c = model_config(model)
    if c['model_type'] != 'qwen3':
        raise ValueError('Basic two-all-reduce-per-layer TP example requires Qwen3 Dense')
    elements = batch * tokens * c['hidden_size']
    payload = 2 * elements
    rounds = schedule(participants, payload)
    ranks = [dict(rank=i, sent_bytes=0, received_bytes=0, reduction_adds=0) for i in range(participants)]
    for row in rounds:
        for edge in row['edges']:
            ranks[edge['sender']]['sent_bytes'] += payload
            ranks[edge['receiver']]['received_bytes'] += payload
            if row['phase'] == 'reduce':
                ranks[edge['receiver']]['reduction_adds'] += elements
    latency = len(rounds) * startup_ns / 1e9
    transfer = len(rounds) * payload / bandwidth_bytes_per_second
    calls = 2 * c['num_hidden_layers']
    return dict(schema_version=1, calculation='qwen-binomial-tree-collective', model=model,
                scenario=dict(batch=batch, tokens=tokens, participants=participants,
                              bandwidth_bytes_per_second=bandwidth_bytes_per_second, startup_ns=startup_ns,
                              root=0, message_dtype='BF16', segmentation=False),
                sources=provenance(model), tree_rounds=rounds, collective_ranks=ranks,
                summary=dict(activation_shape=[batch * tokens, c['hidden_size']], message_bytes_per_rank=payload,
                             rounds_per_phase=len(rounds) // 2, all_reduce_rounds=len(rounds),
                             all_reduce_network_send_bytes=sum(row['sent_bytes'] for row in ranks),
                             all_reduce_global_reduction_adds=sum(row['reduction_adds'] for row in ranks),
                             maximum_rank_send_bytes=max(row['sent_bytes'] for row in ranks),
                             maximum_rank_receive_bytes=max(row['received_bytes'] for row in ranks),
                             all_reduce_startup_seconds=latency, all_reduce_bandwidth_seconds=transfer,
                             all_reduce_modeled_seconds=latency + transfer,
                             dense_tp_all_reduce_calls=calls,
                             dense_tp_serial_collective_seconds=calls * (latency + transfer),
                             measured_collective_seconds=None),
                assumptions=[
                    'Same Qwen3 Dense BF16 [B*T,H] partial activation on every rank. Basic TP calls two output all-reduces per layer; no device placement or backend dispatch claim.',
                    'Binomial reduction rooted at zero followed by the reverse edge schedule for broadcast. Non-power-of-two groups skip absent partners; p=1 is identity. Integer replay validates this schedule, not floating-point bitwise equivalence.',
                    'Each edge sends the full M-byte tensor. Each round completes before the next, with independent simultaneous directed edges and one startup per round. This unsegmented algorithm is not a double binary tree, recursive halving/doubling or a model of every library tree.',
                    'Network volume is 2(p-1)M, equal to ring all-reduce volume, but rank traffic is nonuniform and critical-path transfers are full tensors. Message-size-dependent performance differs despite equal total volume.',
                    'Per-rank reduction additions are separate scalar work; precision, reduction service time, topology hops, link sharing, launch, segmentation and overlap are excluded from the declared timing model.',
                    'Bandwidth is one-direction effective link bandwidth; startup and bandwidth defaults are teaching assumptions. Serial 2L total is not complete TP iteration latency or measured NCCL performance.',
                ])
