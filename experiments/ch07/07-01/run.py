#!/usr/bin/env python3
"""实验 7-1：八卡服务器之间的模型切分。

为 DeepSeek-V4-Pro 与 Kimi K3 先求容量下界，再比较三类候选：
  A. 服务器内 TP／EP（8 卡）；
  B. 服务器间 PP（每机 8 卡，机间只传段边界激活）；
  C. 跨服务器 TP／EP（每层都要跨机集合通信）。
用固定 InfiniBand 与以太网配置的有效带宽与小消息时延，分别算 prefill 与 decode，
说明什么延迟目标下跨服务器推理仍然可行。

容量与工作量由 `calculations/calc.py state|v4-forward|k3-forward` 现场生成；
通信按声明的 α（小消息时延）与有效带宽模型计算，公式在本文件内可读。
"""
import json
import math
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
CALC = os.path.join(ROOT, 'calculations', 'calc.py')
RESULTS = os.path.join(HERE, 'results')
GB = 10 ** 9
GiB = 2 ** 30

CARD_CAPACITY = 80 * GB
CARDS_PER_SERVER = 8
HIDDEN = {'deepseek-v4-pro': 7168, 'kimi-k3': 7168}
LAYERS = {'deepseek-v4-pro': 61, 'kimi-k3': 93}
ACT_BYTES = 2

LINKS = [
    ('机内 NVLink 级 450 GB/s、α=3 μs', 450e9, 3e-6),
    ('InfiniBand 400 Gb/s（50 GB/s）、α=5 μs', 50e9, 5e-6),
    ('以太网 200 Gb/s（25 GB/s）、α=20 μs', 25e9, 20e-6),
]

PHASES = [('prefill 8192', 1, 8192, 0), ('decode b64 h8192', 64, 1, 8192)]


def run(args, out):
    path = os.path.join(RESULTS, out)
    proc = subprocess.run([sys.executable, CALC] + args + ['--format', 'json', '--output', path],
                          capture_output=True, text=True)
    if proc.returncode != 0:
        return None, (proc.stderr.strip().splitlines() or ['failed'])[-1]
    return json.load(open(path)), None


def model_state(model, length, batch):
    doc, err = run(['state', '--model', model, '--length', str(length), '--batch', str(batch)],
                   'state-%s-n%d-b%d.json' % (model, length, batch))
    if doc is None:
        return None, err
    return doc['summary']['resident_bytes'], None


def model_weights(model):
    cmd = 'v4-forward' if model.startswith('deepseek') else 'k3-forward'
    args = [cmd, '--batch', '1', '--tokens', '1', '--history', '0']
    if cmd == 'v4-forward':
        args += ['--model', model]
    doc, err = run(args, 'weights-%s.json' % model)
    if doc is None:
        return None, err
    s = doc['summary']
    return s.get('uniform_bf16_parameter_bytes') or s.get('uniform_matrix_weight_payload_bytes'), None


def main() -> int:
    os.makedirs(RESULTS, exist_ok=True)
    rows = []
    for model in ('deepseek-v4-pro', 'kimi-k3'):
        weights, werr = model_weights(model)
        if weights is None:
            rows.append(dict(model=model, error=werr))
            continue
        for phase, batch, tokens, history in PHASES:
            state, serr = model_state(model, max(history, tokens), batch)
            if state is None:
                rows.append(dict(model=model, phase=phase, error=serr))
                continue
            total = weights + state
            min_cards = math.ceil(total / CARD_CAPACITY)
            servers = math.ceil(min_cards / CARDS_PER_SERVER)
            # 每层激活消息（一次 all-reduce 的载荷）
            positions = batch * tokens
            message = positions * HIDDEN[model] * ACT_BYTES
            for link, bw, alpha in LINKS:
                for plan, crossings, msg in [
                    ('A 服务器内 TP／EP', LAYERS[model], message),
                    ('B 服务器间 PP（只传段边界）', max(1, servers - 1), message),
                    ('C 跨服务器 TP／EP（每层跨机）', LAYERS[model], message),
                ]:
                    if plan.startswith('A') and servers > 1:
                        continue     # 单机放不下时，A 不可行
                    if plan.startswith('A') and link.startswith('Infini'):
                        continue
                    if plan.startswith('A') and link.startswith('以太网'):
                        continue
                    if not plan.startswith('A') and link.startswith('机内'):
                        continue
                    seconds = crossings * (alpha + msg / bw)
                    rows.append(dict(model=model, phase=phase, link=link, plan=plan,
                                     weights_bytes=weights, state_bytes=state,
                                     min_cards=min_cards, servers=servers,
                                     message_bytes=msg, crossings=crossings,
                                     communication_seconds=seconds))

    result = dict(schema_version=1, experiment='7-1', title='八卡服务器之间的模型切分',
                  card_capacity_bytes=CARD_CAPACITY, cards_per_server=CARDS_PER_SERVER,
                  links=[dict(name=n, bandwidth=b, alpha_seconds=a) for n, b, a in LINKS],
                  rows=rows,
                  communication_model='每次交接 = α + 载荷/有效带宽；'
                                      'A/C 按每层一次、B 按段边界一次。',
                  source_note='容量与权重由 calculations/calc.py 现场生成；'
                              '互联有效带宽与 α 是声明输入。',
                  python_version=sys.version)
    json.dump(result, open(os.path.join(RESULTS, 'split.json'), 'w'), indent=2, ensure_ascii=False)

    lines = ['# 实验 7-1 结果：八卡服务器之间的模型切分', '',
             '每卡 %.0f GB，每机 %d 卡；每次交接 = α + 载荷/有效带宽。' % (
                 CARD_CAPACITY / GB, CARDS_PER_SERVER), '',
             '## 容量下界', '',
             '| 模型 | 阶段 | 统一 BF16 权重 | 状态 | 最少卡数 | 最少服务器 |',
             '| --- | --- | ---: | ---: | ---: | ---: |']
    seen = set()
    for r in rows:
        if 'error' in r or (r['model'], r['phase']) in seen:
            continue
        seen.add((r['model'], r['phase']))
        lines.append('| %s | %s | %.1f GB | %.2f GB | %d | %d |' % (
            r['model'], r['phase'], r['weights_bytes'] / GB, r['state_bytes'] / GB,
            r['min_cards'], r['servers']))
    lines += ['', '## 通信预算', '',
              '| 模型 | 阶段 | 互联 | 方案 | 每次载荷 | 交接次数 | 通信时间 |',
              '| --- | --- | --- | --- | ---: | ---: | ---: |']
    for r in rows:
        if 'error' in r:
            continue
        lines.append('| %s | %s | %s | %s | %.2f MiB | %d | %.2f ms |' % (
            r['model'], r['phase'], r['link'], r['plan'],
            r['message_bytes'] / 2 ** 20, r['crossings'],
            r['communication_seconds'] * 1e3))
    lines.append('')
    open(os.path.join(RESULTS, 'split.md'), 'w').write('\n'.join(lines))
    print('\n'.join(lines))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
