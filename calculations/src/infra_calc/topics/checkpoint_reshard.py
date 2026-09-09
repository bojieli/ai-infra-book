"""Logical row-major checkpoint ranges, with exact source/destination byte offsets."""
from ..models import qwen3, qwen3_moe
from ..sources import model_config, provenance
from ..units import positive_int


def partition_ranges(rows, columns, participants, layout):
    """Balanced contiguous ranges; row layout never splits an individual row."""
    if layout not in ('rows', 'flat'):
        raise ValueError('Layout must be rows or flat')
    count = rows if layout == 'rows' else rows*columns
    if participants > count:
        raise ValueError('Empty checkpoint shards are outside this layout model')
    unit = columns if layout == 'rows' else 1
    quotient, remainder = divmod(count, participants)
    ranges = []
    start = 0
    for rank in range(participants):
        end = start + (quotient + (rank < remainder))*unit
        ranges.append((start, end))
        start = end
    return ranges


def plan(rows, columns, source_parts, target_parts, source_layout, target_layout, element_bytes):
    for name, value in (('rows', rows), ('columns', columns), ('source_parts', source_parts),
                        ('target_parts', target_parts), ('element_bytes', element_bytes)):
        positive_int(value, name)
    sources = partition_ranges(rows, columns, source_parts, source_layout)
    targets = partition_ranges(rows, columns, target_parts, target_layout)
    pieces = []
    for target_rank, (target_start, target_end) in enumerate(targets):
        for source_rank, (source_start, source_end) in enumerate(sources):
            start, end = max(source_start, target_start), min(source_end, target_end)
            if start >= end:
                continue
            pieces.append(dict(source_rank=source_rank, target_rank=target_rank,
                               global_element_start=start, global_element_end=end,
                               first_coordinate=list(divmod(start, columns)),
                               last_coordinate=list(divmod(end-1, columns)),
                               source_file_offset_bytes=(start-source_start)*element_bytes,
                               target_buffer_offset_bytes=(start-target_start)*element_bytes,
                               length_bytes=(end-start)*element_bytes))
    return dict(source_shard_bytes=[(end-start)*element_bytes for start, end in sources],
                target_shard_bytes=[(end-start)*element_bytes for start, end in targets], pieces=pieces)


def calculate(model='qwen3-8b', source_parts=4, target_parts=8,
              source_layout='rows', target_layout='rows', include_optimizer=True):
    if not isinstance(include_optimizer, bool):
        raise ValueError('include_optimizer must be boolean')
    config = model_config(model)
    adapter = qwen3_moe if config['model_type'] == 'qwen3_moe' else qwen3
    adapter.validate(config)
    rows = config['moe_intermediate_size'] if config['model_type'] == 'qwen3_moe' else config['intermediate_size']
    columns = config['hidden_size']
    components = [('weight_bf16', 2)]
    if include_optimizer:
        components += [('master_fp32', 4), ('adam_m_fp32', 4), ('adam_v_fp32', 4)]
    plans = []
    for name, width in components:
        layout = plan(rows, columns, source_parts, target_parts, source_layout, target_layout, width)
        # One raw file per component per source rank; no invented container header.
        for piece in layout['pieces']:
            piece['source_file'] = f'{name}.rank{piece["source_rank"]}.bin'
        plans.append(dict(component=name, bytes_per_element=width, **layout))
    read_bytes = sum(piece['length_bytes'] for item in plans for piece in item['pieces'])
    source_bytes = sum(sum(item['source_shard_bytes']) for item in plans)
    target_bytes = sum(sum(item['target_shard_bytes']) for item in plans)
    if read_bytes != source_bytes or source_bytes != target_bytes:
        raise ValueError('Checkpoint payload conservation failed')
    return dict(schema_version=1, calculation='checkpoint-reshard', model=model,
                scenario=dict(model=model, source_parts=source_parts, target_parts=target_parts,
                              source_layout=source_layout, target_layout=target_layout, include_optimizer=include_optimizer),
                sources=provenance(model), checkpoint_component_plans=plans,
                summary=dict(gate_shape=[rows, columns], parameters=rows*columns,
                             bytes_per_parameter=sum(width for _, width in components),
                             logical_checkpoint_bytes=source_bytes, requested_read_bytes=read_bytes,
                             destination_payload_bytes=target_bytes,
                             planned_read_ranges=sum(len(item['pieces']) for item in plans),
                             source_file_count=source_parts*len(components),
                             target_payload_bytes=[sum(item['target_shard_bytes'][rank] for item in plans) for rank in range(target_parts)]),
                assumptions=[
                    '官方Qwen单层gate未融合逻辑矩阵；MoE是单专家，不代表整个checkpoint。行主序、每状态每source rank一个无header原始文件，模型内文件名为计划标识，不声称实际文件存在。',
                    'rows沿输出行按商余数切分；flat沿展平元素按商余数切分，可跨矩阵行边界。无padding、压缩、转置、gate/up融合或文件对齐；真实格式必须先提供逻辑坐标到文件字节的映射。',
                    '每个交集生成一次连续读取，源文件偏移与目标缓冲偏移分别相对各自分片。目标分片对同一逻辑张量不重叠且完整覆盖；全局读取量等于一次有效载荷，不推断物理磁盘IO或网络重复流量。',
                    '训练教学保存格式为BF16权重2＋FP32 master/m/v各4＝14bytes/参数，不含梯度、CPU状态、随机数、数据位置、token buffer和调度器；仅权重模式为推理载荷比较。',
                    '计划没有执行真实checkpoint恢复，也不生成离线重分片文件。这里不计容器metadata、读取启动、共享存储争用、持久化确认、优化器布局转换或完整恢复时间。',
                ])
