#!/usr/bin/env python3
"""实验 7-5：远程读取的在途并发。

远程读取需要多少在途请求？按 KV-Direct 历史条件复算，再扫描消息大小与延迟，
比较“指令式访问”（小消息、每次都等）与“批量异步访问”（大消息、深流水）。

本实验不重算：由 `calculations/calc.py remote-state` 现场生成。
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

BASE = dict(model='qwen3-8b', length=1024, reuses=4, active_transactions=313,
            transaction_bytes=256, remote_latency_ns=2000,
            remote_bandwidth=40_000_000_000, bulk_bandwidth=25_000_000_000,
            local_bandwidth=1_000_000_000_000, remote_startup_ns=5000,
            bulk_startup_ns=10000, local_startup_ns=1000,
            available_local_bytes=268_435_456)

CASES = [('KV-Direct 历史条件（256 B 事务、2 μs）', {})]
for tb in (64, 256, 1024, 4096, 65536):
    for lat in (2000, 10000, 50000):
        CASES.append(('事务 %d B、延迟 %.0f μs' % (tb, lat / 1000),
                      dict(transaction_bytes=tb, remote_latency_ns=lat)))


def main() -> int:
    os.makedirs(RESULTS, exist_ok=True)
    rows = []
    for i, (label, over) in enumerate(CASES):
        cfg = dict(BASE)
        cfg.update(over)
        ipath = os.path.join(RESULTS, 'input-%d.json' % i)
        opath = os.path.join(RESULTS, 'state-%d.json' % i)
        json.dump(cfg, open(ipath, 'w'), indent=1)
        proc = subprocess.run([sys.executable, CALC, 'remote-state', '--inputs', ipath,
                               '--format', 'json', '--output', opath],
                              capture_output=True, text=True)
        if proc.returncode != 0:
            rows.append(dict(label=label, error=(proc.stderr.strip().splitlines() or [''])[-1]))
            continue
        s = json.load(open(opath))['summary']
        # 保持带宽所需的在途请求数 = 带宽 × 往返延迟 ÷ 每次事务字节
        required = cfg['remote_bandwidth'] * (cfg['remote_latency_ns'] / 1e9) / cfg['transaction_bytes']
        rows.append(dict(label=label, transaction_bytes=cfg['transaction_bytes'],
                         latency_ns=cfg['remote_latency_ns'],
                         required_inflight=required,
                         declared_inflight=cfg['active_transactions'],
                         snapshot_payload_bytes=s['snapshot_payload_bytes'],
                         remote_required_transactions=s['remote_required_transactions'],
                         remote_per_read_ns=float(F(s['remote_per_read_exact_ns'])),
                         direct_total_ns=float(F(s['direct_total_exact_ns'])),
                         staged_total_ns=float(F(s['staged_total_exact_ns'])),
                         direct_network_bytes=s['direct_network_bytes'],
                         staged_network_bytes=s['staged_network_bytes']))

    result = dict(schema_version=1, experiment='7-5', title='远程读取的在途并发',
                  base=BASE, rows=rows,
                  source_note='由 calculations/calc.py remote-state 现场生成；'
                              '“保持带宽所需在途数”＝带宽×延迟÷事务字节，是本实验现算的直接除法。',
                  python_version=sys.version)
    json.dump(result, open(os.path.join(RESULTS, 'inflight.json'), 'w'), indent=2, ensure_ascii=False)

    lines = ['# 实验 7-5 结果：远程读取的在途并发', '',
             '固定远端带宽 %.0f GB/s。' % (BASE['remote_bandwidth'] / 1e9), '',
             '| 情形 | 事务字节 | 延迟 | 保持带宽所需在途 | 每次读取 | 直读总时间 | 暂存总时间 | 直读网络字节 | 暂存网络字节 |',
             '| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |']
    for r in rows:
        if 'error' in r:
            lines.append('| %s | — | — | 调用失败：%s | — | — | — | — | — |' % (r['label'], r['error']))
            continue
        lines.append('| %s | %d B | %.0f μs | **%.0f** | %.2f μs | %.2f μs | %.2f μs | %.1f MiB | %.1f MiB |' % (
            r['label'], r['transaction_bytes'], r['latency_ns'] / 1000,
            r['required_inflight'], r['remote_per_read_ns'] / 1000,
            r['direct_total_ns'] / 1000, r['staged_total_ns'] / 1000,
            r['direct_network_bytes'] / 2 ** 20, r['staged_network_bytes'] / 2 ** 20))
    lines.append('')
    open(os.path.join(RESULTS, 'inflight.md'), 'w').write('\n'.join(lines))
    print('\n'.join(lines))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
