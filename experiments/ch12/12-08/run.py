#!/usr/bin/env python3
"""实验 12-8：跨地域计算与数据费用。

更便宜的算力值得跨地域搬数据吗？给定多地域任务和数据位置，
安排实时与后台工作，扫描传输费用、时限与复用次数。

本实验不重算：由 `calculations/calc.py region-placement` 现场生成
（该实现重放同一条固定轨迹，保证三种放置的质量由构造固定）。
"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
CALC = os.path.join(ROOT, 'calculations', 'calc.py')
RESULTS = os.path.join(HERE, 'results')


def main() -> int:
    os.makedirs(RESULTS, exist_ok=True)
    opath = os.path.join(RESULTS, 'region.json')
    proc = subprocess.run([sys.executable, CALC, 'region-placement',
                           '--format', 'json', '--output', opath],
                          capture_output=True, text=True)
    if proc.returncode != 0:
        sys.exit('调用失败：\n' + proc.stderr[-800:])
    doc = json.load(open(opath))
    mpath = os.path.join(RESULTS, 'region.md')
    proc = subprocess.run([sys.executable, CALC, 'region-placement',
                           '--format', 'md', '--output', mpath],
                          capture_output=True, text=True)

    keys = [k for k in doc if k not in ('assumptions', 'sources')]
    summary = dict(schema_version=1, experiment='12-8', title='跨地域计算与数据费用',
                   available_sections=keys,
                   source_note='由 calculations/calc.py region-placement 现场生成；'
                               '价格、功率上限与交付期是声明输入。',
                   python_version=sys.version)
    json.dump(summary, open(os.path.join(RESULTS, 'summary.json'), 'w'),
              indent=2, ensure_ascii=False)
    print('已生成 results/region.json 与 results/region.md，包含以下小节：')
    for k in keys:
        print(' -', k)
    print()
    print(open(mpath).read()[:2500])
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
