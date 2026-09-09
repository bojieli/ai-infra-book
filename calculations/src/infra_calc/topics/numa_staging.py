"""Map a four-GPU Qwen ring onto declared host staging/NUMA paths."""
from ..sources import provenance
from ..traffic import account
from ..units import positive_int
from . import ring_collective


def calculate(tokens: int = 1024, placement: str = 'all-a', order: str = 'grouped',
              pcie_bytes_per_second: int = 12_000_000_000,
              dram_bytes_per_second: int = 40_000_000_000,
              intersocket_bytes_per_second: int = 8_000_000_000, startup_ns: int = 0) -> dict:
    positive_int(tokens, 'tokens')
    if placement not in ('all-a', 'sender-local') or order not in ('grouped', 'alternating'):
        raise ValueError('Choose all-a/sender-local buffers and grouped/alternating ring')
    # The logical ring uses rank IDs; the mapping below assigns physical GPUs.
    logical = ring_collective.calculate(tokens=tokens, participants=4)
    gpus = [0, 1, 2, 3] if order == 'grouped' else [0, 2, 1, 3]
    numa = ['A', 'A', 'B', 'B']
    bandwidths = {f'gpu{i}_{direction}': pcie_bytes_per_second
                  for i in range(4) for direction in ('to_host', 'from_host')}
    bandwidths.update(dram_A=dram_bytes_per_second, dram_B=dram_bytes_per_second,
                      A_to_B=intersocket_bytes_per_second, B_to_A=intersocket_bytes_per_second)
    paths, descriptions = {}, []
    for rank in range(4):
        destination = (rank + 1) % 4
        sender, receiver = gpus[rank], gpus[destination]
        source_node, destination_node = numa[sender], numa[receiver]
        buffer_node = 'A' if placement == 'all-a' else source_node
        path = [f'gpu{sender}_to_host']
        if source_node != buffer_node:
            path.append(f'{source_node}_to_{buffer_node}')
        path += [f'dram_{buffer_node}', f'dram_{buffer_node}']  # write then read
        if buffer_node != destination_node:
            path.append(f'{buffer_node}_to_{destination_node}')
        path.append(f'gpu{receiver}_from_host')
        paths[rank, destination] = path
        descriptions.append(dict(source_rank=rank, destination_rank=destination, sender_gpu=sender,
                                 receiver_gpu=receiver, buffer_numa=buffer_node, resources=path))
    counted = account(logical['ring_rounds'], paths, bandwidths, startup_ns)
    return dict(schema_version=1, calculation='qwen-pcie-numa-staging', model='qwen3-8b',
                scenario=dict(tokens=tokens, placement=placement, order=order,
                              rank_to_gpu=gpus, pcie_bytes_per_second=pcie_bytes_per_second,
                              dram_bytes_per_second=dram_bytes_per_second,
                              intersocket_bytes_per_second=intersocket_bytes_per_second, startup_ns=startup_ns),
                sources=provenance('qwen3-8b'), physical_paths=descriptions, physical_traffic=counted,
                summary=dict(message_bytes=logical['summary']['message_bytes_per_rank'],
                             logical_send_bytes=counted['logical_send_bytes'],
                             aggregate_resource_lower_seconds=counted['aggregate_resource_lower_seconds'],
                             sum_round_resource_lower_seconds=counted['sum_round_resource_lower_seconds'],
                             barrier_lower_with_startup_seconds=counted['barrier_lower_with_startup_seconds'],
                             buffer_resident_bytes=None, measured_all_reduce_seconds=None),
                assumptions=[
                    'Four-GPU teaching topology: G0/G1 on NUMA A and G2/G3 on B. Logical ring schedule comes from the actual Qwen3-8B BF16 [T,4096] activation payload.',
                    'Every edge stages through exactly one host buffer: sender writes it, receiver reads it, with no extra CPU memcpy. Allocation process identity does not identify buffer NUMA placement.',
                    'GPU-to-host and host-to-GPU PCIe are independent directional resources. Each NUMA DRAM has a shared read-plus-write bandwidth, so its resource appears twice per staged transfer. A-to-B and B-to-A are independent directions.',
                    'All rates are explicit effective teaching inputs, not official GPU/P2P specifications or measured bandwidth. This path does not require assuming consumer-GPU P2P support.',
                    'Aggregate maximum service time is a lower bound. Summing per-round resource maxima additionally respects declared ring round barriers; startup is optional. Intra-round path dependencies, host bridges, protocol bytes, reductions and synchronization can raise actual time.',
                    'Traffic is not buffer residency: no double-buffer depth or allocation lifetime has been supplied, so buffer capacity remains unknown. Physical hops sum resource service without relabeling it as logical collective payload.',
                ])
