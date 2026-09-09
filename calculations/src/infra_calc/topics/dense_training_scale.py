"""Nominal Dense 6ND scaling: fixed-token versus proportional-data questions."""
from fractions import Fraction
from math import ceil, isqrt
from .. import hardware
from ..sources import records
from ..units import positive_int


def calculate(parameters=None, cards=16384, task_tokens=20*10**12, data_rule='fixed',
              tokens_per_parameter=20, efficiencies=None, deadlines_days=None,
              unavailable_days=0, state_bytes_per_parameter=16, devices=None):
    parameters=[10**12,5*10**12,10*10**12] if parameters is None else parameters
    efficiencies=['3/10','2/5','1/2'] if efficiencies is None else efficiencies
    deadlines_days=[90,180] if deadlines_days is None else deadlines_days
    devices=['a100-80gb-sxm','h100-sxm','b200-sxm'] if devices is None else devices
    for name,value in (('cards',cards),('task_tokens',task_tokens),('tokens_per_parameter',tokens_per_parameter),('state_bytes_per_parameter',state_bytes_per_parameter)):
        positive_int(value,name)
    positive_int(unavailable_days,'unavailable_days',allow_zero=True)
    for name,values in (('parameters',parameters),('deadlines_days',deadlines_days)):
        if not isinstance(values,list) or not values:raise ValueError(f'Nonempty {name} required')
        for value in values:positive_int(value,name)
    if any(d<=unavailable_days for d in deadlines_days):raise ValueError('No positive training time before deadline')
    if data_rule not in ('fixed','proportional'):raise ValueError('Choose fixed or proportional data budget')
    if not isinstance(efficiencies,list) or not efficiencies:raise ValueError('Supply efficiencies')
    ratios=[]
    for value in efficiencies:
        if isinstance(value,bool) or not isinstance(value,(str,int)):raise ValueError('Efficiency must be exact string/int')
        ratio=Fraction(value)
        if not 0<ratio<=1:raise ValueError('Efficiency must be in (0,1]')
        ratios.append(ratio)
    if not isinstance(devices,list) or not devices or len(set(devices))!=len(devices):raise ValueError('Distinct device IDs required')
    catalog={d['id']:d for d in hardware.catalog()['devices']};rows=[];bounds=[];source_ids=set()
    for identifier in devices:
        if identifier not in catalog:raise ValueError('Unknown official hardware profile')
        device=catalog[identifier]
        if device['spec_scope']!='single_device':raise ValueError('Single-device peak and capacity required')
        peak=hardware.select_peak(device,'BF16','FP32','tensor','dense')
        capacity=device['memory']['nominal_capacity']
        if capacity is None:raise ValueError('Verified nominal capacity required')
        capacity=int(Fraction(str(capacity))*10**9)
        rate=Fraction(str(peak['tera_ops_per_second']))*10**12;source_ids.update(device['source_ids'])
        for efficiency in ratios:
            effective=rate*efficiency
            for n in parameters:
                tokens=task_tokens if data_rule=='fixed' else tokens_per_parameter*n
                work=6*n*tokens
                seconds=Fraction(work,1)/(cards*effective)
                persistent=n*state_bytes_per_parameter
                capacity_count=ceil(Fraction(persistent,capacity))
                requirements=[]
                for deadline in deadlines_days:
                    available=(deadline-unavailable_days)*86400
                    compute_count=ceil(Fraction(work,1)/(available*effective))
                    requirements.append(dict(deadline_days=deadline,compute_card_count=compute_count,
                                             state_card_count=capacity_count,necessary_card_count=max(compute_count,capacity_count)))
                rows.append(dict(device=identifier,parameters=n,task_tokens=tokens,algorithm_flops=work,
                                 efficiency_exact=str(efficiency),peak_bf16_fp32_dense_tflops=peak['tera_ops_per_second'],
                                 training_days_exact=str(seconds/86400),training_days=float(seconds/86400),
                                 calendar_days_exact=str(seconds/86400+unavailable_days),
                                 persistent_state_bytes=persistent,persistent_average_bytes_exact=str(Fraction(persistent,cards)),
                                 aggregate_persistent_capacity_fits=capacity_count<=cards,deadline_requirements=requirements))
            for deadline in deadlines_days:
                supply=cards*effective*(deadline-unavailable_days)*86400
                if data_rule=='fixed':
                    bound=supply/(6*task_tokens);maximum=bound.numerator//bound.denominator
                else:
                    squared=supply/(6*tokens_per_parameter)
                    maximum=isqrt(squared.numerator//squared.denominator)
                state_max=cards*capacity//state_bytes_per_parameter
                bounds.append(dict(device=identifier,efficiency_exact=str(efficiency),deadline_days=deadline,
                                   max_parameters_compute=maximum,max_parameters_persistent_capacity=state_max,
                                   max_parameters_necessary_conditions=min(maximum,state_max)))
    sources=[{k:r[k] for k in ('file','url','revision','sha256')} for r in records() if r.get('id') in source_ids]
    return dict(schema_version=1,calculation='dense-training-scale',model='nominal-dense-teaching-models',
                scenario=dict(parameters=parameters,cards=cards,task_tokens=task_tokens,data_rule=data_rule,
                              tokens_per_parameter=tokens_per_parameter,efficiencies=[str(v) for v in ratios],
                              deadlines_days=deadlines_days,unavailable_days=unavailable_days,
                              state_bytes_per_parameter=state_bytes_per_parameter,devices=devices),sources=sources,
                dense_scale_rows=rows,dense_scale_bounds=bounds,
                summary=dict(scaling_rule='linear in N at fixed D' if data_rule=='fixed' else 'quadratic in N when D=kN',
                             device_configurations=len(devices),model_sizes=len(parameters),evaluated_rows=len(rows),
                             evaluated_parameter_bounds=len(bounds)),
                assumptions=[
                    '1T/5T/10T为名义Dense教学规模，不对应下载模型config，6ND为粗估算法工作，不含单独的长序列注意力修正；不能替代官方Qwen/V4/K3逐算子模型或用MoE总参数代N。',
                    'fixed使用同一task_tokens，工作随N线性；proportional使用D=tokens_per_parameter×N，工作随N平方，task_tokens在该规则下不使用。20tokens/parameter只是教学假设，不宣称计算最优训练配方。',
                    '峰值严格BF16输入/FP32累加/tensor/dense/single_device；效率为本6ND分子对应的教学MFU，不与另一矩阵或实测FLOPs口径直接混用，不使用结构化稀疏宣传值。',
                    '未含在稳态效率中的日历停顿unavailable_days单独扣除期限/加回完成时间；若效率已包含通信/重算/气泡耗时，不再重复附加。固定效率不保证规模增大后仍能实现。',
                    '期限卡数按ceil取整，参数上界按floor；D=kN时用整数平方根确保N通过而N+1超过算力预算。容量只按理想分片持久状态16bytes等显式输入，名义GB转十进制bytes，不含激活、工作区、布局约束或最忙rank。',
                    '算力/总容量两必要条件均通过不证明实际可部署。未估通信拓扑、输入供应、恢复可靠性、质量或成本；输出参数界不构成某GPU的固有参数上限。',
                ])
