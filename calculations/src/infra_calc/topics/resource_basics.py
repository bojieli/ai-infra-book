"""Chapter-one unit conversion and per-device capacity, with teaching inputs.

Nominal 70B is deliberately not a substitute for an official checkpoint count.
The allocation is explicit: aggregate capacity is necessary, never sufficient.
"""
from ..units import positive_int, positive_number


def calculate(parameters: int = 70_000_000_000, weight_bits: int = 16, cards: int = 2,
              card_capacity_bytes: int = 80_000_000_000,
              state_bytes_per_card: int = 0, workspace_bytes_per_card: int = 0,
              metadata_bytes_per_card: int = 0, shard_parameters: list[int] | None = None,
              link_bits_per_second: int = 400_000_000_000, payload_bytes: int | None = None,
              messages: int = 1, startup_seconds: float = 0.000003,
              link_efficiency: float = 1.0) -> dict:
    for key, value in (('parameters', parameters), ('cards', cards), ('card_capacity_bytes', card_capacity_bytes),
                       ('link_bits_per_second', link_bits_per_second), ('messages', messages)):
        positive_int(value, key)
    if weight_bits not in (4, 8, 16, 32):
        raise ValueError('Teaching storage width must be 4, 8, 16 or 32 bits')
    for key, value in (('state_bytes_per_card', state_bytes_per_card), ('workspace_bytes_per_card', workspace_bytes_per_card),
                       ('metadata_bytes_per_card', metadata_bytes_per_card)):
        positive_int(value, key, allow_zero=True)
    positive_number(startup_seconds, 'startup_seconds')
    positive_number(link_efficiency, 'link_efficiency')
    if link_efficiency > 1:
        raise ValueError('Link efficiency cannot exceed one')
    if shard_parameters is None:
        q, remainder = divmod(parameters, cards)
        shard_parameters = [q + (i < remainder) for i in range(cards)]
    if len(shard_parameters) != cards:
        raise ValueError('One explicit parameter allocation is required per card')
    for count in shard_parameters:
        positive_int(count, 'shard parameter count', allow_zero=True)
    if sum(shard_parameters) != parameters:
        raise ValueError('Shards must conserve the nominal parameter count')
    rows = []
    for card, count in enumerate(shard_parameters):
        packed = (count * weight_bits + 7) // 8
        occupied = packed + metadata_bytes_per_card + state_bytes_per_card + workspace_bytes_per_card
        rows.append(dict(card=card, parameters=count, packed_weight_bytes=packed,
                         metadata_bytes=metadata_bytes_per_card, state_bytes=state_bytes_per_card,
                         workspace_bytes=workspace_bytes_per_card, occupied_bytes=occupied,
                         capacity_bytes=card_capacity_bytes, headroom_bytes=card_capacity_bytes - occupied,
                         fits_declared_budget=occupied <= card_capacity_bytes))
    weight_bytes = sum(row['packed_weight_bytes'] for row in rows)
    if payload_bytes is None:
        payload_bytes = weight_bytes
    positive_int(payload_bytes, 'payload_bytes', allow_zero=True)
    occupied = sum(row['occupied_bytes'] for row in rows)
    raw_bandwidth = link_bits_per_second / 8
    bandwidth_term = payload_bytes / (raw_bandwidth * link_efficiency)
    startup_term = messages * startup_seconds
    return dict(schema_version=1, calculation='resource-basics', model='nominal-teaching-model',
                scenario=dict(parameters=parameters, weight_bits=weight_bits, cards=cards,
                              card_capacity_bytes=card_capacity_bytes, state_bytes_per_card=state_bytes_per_card,
                              workspace_bytes_per_card=workspace_bytes_per_card, metadata_bytes_per_card=metadata_bytes_per_card,
                              shard_parameters=shard_parameters, link_bits_per_second=link_bits_per_second,
                              payload_bytes=payload_bytes, messages=messages, startup_seconds=startup_seconds,
                              link_efficiency=link_efficiency),
                sources=[], capacity_cards=rows,
                summary=dict(weight_payload_bytes=weight_bytes, weight_payload_GB=weight_bytes / 10**9,
                             weight_payload_GiB=weight_bytes / 2**30,
                             per_card_capacity_GB=card_capacity_bytes / 10**9,
                             per_card_capacity_GiB=card_capacity_bytes / 2**30,
                             aggregate_capacity_bytes=cards * card_capacity_bytes,
                             aggregate_occupied_bytes=occupied,
                             aggregate_capacity_sufficient=occupied <= cards * card_capacity_bytes,
                             every_card_fits_declared_budget=all(row['fits_declared_budget'] for row in rows),
                             raw_one_direction_bytes_per_second=raw_bandwidth,
                             raw_one_direction_GB_per_second=raw_bandwidth / 10**9,
                             raw_one_direction_GiB_per_second=raw_bandwidth / 2**30,
                             ideal_payload_service_seconds=payload_bytes / raw_bandwidth,
                             modeled_payload_service_seconds=bandwidth_term,
                             modeled_startup_seconds=startup_term,
                             modeled_serial_transfer_seconds=startup_term + bandwidth_term,
                             startup_bandwidth_crossover_payload_bytes=startup_term * raw_bandwidth * link_efficiency,
                             measured_transfer_seconds=None),
                assumptions=[
                    '70B means exactly 70×10^9 nominal teaching parameters, not the count of Llama/Qwen or a downloaded checkpoint. Decimal GB=10^9 bytes and binary GiB=2^30 bytes.',
                    'Storage width is not a hardware compute precision/accumulator declaration. Packed bytes round up separately per card; real per-tensor/group padding, scales and zero points must be provided in metadata or a model-specific adapter.',
                    'Default sharding is an arithmetic balanced partition, not proof that a real model supports this placement. Explicit shards must conserve parameters; replication and actual layer/TP constraints need separate placement calculations.',
                    'State, workspace and metadata are explicit per-card reserved bytes. Zero means excluded from this teaching example, not proven absent in deployment. A fit is conditional on these declared budgets.',
                    '400 Gb/s converts to 50 GB/s raw in one direction. Do not double that rate for a one-way transfer. Efficiency is a scenario assumption for protocol/shared-path losses, not a measured device specification.',
                    'payload_bytes is the total serial payload across messages, not the size of each message. Model time is messages×startup + total_payload/effective_bandwidth; startup and bandwidth terms are not a measured latency or a parallel schedule.',
                ])
