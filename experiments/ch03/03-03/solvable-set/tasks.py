import itertools

# 八道可验证子集计数题，元素数 4/5/6/7 各两道；难度代理＝元素数，运行前固定。
TASKS = [
    dict(id='four-a', values=[2, 3, 5, 7], target=10),
    dict(id='four-b', values=[1, 4, 6, 9], target=10),
    dict(id='five-a', values=[1, 2, 3, 5, 8], target=8),
    dict(id='five-b', values=[2, 4, 5, 7, 9], target=11),
    dict(id='six-a', values=[1, 2, 3, 4, 5, 6], target=9),
    dict(id='six-b', values=[2, 3, 5, 7, 8, 11], target=15),
    dict(id='seven-a', values=[1, 2, 3, 4, 5, 6, 7], target=12),
    dict(id='seven-b', values=[1, 3, 4, 6, 8, 9, 11], target=17),
]


def answer(t):
    return sum(sum(v for v, b in zip(t['values'], mask) if b) == t['target']
               for mask in itertools.product([0, 1], repeat=len(t['values'])))


def dp(t):
    counts = [1] + [0] * t['target']
    for v in t['values']:
        for n in range(t['target'], v - 1, -1):
            counts[n] += counts[n - v]
    return counts[-1]


def prompt(t):
    return ('How many subsets of ' + str(t['values']) + ' have sum exactly ' + str(t['target']) +
            '? Each listed element can be selected at most once. The empty set counts if its sum matches. '
            'Count subsets, not permutations. Think briefly, then give the final answer as exactly one '
            'JSON object with an integer count field, for example {"count": 3}.')


if __name__ == '__main__':
    for t in TASKS:
        assert answer(t) == dp(t), t['id']
        print(t['id'], len(t['values']), answer(t))
