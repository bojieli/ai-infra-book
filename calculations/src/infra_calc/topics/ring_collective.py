"""Explicit ring reduce-scatter/all-gather schedule for Qwen activation payloads."""
from ..sources import model_config, provenance
from ..units import positive_int


def schedule(participants: int, chunk_bytes: int) -> list[dict]:
    rounds = []
    for phase in ('reduce_scatter', 'all_gather'):
        for step in range(participants - 1):
            edges = [dict(sender=rank, receiver=(rank + 1) % participants,
                          chunk=(rank - step + (1 if phase == 'all_gather' else 0)) % participants,
                          bytes=chunk_bytes) for rank in range(participants)]
            rounds.append(dict(phase=phase, step=step, edges=edges))
    return rounds


def calculate(model: str = 'qwen3-8b', batch: int = 1, tokens: int = 1,
              participants: int = 8, bandwidth_bytes_per_second: int = 50_000_000_000,
              startup_ns: int = 2000) -> dict:
    for key, value in (('batch', batch), ('tokens', tokens), ('participants', participants),
                       ('bandwidth_bytes_per_second', bandwidth_bytes_per_second)):
        positive_int(value, key)
    positive_int(startup_ns, 'startup_ns', allow_zero=True)
    c = model_config(model)
    if c['model_type'] != 'qwen3':
        raise ValueError('Two all-reduces per layer assumption requires the Qwen3 Dense TP teaching path')
    hidden, layers = c['hidden_size'], c['num_hidden_layers']
    elements, payload = batch * tokens * hidden, 2 * batch * tokens * hidden
    if elements % participants:
        raise ValueError('Equal ring chunks must contain an integer number of BF16 elements')
    chunk = payload // participants
    phase_rounds = participants - 1
    phase_send = phase_rounds * chunk
    phase_time = phase_rounds * startup_ns / 1e9 + phase_send / bandwidth_bytes_per_second
    phases = [dict(name=name, rounds=phase_rounds,
                   initial_bytes_per_rank=payload if name == 'reduce_scatter' else chunk,
                   final_bytes_per_rank=chunk if name == 'reduce_scatter' else payload,
                   send_bytes_per_rank=phase_send, receive_bytes_per_rank=phase_send,
                   total_network_send_bytes=participants * phase_send,
                   reduction_adds_per_rank=phase_send // 2 if name == 'reduce_scatter' else 0,
                   modeled_seconds=phase_time) for name in ('reduce_scatter', 'all_gather')]
    per_call = 2 * phase_time
    return dict(schema_version=1, calculation='qwen-ring-collective', model=model,
                scenario=dict(batch=batch, tokens=tokens, participants=participants,
                              bandwidth_bytes_per_second=bandwidth_bytes_per_second, startup_ns=startup_ns,
                              message_dtype='BF16', message_scope='full activation per rank for all-reduce'),
                sources=provenance(model), ring_rounds=schedule(participants, chunk), collective_phases=phases,
                summary=dict(activation_shape=[batch * tokens, hidden], message_bytes_per_rank=payload,
                             chunk_bytes=chunk, all_reduce_rounds=2 * phase_rounds,
                             all_reduce_send_bytes_per_rank=2 * phase_send,
                             all_reduce_receive_bytes_per_rank=2 * phase_send,
                             all_reduce_network_send_bytes=2 * participants * phase_send,
                             all_reduce_global_reduction_adds=(participants - 1) * elements,
                             all_reduce_startup_seconds=2 * phase_rounds * startup_ns / 1e9,
                             all_reduce_bandwidth_seconds=2 * phase_send / bandwidth_bytes_per_second,
                             all_reduce_modeled_seconds=per_call,
                             dense_tp_all_reduce_calls=2 * layers,
                             dense_tp_serial_collective_seconds=2 * layers * per_call,
                             measured_collective_seconds=None),
                assumptions=[
                    'Qwen3 Dense BF16 [B*T,H] partial output per rank; two row-parallel output all-reduces per layer is an explicit basic TP execution assumption, not every backend implementation.',
                    'Reduce-scatter starts with the full M-byte partial tensor on each rank and ends with M/p reduced bytes; all-gather starts with those M/p bytes and ends with M bytes. Do not interpret M as per-rank input for both phases.',
                    'Every round sends one chunk to the next rank. After reduce-scatter rank r owns reduced chunk (r+1) mod p; all-gather follows that ownership. p=1 is an identity with zero communication.',
                    'Per-rank sent and received bytes are separate endpoint counters. Network payload sums sends once, not sends plus receives. Physical hops, shared links, multiport paths and staging require a topology model.',
                    'Time assumes a balanced ring with simultaneous independent directed edges, one startup per round and one-direction effective link bandwidth. Reduction compute, launch, contention, overlap and channels are not measured here.',
                    'Reduction scalar additions are logical counts; accumulator precision and floating-point reassociation require a backend-specific analysis. They are not Tensor FLOPs.',
                    'Serial 2L-call total deliberately excludes overlap and fusion. Only communication for the stated TP path is counted; weights, KV placement, compute and device feasibility are separate.',
                ])
