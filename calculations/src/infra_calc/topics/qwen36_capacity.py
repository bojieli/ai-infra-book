"""Necessary resident-byte budgets for the pinned Qwen3.6 checkpoint.

Checkpoint storage and declared persistent state are counted separately. This
is a capacity screen; neither a runtime allocation trace nor throughput model.
"""
import json
from math import prod

from .. import hardware
from ..sources import read_source, records
from ..units import positive_int
from . import qwen36_forward

DEVICES = ('rtx4090', 'rtx5090', 'h100-sxm',
           'rtx-pro6000-blackwell-ws', 'm2-max-38gpu-96gb')


def calculate(batch=1, length=8192, reserve_bytes=2 * 1024**3,
              include_auxiliary_weights=False):
    """Screen a complete history after a single-token append, without sharding."""
    positive_int(batch, 'batch')
    positive_int(length, 'length')
    positive_int(reserve_bytes, 'reserve_bytes', allow_zero=True)
    if type(include_auxiliary_weights) is not bool:
        raise ValueError('include_auxiliary_weights must be boolean')
    forward = qwen36_forward.calculate(batch=batch, tokens=1, history=length - 1)
    index = json.loads(read_source(qwen36_forward.EVIDENCE_ROOT + '/model/model.safetensors.index.json'))
    tensor_bytes = {}
    for shard in sorted(set(index['weight_map'].values())):
        header = json.loads(read_source(qwen36_forward.EVIDENCE_ROOT + '/headers/' + shard + '.json'))
        for name, tensor in header.items():
            if name == '__metadata__':
                continue
            if tensor['dtype'] != 'BF16':
                raise ValueError('This fixed checkpoint capacity contract requires BF16 storage')
            size = 2 * prod(tensor['shape'])
            if tensor['data_offsets'][1] - tensor['data_offsets'][0] != size:
                raise ValueError('Checkpoint shape/byte mismatch')
            if name in tensor_bytes or index['weight_map'].get(name) != shard:
                raise ValueError('Duplicate or wrong-shard checkpoint tensor')
            tensor_bytes[name] = size
    if tensor_bytes.keys() != index['weight_map'].keys():
        raise ValueError('Incomplete checkpoint inventory')
    text_bytes = forward['summary']['base_checkpoint_bytes']
    whole_bytes = sum(tensor_bytes.values())
    weights = whole_bytes if include_auxiliary_weights else text_bytes
    state = forward['state']
    parts = dict(selected_checkpoint_weight_bytes=weights,
                 full_attention_kv_bytes=state['full_kv_after_bytes'],
                 recurrent_fp32_bytes=state['linear_recurrent_fp32_bytes'],
                 convolution_bf16_bytes=state['linear_conv_slot_bytes'],
                 declared_reserve_bytes=reserve_bytes)
    required = sum(parts.values())
    catalog = {d['id']: d for d in hardware.catalog()['devices']}
    devices = []
    source_ids = set()
    for identifier in DEVICES:
        device = catalog[identifier]
        memory = device['memory']
        if memory['capacity_unit'] != 'GB':
            raise ValueError('This screen interprets official nominal GB as decimal bytes')
        capacity = int(memory['nominal_capacity'] * 10**9)
        source_ids.update(device['source_ids'])
        devices.append(dict(device=identifier, nominal_capacity_bytes=capacity,
                            memory_evidence=memory,
                            necessary_budget_fits=required <= capacity,
                            headroom_after_declared_budget_bytes=capacity - required,
                            runtime_feasibility=None, tokens_per_second=None))
    sources = forward['sources'] + [
        {k: r[k] for k in ('file', 'url', 'revision', 'sha256')}
        for r in records() if r.get('id') in source_ids and r['status'] == 'downloaded'
    ]
    return dict(schema_version=1, calculation='qwen36-capacity', model=qwen36_forward.MODEL,
                scenario=dict(batch=batch, length=length, reserve_bytes=reserve_bytes,
                              include_auxiliary_weights=include_auxiliary_weights),
                sources=sources, summary=dict(base_text_checkpoint_bytes=text_bytes,
                    entire_checkpoint_bytes=whole_bytes,
                    auxiliary_checkpoint_bytes=whole_bytes-text_bytes,
                    budget_components_bytes=parts, necessary_budget_bytes=required),
                devices=devices, assumptions=[
                    '全部路由专家常驻；A3B不是驻留权重大小。默认仅基础文本权重，选项可保留视觉/MTP文件中的全部权重，但不会凭此假装已计它们的执行状态。',
                    '所有原始张量为BF16存储；线性递推状态按声明参考路径FP32，卷积槽与完整attention KV按BF16。运行时权重重排、转换、分配器和临时峰值未测。',
                    'length是追加后的完整attention历史长度；递推状态与卷积槽不随历史线性增长。B个请求独立，不假定前缀共享。',
                    'reserve_bytes为明确的额外预算假设，默认2GiB，并非测得workspace。官方名义GB按十进制计，不能等同可分配空间；Mac还与CPU/OS共享。',
                    '超过预算即可在这些假设下排除；通过必要容量筛选不证明能加载、达到延迟目标或满足质量。此处没有低位量化、卸载或多卡切分。'])


def markdown(result):
    lines = ['# Qwen3.6-35B-A3B 必要容量筛选', '',
             '| 组成 | bytes |', '|---|---:|']
    lines += [f'| {k} | {v} |' for k, v in result['summary']['budget_components_bytes'].items()]
    lines += ['', '| 设备 | 名义 bytes | 必要预算通过 | 剩余 bytes |', '|---|---:|---|---:|']
    lines += [f"| {d['device']} | {d['nominal_capacity_bytes']} | {d['necessary_budget_fits']} | {d['headroom_after_declared_budget_bytes']} |" for d in result['devices']]
    lines += ['', *result['assumptions'], '', '```json', json.dumps(result, ensure_ascii=False, indent=2), '```', '']
    return '\n'.join(lines)
