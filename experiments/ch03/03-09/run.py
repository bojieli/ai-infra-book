#!/usr/bin/env python3
"""实验 3-9：Llama 与 Qwen 的训练投入。

从固定公开报告抄录的输入出发，计算 D/N、6ND 近似和代际增长倍数；
MoE 单列总参数与激活参数，并保留数据质量与阶段差异的说明。

本实验不重算：由 `calculations/calc.py training-history` 现场生成
（该命令带官方原件哈希校验）。只依赖标准库。
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

SMALL = ['llama1-7b', 'llama2-7b', 'llama31-8b', 'qwen25-7b-proxy', 'qwen3-8b-proxy']
LARGE = ['llama1-65b', 'llama2-70b', 'llama31-70b', 'llama31-405b',
         'deepseek-v3-pretraining', 'deepseek-v4-flash', 'deepseek-v4-pro']


def main() -> int:
    os.makedirs(RESULTS, exist_ok=True)
    out = os.path.join(RESULTS, 'training-history.json')
    proc = subprocess.run([sys.executable, CALC, 'training-history',
                           '--format', 'json', '--output', out],
                          capture_output=True, text=True)
    if proc.returncode != 0:
        sys.exit('调用失败：\n' + proc.stderr[-900:])
    doc = json.load(open(out))
    rows = {r['input']['id']: r for r in doc['training_history_rows']}

    def pack(ids, group):
        packed = []
        for i in ids:
            r = rows.get(i)
            if r is None:
                continue
            inp = r['input']
            packed.append(dict(
                group=group, id=i,
                parameter_proxy=inp['parameter_proxy'],
                parameter_proxy_kind=inp['parameter_proxy_kind'],
                training_tokens=inp['training_tokens'],
                tokens_per_parameter=(float(F(r['tokens_per_parameter_exact']))
                                      if r['tokens_per_parameter_exact'] else None),
                six_nd_flops=r['proxy_flops'],
                total_reported=r['parameter_context']['total_reported'],
                active_reported=r['parameter_context']['active_reported'],
                gpu_hours=inp.get('gpu_hours'),
                source=inp.get('source_id'), location=inp.get('source_location'),
                scope_notes=inp.get('scope_notes')))
        return packed

    small, large = pack(SMALL, '7–8B 级'), pack(LARGE, '大模型')

    def growth(packed):
        base = next((r for r in packed if r['six_nd_flops']), None)
        for r in packed:
            r['flops_vs_first'] = (r['six_nd_flops'] / base['six_nd_flops']
                                   if base and r['six_nd_flops'] else None)
            r['tokens_vs_first'] = (r['training_tokens'] / base['training_tokens']
                                    if base and r['training_tokens'] else None)
        return packed

    growth(small)
    growth(large)

    result = dict(schema_version=1, experiment='3-9', title='Llama 与 Qwen 的训练投入',
                  source_note='由 calculations/calc.py training-history 现场生成，含官方原件哈希校验。',
                  small=small, large=large,
                  caveats=[
                      '参数量是各报告的名义值代理，不是 checkpoint 精确权重计数。',
                      '6ND 只是近似：它不含注意力随长度增长的部分（见实验 3-6），也不含非矩阵与优化器工作。',
                      '训练 token 数的口径各报告不同（是否含多阶段、是否含重复），不能直接当作数据质量指标。',
                      'MoE 的总参数与激活参数必须分列；用激活参数算 6ND 会低估权重容量需求，用总参数算会高估计算。',
                      '“投入更大”不等于“模型更好”：阶段组成、数据质量与后训练都不在这张表里。',
                  ],
                  python_version=sys.version)
    json.dump(result, open(os.path.join(RESULTS, 'investment.json'), 'w'), indent=2, ensure_ascii=False)

    lines = ['# 实验 3-9 结果：Llama 与 Qwen 的训练投入', '']
    for title, packed in (('7–8B 级', small), ('大模型', large)):
        lines += ['## %s' % title, '',
                  '| 模型 | 参数代理 | 训练 token | D/N | 6ND 近似 | 相对首行 FLOPs | GPU 小时 |',
                  '| --- | ---: | ---: | ---: | ---: | ---: | ---: |']
        for r in packed:
            lines.append('| %s | %s | %s | %s | %s | %s | %s |' % (
                r['id'],
                '%.1f B' % (r['parameter_proxy'] / 1e9) if r['parameter_proxy'] else '未公开',
                '%.1f T' % (r['training_tokens'] / 1e12) if r['training_tokens'] else '未公开',
                '%.1f' % r['tokens_per_parameter'] if r['tokens_per_parameter'] else '—',
                '%.3g' % r['six_nd_flops'] if r['six_nd_flops'] else '—',
                '%.1f×' % r['flops_vs_first'] if r['flops_vs_first'] else '—',
                '{:,}'.format(r['gpu_hours']) if r['gpu_hours'] else '未公开'))
        lines.append('')
    lines += ['## 保留的差异', ''] + ['- ' + c for c in result['caveats']] + ['']
    open(os.path.join(RESULTS, 'investment.md'), 'w').write('\n'.join(lines))
    print('\n'.join(lines))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
