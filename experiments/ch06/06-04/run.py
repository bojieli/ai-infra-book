#!/usr/bin/env python3
"""实验 6-4：环与树的选择条件。

这条消息用环还是树更合适？扫描消息大小与参与者数量，比较环形与树形
all-reduce 的轮次、每 rank 收发字节与建模时间，给出选择条件。

四个参与者的手画对照单列（轮次与字节），再用扫描给出交叉点。
本实验不重算：由 `calculations/calc.py ring-collective|tree-collective` 现场生成。
"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
CALC = os.path.join(ROOT, 'calculations', 'calc.py')
RESULTS = os.path.join(HERE, 'results')
KiB = 1024
MiB = 2 ** 20

TOKENS = [1, 4, 16, 64, 256, 1024, 4096, 8192]
PARTICIPANTS = [4, 8, 16]
BANDWIDTH = 50_000_000_000     # 50 GB/s 单向有效（声明输入）
STARTUP_NS = 4000              # 每次消息的启动时间（声明输入）


def run(cmd, tokens, parts, out):
    path = os.path.join(RESULTS, out)
    proc = subprocess.run([sys.executable, CALC, cmd, '--model', 'qwen3-8b',
                           '--tokens', str(tokens), '--participants', str(parts),
                           '--bandwidth-bytes-per-second', str(BANDWIDTH),
                           '--startup-ns', str(STARTUP_NS),
                           '--format', 'json', '--output', path],
                          capture_output=True, text=True)
    if proc.returncode != 0:
        sys.exit('调用失败 %s t=%d p=%d：\n%s' % (cmd, tokens, parts, proc.stderr[-600:]))
    return json.load(open(path))


def main() -> int:
    os.makedirs(RESULTS, exist_ok=True)
    rows = []
    for parts in PARTICIPANTS:
        for tokens in TOKENS:
            ring = run('ring-collective', tokens, parts, 'ring-p%d-t%d.json' % (parts, tokens))
            tree = run('tree-collective', tokens, parts, 'tree-p%d-t%d.json' % (parts, tokens))
            r, t = ring['summary'], tree['summary']
            rows.append(dict(
                participants=parts, tokens=tokens,
                message_bytes=r['message_bytes_per_rank'],
                ring_rounds=r['all_reduce_rounds'], tree_rounds=t['all_reduce_rounds'],
                ring_send_bytes=r['all_reduce_send_bytes_per_rank'],
                tree_send_bytes=t['maximum_rank_send_bytes'],
                ring_startup_seconds=r['all_reduce_startup_seconds'],
                tree_startup_seconds=t['all_reduce_startup_seconds'],
                ring_bandwidth_seconds=r['all_reduce_bandwidth_seconds'],
                tree_bandwidth_seconds=t['all_reduce_bandwidth_seconds'],
                ring_seconds=r['all_reduce_modeled_seconds'],
                tree_seconds=t['all_reduce_modeled_seconds'],
                better='ring' if r['all_reduce_modeled_seconds'] <= t['all_reduce_modeled_seconds'] else 'tree'))

    crossings = []
    for parts in PARTICIPANTS:
        sub = [r for r in rows if r['participants'] == parts]
        prev = None
        for r in sub:
            if prev and prev['better'] != r['better']:
                crossings.append(dict(participants=parts,
                                      between_bytes=[prev['message_bytes'], r['message_bytes']],
                                      from_policy=prev['better'], to_policy=r['better']))
            prev = r

    result = dict(schema_version=1, experiment='6-4', title='环与树的选择条件',
                  bandwidth_bytes_per_second=BANDWIDTH, startup_ns=STARTUP_NS,
                  source_note='由 calculations/calc.py ring-collective|tree-collective 现场生成；'
                              '带宽与启动时间是声明输入。',
                  rows=rows, crossings=crossings, python_version=sys.version)
    json.dump(result, open(os.path.join(RESULTS, 'ring-tree.json'), 'w'), indent=2, ensure_ascii=False)

    lines = ['# 实验 6-4 结果：环与树', '',
             '单向 %.0f GB/s、每次消息启动 %.1f μs（声明输入）。' % (
                 BANDWIDTH / 1e9, STARTUP_NS / 1000), '',
             '## 四个参与者的手画对照', '',
             '| 每 rank 消息 | 环轮次 | 树轮次 | 环每 rank 发送 | 树最忙 rank 发送 | 环用时 | 树用时 | 更快 |',
             '| ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |']
    for r in rows:
        if r['participants'] != 4:
            continue
        lines.append('| %s | %d | %d | %s | %s | %.1f μs | %.1f μs | %s |' % (
            '%.1f KiB' % (r['message_bytes'] / KiB) if r['message_bytes'] < MiB
            else '%.1f MiB' % (r['message_bytes'] / MiB),
            r['ring_rounds'], r['tree_rounds'],
            '%.1f KiB' % (r['ring_send_bytes'] / KiB),
            '%.1f KiB' % (r['tree_send_bytes'] / KiB),
            r['ring_seconds'] * 1e6, r['tree_seconds'] * 1e6,
            '环' if r['better'] == 'ring' else '树'))
    lines += ['', '## 扫描：消息大小 × 参与者', '',
              '| 参与者 | 每 rank 消息 | 环用时 | 树用时 | 更快 |',
              '| ---: | ---: | ---: | ---: | --- |']
    for r in rows:
        lines.append('| %d | %s | %.1f μs | %.1f μs | %s |' % (
            r['participants'],
            '%.1f KiB' % (r['message_bytes'] / KiB) if r['message_bytes'] < MiB
            else '%.1f MiB' % (r['message_bytes'] / MiB),
            r['ring_seconds'] * 1e6, r['tree_seconds'] * 1e6,
            '环' if r['better'] == 'ring' else '树'))
    lines += ['', '## 交叉点', '']
    for c in crossings:
        lines.append('- %d 个参与者：在每 rank 消息 %.1f KiB 与 %.1f KiB 之间由「%s」转为「%s」。' % (
            c['participants'], c['between_bytes'][0] / KiB, c['between_bytes'][1] / KiB,
            '树' if c['from_policy'] == 'tree' else '环',
            '树' if c['to_policy'] == 'tree' else '环'))
    lines.append('')
    open(os.path.join(RESULTS, 'ring-tree.md'), 'w').write('\n'.join(lines))
    print('\n'.join(lines))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
