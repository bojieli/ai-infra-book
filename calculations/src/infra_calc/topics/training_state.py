"""Explicit mixed-precision Adam state ownership under ZeRO stages 0–3.

This is a persistent-state capacity ledger, not a backend peak-memory estimator.
Partition padding is selectable and fully specified, rather than inferred from DP.
"""
import hashlib
import json
from math import prod

from ..models import qwen3, qwen3_moe
from ..sources import PROJECT, model_config, provenance
from ..units import positive_int


def calculate(model='qwen3-8b', participants=8, gradient_bytes=2,
              partition='flat', extra_live_bytes=0, capacity_bytes=24*1024**3):
    for name, value in (('participants', participants), ('gradient_bytes', gradient_bytes)):
        positive_int(value, name)
    for name, value in (('extra_live_bytes', extra_live_bytes), ('capacity_bytes', capacity_bytes)):
        positive_int(value, name, allow_zero=True)
    if gradient_bytes not in (2, 4):
        raise ValueError('Gradient storage must explicitly be BF16 (2) or FP32 (4)')
    if partition not in ('flat', 'per_tensor'):
        raise ValueError('Partition must be flat or per_tensor')
    config = model_config(model)
    if config['model_type'] not in ('qwen3', 'qwen3_moe'):
        raise ValueError('Only full-parameter Qwen adapters are supported here')
    adapter = qwen3_moe if config['model_type'] == 'qwen3_moe' else qwen3
    weights = adapter.weights(config)
    parameters = sum(weight.parameters for weight in weights)
    tensors = [dict(name=w.name, shape=list(w.shape), copies=w.copies,
                    parameters_each=prod(w.shape), parameters=w.parameters,
                    shard_elements_each=(prod(w.shape)+participants-1)//participants)
               for w in weights]
    if partition == 'flat':
        shard_elements = (parameters + participants - 1) // participants
    else:
        shard_elements = sum(row['shard_elements_each'] * row['copies'] for row in tensors)
    # The master weights and moments share the optimizer partition at stages >= 1.
    components = [('weights_bf16', 2, 3), ('gradients', gradient_bytes, 2),
                  ('master_weights_fp32', 4, 1), ('adam_m_fp32', 4, 1),
                  ('adam_v_fp32', 4, 1)]
    rows = []
    for stage in range(4):
        ledger = []
        for name, width, first_sharded_stage in components:
            sharded = stage >= first_sharded_stage
            elements = shard_elements if sharded else parameters
            per_rank = elements * width
            ledger.append(dict(component=name, bytes_per_element=width, sharded=sharded,
                               per_rank_bytes=per_rank, cluster_bytes=per_rank*participants,
                               unique_payload_bytes=parameters*width,
                               partition_padding_bytes=(shard_elements*participants-parameters)*width if sharded else 0,
                               replicated_extra_bytes=0 if sharded else parameters*width*(participants-1)))
        persistent = sum(item['per_rank_bytes'] for item in ledger)
        # Extra simultaneously live allocations must be supplied separately by a schedule.
        required = persistent + extra_live_bytes
        rows.append(dict(stage=stage, components=ledger, persistent_bytes_per_rank=persistent,
                         persistent_bytes_cluster=persistent*participants,
                         supplied_extra_live_bytes=extra_live_bytes,
                         specified_live_bytes_per_rank=required,
                         signed_capacity_headroom_bytes=capacity_bytes-required,
                         specified_allocations_fit=required <= capacity_bytes))
    lock = json.loads((PROJECT/'configs/training-state.lock.json').read_text())
    if hashlib.sha256((PROJECT/lock['file']).read_bytes()).hexdigest() != lock['sha256']:
        raise ValueError('Archived ZeRO documentation hash mismatch')
    return dict(schema_version=1, calculation='training-state', model=model,
                scenario=dict(model=model, participants=participants, gradient_bytes=gradient_bytes,
                              partition=partition, extra_live_bytes=extra_live_bytes, capacity_bytes=capacity_bytes),
                sources=provenance(model)+[lock], training_state_tensors=tensors, training_state_stages=rows,
                summary=dict(parameters=parameters, tensor_instances=sum(w.copies for w in weights),
                             bytes_per_parameter_unsharded=14+gradient_bytes,
                             unsharded_persistent_bytes=parameters*(14+gradient_bytes),
                             padded_shard_elements_per_rank=shard_elements,
                             padding_elements_per_sharded_component=shard_elements*participants-parameters,
                             minimum_persistent_bytes_per_rank=rows[3]['persistent_bytes_per_rank'],
                             stages_fitting_specified_allocations=[row['stage'] for row in rows if row['specified_allocations_fit']]),
                assumptions=[
                    '全参数Adam教学配置：BF16参数2bytes，梯度显式BF16/FP32，FP32 master及两个moment各4bytes。16/18bytes由此得到，不代表所有BF16优化器实现的默认值。',
                    'ZeRO stage1分片optimizer（含master），stage2再分片梯度，stage3再分片参数；无TP/PP/EP、offload或冻结参数。MoE总持久状态包含所有专家，不按top-k缩小。',
                    'flat把完整参数展平后补齐到DP整数倍；per_tensor逐物理张量补齐后每rank等长。两者是声明的布局模型，具体框架bucket、对齐、持久化阈值需另核验。',
                    '这里只计已物化的持久状态：初始化懒分配、完整梯度临时值、all-gather、prefetch、casting、激活、通信bucket和allocator另计。extra_live_bytes须是同一峰值时刻额外分配且不重复计算的输入，默认0不等于实际额外开销0。',
                    '容量为输入的净预算，不是某设备的官方容量。specified_allocations_fit仅表示所列分配能放下，不能证明训练峰值、拓扑或吞吐可行；张量清单存JSON供独立核算。',
                ])
