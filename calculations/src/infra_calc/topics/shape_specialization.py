"""One Qwen FFN layer: exact affine lifetime costs for three shape policies."""
from fractions import Fraction
from itertools import combinations
from ..models import qwen3
from ..sources import model_config, provenance
from ..units import positive_int


def calculate(model='qwen3-8b', shapes=None, buckets=None, specialized_tokens=None,
              cached_artifacts=None, repetitions=100,
              generic_flops_per_second=100*10**12, bucket_flops_per_second=200*10**12,
              specialized_flops_per_second=250*10**12,
              generic_compile_ns=100000000, bucket_compile_ns=200000000,
              specialized_compile_ns=300000000):
    shapes = shapes if shapes is not None else [dict(tokens=256,count=8),dict(tokens=1536,count=1),dict(tokens=2048,count=1)]
    buckets = buckets if buckets is not None else [512,2048]
    specialized_tokens = specialized_tokens if specialized_tokens is not None else [256,1536,2048]
    cached_artifacts = cached_artifacts if cached_artifacts is not None else []
    inputs = dict(model=model,shapes=shapes,buckets=buckets,specialized_tokens=specialized_tokens,
                  cached_artifacts=cached_artifacts,repetitions=repetitions,
                  generic_flops_per_second=generic_flops_per_second,bucket_flops_per_second=bucket_flops_per_second,
                  specialized_flops_per_second=specialized_flops_per_second,generic_compile_ns=generic_compile_ns,
                  bucket_compile_ns=bucket_compile_ns,specialized_compile_ns=specialized_compile_ns)
    for name,value in inputs.items():
        if name.endswith(('_ns','_second')) or name=='repetitions':positive_int(value,name)
    if not isinstance(shapes,list) or not shapes:raise ValueError('shapes must be a nonempty list')
    seen=set()
    for shape in shapes:
        positive_int(shape['tokens'],'tokens');positive_int(shape['count'],'count')
        if shape['tokens'] in seen:raise ValueError('duplicate shape tokens')
        seen.add(shape['tokens'])
    for name,values in [('buckets',buckets),('specialized_tokens',specialized_tokens)]:
        if not isinstance(values,list):raise ValueError(name+' must be a list')
        for value in values:positive_int(value,name)
        if len(values)!=len(set(values)):raise ValueError('duplicate '+name)
    config=model_config(model);qwen3.validate(config)
    if max(list(seen)+buckets+specialized_tokens)>config['max_position_embeddings']:
        raise ValueError('shape exceeds pinned context')
    allowed={'generic'}|{'bucket:'+str(t) for t in buckets}|{'specialized:'+str(t) for t in specialized_tokens}
    if not isinstance(cached_artifacts,list) or any(not isinstance(x,str) or x not in allowed for x in cached_artifacts):
        raise ValueError('cache entries must name configured artifacts')
    flop_per_token=6*config['hidden_size']*config['intermediate_size']
    rows=[]
    for policy in ('generic','bucket','specialized'):
        artifacts={};mapping=[];execution=Fraction(0);work=padding=fallback_calls=0
        for shape in shapes:
            tokens,count=shape['tokens'],shape['count']
            artifact='generic';executed=tokens;rate=generic_flops_per_second;compile_cost=generic_compile_ns
            if policy=='bucket':
                candidate=next((b for b in sorted(buckets) if b>=tokens),None)
                if candidate is not None:
                    executed=candidate;artifact='bucket:'+str(candidate)
                    rate=bucket_flops_per_second;compile_cost=bucket_compile_ns
            elif policy=='specialized' and tokens in specialized_tokens:
                artifact='specialized:'+str(tokens);rate=specialized_flops_per_second;compile_cost=specialized_compile_ns
            fallback=policy!='generic' and artifact=='generic'
            fallback_calls+=count if fallback else 0
            artifacts[artifact]=0 if artifact in cached_artifacts else compile_cost
            flops=flop_per_token*executed
            execution+=count*Fraction(flops*10**9,rate)
            work+=count*flops;padding+=count*flop_per_token*(executed-tokens)
            mapping.append(dict(tokens=tokens,count=count,executed_tokens=executed,artifact=artifact,fallback=fallback,
                                per_call_matrix_flops=flops))
        setup=sum(artifacts.values());total=setup+repetitions*execution
        rows.append(dict(policy=policy,artifacts=artifacts,shape_mapping=mapping,prepare_ns=setup,
                         cohort_execution_ns=float(execution),cohort_execution_exact_ns=str(execution),
                         lifetime_ns=float(total),lifetime_exact_ns=str(total),
                         cohort_matrix_flops=work,cohort_padding_flops=padding,fallback_calls=fallback_calls))
    crossings=[]
    for a,b in combinations(rows,2):
        intercept=a['prepare_ns']-b['prepare_ns']
        slope=Fraction(a['cohort_execution_exact_ns'])-Fraction(b['cohort_execution_exact_ns'])
        root=Fraction(-intercept)/slope if slope else None
        crossings.append(dict(policy_a=a['policy'],policy_b=b['policy'],difference_intercept_ns=intercept,
                              difference_slope_exact_ns=str(slope),equality_repetitions_exact=str(root) if root is not None else None,
                              condition='A faster iff intercept + repetitions * slope < 0; repetitions is a positive integer'))
    return dict(schema_version=1,calculation='qwen-shape-specialization',model=model,
                scenario={k:v for k,v in inputs.items() if k!='model'},sources=provenance(model),
                specialization_policies=rows,specialization_crossings=crossings,
                summary=dict(cohort_calls=sum(s['count'] for s in shapes),
                             cohort_real_matrix_flops=sum(s['count']*s['tokens']*flop_per_token for s in shapes),
                             selected_policy=min(rows,key=lambda r:Fraction(r['lifetime_exact_ns']))['policy'],
                             actual_gpu_seconds=None),
                assumptions=[
                    '工作对象为官方Qwen Dense单层FFN三个矩阵，FLOPs=6*M*H*F；不包含激活函数、注意力、通信或完整模型。形状频数为显式教学输入。',
                    '100/200/250TFLOP/s是按同一有效矩阵口径定义的教学服务率，不是GPU官方峰值或实测，不从率差声称编译器实际加速。分桶用补齐后的行数重新计工作。',
                    '按最小可容纳桶分派，超出桶上限或未列入特化集合时用通用路径；通用编译仅在实际使用时计一次。每个用到的artifact每实例准备一次，缓存命中准备为零，不按调用次数重复编译。',
                    '缓存是声明可直接使用的已兼容工件，未计加载／校验时间；实例之间是否共享须由输入指定。三个策略是互斥部署方案，不把它们的准备成本加在一起。',
                    '总时间=缺失工件准备+频数组重复次数*执行时间；串行预算，不模拟编译重叠、缓存淘汰或形状到达顺序。交叉条件为精确仿射不等式，不保证交点在正整数部署范围内。',
                ])
