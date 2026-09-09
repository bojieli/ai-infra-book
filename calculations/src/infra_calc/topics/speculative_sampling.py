"""Exact finite-vocabulary probability ledger for one speculative sample.

Algorithm reference: https://proceedings.mlr.press/v202/leviathan23a.html
This enumerates probability mass, not random trials or an inference engine.
"""
from fractions import Fraction


def distribution(values, name):
    if not isinstance(values, list) or not values:
        raise ValueError(f'{name} must be a nonempty list')
    if any(isinstance(v, bool) or not isinstance(v, (int, str)) for v in values):
        raise ValueError(f'{name} requires exact integer or fraction/decimal strings')
    try:
        result = [Fraction(v) for v in values]
    except (ValueError, ZeroDivisionError) as exc:
        raise ValueError(f'Invalid {name} probability') from exc
    if any(v < 0 for v in result) or sum(result) != 1:
        raise ValueError(f'{name} probabilities must be nonnegative and sum exactly to 1')
    return result


def calculate(target=None, draft=None):
    p = distribution(['1/2', '1/3', '1/6'] if target is None else target, 'target')
    q = distribution(['1/6', '1/3', '1/2'] if draft is None else draft, 'draft')
    if len(p) != len(q):
        raise ValueError('Target and draft must use the same indexed vocabulary')
    accepted = [min(a, b) for a, b in zip(p, q)]
    rejection = 1 - sum(accepted)
    residual = [max(Fraction(0), a-b)/rejection for a, b in zip(p, q)] if rejection else None
    # Explicitly sum every (proposed token, rejected, replacement token) path.
    branches = []
    output = accepted.copy()
    wrong = accepted.copy()
    for i, (proposal, keep) in enumerate(zip(q, accepted)):
        rejected = proposal - keep
        if not rejected:
            continue
        for j in range(len(p)):
            mass = rejected * residual[j]
            wrong_mass = rejected * p[j]
            output[j] += mass
            wrong[j] += wrong_mass
            branches.append(dict(proposal_token=i, replacement_token=j,
                                 corrected_mass_exact=str(mass), wrong_mass_exact=str(wrong_mass)))
    rows = [dict(token=i, target_exact=str(p[i]), draft_exact=str(q[i]),
                 conditional_accept_exact=str(accepted[i]/q[i]) if q[i] else None,
                 accepted_mass_exact=str(accepted[i]),
                 residual_exact=str(residual[i]) if residual is not None else None,
                 output_exact=str(output[i]), wrong_output_exact=str(wrong[i])) for i in range(len(p))]
    return dict(schema_version=1, calculation='speculative-sampling',
                scenario=dict(target=list(map(str, p)), draft=list(map(str, q))), sources=[],
                sampling_tokens=rows, rejection_branches=branches,
                summary=dict(vocabulary_size=len(p), acceptance_exact=str(sum(accepted)),
                             rejection_exact=str(rejection), output_mass_exact=str(sum(output)),
                             output_matches_target=output == p,
                             total_variation_exact=str(sum(abs(a-b) for a, b in zip(output, p))/2),
                             wrong_total_variation_exact=str(sum(abs(a-b) for a, b in zip(wrong, p))/2)),
                assumptions=[
                    '单个固定前缀上的教学概率，词表以共同索引对齐；输入必须已完成temperature/top-k/top-p等处理且归一化，不代表任何真实模型准确率。',
                    '接受概率min(1,p/q)，拒绝后按正残差max(0,p-q)归一化采样。逐项枚举接受质量与每条拒绝→替换路径；全部采用有理数。',
                    'q=0的提议不可达，条件接受率记null；拒绝总质量为零时残差分布不可达，记null，不计算0/0。',
                    '错误对照在拒绝后直接从原目标p重采样；某些特殊分布仍恰好无偏，不能用这类样例替代一般正确性。',
                    '算法依据：[Leviathan et al., ICML 2023, Algorithm 1 / Appendix A.1](https://proceedings.mlr.press/v202/leviathan23a.html)。本模块只验证单步概率质量，不验证多token引擎、随机数实现、浮点误差或KV回滚。',
                ])
