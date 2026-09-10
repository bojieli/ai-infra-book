#!/usr/bin/env python3
"""实验 7-9：多路径与重传成本。

多路径什么时候反而增加重传？用配套简化事件程序改变路径延迟与丢包，
比较重传字节、乱序状态与完成分布；与固定版本 OpenURMA 的对应行为对照。

本实验不重算：由 `calculations/calc.py packet-reorder` 现场生成
（该实现是本书配套的简化事件程序，逐包时序完整导出）。
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
KiB = 1024

BASE = dict(model='qwen3-8b', tokens=1, packet_bytes=1024,
            path_delays_ns=[1000, 9000], path_bytes_per_second=1_000_000_000,
            lost_packets=[0], recovery_delay_ns=20000)

CASES = [
    ('单路径、无丢包', dict(path_delays_ns=[1000], lost_packets=[])),
    ('单路径、丢 1 包', dict(path_delays_ns=[1000], lost_packets=[0])),
    ('双路径均衡（1／1 μs）、无丢包', dict(path_delays_ns=[1000, 1000], lost_packets=[])),
    ('双路径均衡、丢 1 包', dict(path_delays_ns=[1000, 1000], lost_packets=[0])),
    ('双路径失衡（1／9 μs）、无丢包', dict(path_delays_ns=[1000, 9000], lost_packets=[])),
    ('双路径失衡、丢 1 包', dict(path_delays_ns=[1000, 9000], lost_packets=[0])),
    ('双路径重度失衡（1／40 μs）、无丢包', dict(path_delays_ns=[1000, 40000], lost_packets=[])),
    ('双路径重度失衡、丢 1 包', dict(path_delays_ns=[1000, 40000], lost_packets=[0])),
    ('四路径失衡、丢 2 包', dict(path_delays_ns=[1000, 5000, 9000, 20000], lost_packets=[0, 3])),
    ('双路径失衡、恢复更慢（100 μs）', dict(path_delays_ns=[1000, 9000], recovery_delay_ns=100000)),
]


def main() -> int:
    os.makedirs(RESULTS, exist_ok=True)
    rows = []
    for i, (label, over) in enumerate(CASES):
        cfg = dict(BASE)
        cfg.update(over)
        ipath = os.path.join(RESULTS, 'input-%d.json' % i)
        opath = os.path.join(RESULTS, 'reorder-%d.json' % i)
        json.dump(cfg, open(ipath, 'w'), indent=1)
        proc = subprocess.run([sys.executable, CALC, 'packet-reorder', '--inputs', ipath,
                               '--format', 'json', '--output', opath],
                              capture_output=True, text=True)
        if proc.returncode != 0:
            rows.append(dict(label=label, error=(proc.stderr.strip().splitlines() or [''])[-1]))
            continue
        s = json.load(open(opath))['summary']
        rows.append(dict(label=label, paths=len(cfg['path_delays_ns']),
                         lost=len(cfg['lost_packets']), summary=s,
                         first_delivery_ns=float(F(s['first_ordered_delivery_exact_ns'])),
                         completion_ns=float(F(s['completion_exact_ns'])),
                         reorder_area=float(F(s['reorder_area_exact_byte_ns']))))

    result = dict(schema_version=1, experiment='7-9', title='多路径与重传成本',
                  base=BASE, rows=rows,
                  source_note='由 calculations/calc.py packet-reorder 现场生成；'
                              '这是本书配套的简化事件程序，不是 OpenURMA 实现。',
                  python_version=sys.version)
    json.dump(result, open(os.path.join(RESULTS, 'multipath.json'), 'w'), indent=2, ensure_ascii=False)

    lines = ['# 实验 7-9 结果：多路径与重传成本', '',
             '载荷 %d 包 × %d B；路径速率 %.0f Gb/s；丢包恢复 %.0f μs（除非另注）。' % (
                 8, BASE['packet_bytes'], BASE['path_bytes_per_second'] * 8 / 1e9,
                 BASE['recovery_delay_ns'] / 1000), '',
             '| 情形 | 路径 | 丢包 | 发送字节 | 重传字节 | 峰值乱序保留 | 首次有序交付 | 完成 |',
             '| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |']
    for r in rows:
        if 'error' in r:
            lines.append('| %s | — | — | 调用失败：%s | — | — | — | — |' % (r['label'], r['error']))
            continue
        s = r['summary']
        lines.append('| %s | %d | %d | %.1f KiB | %.1f KiB | %.1f KiB（%d 包） | %.1f μs | %.1f μs |' % (
            r['label'], r['paths'], r['lost'],
            s['sent_bytes'] / KiB, s['retransmitted_bytes'] / KiB,
            s['peak_retained_reorder_bytes'] / KiB, s['peak_retained_packets'],
            r['first_delivery_ns'] / 1000, r['completion_ns'] / 1000))
    lines.append('')
    open(os.path.join(RESULTS, 'multipath.md'), 'w').write('\n'.join(lines))
    print('\n'.join(lines))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
