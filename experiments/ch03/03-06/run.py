#!/usr/bin/env python3
"""实验 3-6：各训练阶段的工作量。

对固定 dense（Qwen3-8B）与 V4-Flash 配置，从前向、反向与状态计数开始，
比较三个阶段：预训练、长上下文中期训练、SFT。逐项指出 6ND 漏掉了什么，
并给出影响预算的范围。

本实验不重算：由 `calculations/calc.py training-matrix|training-nonmatrix|
training-state` 现场生成。只依赖标准库。
"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
CALC = os.path.join(ROOT, 'calculations', 'calc.py')
RESULTS = os.path.join(HERE, 'results')
GiB = 2 ** 30
TFLOP = 10 ** 12

# 三个阶段用同一模型、不同序列长度与损失 token 数表示
STAGES = [
    ('预训练（4K 序列，全 token 计损失）', 4096, None),
    ('长上下文中期训练（32K 序列，全 token 计损失）', 32768, None),
    ('SFT（4K 序列，仅 1/4 token 计损失）', 4096, 1024),
]


def run(args, out):
    path = os.path.join(RESULTS, out)
    proc = subprocess.run([sys.executable, CALC] + args + ['--format', 'json', '--output', path],
                          capture_output=True, text=True)
    if proc.returncode != 0:
        sys.exit('调用失败：%s\n%s' % (' '.join(args), proc.stderr[-900:]))
    return json.load(open(path))


def main() -> int:
    os.makedirs(RESULTS, exist_ok=True)
    rows = []
    for model in ('qwen3-8b', 'deepseek-v4-flash'):
        for label, tokens, supervised in STAGES:
            args = ['training-matrix', '--model', model, '--tokens', str(tokens)]
            if supervised:
                args += ['--supervised-tokens', str(supervised), '--head-strategy', 'compact']
            tag = '%s-t%d%s' % (model, tokens, '-sft' if supervised else '')
            try:
                doc = run(args, 'matrix-%s.json' % tag)
            except SystemExit as exc:
                rows.append(dict(model=model, stage=label, error=str(exc)))
                continue
            s = doc['summary']
            rows.append(dict(model=model, stage=label, tokens=tokens,
                             supervised_tokens=supervised or tokens,
                             parameters=s['parameters'],
                             forward_matrix_flops=s['forward_matrix_flops'],
                             backward_matrix_flops=s['backward_matrix_flops'],
                             training_matrix_flops=s['training_matrix_flops'],
                             attention_training_matrix_flops=s['attention_training_matrix_flops'],
                             six_nd_flops=s['six_nd_flops'],
                             matrix_minus_six_nd_flops=s['matrix_minus_six_nd_flops'],
                             matrix_to_six_nd_ratio=s['matrix_to_six_nd_ratio'],
                             executed_head_rows=s.get('executed_head_rows'),
                             unsharded_parameter_state_bytes=s['unsharded_parameter_state_bytes']))

    # V4-Flash 没有统一的训练适配器；改用官方源码派生的四个训练子账
    v4 = []
    for cmd, out in [('v4-training-primitives', 'v4-primitives.json'),
                     ('v4-attention-training', 'v4-attention.json'),
                     ('v4-moe-training', 'v4-moe.json'),
                     ('v4-compressor-training', 'v4-compressor.json'),
                     ('v4-hc-training', 'v4-hc.json')]:
        doc = run([cmd], out)
        v4.append(dict(ledger=cmd, summary=doc.get('summary') or doc.get('totals')))

    nonmatrix = run(['training-nonmatrix'], 'nonmatrix.json')
    state = run(['training-state'], 'state.json')

    ns = nonmatrix['summary']
    missing = dict(
        forward_scalar_flops=ns['forward_scalar_flops'],
        backward_scalar_flops=ns['backward_scalar_flops'],
        optimizer_scalar_flops=ns['optimizer_scalar_flops'],
        special_ops=ns['accounted_special_ops'],
        nonlinear_saved_bytes=ns['nonlinear_saved_at_forward_end_bytes'],
        parameter_state_bytes=ns['original_parameter_state_bytes'],
        still_unknown=[k for k, v in ns.items() if v is None])

    result = dict(schema_version=1, experiment='3-6', title='各训练阶段的工作量',
                  source_note='由 calculations/calc.py 现场生成。',
                  stages=[s[0] for s in STAGES], rows=rows, v4_training_ledgers=v4,
                  six_nd_missing=missing,
                  training_state_summary=state['summary'],
                  python_version=sys.version)
    json.dump(result, open(os.path.join(RESULTS, 'training-stages.json'), 'w'), indent=2, ensure_ascii=False)

    lines = ['# 实验 3-6 结果：各训练阶段的工作量', '',
             '## 三个阶段的矩阵工作与 6ND 对照', '',
             '| 模型 | 阶段 | 计损失 token | 输出头行数 | 前向 TFLOPs | 反向 TFLOPs | 训练矩阵合计 | 其中注意力 | 6ND | 矩阵/6ND |',
             '| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |']
    for r in rows:
        if 'error' in r:
            lines.append('| %s | %s | — | — | 无统一训练适配器，改用下方 V4 子账 | | | | | |' % (r['model'], r['stage']))
            continue
        lines.append('| %s | %s | %d | %s | %.2f | %.2f | %.2f | %.2f | %.2f | %.4f |' % (
            r['model'], r['stage'], r['supervised_tokens'], r.get('executed_head_rows'),
            r['forward_matrix_flops'] / TFLOP, r['backward_matrix_flops'] / TFLOP,
            r['training_matrix_flops'] / TFLOP, r['attention_training_matrix_flops'] / TFLOP,
            r['six_nd_flops'] / TFLOP, r['matrix_to_six_nd_ratio']))
    if v4:
        lines += ['', '## V4-Flash 的训练子账（官方源码派生，非完整训练步）', '',
                  '| 子账 | 主要字段 |', '| --- | --- |']
        for r in v4:
            summ = r['summary'] or {}
            items = ['%s %.4g' % (k, v) for k, v in summ.items()
                     if isinstance(v, (int, float))][:4]
            lines.append('| `%s` | %s |' % (r['ledger'], '；'.join(items) or '（见 JSON）'))
    lines += ['', '## 6ND 漏掉的工作（Qwen3-8B 单步口径）', '',
              '| 项目 | 数值 |', '| --- | ---: |',
              '| 前向标量 FLOPs | %.3f GFLOPs |' % (missing['forward_scalar_flops'] / 1e9),
              '| 反向标量 FLOPs | %.3f GFLOPs |' % (missing['backward_scalar_flops'] / 1e9),
              '| 优化器标量 FLOPs | %.3f GFLOPs |' % (missing['optimizer_scalar_flops'] / 1e9),
              '| 前向末保存的非线性中间量 | %.3f GiB |' % (missing['nonlinear_saved_bytes'] / GiB),
              '| 参数状态（未切分） | %.3f GiB |' % (missing['parameter_state_bytes'] / GiB)]
    lines += ['', '特殊函数原语计数：' + '、'.join('%s %d' % (k, v) for k, v in missing['special_ops'].items()), '',
              '仍未知（不填造）：' + '、'.join(missing['still_unknown']), '']
    open(os.path.join(RESULTS, 'training-stages.md'), 'w').write('\n'.join(lines))
    print('\n'.join(lines))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
