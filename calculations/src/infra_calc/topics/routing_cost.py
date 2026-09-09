"""Exact fictional billing and joint quality/deadline exercise from chapter 11."""
from fractions import Fraction

from ..units import positive_int


def calculate(tasks=1000, prefix_tokens=19000, fresh_tokens=1000,
              b_hit_fraction='1', deadline_seconds=6):
    for name, value in (('tasks', tasks), ('prefix_tokens', prefix_tokens),
                        ('fresh_tokens', fresh_tokens), ('deadline_seconds', deadline_seconds)):
        positive_int(value, name)
    if not isinstance(b_hit_fraction, str):
        raise ValueError('Use an exact fraction string for b_hit_fraction')
    hit = Fraction(b_hit_fraction)
    if not 0 <= hit <= 1:
        raise ValueError('Hit fraction must be in [0,1]')
    candidates = {
        'A': dict(input_price=Fraction(1), cache_price=Fraction(1,10), output_price=Fraction(4),
                  reasoning=1800, visible=200, quality=Fraction(4,5)),
        'B': dict(input_price=Fraction(2), cache_price=Fraction(1,5), output_price=Fraction(8),
                  reasoning=100, visible=200, quality=Fraction(49,50)),
    }
    rows = []
    for name, p in candidates.items():
        h = Fraction(1) if name == 'A' else hit
        output_cost = (p['reasoning'] + p['visible']) * p['output_price'] / 10**6
        hit_cost = (fresh_tokens*p['input_price'] + prefix_tokens*p['cache_price']) / 10**6 + output_cost
        miss_cost = (fresh_tokens+prefix_tokens)*p['input_price']/10**6 + output_cost
        cost = h*hit_cost + (1-h)*miss_cost
        # Given complete request times, independent quality probability in both branches.
        hit_seconds, miss_seconds = (10,10) if name == 'A' else (4,12)
        timely = h * (hit_seconds <= deadline_seconds) + (1-h) * (miss_seconds <= deadline_seconds)
        joint = p['quality'] * timely
        rows.append(dict(candidate=name, hit_fraction_exact=str(h),
                         input_tokens=prefix_tokens+fresh_tokens,
                         reasoning_tokens=p['reasoning'], visible_output_tokens=p['visible'],
                         billed_output_tokens=p['reasoning']+p['visible'],
                         hit_attempt_cost_exact=str(hit_cost), miss_attempt_cost_exact=str(miss_cost),
                         expected_attempt_cost_exact=str(cost), total_cost_exact=str(tasks*cost),
                         expected_quality_successes_exact=str(tasks*p['quality']),
                         cost_per_quality_success_exact=str(cost/p['quality']),
                         expected_joint_successes_exact=str(tasks*joint),
                         joint_success_fraction_exact=str(joint),
                         cost_per_joint_success_exact=str(cost/joint) if joint else None))
    a_cost = Fraction(rows[0]['cost_per_quality_success_exact'])
    b_hit_cost = Fraction(rows[1]['hit_attempt_cost_exact'])
    b_miss_cost = Fraction(rows[1]['miss_attempt_cost_exact'])
    crossover = (b_miss_cost - a_cost*candidates['B']['quality']) / (b_miss_cost-b_hit_cost)
    # Target P(quality AND finish by deadline)>=0.9 under the stated independence.
    target = Fraction(9,10)
    if deadline_seconds < 4:
        min_hit = None
    elif deadline_seconds < 12:
        min_hit = target/candidates['B']['quality']
    else:
        min_hit = Fraction(0)
    return dict(
        schema_version=1, calculation='routing-cost',
        scenario=dict(tasks=tasks, prefix_tokens=prefix_tokens, fresh_tokens=fresh_tokens,
                      b_hit_fraction=b_hit_fraction, deadline_seconds=deadline_seconds),
        sources=[], routing_cost_rows=rows,
        summary=dict(
            cost_crossover_b_hit_fraction_exact=str(crossover),
            cost_crossover_in_unit_interval=0 <= crossover <= 1,
            b_cheaper_per_quality_success=Fraction(rows[1]['cost_per_quality_success_exact']) < a_cost,
            target_joint_success_fraction_exact=str(target),
            minimum_b_hit_for_joint_target_exact=str(min_hit) if min_hit is not None else None,
            b_meets_joint_target=Fraction(rows[1]['joint_success_fraction_exact']) >= target,
        ),
        assumptions=[
            '正文假想A/B价格：每百万token输入/缓存/输出为A=1/0.1/4、B=2/0.2/8；非供应商价格或实测。A reasoning1800+visible200，B100+200，输出计费包含reasoning一次，不再重复加收。',
            'A缓存固定全命中，B在指定相同长度前缀上按完整命中/未命中两分支。新输入总按输入价；缓存创建、存储、工具、环境费用在此教学题设为0，实际费用需另计。',
            '质量成功率A=0.8、B=0.98为给定输入，与缓存分支独立；分母用预期成功数，分子保留全部提交尝试费用。不是有限样本实测比率，也不假设自动重试到成功。',
            '给定完整请求时长A=10秒，B命中4秒/未命中12秒；满足时限使用<=。联合质量/截止时间成功率分开计算，零成功费用比为null，不以平均延迟代替尾部或完成率。',
            '成本交点是精确代数值，可能落在[0,1]之外；另给可实现标志。改变前缀/新输入改变费用，但本题保持给定请求时长不变，不冒充token数到延迟的预测模型。',
        ],
    )
