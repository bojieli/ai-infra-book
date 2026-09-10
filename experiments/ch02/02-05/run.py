#!/usr/bin/env python3
"""实验 2-5：混合结构的状态与检索能力。

以 Kimi K3 与 DeepSeek-V4 为主，在同一长度、同一 batch 下输出：
  - 常驻状态（KDA 状态、MLA 历史、V4 索引与压缩缓冲分别列出）；
  - prefill 与 decode 的 FLOPs 与读写；
  - 先按统一状态精度比较机制，再按各自真实格式重算。

固定检索质量记录在 ../02-09/paired-retrieval/ 中单独保存，本脚本只汇总资源侧。
本实验不重算：由 `calculations/calc.py state|k3-forward|v4-forward` 现场生成。
"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
CALC = os.path.join(ROOT, 'calculations', 'calc.py')
RESULTS = os.path.join(HERE, 'results')
MiB = 2 ** 20
GiB = 2 ** 30
TFLOP = 10 ** 12

LENGTH = 32768
BATCH = 1


def run(args, out):
    path = os.path.join(RESULTS, out)
    proc = subprocess.run([sys.executable, CALC] + args + ['--format', 'json', '--output', path],
                          capture_output=True, text=True)
    if proc.returncode != 0:
        sys.exit('调用失败：%s\n%s' % (' '.join(args), proc.stderr[-900:]))
    return json.load(open(path))


def main() -> int:
    os.makedirs(RESULTS, exist_ok=True)
    states = []
    # 统一状态精度（2 字节）与各自默认（真实格式）分别取一次
    for model, extra, tag in [
        ('kimi-k3', ['--mla-path', 'compact'], 'K3（MLA compact ＋ KDA）'),
        ('kimi-k3', ['--mla-path', 'expanded'], 'K3（MLA expanded ＋ KDA）'),
        ('deepseek-v4-flash', [], 'V4-Flash（窗口＋压缩＋索引）'),
        ('deepseek-v4-pro', [], 'V4-Pro（窗口＋压缩＋索引）'),
        ('qwen3-8b', [], 'Qwen3-8B（GQA 对照）'),
    ]:
        doc = run(['state', '--model', model, '--length', str(LENGTH), '--batch', str(BATCH)] + extra,
                  'state-%s-%s.json' % (model, (extra[1] if extra else 'native')))
        states.append(dict(label=tag, model=model, components=doc['components'],
                           summary=doc['summary'], layer_counts=doc.get('layer_counts')))

    forwards = []
    for label, args, out in [
        ('K3 prefill 8192', ['k3-forward', '--batch', '1', '--tokens', '8192', '--history', '0'], 'k3-prefill.json'),
        ('K3 decode 历史 8192', ['k3-forward', '--batch', '1', '--tokens', '1', '--history', '8192'], 'k3-decode.json'),
        ('V4-Flash prefill 8192', ['v4-forward', '--model', 'deepseek-v4-flash', '--batch', '1',
                                   '--tokens', '8192', '--history', '0'], 'v4f-prefill.json'),
        ('V4-Flash decode 历史 8192', ['v4-forward', '--model', 'deepseek-v4-flash', '--batch', '1',
                                       '--tokens', '1', '--history', '8192'], 'v4f-decode.json'),
    ]:
        doc = run(args, out)
        forwards.append(dict(label=label, summary=doc['summary'], coverage=doc.get('coverage')))

    result = dict(schema_version=1, experiment='2-5', title='混合结构的状态与检索能力',
                  scenario=dict(length=LENGTH, batch=BATCH),
                  source_note='由 calculations/calc.py 现场生成；本实验不另行实现公式。',
                  states=states, forwards=forwards,
                  quality_record='../02-09/paired-retrieval/README.md',
                  python_version=sys.version)
    json.dump(result, open(os.path.join(RESULTS, 'hybrid.json'), 'w'), indent=2, ensure_ascii=False)

    lines = ['# 实验 2-5 结果：混合结构的状态与检索能力', '',
             '同一条件：历史 %d token、batch=%d。' % (LENGTH, BATCH), '',
             '## 常驻状态的构成', '',
             '| 模型／路径 | 常驻合计 | 分项 |', '| --- | ---: | --- |']
    for s in states:
        parts = []
        for k, v in s['components'].items():
            if k.endswith('_bytes') and isinstance(v, (int, float)) and v > 0:
                parts.append('%s %.1f MiB' % (k.replace('_bytes', ''), v / MiB))
        lines.append('| %s | %.3f GiB | %s |' % (
            s['label'], s['summary']['resident_bytes'] / GiB, '；'.join(parts[:6])))
    lines += ['', '## prefill 与 decode 的工作', '',
              '| 场景 | 矩阵 TFLOPs | 标量 GFLOPs |', '| --- | ---: | ---: |']
    for f in forwards:
        s = f['summary']
        mf = s.get('matrix_flops_effective_attention', s.get('matrix_flops', 0))
        sf = s.get('accounted_scalar_flops', s.get('scalar_flops', 0))
        lines.append('| %s | %.4f | %.1f |' % (f['label'], mf / TFLOP, sf / 1e9))
    lines += ['', '固定检索质量记录见 [../02-09/paired-retrieval/README.md](../02-09/paired-retrieval/README.md)。', '']
    open(os.path.join(RESULTS, 'hybrid.md'), 'w').write('\n'.join(lines))
    print('\n'.join(lines))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
