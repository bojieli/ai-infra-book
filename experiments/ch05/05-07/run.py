#!/usr/bin/env python3
"""实验 5-7：形状特化的复用阈值。

为每种长度编译一份程序值不值？给定形状分布，比较三种策略的
“准备成本 ＋ 重复次数 × 每次执行成本”：
  - 通用程序（一次编译，执行最慢）；
  - 分桶（少量编译，执行居中）；
  - 逐形状特化（编译最多，执行最快）。
再扫描复用次数，找出策略翻转的阈值。

本实验不重算：由 `calculations/calc.py shape-specialization` 现场生成，
并复用其已发布的四个场景。只依赖 Python 3 标准库。
"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
CALC = os.path.join(ROOT, 'calculations', 'calc.py')
RESULTS = os.path.join(HERE, 'results')

BASE = dict(
    shapes=[dict(tokens=256, count=8), dict(tokens=1536, count=1), dict(tokens=2048, count=1)],
    buckets=[512, 2048],
    specialized_tokens=[256, 1536, 2048],
    cached_artifacts=[],
    generic_flops_per_second=100_000_000_000_000,
    bucket_flops_per_second=200_000_000_000_000,
    specialized_flops_per_second=250_000_000_000_000,
    generic_compile_ns=100_000_000,
    bucket_compile_ns=200_000_000,
    specialized_compile_ns=300_000_000,
)

REPETITIONS = [1, 2, 5, 10, 20, 40, 70, 140, 400, 1000]


def run(inputs, out):
    ipath = os.path.join(RESULTS, 'input-%s.json' % out)
    opath = os.path.join(RESULTS, 'spec-%s.json' % out)
    json.dump(inputs, open(ipath, 'w'), indent=1)
    proc = subprocess.run([sys.executable, CALC, 'shape-specialization', '--inputs', ipath,
                           '--format', 'json', '--output', opath], capture_output=True, text=True)
    if proc.returncode != 0:
        sys.exit('调用失败 %s：\n%s' % (out, proc.stderr[-800:]))
    return json.load(open(opath))


def main() -> int:
    os.makedirs(RESULTS, exist_ok=True)
    scan = []
    for reps in REPETITIONS:
        cfg = dict(BASE, repetitions=reps)
        doc = run(cfg, 'r%d' % reps)
        row = dict(repetitions=reps, selected=doc['summary']['selected_policy'],
                   policies={p['policy']: p for p in doc['specialization_policies']},
                   crossings=doc.get('specialization_crossings'))
        scan.append(row)

    # 变体：编译成本翻倍、缓存命中（准备成本归零）
    variants = []
    for label, over in [
        ('基线（重复 70 次）', dict(repetitions=70)),
        ('编译成本翻倍', dict(repetitions=70, generic_compile_ns=200_000_000,
                             bucket_compile_ns=400_000_000, specialized_compile_ns=600_000_000)),
        ('特化产物已缓存', dict(repetitions=70,
                             cached_artifacts=['specialized:256', 'specialized:1536',
                                               'specialized:2048'])),
        ('长尾形状更分散', dict(repetitions=70,
                               shapes=[dict(tokens=t, count=1) for t in
                                       (256, 512, 768, 1024, 1536, 2048, 3072, 4096)],
                               specialized_tokens=[256, 512, 768, 1024, 1536, 2048, 3072, 4096],
                               buckets=[1024, 4096])),
    ]:
        cfg = dict(BASE)
        cfg.update(over)
        doc = run(cfg, label.replace(' ', '').replace('（', '').replace('）', ''))
        variants.append(dict(label=label, selected=doc['summary']['selected_policy'],
                             policies={p['policy']: p for p in doc['specialization_policies']},
                             crossings=doc.get('specialization_crossings')))

    result = dict(schema_version=1, experiment='5-7', title='形状特化的复用阈值',
                  base_inputs=BASE, scan=scan, variants=variants,
                  source_note='由 calculations/calc.py shape-specialization 现场生成；'
                              '服务率与准备时间均为教学输入。',
                  python_version=sys.version)
    json.dump(result, open(os.path.join(RESULTS, 'specialization.json'), 'w'),
              indent=2, ensure_ascii=False)

    names = sorted({k for row in scan for k in row['policies']})
    lines = ['# 实验 5-7 结果：形状特化的复用阈值', '',
             '形状分布：256×8、1536×1、2048×1；分桶 512／2048；'
             '编译成本 100／200／300 ms，执行速率 100／200／250 TFLOPs/s（均为教学输入）。', '',
             '## 复用次数扫描（总时间，秒）', '',
             '| 重复次数 | ' + ' | '.join(names) + ' | 最优 |',
             '| ---: | ' + ' | '.join(['---:'] * len(names)) + ' | --- |']
    for row in scan:
        cells = []
        for n in names:
            p = row['policies'].get(n)
            v = p['lifetime_ns'] / 1e9 if p and 'lifetime_ns' in p else None
            cells.append('%.4f' % v if v is not None else '—')
        lines.append('| %d | %s | %s |' % (row['repetitions'], ' | '.join(cells), row['selected']))
    lines += ['', '## 变体', '', '| 情形 | 最优策略 |', '| --- | --- |']
    for v in variants:
        lines.append('| %s | %s |' % (v['label'], v['selected']))
    lines.append('')
    open(os.path.join(RESULTS, 'specialization.md'), 'w').write('\n'.join(lines))
    print('\n'.join(lines))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
