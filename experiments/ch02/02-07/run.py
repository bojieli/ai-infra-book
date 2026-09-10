#!/usr/bin/env python3
"""实验 2-7：模型规模与硬件的适配范围。

对 24／48／80／96 GB 单卡，逐项计算 8B 与 70B 级模型的权重、KV、工作区与
可并发请求数；改变精度（16／8／4 bit）与历史长度（8K／32K），观察可行范围
怎样变化。再用 235B 的八卡放置结果说明“总容量够”仍需检查逐卡余量。

本实验不重算：全部由 `calculations/calc.py capacity-scan|qwen235-placement`
现场生成。只依赖 Python 3 标准库。
"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
CALC = os.path.join(ROOT, 'calculations', 'calc.py')
RESULTS = os.path.join(HERE, 'results')
GB = 10 ** 9
GiB = 2 ** 30

CAPACITIES = ['24000000000', '48000000000', '80000000000', '96000000000']
MODELS = ['qwen3-8b', 'qwen3-32b', 'deepseek-r1-distill-llama-70b']
LENGTHS = [8192, 32768]


def run(args, out):
    path = os.path.join(RESULTS, out)
    proc = subprocess.run([sys.executable, CALC] + args + ['--format', 'json', '--output', path],
                          capture_output=True, text=True)
    if proc.returncode != 0:
        sys.exit('调用失败：%s\n%s' % (' '.join(args), proc.stderr[-800:]))
    return json.load(open(path))


def main() -> int:
    os.makedirs(RESULTS, exist_ok=True)
    rows = []
    for model in MODELS:
        for length in LENGTHS:
            doc = run(['capacity-scan', '--model', model, '--length', str(length),
                       '--capacities'] + CAPACITIES,
                      'capacity-%s-n%d.json' % (model, length))
            for c in doc['capacity_comparisons']:
                rows.append(dict(model=model, length=length, **c))

    placement = run(['qwen235-placement'], 'qwen235-placement.json')

    result = dict(schema_version=1, experiment='2-7', title='模型规模与硬件的适配范围',
                  source_note='由 calculations/calc.py 现场生成，本实验不另行实现公式。',
                  capacities=[int(c) for c in CAPACITIES], lengths=LENGTHS,
                  rows=rows, placement=placement,
                  python_version=sys.version)
    json.dump(result, open(os.path.join(RESULTS, 'capacity.json'), 'w'), indent=2, ensure_ascii=False)

    lines = ['# 实验 2-7 结果：模型规模与硬件的适配范围', '',
             '工作区按 %.1f GiB 声明；KV 按 BF16。' % (rows[0]['workspace_bytes'] / GiB), '',
             '## 单卡可行范围（最大并发请求数）', '',
             '| 模型 | 历史 | 位宽 | 权重 | 24 GB | 48 GB | 80 GB | 96 GB |',
             '| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |']
    index = {}
    for r in rows:
        index.setdefault((r['model'], r['length'], r['matrix_bits']), {})[r['capacity_bytes']] = r
    for key in sorted(index, key=lambda k: (MODELS.index(k[0]), k[1], -k[2])):
        model, length, bits = key
        cells = index[key]
        first = next(iter(cells.values()))
        def cell(cap):
            r = cells.get(int(cap))
            if r is None:
                return '—'
            if not r['weights_and_workspace_fit']:
                return '权重放不下'
            return str(r['maximum_requests'])
        lines.append('| %s | %d | %d bit | %.1f GB | %s | %s | %s | %s |' % (
            model, length, bits, first['weight_bytes'] / GB,
            cell(CAPACITIES[0]), cell(CAPACITIES[1]), cell(CAPACITIES[2]), cell(CAPACITIES[3])))
    sc = placement['scenario']
    lines += ['', '## Qwen3-235B-A22B 的八卡放置（TP=%d、EP=%d、PP=%d，逐卡 %.0f GB）' % (
        sc['tp'], sc['ep'], sc['pp'], sc['capacity_bytes'] / GB), '',
        '| 位宽 | 八卡物理权重合计 | 权重＋工作区逐卡通过 | 最大并发请求 | 受限的卡 |',
        '| ---: | ---: | :---: | ---: | --- |']
    for c in placement['cohort']:
        lines.append('| %d bit | %.1f GB | %s | %d | %s |' % (
            c['bits'], c['physical_weight_bytes'] / GB,
            '是' if c['all_weights_workspace_fit'] else '否',
            c['maximum_requests'],
            '、'.join(str(x) for x in c['limiting_ranks'])))
    per_rank = []
    for rank in placement['ranks']:
        total = {}
        for t in rank['tensors']:
            for st in t['storage']:
                total[st['bits']] = total.get(st['bits'], 0) + st['total_bytes'] * (t['copies'] or 1) // (t['copies'] or 1)
        per_rank.append(dict(rank=rank['rank'], layer_range=rank['layer_range'],
                             expert_range=rank['expert_range']))
    lines += ['', '八卡合计容量 %.0f GB，16 bit 时物理权重 %.1f GB——总容量看似有余量，'
              '但受限的卡是全部 8 张，说明瓶颈在逐卡余量而不是总和。' % (
                  8 * sc['capacity_bytes'] / GB, placement['cohort'][0]['physical_weight_bytes'] / GB), '']
    open(os.path.join(RESULTS, 'capacity.md'), 'w').write('\n'.join(lines))
    print('\n'.join(lines))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
