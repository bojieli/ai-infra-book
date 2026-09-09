"""Official dense Qwen decode: shared weights, per-request KV, capacity bounds."""
from fractions import Fraction
from math import ceil
from .. import hardware
from ..models import forward,qwen3
from ..sources import model_config,records
from ..schema import Scenario
from ..units import positive_int


def calculate(model='qwen3-8b',device='h100-sxm',history=2048,batches=None,workspace_bytes=0):
    positive_int(history,'history',allow_zero=True)
    positive_int(workspace_bytes,'workspace_bytes',allow_zero=True)
    batches=[1,4,16,64] if batches is None else batches
    if not isinstance(batches,list) or not batches:raise ValueError('Supply nonempty batches')
    for batch in batches:positive_int(batch,'batch')
    if len(set(batches))!=len(batches):raise ValueError('Duplicate batch')
    config=model_config(model);qwen3.validate(config)
    weights=qwen3.weights(config)
    resident=sum(w.parameters for w in weights)*2
    # Dense matrices and affine norms are shared once per ideal batch;
    # embedding is indexed per token instead of scanning the whole table.
    shared=sum(w.parameters for w in weights if w.name!='model.embed_tokens.weight')*2
    embedding=config['hidden_size']*2
    work=forward(model,Scenario(tokens=1,history=history,output_head='last'))
    unit=work['summary']['kv_bytes_per_token_per_request']
    single_flops=work['summary']['matrix_flops']
    per_request_kv_read=history*unit
    per_request_kv_write=unit
    per_request=per_request_kv_read+per_request_kv_write+embedding
    profile=hardware.select_device(device)
    if profile['spec_scope']!='single_device':raise ValueError('Single-device comparison required')
    peak=hardware.select_peak(profile,'BF16','FP32','tensor','dense')
    memory=profile['memory']
    if memory['nominal_capacity'] is None or memory['bandwidth_bytes_per_second'] is None:
        raise ValueError('Official capacity and bandwidth required')
    compute=Fraction(str(peak['tera_ops_per_second']))*10**12
    bandwidth=Fraction(str(memory['bandwidth_bytes_per_second']))
    capacity=int(Fraction(str(memory['nominal_capacity']))*10**9)
    denominator=Fraction(single_flops)*bandwidth/compute-per_request
    crossover=max(1,ceil(Fraction(shared)/denominator)) if denominator>0 else None
    maximum=max(0,(capacity-resident-workspace_bytes)//((history+1)*unit))
    rows=[]
    for batch in batches:
        traffic=shared+batch*per_request
        footprint=resident+batch*(history+1)*unit+workspace_bytes
        flops=batch*single_flops
        compute_s=Fraction(flops)/compute;memory_s=Fraction(traffic)/bandwidth
        lower=max(compute_s,memory_s)
        feasible=footprint<=capacity
        rows.append(dict(batch=batch,matrix_flops=flops,shared_weight_read_bytes=shared,
                         kv_history_read_bytes=batch*per_request_kv_read,kv_append_write_bytes=batch*unit,
                         embedding_read_bytes=batch*embedding,declared_traffic_bytes=traffic,
                         serial_declared_traffic_bytes=batch*(shared+per_request),
                         saved_weight_read_bytes=(batch-1)*shared,
                         declared_resident_bytes=footprint,capacity_feasible=feasible,
                         matrix_intensity_exact=str(Fraction(flops,traffic)),
                         compute_lower_ns_exact=str(compute_s*10**9),memory_lower_ns_exact=str(memory_s*10**9),
                         runnable_lower_ns_exact=str(lower*10**9) if feasible else None,
                         throughput_upper_tokens_per_second=float(Fraction(batch)/lower) if feasible else None,
                         dominant_resource='compute' if compute_s>=memory_s else 'memory'))
    sources=work['sources']+[{key:r[key] for key in ('file','url','revision','sha256')}
                            for r in records() if r.get('id') in profile['source_ids']]
    return dict(schema_version=1,calculation='batch-reuse',scenario=dict(model=model,device=device,history=history,batches=batches,workspace_bytes=workspace_bytes),
                sources=sources,selected_peak=peak,batch_reuse_rows=rows,
                summary=dict(weight_resident_bytes=resident,shared_decode_weight_read_bytes=shared,
                             kv_bytes_per_request_token=unit,per_request_history_read_bytes=per_request_kv_read,
                             nominal_device_capacity_bytes=capacity,declared_capacity_max_batch=maximum,
                             kv_history_equals_weights_batch=ceil(Fraction(shared,per_request_kv_read)) if per_request_kv_read else None,
                             compute_memory_crossover_batch=crossover,
                             crossover_capacity_feasible=crossover is not None and crossover<=maximum,
                             single_request_matrix_flops=single_flops,
                             hardware_ridge_flops_per_byte_exact=str(compute/bandwidth)),
                assumptions=[
                    '固定官方Dense Qwen配置，BF16权重／激活／KV；设备峰值严格选择BF16输入、FP32累加、Tensor、dense，不使用稀疏宣传峰值或混入INT8/FP8。MoE路由／专家并集需另一模型。',
                    '一次迭代每请求生成1token、history相同；矩阵FLOPs来自真实算子，batch线性扩展。非embedding权重理想跨batch读一次，embedding按请求读取一行；驻留仍包含完整embedding。',
                    '每请求旧KV读一次、新KV写一次；新K/V在片上供当前注意力使用，不另计外部重读。假定GQA共享和融合，逻辑接口字节不等于实际HBM流量；中间激活、转换、tile重读和非矩阵计算未包含。',
                    '容量按厂商标称GB乘10^9，加入完整权重、步末KV和显式workspace；默认workspace=0表示尚未计，不证明实际引擎可用。容量不通过时可运行时间与吞吐留null。',
                    '计算／带宽取max只是资源下界，吞吐为该条件下上界；没有执行GPU，不给实测效率、凑批等待、TTFT或SLO保证。',
                    '计算交叉点解B*F/compute=(shared+B*per_request)/bandwidth；分母非正则无有限计算主导交叉点。KV等权重交叉点只比较旧KV读取与共享权重，两个交叉点不可混同。',
                ])
