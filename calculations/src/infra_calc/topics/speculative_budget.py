"""Finite-output expected completion time with one-time draft preparation.

Bellman state is (remaining output tokens, draft prepared). Histograms and
costs are explicit stationary teaching inputs, not online profiling data.
"""
from fractions import Fraction
from ..units import positive_int


DEFAULT_OPTIONS = [
    dict(id='draft-1', accepted_counts=[1, 3], draft_ns=100000, verify_ns=1000000),
    dict(id='draft-2', accepted_counts=[4, 3, 9], draft_ns=100000, verify_ns=1150000),
    dict(id='draft-4', accepted_counts=[64, 48, 36, 27, 81], draft_ns=100000, verify_ns=1400000),
]


def calculate(output_tokens=16, baseline_token_ns=1000000, setup_ns=2000000, options=None):
    positive_int(output_tokens, 'output_tokens', allow_zero=True)
    positive_int(baseline_token_ns, 'baseline_token_ns')
    positive_int(setup_ns, 'setup_ns', allow_zero=True)
    if output_tokens > 4096:
        raise ValueError('Exact teaching solver supports at most 4096 output tokens')
    options = DEFAULT_OPTIONS if options is None else options
    if not isinstance(options, list) or not 1 <= len(options) <= 16:
        raise ValueError('Supply 1..16 draft options')
    actions = [dict(id='baseline', counts=[1], cost=baseline_token_ns, drafts=0)]
    normalized = []
    for option in options:
        name = option['id']
        if not isinstance(name, str) or not name or any(a['id'] == name for a in actions):
            raise ValueError('Option IDs must be nonempty unique strings, excluding baseline')
        counts = option['accepted_counts']
        if not isinstance(counts, list) or not 2 <= len(counts) <= 65:
            raise ValueError('Histogram must cover accepted lengths 0..k, k=1..64')
        for count in counts:
            positive_int(count, 'accepted count', allow_zero=True)
        if not sum(counts):
            raise ValueError('Histogram cannot be empty')
        draft = positive_int(option['draft_ns'], 'draft_ns', allow_zero=True)
        verify = positive_int(option['verify_ns'], 'verify_ns')
        commit = positive_int(option.get('commit_ns', 0), 'commit_ns', allow_zero=True)
        actions.append(dict(id=name, counts=counts[:], cost=draft+verify+commit, drafts=len(counts)-1))
        normalized.append(dict(id=name, accepted_counts=counts[:], draft_ns=draft, verify_ns=verify, commit_ns=commit))

    # Ledger: time, rounds, drafted tokens, produced-but-clipped output tokens,
    # expected number of preparations (also probability that setup is used).
    zero = (Fraction(0),)*5
    values = {(0, False): zero, (0, True): zero}
    choices = {}

    def candidate(remaining, warm, action, table):
        is_draft = action['drafts'] > 0
        prepare = is_draft and not warm
        ledger = [Fraction(action['cost'] + setup_ns*prepare), Fraction(1),
                  Fraction(action['drafts']), Fraction(0), Fraction(int(prepare))]
        total = sum(action['counts'])
        for accepted, count in enumerate(action['counts']):
            if not count:
                continue
            produced = accepted + 1
            delivered = min(remaining, produced)
            probability = Fraction(count, total)
            future = table[remaining-delivered, warm or is_draft]
            for i in range(5):
                ledger[i] += probability*future[i]
            ledger[3] += probability*(produced-delivered)
        return tuple(ledger)

    rows = []
    for remaining in range(1, output_tokens+1):
        for warm in (False, True):
            candidates = [(candidate(remaining, warm, a, values), a) for a in actions]
            # Input order breaks equal-time ties; baseline is preferred on ties.
            best, action = min(candidates, key=lambda item: item[0][0])
            values[remaining, warm] = best
            choices[remaining, warm] = action['id']
            rows.append(dict(remaining_tokens=remaining, prepared=warm, selected=action['id'],
                             expected_ns_exact=str(best[0]),
                             candidate_ns_exact={a['id']:str(v[0]) for v,a in candidates}))

    def ledger_row(name, ledger):
        return dict(policy=name, expected_ns_exact=str(ledger[0]), expected_rounds_exact=str(ledger[1]),
                    expected_drafted_tokens_exact=str(ledger[2]), expected_clipped_tokens_exact=str(ledger[3]),
                    preparation_probability_exact=str(ledger[4]))

    policies = [ledger_row('adaptive', values[output_tokens, False])]
    for action in actions:
        table = {(0, False): zero, (0, True): zero}
        for remaining in range(1, output_tokens+1):
            for warm in (False, True):
                table[remaining, warm] = candidate(remaining, warm, action, table)
        policies.append(ledger_row(action['id'], table[output_tokens, False]))
    best = values[output_tokens, False]
    baseline = output_tokens*baseline_token_ns
    return dict(schema_version=1, calculation='speculative-budget', sources=[],
                scenario=dict(output_tokens=output_tokens, baseline_token_ns=baseline_token_ns,
                              setup_ns=setup_ns, options=normalized),
                budget_states=rows, budget_policies=policies,
                summary=dict(output_tokens=output_tokens, baseline_ns=baseline,
                             optimal_expected_ns_exact=str(best[0]),
                             expected_speedup_exact=str(Fraction(baseline)/best[0]) if best[0] else None,
                             first_action=choices.get((output_tokens, False)),
                             preparation_probability_exact=str(best[4]),
                             fixed_best=min(policies[1:], key=lambda p: Fraction(p['expected_ns_exact']))['policy']),
                assumptions=[
                    '有限输出上限的教学期望模型；每个候选的连续接受长度直方图与成本在各轮、各历史位置保持不变。分布不是由单一平均接受率推断，默认计数特意构造自独立3/4接受概率。',
                    '状态为剩余输出数和是否完成草稿准备；首次选择草稿支付setup一次，普通decode不触发准备。所有草稿选项共享同一准备状态与费用，不代表多个独立检查点可免费互换。',
                    '每轮产出a+1，交付min(remaining,a+1)；末轮截断不减已付起草、验证和提交费用。剩余为0时不启动任何工作。不模拟随机EOS、prefill、工具、排队或任务成功率。',
                    'Bellman递推逐状态最小化期望完成时间，基线也是候选；各固定长度策略另行递推，不能用输出数乘稳态每token时间代替有限请求。仅在给定平稳成本／概率与单请求目标下最优，不是已部署在线学习策略。',
                    '时长和直方图均为显式教学输入，未从官方模型FLOPs或硬件峰值推定实际延迟；模型矩阵与KV工作另见speculative-round。',
                ])
