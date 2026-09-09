"""Finite independent prefix candidates: expected saved matrix work per capacity."""
from fractions import Fraction
from ..models import forward
from ..schema import Scenario
from ..units import positive_int
from .state import calculate as state_calculate


def choose(candidates,budget):
    """Exact 0/1 capacity choice with dominated weight/value states removed."""
    states={0:(Fraction(0),())}
    for index,row in enumerate(candidates):
        expanded=dict(states)
        value=Fraction(row['expected_saved_matrix_flops_exact'])
        for weight,(score,chosen) in states.items():
            new_weight=weight+row['resident_bytes']
            proposal=(score+value,chosen+(index,))
            if new_weight<=budget and proposal[0]>expanded.get(new_weight,(Fraction(-1),()))[0]:
                expanded[new_weight]=proposal
        states={};best=Fraction(-1)
        for weight,entry in sorted(expanded.items()):
            if entry[0]>best:
                states[weight]=entry;best=entry[0]
    weight,(score,indices)=max(states.items(),key=lambda entry:(entry[1][0],-entry[0]))
    return dict(selected=[candidates[i]['id'] for i in indices],resident_bytes=weight,
                expected_saved_matrix_flops_exact=str(score))


def calculate(model='qwen3-8b',page_tokens=16,budget_bytes=180*1024**2,candidates=None):
    positive_int(page_tokens,'page_tokens');positive_int(budget_bytes,'budget_bytes',allow_zero=True)
    if candidates is None:
        candidates=[dict(id=str(n),prefix_tokens=n,suffix_tokens=1,expected_reuses='1') for n in (512,768,1024)]
    if not isinstance(candidates,list) or not candidates or len(candidates)>24:
        raise ValueError('Provide 1 to 24 independent prefix candidates')
    if len({row['id'] for row in candidates})!=len(candidates):raise ValueError('Duplicate candidate ID')
    per_token=state_calculate(model,length=1)['summary']['kv_bytes_per_token_per_request']
    rows=[];sources=None
    for candidate in candidates:
        prefix=candidate['prefix_tokens'];suffix=candidate['suffix_tokens']
        positive_int(prefix,'prefix_tokens');positive_int(suffix,'suffix_tokens')
        reuses=Fraction(candidate['expected_reuses'])
        if reuses<0:raise ValueError('Expected reuses cannot be negative')
        full=forward(model,Scenario(tokens=prefix+suffix,output_head='last'))
        hit=forward(model,Scenario(tokens=suffix,history=prefix,output_head='last'))
        sources=full['sources']
        saved=full['summary']['matrix_flops']-hit['summary']['matrix_flops']
        resident=((prefix+page_tokens-1)//page_tokens)*page_tokens*per_token
        rows.append(dict(id=candidate['id'],prefix_tokens=prefix,suffix_tokens=suffix,
                         expected_reuses_exact=str(reuses),resident_bytes=resident,
                         logical_kv_bytes=prefix*per_token,
                         full_matrix_flops=full['summary']['matrix_flops'],
                         hit_matrix_flops=hit['summary']['matrix_flops'],saved_matrix_flops=saved,
                         expected_saved_matrix_flops_exact=str(saved*reuses),
                         value_per_byte_exact=str(saved*reuses/resident)))
    optimal=choose(rows,budget_bytes)
    remaining=budget_bytes;greedy=[];value=Fraction(0)
    for row in sorted(rows,key=lambda row:-Fraction(row['value_per_byte_exact'])):
        if row['resident_bytes']<=remaining and Fraction(row['expected_saved_matrix_flops_exact'])>0:
            remaining-=row['resident_bytes'];greedy.append(row['id'])
            value+=Fraction(row['expected_saved_matrix_flops_exact'])
    return dict(schema_version=1,calculation='prefix-value',
                scenario=dict(model=model,page_tokens=page_tokens,budget_bytes=budget_bytes,candidates=candidates),
                sources=sources,prefix_candidates=rows,
                prefix_choices=dict(optimal=optimal,density_greedy=dict(selected=greedy,resident_bytes=budget_bytes-remaining,
                                                                      expected_saved_matrix_flops_exact=str(value))),
                summary=dict(kv_bytes_per_token=per_token,optimal_selected=optimal['selected'],
                             optimal_resident_bytes=optimal['resident_bytes'],
                             optimal_expected_saved_matrix_flops_exact=optimal['expected_saved_matrix_flops_exact'],
                             density_greedy_selected=greedy,density_greedy_resident_bytes=budget_bytes-remaining,
                             density_greedy_expected_saved_matrix_flops_exact=str(value),
                             optimal_minus_greedy_flops_exact=str(Fraction(optimal['expected_saved_matrix_flops_exact'])-value)),
                assumptions=[
                    '每候选来自独立前缀身份，不共享物理页或互相包含；同模型、格式和位置语义满足复用条件。整前缀准入或不准入，不做部分命中；页尾按完整页占用。',
                    '每次后续请求还有至少一个suffix token以重算末端logits。官方Qwen full前向与history=prefix的suffix前向相减，已命中历史仍参与suffix注意力；不能把命中token直接当全部注意力免算。',
                    '目标仅为有限候选集合中最大化预期节省的矩阵FLOPs，expected_reuses是显式非负有理数假设，不是从模型配置推断的命中率。线性期望无需假设候选复用独立，但未模拟复用时间或TTL。',
                    '精确0/1选择与单位字节价值贪心对照；不可拆分大小使贪心可能留下不可用余量。精确最优只针对此静态独立候选模型，不是最优在线淘汰策略。',
                    '省下FLOPs不等于省下墙钟：不含取回延迟、调度、查表和质量差异；scalar／special运算不纳入此单一目标。留存容量对其它活跃请求的代价需服务层另算。',
                ])
