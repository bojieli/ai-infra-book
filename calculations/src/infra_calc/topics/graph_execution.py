"""Graph boundary costs and exact amortization under declared serial timing."""
from fractions import Fraction
from ..models import qwen3
from ..sources import model_config, provenance
from ..units import positive_int


def amortization(setup_ns, saving_ns):
    """Smallest positive call counts for total cost <= and < baseline."""
    if saving_ns <= 0:
        return dict(break_even_calls=1 if saving_ns == 0 and setup_ns == 0 else None,
                    strictly_faster_calls=None)
    ratio = Fraction(setup_ns) / saving_ns
    ceiling = (ratio.numerator + ratio.denominator - 1) // ratio.denominator
    return dict(break_even_calls=max(1, ceiling),
                strictly_faster_calls=max(1, ratio.numerator // ratio.denominator + 1))


def calculate(model='qwen3-8b', input_tokens=256, real_tokens=1536,
              padded_tokens=2048, copy_bandwidth_bytes_per_second=2*10**12,
              device_ns=20000, exposed_submit_ns=20000, replay_ns=3000,
              metadata_ns=2000, indirect_ns=6000, setup_ns=10**9,
              calls=100000, config_ns=20000, segments=100,
              device_speedup=4, config_speedup=4):
    values = locals().copy()
    for name, value in values.items():
        if name != 'model':
            positive_int(value, name)
    if padded_tokens < real_tokens:
        raise ValueError('padded_tokens must be at least real_tokens')
    config = model_config(model)
    qwen3.validate(config)
    if max(input_tokens,padded_tokens) > config['max_position_embeddings']:
        raise ValueError('Tokens exceed pinned context')
    hidden, intermediate = config['hidden_size'], config['intermediate_size']
    tensor_bytes = 2*input_tokens*hidden
    copy_traffic = 2*tensor_bytes
    copy_ns = Fraction(copy_traffic*10**9, copy_bandwidth_bytes_per_second)
    eager_ns = Fraction(device_ns+exposed_submit_ns)
    graph_base = Fraction(device_ns+replay_ns+metadata_ns)
    paths = [('eager',eager_ns,0), ('copy',graph_base+copy_ns,setup_ns),
             ('indirect',graph_base+indirect_ns,setup_ns),
             ('direct-output',graph_base,setup_ns)]
    rows = []
    for name, execution, preparation in paths:
        saving = eager_ns-execution
        total = preparation+calls*execution
        rows.append(dict(path=name, execution_ns=float(execution),
                         execution_exact_ns=str(execution), setup_ns=preparation,
                         lifetime_total_ns=float(total), lifetime_total_exact_ns=str(total),
                         per_call_saving_ns=float(saving),
                         **amortization(preparation,saving)))
    # Configuration and device execution are two independent serial resources.
    pipeline_rows = []
    for name, host, gpu in [('base',Fraction(config_ns),Fraction(device_ns)),
                            ('faster-device',Fraction(config_ns),Fraction(device_ns,device_speedup)),
                            ('faster-both',Fraction(config_ns,config_speedup),Fraction(device_ns,device_speedup))]:
        finish = host+gpu+(segments-1)*max(host,gpu)
        pipeline_rows.append(dict(variant=name, config_ns=float(host), device_ns=float(gpu),
                                  serial_total_ns=float(segments*(host+gpu)),
                                  overlapped_total_ns=float(finish),
                                  overlapped_total_exact_ns=str(finish)))
    ffn_parameters = 3*hidden*intermediate
    actual_work = 2*real_tokens*ffn_parameters
    padding_work = 2*(padded_tokens-real_tokens)*ffn_parameters
    return dict(schema_version=1,calculation='qwen-graph-execution',model=model,
                scenario={key:value for key,value in values.items() if key != 'model'},
                sources=provenance(model),graph_paths=rows,configuration_pipeline=pipeline_rows,
                summary=dict(input_tensor_bytes=tensor_bytes,extra_copy_interface_bytes=copy_traffic,
                             extra_copy_ns=float(copy_ns),extra_copy_exact_ns=str(copy_ns),
                             layer_ffn_matrix_parameters=ffn_parameters,
                             real_ffn_matrix_flops=actual_work,padding_ffn_matrix_flops=padding_work,
                             padding_over_real_fraction=str(Fraction(padding_work,actual_work)),
                             minimum_serial_steady_external_input_path=min(rows[:3],key=lambda row:Fraction(row['execution_exact_ns']))['path'],
                             minimum_lifetime_external_input_path=min(rows[:3],key=lambda row:Fraction(row['lifetime_total_exact_ns']))['path'],
                             actual_gpu_seconds=None),
                assumptions=[
                    '官方Qwen Dense H/F用于BF16边界张量和单层三矩阵FFN；输入拷贝token数与padding例子独立，不能推成两个真实batch执行时间相同。',
                    '默认设备20us、已暴露提交等待20us、重放3us、元数据2us、间接寻址6us，以及2TB/s有效拷贝流量带宽均是教学供给，不是硬件规格或测量。复制按源读加目的写，正常算子读取仍存在。',
                    '图路径每条额外准备成本显式设为setup_ns，默认1秒；以串行关键路径相加并计实际calls，分别报告不亏和严格更快的最小正整数次数。每次无正收益时不声称有限回本。',
                    'direct-output仅在上游能直接写入稳定输出时适用，不参与外部输入路径选择；indirect为声明可用的教学路径，未声称已集成GraCE到任意引擎。',
                    '配置流水假设后段配置不依赖前段输出、缓冲足够且资源独立；启动和排空计入。其重叠时间不可与前面的串行图预算混加。',
                    'padding只算单层FFN三个矩阵有效增量，不按该比例扩大attention或空request槽。图内存池共享、重捕获、KV挤占和实际调度仍需另核。',
                ])
