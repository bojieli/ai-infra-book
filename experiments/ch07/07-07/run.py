#!/usr/bin/env python3
"""实验 7-7：操作顺序与依赖等待。

三个事务在丢包与接收停顿下的时序：先算严格顺序与按依赖放松两种排程
各自的完成时刻与可省等待；再保持必要顺序，比较源端等待与目标端检查；
最后加入“先读旧数据、后返回可用标志”的反例，说明只调整返回顺序为何不够。

本实验不重算：由 `calculations/calc.py operation-ordering` 现场生成。
"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
CALC = os.path.join(ROOT, 'calculations', 'calc.py')
RESULTS = os.path.join(HERE, 'results')

BASE = dict(model='qwen3-8b', tokens=1, write_ns=20000, recovery_ns=80000,
            notification_ns=2000, independent_ns=10000, shared_resource=False,
            read_example=dict(speculative_read_ns=1000, data_visible_ns=2000,
                              flag_visible_ns=3000, flag_read_ns=4000,
                              response_ns=5000, reread_latency_ns=2000))

CASES = [
    ('基线：写 20 μs、恢复 80 μs、通知 2 μs、独立操作 10 μs', {}),
    ('恢复更慢（200 μs）', dict(recovery_ns=200000)),
    ('独立操作更重（50 μs）', dict(independent_ns=50000)),
    ('共享资源（独立操作不能真正并行）', dict(shared_resource=True)),
    ('通知更贵（20 μs）', dict(notification_ns=20000)),
]


def main() -> int:
    os.makedirs(RESULTS, exist_ok=True)
    rows = []
    for i, (label, over) in enumerate(CASES):
        cfg = dict(BASE)
        cfg.update(over)
        ipath = os.path.join(RESULTS, 'input-%d.json' % i)
        opath = os.path.join(RESULTS, 'order-%d.json' % i)
        json.dump(cfg, open(ipath, 'w'), indent=1)
        proc = subprocess.run([sys.executable, CALC, 'operation-ordering', '--inputs', ipath,
                               '--format', 'json', '--output', opath],
                              capture_output=True, text=True)
        if proc.returncode != 0:
            rows.append(dict(label=label, error=(proc.stderr.strip().splitlines() or [''])[-1]))
            continue
        doc = json.load(open(opath))
        rows.append(dict(label=label, summary=doc['summary'],
                         schedules=doc['request_schedules'],
                         stale=doc['stale_read_example']))

    result = dict(schema_version=1, experiment='7-7', title='操作顺序与依赖等待',
                  base=BASE, rows=rows,
                  source_note='由 calculations/calc.py operation-ordering 现场生成。',
                  python_version=sys.version)
    json.dump(result, open(os.path.join(RESULTS, 'ordering.json'), 'w'), indent=2, ensure_ascii=False)

    lines = ['# 实验 7-7 结果：操作顺序与依赖等待', '',
             '## 严格顺序 vs 按依赖放松', '',
             '| 情形 | 严格：全部完成 | 依赖：全部完成 | 严格：独立操作完成 | 依赖：独立操作完成 | 可省等待 | 通知可见 |',
             '| --- | ---: | ---: | ---: | ---: | ---: | ---: |']
    for r in rows:
        if 'error' in r:
            lines.append('| %s | 调用失败：%s | — | — | — | — | — |' % (r['label'], r['error']))
            continue
        s = r['summary']
        lines.append('| %s | %.0f μs | %.0f μs | %.0f μs | **%.0f μs** | %.0f μs | %.0f μs |' % (
            r['label'], s['strict_all_done_ns'] / 1000, s['dependency_all_done_ns'] / 1000,
            s['strict_independent_done_ns'] / 1000, s['dependency_independent_done_ns'] / 1000,
            s['all_done_saved_ns'] / 1000, s['notification_visible_ns'] / 1000))
    stale = rows[0]['stale'] if 'stale' in rows[0] else {}
    s0 = rows[0]['summary']
    lines += ['', '## 反例：先读旧数据、后返回可用标志', '',
              '- 推测读返回的响应是否有效：**%s**' % ('是' if s0['stale_response_valid'] else '否'),
              '- 是否必须重读：**%s**' % ('是' if s0['reread_required'] else '否'),
              '- 经校验的读取交付时刻：%.0f μs' % (s0['validated_read_delivery_ns'] / 1000),
              '', '完整时序见 results/ordering.json 的 `request_schedules` 与 `stale_read_example`。', '']
    open(os.path.join(RESULTS, 'ordering.md'), 'w').write('\n'.join(lines))
    print('\n'.join(lines))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
