"""Separate benchmark ratios from frequency-weighted deployment and fallback."""
from fractions import Fraction
from .graph_execution import amortization
from ..units import positive_int


def nonnegative(value, name):
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(name+' must be a nonnegative integer')


def calculate(shapes=None, dispatch_ns=0, extra_setup_ns=600*10**9, repetitions=1):
    if shapes is None:
        shapes = [dict(name='x',count=1,baseline_ns=100000,
                       candidates={'A':dict(ns=10000,valid=True),'B':dict(ns=50000,valid=True)}),
                  dict(name='y',count=1,baseline_ns=100000,
                       candidates={'A':dict(ns=200000,valid=True),'B':dict(ns=50000,valid=True)})]
    nonnegative(dispatch_ns,'dispatch_ns')
    nonnegative(extra_setup_ns,'extra_setup_ns')
    positive_int(repetitions,'repetitions')
    if not isinstance(shapes,list) or not shapes:
        raise ValueError('shapes must be a nonempty list')
    names=set();candidates=set()
    for shape in shapes:
        if not isinstance(shape.get('name'),str) or not shape['name'] or shape['name'] in names:
            raise ValueError('shape names must be unique nonempty strings')
        names.add(shape['name'])
        nonnegative(shape['count'],'count')
        positive_int(shape['baseline_ns'],'baseline_ns')
        if not isinstance(shape['candidates'],dict):
            raise ValueError('candidates must be a mapping')
        for name, candidate in shape['candidates'].items():
            if not isinstance(name,str) or not name or name=='baseline':
                raise ValueError('candidate name must be nonempty and not baseline')
            positive_int(candidate['ns'],'candidate ns')
            if type(candidate['valid']) is not bool:
                raise ValueError('valid must be an explicit boolean')
            candidates.add(name)
    calls=sum(shape['count'] for shape in shapes)
    if calls==0:
        raise ValueError('at least one deployment call required')
    rows=[];effective={}
    for name in ['baseline']+sorted(candidates):
        times=[];ratios=[];fallback_calls=0
        for shape in shapes:
            candidate=shape['candidates'].get(name)
            valid=candidate is not None and candidate['valid']
            time=shape['baseline_ns'] if name=='baseline' or not valid else candidate['ns']
            times.append(time)
            ratios.append(Fraction(1) if name=='baseline' else Fraction(shape['baseline_ns'],time) if valid else Fraction(0))
            if name!='baseline' and not valid:
                fallback_calls+=shape['count']
        effective[name]=times
        total=sum(shape['count']*time for shape,time in zip(shapes,times))
        score=sum(ratios)/len(shapes)
        rows.append(dict(candidate=name,shape_mean_ratio=float(score),shape_mean_ratio_exact=str(score),
                         cohort_execution_ns=total,mean_execution_ns=float(Fraction(total,calls)),
                         fallback_calls=fallback_calls))
    best=min(rows,key=lambda row:row['cohort_execution_ns'])
    selected=[];mixed_total=0
    for i,shape in enumerate(shapes):
        winner=min(effective,key=lambda name:effective[name][i])
        execution=effective[winner][i]+dispatch_ns
        mixed_total+=shape['count']*execution
        selected.append(dict(shape=shape['name'],count=shape['count'],selected=winner,
                             selected_execution_ns=effective[winner][i],dispatch_ns=dispatch_ns,
                             deployed_execution_ns=execution))
    saving=best['cohort_execution_ns']-mixed_total
    mean_saving=Fraction(saving,calls)
    crossover=None
    # Two-shape/two-candidate comparison: p weights first shape, 1-p second.
    if len(shapes)==2 and len(candidates)==2:
        a,b=sorted(candidates)
        intercept=effective[a][1]-effective[b][1]
        slope=effective[a][0]-effective[b][0]-intercept
        crossover=dict(candidate_a=a,candidate_b=b,difference_intercept_ns=intercept,
                       difference_slope_ns=slope,
                       equality_first_shape_fraction=str(Fraction(-intercept,slope)) if slope else None,
                       a_faster_condition='intercept + slope * p < 0, with 0 <= p <= 1')
    return dict(schema_version=1,calculation='optimization-deployment',
                scenario=dict(shapes=shapes,dispatch_ns=dispatch_ns,extra_setup_ns=extra_setup_ns,repetitions=repetitions),
                sources=[],deployment_candidates=rows,deployment_selections=selected,crossover=crossover,
                summary=dict(cohort_calls=calls,best_uniform=best['candidate'],
                             best_uniform_cohort_ns=best['cohort_execution_ns'],mixed_cohort_ns=mixed_total,
                             mixed_mean_ns=float(Fraction(mixed_total,calls)),
                             mixed_saving_per_call_exact_ns=str(mean_saving),
                             mixed_lifetime_total_ns=extra_setup_ns+repetitions*mixed_total,
                             uniform_lifetime_total_ns=repetitions*best['cohort_execution_ns'],
                             **amortization(extra_setup_ns,mean_saving),
                             whole_cohort_thresholds=amortization(extra_setup_ns,Fraction(saving)),
                             actual_request_seconds=None),
                assumptions=[
                    '默认x/y与100/10/200/50us均为正文教学输入，不假称Qwen算子或GPU测量；可输入已核对的逐形状候选时间和频数。',
                    '形状平均比值等权纳入全部形状，失败／缺失候选记零仅用于本例分数。部署遇已知失败／缺失项按baseline时间回退，不能用零分当零耗时；未模拟运行中失败后再重试。',
                    '逐形状分派在有效候选和baseline中选择最短时间，再给每次调用加dispatch_ns。统一路径的输入耗时已包含其已有开销；分派策略是固定输入下的理想选择，不证明真实引擎采用。',
                    'extra_setup_ns是相对最佳统一路径的额外准备预算，默认600秒；共同准备成本抵消，不再重复加入。失败搜索、编译、验证若消耗额外串行预算须纳入此输入。',
                    'per-call阈值假定固定频数比例可按平均成本延拓；whole_cohort_thresholds以完整频数组重复，保持整数调用组成。严格更快与恰好摊平分开，节省非正时没有有限回本。',
                    '时间按串行成本汇总，不是带重叠的请求关键路径；CPU/GPU/API费用及质量影响需要各自资源与验证记录。',
                ])
