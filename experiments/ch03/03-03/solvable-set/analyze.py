#!/usr/bin/env python3
"""离线分析 3-3 可完成题集实跑：串行／并行／按规模分配三策略的代价与质量。

只读 results/raw.jsonl 与 results/tasks.json，不启动模型。
"""
import json
import os
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(HERE, 'results')


def main() -> int:
    raw_path = os.path.join(RESULTS, 'raw.jsonl')
    if not os.path.exists(raw_path):
        sys.exit('缺少 results/raw.jsonl：先运行 run.py')
    rows = [json.loads(line) for line in open(raw_path)]
    truth = json.load(open(os.path.join(RESULTS, 'tasks.json')))['answers']

    per_policy = {}
    for r in rows:
        p = per_policy.setdefault(r['policy'], dict(
            groups=0, requests=0, correct=0, input_tokens=0, output_tokens=0,
            seconds=0.0, truncated=0, no_delimiter=0, parse_error=0,
            candidate_correct=0))
        p['groups'] += 1
        p['correct'] += 1 if r['correct'] else 0
        p['seconds'] += r['scored_at'] - r['start']
        for c in r['candidates']:
            p['requests'] += 1
            p['input_tokens'] += len(c['input_ids'])
            p['output_tokens'] += len(c['output_ids'])
            if c['finish_reason'] == 'length':
                p['truncated'] += 1
            if c['value'] is None:
                if c['error'] and 'delimiter' in c['error']:
                    p['no_delimiter'] += 1
                else:
                    p['parse_error'] += 1
            elif c['value'] == truth[r['task']]:
                p['candidate_correct'] += 1

    # 按元素数（难度代理）分组
    per_difficulty = {}
    for r in rows:
        size = len(json.load(open(os.path.join(RESULTS, 'tasks.json')))['tasks'][0]['values'])
        break
    tasks = {t['id']: t for t in json.load(open(os.path.join(RESULTS, 'tasks.json')))['tasks']}
    for r in rows:
        n = len(tasks[r['task']]['values'])
        d = per_difficulty.setdefault(n, dict(groups=0, correct=0, output_tokens=0))
        d['groups'] += 1
        d['correct'] += 1 if r['correct'] else 0
        d['output_tokens'] += sum(len(c['output_ids']) for c in r['candidates'])

    summary = dict(
        schema_version=1, experiment='3-3', variant='solvable-set',
        groups=len(rows), policies=per_policy, per_difficulty=per_difficulty,
        cost_per_correct={
            k: dict(
                output_tokens=(v['output_tokens'] / v['correct']) if v['correct'] else None,
                seconds=(v['seconds'] / v['correct']) if v['correct'] else None,
                requests=(v['requests'] / v['correct']) if v['correct'] else None)
            for k, v in per_policy.items()},
        note='每组一道题一次尝试；正确按“选出的答案等于真值”判定，'
             '真值只在选完后使用。费用为 null（无计价输入）。')
    json.dump(summary, open(os.path.join(RESULTS, 'summary.json'), 'w'),
              indent=2, ensure_ascii=False)

    lines = ['# 3-3 可完成题集结果：串行／并行／按规模分配', '',
             '八道子集计数题（元素数 4/5/6/7 各两道）、两轮、三策略，共 %d 组。'
             '每候选总输出上限 8,192，thinking 开启。' % len(rows), '',
             '| 策略 | 组数 | 正确任务 | 请求数 | 累计输出 token | 耗时和 | 截断候选 | 每正确结果 token | 每正确结果秒 |',
             '| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |']
    for k in ('serial', 'parallel', 'adaptive'):
        v = per_policy.get(k)
        if not v:
            continue
        c = summary['cost_per_correct'][k]
        lines.append('| %s | %d | %d/%d | %d | %d | %.1f s | %d | %s | %s |' % (
            {'serial': '串行', 'parallel': '并行', 'adaptive': '按规模分配'}[k],
            v['groups'], v['correct'], v['groups'], v['requests'],
            v['output_tokens'], v['seconds'], v['truncated'],
            '%.0f' % c['output_tokens'] if c['output_tokens'] else '—',
            '%.2f' % c['seconds'] if c['seconds'] else '—'))
    lines += ['', '## 按难度（元素数）', '',
              '| 元素数 | 组数 | 正确 | 累计输出 token |', '| ---: | ---: | ---: | ---: |']
    for n in sorted(per_difficulty):
        d = per_difficulty[n]
        lines.append('| %d | %d | %d | %d |' % (n, d['groups'], d['correct'], d['output_tokens']))
    lines.append('')
    open(os.path.join(RESULTS, 'summary.md'), 'w').write('\n'.join(lines))
    print('\n'.join(lines))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
