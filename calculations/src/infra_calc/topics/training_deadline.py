"""Official matrix-work budget and separate compute/state device-count bounds."""
from fractions import Fraction
from math import ceil

from .. import hardware
from ..sources import provenance, records
from ..units import positive_int
from .training_matrix import calculate as training_matrix


def calculate(model='qwen3-8b', task_tokens=100*10**9, sequence_tokens=8192,
              deadline_days=30, unavailable_seconds=0, gradient_bytes=2,
              efficiencies=None, devices=None):
    for name,value in (('task_tokens',task_tokens),('sequence_tokens',sequence_tokens),('deadline_days',deadline_days)):
        positive_int(value,name)
    positive_int(unavailable_seconds,'unavailable_seconds',allow_zero=True)
    if gradient_bytes not in (2,4) or isinstance(gradient_bytes,bool):raise ValueError('Explicit BF16/FP32 gradients required')
    available=deadline_days*86400-unavailable_seconds
    if available<=0:raise ValueError('No training time remains before deadline')
    efficiencies=['3/10','2/5','1/2'] if efficiencies is None else efficiencies
    if not isinstance(efficiencies,list) or not efficiencies:raise ValueError('Supply matrix-work efficiencies')
    ratios=[]
    for value in efficiencies:
        if isinstance(value,bool) or not isinstance(value,(str,int)):raise ValueError('Use exact string/int efficiencies')
        ratio=Fraction(value)
        if not 0<ratio<=1:raise ValueError('Efficiency must be in (0,1]')
        ratios.append(ratio)
    devices=['rtx4090','rtx5090','a100-80gb-sxm','a800-40gb-active','h20-sxm5-96gb','h20-sxm5-141gb','h100-sxm','b200-sxm'] if devices is None else devices
    if not isinstance(devices,list) or not devices or len(set(devices))!=len(devices):raise ValueError('Distinct device IDs required')
    count,tail=divmod(task_tokens,sequence_tokens)
    full=training_matrix(model=model,tokens=sequence_tokens,gradient_bytes=gradient_bytes)
    remainder=training_matrix(model=model,tokens=tail,gradient_bytes=gradient_bytes) if tail else None
    full_work=full['summary']['training_matrix_flops']
    tail_work=remainder['summary']['training_matrix_flops'] if remainder else 0
    total=count*full_work+tail_work
    parameters=full['summary']['parameters']
    persistent=full['summary']['unsharded_parameter_state_bytes']
    catalog={d['id']:d for d in hardware.catalog()['devices']}
    sources=provenance(model);source_ids=set();rows=[];availability=[]
    for identifier in devices:
        device=catalog.get(identifier)
        if device is None:
            availability.append(dict(device=identifier,status='unavailable',reason='No locked official hardware profile',capacity_bound_devices=None))
            continue
        source_ids.update(device['source_ids'])
        if device['spec_scope']!='single_device':
            availability.append(dict(device=identifier,status='unavailable',reason='This count requires single-device specifications',capacity_bound_devices=None))
            continue
        nominal=device['memory']['nominal_capacity']
        capacity=int(Fraction(str(nominal))*10**9) if nominal is not None else None
        capacity_count=ceil(Fraction(persistent,capacity)) if capacity else None
        try:
            peak=hardware.select_peak(device,'BF16','FP32','tensor','dense')
        except ValueError as error:
            availability.append(dict(device=identifier,status='unavailable',reason=str(error),capacity_bound_devices=capacity_count))
            continue
        rate=Fraction(str(peak['tera_ops_per_second']))*10**12
        availability.append(dict(device=identifier,status='available',capacity_bound_devices=capacity_count,
                                 nominal_capacity_bytes=capacity,selected_peak=peak))
        for efficiency in ratios:
            count_compute=ceil(Fraction(total,1)/(available*rate*efficiency))
            combined=max(count_compute,capacity_count) if capacity_count is not None else None
            elapsed=Fraction(total,1)/(combined*rate*efficiency) if combined else None
            rows.append(dict(device=identifier,matrix_work_efficiency_exact=str(efficiency),
                             bf16_fp32_dense_peak_flops_exact=str(rate),nominal_capacity_bytes=capacity,
                             compute_count_bound=count_compute,persistent_capacity_count_bound=capacity_count,
                             combined_necessary_count=combined,
                             conditional_training_seconds_exact=str(elapsed) if elapsed else None,
                             excluded_calendar_seconds=unavailable_seconds,
                             conditional_calendar_seconds_exact=str(elapsed+unavailable_seconds) if elapsed else None,
                             persistent_average_bytes_at_combined_count_exact=str(Fraction(persistent,combined)) if combined else None))
    sources += [{k:r[k] for k in ('file','url','revision','sha256')} for r in records() if r.get('id') in source_ids]
    return dict(schema_version=1,calculation='training-deadline',model=model,
                scenario=dict(model=model,task_tokens=task_tokens,sequence_tokens=sequence_tokens,deadline_days=deadline_days,
                              unavailable_seconds=unavailable_seconds,gradient_bytes=gradient_bytes,
                              efficiencies=[str(v) for v in ratios],devices=devices),sources=sources,
                training_deadline_devices=availability,training_deadline_rows=rows,
                summary=dict(parameters=parameters,full_sequences=count,tail_sequence_tokens=tail,
                             full_sequence_matrix_flops=full_work,tail_sequence_matrix_flops=tail_work,
                             task_training_matrix_flops=total,matrix_flops_per_task_token_exact=str(Fraction(total,task_tokens)),
                             required_tokens_per_available_second_exact=str(Fraction(task_tokens,available)),
                             persistent_state_bytes=persistent,available_training_seconds=available,
                             usable_hardware_profiles=sum(d['status']=='available' for d in availability),
                             missing_hardware_profiles=[d['device'] for d in availability if d['status']!='available']),
                assumptions=[
                    '复用官方Qwen完整线性及有效因果QK/PV前后向矩阵账，序列互相独立、输出头覆盖全部输入行。task_tokens为实际参与这些矩阵的有效位置，不额外推断padding/文本token/标签覆盖；尾序列单独计算，不用固定长序列每token工作乘剩余token。',
                    '效率为矩阵子账定义的BF16/FP32 dense峰值比例，30/40/50%为教学敏感性，不直接借用其它FLOPs口径的公开MFU。若效率已含通信、重计算与气泡耗时，不再重复加时间；本处未证实任何拓扑能达到输入效率。',
                    '设备峰值严格选择BF16输入、FP32累加、tensor、dense及single_device；不以structured sparsity、TF32、FP8或整机值替代缺项。不可用型号保留原因和可得容量下界，不猜测参数。',
                    '时间下界为矩阵FLOPs/(有效训练秒×峰值×效率)向上取整。容量下界为完整参数/梯度/master/Adam持久字节除官方标称GB（十进制），假设理想任意分片；二者取max仍只是必要下界，不是已证明可部署的卡数。',
                    'MoE矩阵按实际top-k直方图计算，持久容量包含全部专家；未包含激活、临时聚合、allocator、TP/PP/EP可除性、通信拓扑和每rank不均衡。平均状态字节不是最忙rank峰值。',
                    'unavailable_seconds为明确排除的日历时间预算，先从期限扣除，再算稳态矩阵效率；不能把相同保存/故障/数据停顿同时扣时间又包含进效率。输出条件式时间不代表实际训练交付或质量达标。',
                ])
