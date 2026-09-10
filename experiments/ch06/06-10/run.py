#!/usr/bin/env python3
"""实验 6-10：超节点规模与系统成本。

更大的超节点比更多的小型超节点划算吗？在固定的八卡资源上比较
tp8×1 副本、tp4×2 副本、tp2×4 副本三种组织；改变模型、并发、延迟目标
与故障恢复成本，给出选择改变的条件。

本实验不重算：由 `calculations/calc.py supernode-cohort-cost` 现场生成。
"""
import json
import os
import subprocess
import sys
from fractions import Fraction as F

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
CALC = os.path.join(ROOT, 'calculations', 'calc.py')
RESULTS = os.path.join(HERE, 'results')

BASE = dict(model='qwen3-8b', requests=4, prompt=256, outputs=8, deadline_ms=250,
            fault_at_ms=None, recovery_ms=100, recovery_fee='0',
            minimum_valid_fraction='3/4')

CASES = [
    ('基线：4 并发、250 ms 目标、无故障', {}),
    ('并发升到 16', dict(requests=16)),
    ('延迟目标收紧到 120 ms', dict(deadline_ms=120)),
    ('延迟目标放宽到 500 ms', dict(deadline_ms=500)),
    ('输出长度 8→64', dict(outputs=64, deadline_ms=1500)),
    ('注入故障（t=50 ms），恢复 200 ms、恢复计费 1', dict(fault_at_ms=50, recovery_ms=200, recovery_fee='1')),
    ('注入故障且恢复更贵（恢复计费 5）', dict(fault_at_ms=50, recovery_ms=200, recovery_fee='5')),
    ('换更大模型 Qwen3-32B', dict(model='qwen3-32b', deadline_ms=800)),
]


def run(cfg, tag):
    ipath = os.path.join(RESULTS, 'input-%s.json' % tag)
    opath = os.path.join(RESULTS, 'cohort-%s.json' % tag)
    json.dump(cfg, open(ipath, 'w'), indent=1)
    proc = subprocess.run([sys.executable, CALC, 'supernode-cohort-cost', '--inputs', ipath,
                           '--format', 'json', '--output', opath], capture_output=True, text=True)
    if proc.returncode != 0:
        return None, (proc.stderr.strip().splitlines() or ['failed'])[-1]
    return json.load(open(opath)), None


def main() -> int:
    os.makedirs(RESULTS, exist_ok=True)
    rows = []
    for i, (label, over) in enumerate(CASES):
        cfg = dict(BASE)
        cfg.update(over)
        doc, err = run(cfg, 'c%d' % i)
        if doc is None:
            rows.append(dict(label=label, scenario=cfg, error=err))
            continue
        rows.append(dict(label=label, scenario=cfg,
                         candidates=doc['candidates'], selection=doc['selection']))

    result = dict(schema_version=1, experiment='6-10', title='超节点规模与系统成本',
                  base=BASE, rows=rows,
                  source_note='由 calculations/calc.py supernode-cohort-cost 现场生成；'
                              '费用与恢复时间是声明输入。',
                  python_version=sys.version)
    json.dump(result, open(os.path.join(RESULTS, 'cohort.json'), 'w'), indent=2, ensure_ascii=False)

    lines = ['# 实验 6-10 结果：超节点规模与系统成本', '',
             '同一组八卡资源，三种组织：tp8×1 副本（一个大超节点）、tp4×2、tp2×4（多个小超节点）。', '',
             '| 情形 | 组织 | 容量通过 | SLO 有效数 | 完成 ms | 每有效请求费用 | 选中 |',
             '| --- | --- | :---: | ---: | ---: | ---: | :---: |']
    for r in rows:
        if 'error' in r:
            lines.append('| %s | — | — | — | — | 调用失败：%s | — |' % (r['label'], r['error']))
            continue
        winners = set(r['selection'].get('winners', []))
        for c in r['candidates']:
            cost = c.get('cost') or {}
            fee = cost.get('cost_per_slo_valid_request_exact')
            sched = c.get('schedule') or {}
            lines.append('| %s | %s | %s | %s | %s | %s | %s |' % (
                r['label'], c['id'], '是' if c.get('capacity_fits') else '否',
                c.get('valid_requests') if c.get('valid_requests') is not None else '—',
                sched.get('horizon_ms', '—'),
                ('%.4g' % float(F(fee))) if fee else '—',
                '★' if c['id'] in winners else ''))
    lines.append('')
    open(os.path.join(RESULTS, 'cohort.md'), 'w').write('\n'.join(lines))
    print('\n'.join(lines))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
