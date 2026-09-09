"""FIFO inference pipeline with explicit compute, transfer and feedback timing.

Durations are scenario inputs. An activation's sender and receiver buffers have
separate declared lifetimes; no measured accelerator performance is invented.
"""
from heapq import heappop, heappush
from ..sources import model_config, provenance
from ..units import positive_int


def peak_intervals(intervals: list[tuple[int, int, int]]) -> int:
    events = []
    for start, end, size in intervals:
        if end > start:
            events.extend(((start, size), (end, -size)))
    current = peak = 0
    for time, delta in sorted(events, key=lambda item: (item[0], item[1])):
        current += delta  # release before allocation when timestamps coincide
        peak = max(peak, current)
    return peak


def calculate(model: str = 'qwen3-8b', microbatches: int = 4, requests_per_microbatch: int = 1,
              steps: int = 4, stage_ns: list[int] | None = None,
              transfer_ns: list[int] | None = None, feedback_ns: int = 100_000,
              buffer_slots: int | None = None) -> dict:
    stage_ns = [1_000_000] * 4 if stage_ns is None else stage_ns
    if not isinstance(stage_ns, list) or not stage_ns:
        raise ValueError('At least one stage duration is required')
    transfer_ns = [100_000] * (len(stage_ns) - 1) if transfer_ns is None else transfer_ns
    if buffer_slots is not None:
        positive_int(buffer_slots, 'buffer_slots')
    for key, value in (('microbatches', microbatches), ('requests_per_microbatch', requests_per_microbatch), ('steps', steps)):
        positive_int(value, key)
    if not isinstance(stage_ns, list) or not stage_ns:
        raise ValueError('At least one stage duration is required')
    if not isinstance(transfer_ns, list) or len(transfer_ns) != len(stage_ns) - 1:
        raise ValueError('One transfer duration per pipeline boundary is required')
    for value in stage_ns:
        positive_int(value, 'stage duration ns')
    for value in transfer_ns:
        positive_int(value, 'transfer duration ns', allow_zero=True)
    positive_int(feedback_ns, 'feedback ns', allow_zero=True)
    c = model_config(model)
    if c['model_type'] != 'qwen3':
        raise ValueError('Pipeline activation shape currently uses Qwen3 Dense')
    if len(stage_ns) > c['num_hidden_layers']:
        raise ValueError('Pipeline has more stages than decoder layers')
    size = 2 * requests_per_microbatch * c['hidden_size']
    stage_free = [0] * len(stage_ns)
    link_free = [0] * len(transfer_ns)
    sender_slots = [[(0, slot) for slot in range(buffer_slots or 0)] for _ in transfer_ns]
    receiver_slots = [[(0, slot) for slot in range(buffer_slots or 0)] for _ in transfer_ns]
    ready = [0] * microbatches
    operations, transfers, completions = [], [], [[] for _ in range(microbatches)]
    sender_intervals = [[] for _ in transfer_ns]
    receiver_intervals = [[] for _ in transfer_ns]
    for step in range(steps):
        for microbatch in range(microbatches):
            incoming_transfer = None
            available = ready[microbatch]
            for stage, duration in enumerate(stage_ns):
                baseline_start = max(available, stage_free[stage])
                sender_ready, sender_slot = (heappop(sender_slots[stage]) if buffer_slots is not None and stage < len(transfer_ns)
                                             else (0, None))
                start = max(baseline_start, sender_ready)
                end = start + duration
                operations.append(dict(step=step, microbatch=microbatch, stage=stage,
                                       ready_ns=available, start_ns=start, end_ns=end,
                                       sender_slot=sender_slot, sender_buffer_wait_ns=start - baseline_start))
                stage_free[stage] = end
                if incoming_transfer is not None:
                    receiver_intervals[stage - 1].append((incoming_transfer['start_ns'], end, size))
                    incoming_transfer['receiver_release_ns'] = end
                    if buffer_slots is not None:
                        heappush(receiver_slots[stage - 1], (end, incoming_transfer['receiver_slot']))
                if stage < len(transfer_ns):
                    baseline_send = max(end, link_free[stage])
                    receiver_ready, receiver_slot = heappop(receiver_slots[stage]) if buffer_slots is not None else (0, None)
                    send_start = max(baseline_send, receiver_ready)
                    send_end = send_start + transfer_ns[stage]
                    incoming_transfer = dict(step=step, microbatch=microbatch, boundary=stage,
                                             produced_ns=end, start_ns=send_start, end_ns=send_end, bytes=size,
                                             sender_slot=sender_slot, receiver_slot=receiver_slot,
                                             sender_reserved_ns=start if buffer_slots is not None else end,
                                             receiver_buffer_wait_ns=send_start - baseline_send)
                    transfers.append(incoming_transfer)
                    sender_intervals[stage].append((start if buffer_slots is not None else end, send_end, size))
                    if buffer_slots is not None:
                        heappush(sender_slots[stage], (send_end, sender_slot))
                    link_free[stage] = send_end
                    available = send_end
            completions[microbatch].append(end)
            ready[microbatch] = end + feedback_ns
    finish = max(row[-1] for row in completions)
    jobs = microbatches * steps
    buffers = [dict(boundary=i, sender_peak_bytes=peak_intervals(sender_intervals[i]),
                    receiver_peak_bytes=peak_intervals(receiver_intervals[i]),
                    joint_peak_bytes=peak_intervals(sender_intervals[i] + receiver_intervals[i]))
               for i in range(len(transfer_ns))]
    all_intervals = [item for intervals in sender_intervals + receiver_intervals for item in intervals]
    return dict(schema_version=1, calculation='qwen-fifo-inference-pipeline', model=model,
                scenario=dict(microbatches=microbatches, requests_per_microbatch=requests_per_microbatch, steps=steps,
                              stage_ns=stage_ns, transfer_ns=transfer_ns, feedback_ns=feedback_ns, buffer_slots=buffer_slots),
                sources=provenance(model), pipeline_operations=operations, pipeline_transfers=transfers,
                completion_ns_by_microbatch=completions, pipeline_buffers=buffers,
                stage_utilization=[dict(stage=i, busy_ns=jobs * duration, idle_ns=finish - jobs * duration,
                                        utilization=jobs * duration / finish) for i, duration in enumerate(stage_ns)],
                summary=dict(activation_bytes_per_boundary=size, total_jobs=jobs,
                             reserved_boundary_pool_bytes=2 * len(transfer_ns) * buffer_slots * size if buffer_slots is not None else None,
                             summed_sender_buffer_wait_ns=sum(row['sender_buffer_wait_ns'] for row in operations),
                             summed_receiver_buffer_wait_ns=sum(row['receiver_buffer_wait_ns'] for row in transfers),
                             total_processed_tokens=jobs * requests_per_microbatch, finish_ns=finish,
                             first_completion_ns=min(row[0] for row in completions),
                             last_first_step_completion_ns=max(row[0] for row in completions),
                             maximum_inter_step_completion_ns=max((b - a for row in completions for a, b in zip(row, row[1:])), default=None),
                             transfer_payload_bytes=len(transfers) * size,
                             declared_boundary_buffer_peak_bytes=peak_intervals(all_intervals),
                             throughput_tokens_per_second=jobs * requests_per_microbatch * 1e9 / finish,
                             actual_workspace_peak_bytes=None, measured_finish_ns=None),
                assumptions=[
                    'Each microbatch is a persistent group of requests; each step appends one token per request. All groups are initially ready. This excludes prompt prefill and does not label first completion as real TTFT.',
                    'Durations are explicit teaching or imported observations, not inferred from FLOPs or hardware peak. Stages and boundary links are independent serial resources; compute and transfers may overlap.',
                    'The fixed FIFO job order is step-major then microbatch index, identical at every stage/link. A group next step waits for its previous final-stage completion plus feedback lag. This is a specified policy, not an optimal/work-conserving scheduler claim.',
                    'Feedback is a per-group readiness lag with no shared feedback resource. It can represent assumed sampling/return delay but does not count their traffic or contention.',
                    'Hidden activations are BF16 [requests_per_microbatch,H] using official Qwen width. This models TP=1 pipeline boundaries; TP replication/sharding needs separate mapping.',
                    'With unlimited buffers, sender lifetime starts at production. With finite slots, output storage is conservatively reserved before producer compute and held through transfer completion. Receiver allocation starts at transfer start and ends after consumer compute; copies are separate.',
                    'buffer_slots=None preserves the unlimited-queue baseline. Finite slots constrain each boundary sender and receiver pool separately; earliest-free slots are reused only after recorded release. Producer or transfer waits when no slot is available. This reservation policy is explicit, not a claim of optimal overlap.',
                    'Reserved pool bytes differ from live bytes. Both exclude input/output, intra-stage activations, weights, KV, allocator alignment and scratch. Summed local buffer waits may overlap and must not be added again to makespan.',
                    'Stage idle time over the observed horizon includes fill/drain, feedback, imbalance and link stalls. It cannot all be called a single pipeline bubble percentage or applied to training schedules.',
                ])
