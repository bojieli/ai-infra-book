"""Audit official safetensors headers without fetching tensor payloads.

Every tensor key, shard assignment, shape/dtype byte length and contiguous data
offset is validated against the official index. Packed FP4 uses an I8 container.
"""
import json
from collections import Counter
from math import prod

from ..sources import read_source


def calculate(model: str) -> dict:
    if model not in ('deepseek-v4-flash', 'deepseek-v4-pro'):
        raise ValueError('Checkpoint header adapter requires V4')
    index = json.loads(read_source(f'sources/{model}/model.safetensors.index.json'))
    sizes = {'F32': 4, 'BF16': 2, 'F8_E4M3': 1, 'F8_E8M0': 1, 'I8': 1, 'I64': 8, 'I32': 4}
    seen = set()
    byte_groups, tensors_by_dtype = Counter(), Counter()
    logical_parameters = 0
    for shard in sorted(set(index['weight_map'].values())):
        header = json.loads(read_source(f'sources/{model}/headers/{shard}.json'))
        offsets = []
        for name, tensor in header.items():
            if name == '__metadata__':
                continue
            if name in seen or index['weight_map'].get(name) != shard:
                raise ValueError(f'Duplicate tensor or index/shard mismatch: {name}')
            seen.add(name)
            dtype, shape = tensor['dtype'], tensor['shape']
            start, end = tensor['data_offsets']
            count = prod(shape)
            if dtype not in sizes or end - start != count * sizes[dtype]:
                raise ValueError(f'Tensor dtype/shape/byte mismatch: {name}')
            offsets.append((start, end))
            owner = 'mtp' if name.startswith('mtp.') else 'base'
            kind = 'quant_scales' if name.endswith('.scale') else 'hash_table' if name.endswith('.tid2eid') else 'parameters'
            byte_groups[f'{owner}_{kind}_bytes'] += end - start
            byte_groups[f'{owner}_total_bytes'] += end - start
            tensors_by_dtype[dtype] += 1
            if owner == 'base' and kind == 'parameters':
                if dtype == 'I8':
                    if '.ffn.experts.' not in name or not name.endswith('.weight'):
                        raise ValueError(f'Unknown I8 interpretation: {name}')
                    logical_parameters += 2 * count  # packed FP4, two values per I8 byte
                elif dtype.startswith('I'):
                    raise ValueError(f'Unclassified integer tensor: {name}')
                else:
                    logical_parameters += count
        cursor = 0
        for start, end in sorted(offsets):
            if start != cursor:
                raise ValueError(f'Overlapping or noncontiguous tensor payload offsets: {shard}')
            cursor = end
    if seen != set(index['weight_map']):
        raise ValueError('Checkpoint headers do not cover every index key')
    total = byte_groups['base_total_bytes'] + byte_groups['mtp_total_bytes']
    if total != index['metadata']['total_size']:
        raise ValueError('Header payload sum differs from official index total_size')
    return dict(verified_tensors=len(seen), verified_shards=len(set(index['weight_map'].values())),
                checkpoint_tensor_payload_bytes=total, byte_groups=dict(byte_groups),
                tensor_count_by_storage_dtype=dict(tensors_by_dtype),
                base_logical_parameters_excluding_scales_and_hash=logical_parameters,
                scope='Official checkpoint tensor payload, excluding file headers and filesystem overhead. Includes separate MTP; runtime dtype conversion, aliasing and allocated model copies may differ. Payload values were not downloaded or numerically validated.')
