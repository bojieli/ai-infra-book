#!/usr/bin/env python3
"""实验 7-6：连接与传输状态的规模。

连接状态和传输状态分开后，省下了什么？给定线程、对端和活跃关系，
计算两种资源组织（每关系一份传输 vs 每对端共享传输），
再加入热点与隔离需求重算。

本实验不重算：由 `calculations/calc.py connection-states` 现场生成。
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


def relations_full(threads, peers):
    return [dict(thread=t, peer=p) for t in range(threads) for p in range(peers)]


def relations_hotspot(threads, peers, hot=4):
    """热点：多数线程只与少数对端通信，少数线程与全部对端通信。"""
    rows = []
    for t in range(threads):
        targets = range(peers) if t < 4 else range(hot)
        for p in targets:
            rows.append(dict(thread=t, peer=p))
    return rows


CASES = [
    ('基线：64 线程 × 128 对端全连接，1 个隔离类', 64, 128, 1, relations_full),
    ('热点：仅 4 个线程全连接，其余只连 4 个对端', 64, 128, 1, relations_hotspot),
    ('隔离：4 个隔离类', 64, 128, 4, relations_full),
    ('规模翻倍：128 线程 × 256 对端', 128, 256, 1, relations_full),
]


def main() -> int:
    os.makedirs(RESULTS, exist_ok=True)
    rows = []
    for i, (label, threads, peers, classes, maker) in enumerate(CASES):
        cfg = dict(threads=threads, peers=peers, isolation_classes=classes,
                   relations=maker(threads, peers))
        ipath = os.path.join(RESULTS, 'input-%d.json' % i)
        opath = os.path.join(RESULTS, 'states-%d.json' % i)
        json.dump(cfg, open(ipath, 'w'), indent=1)
        proc = subprocess.run([sys.executable, CALC, 'connection-states', '--inputs', ipath,
                               '--format', 'json', '--output', opath],
                              capture_output=True, text=True)
        if proc.returncode != 0:
            rows.append(dict(label=label, error=(proc.stderr.strip().splitlines() or [''])[-1]))
            continue
        s = json.load(open(opath))['summary']
        rows.append(dict(label=label, threads=threads, peers=peers,
                         isolation_classes=classes, **s))

    result = dict(schema_version=1, experiment='7-6', title='连接与传输状态的规模',
                  rows=rows,
                  source_note='由 calculations/calc.py connection-states 现场生成。',
                  python_version=sys.version)
    json.dump(result, open(os.path.join(RESULTS, 'states.json'), 'w'), indent=2, ensure_ascii=False)

    lines = ['# 实验 7-6 结果：连接与传输状态的规模', '',
             '| 情形 | 活跃关系 | 每关系一份传输 | 每对端共享传输 | 合计（耦合） | 合计（共享） | 省下 | 预算内 |',
             '| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |']
    for r in rows:
        if 'error' in r:
            lines.append('| %s | 调用失败：%s | — | — | — | — | — | — |' % (r['label'], r['error']))
            continue
        lines.append('| %s | %d | %d | %d | %.2f MiB | %.2f MiB | **%.2f MiB** | 耦合 %s／共享 %s |' % (
            r['label'], r['active_relations'], r['coupled_transport_count'],
            r['shared_transport_count'], r['coupled_total_bytes'] / MiB,
            r['shared_total_bytes'] / MiB, r['saved_bytes'] / MiB,
            '是' if r['coupled_fits_budget'] else '否',
            '是' if r['shared_fits_budget'] else '否'))
    lines.append('')
    open(os.path.join(RESULTS, 'states.md'), 'w').write('\n'.join(lines))
    print('\n'.join(lines))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
