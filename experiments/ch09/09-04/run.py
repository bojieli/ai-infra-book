#!/usr/bin/env python3
"""实验 9-4：PD 与 AF 的交接频次。

为什么同样带宽下 PD 和 AF 表现不同？固定同一教学 GQA 模型：
  PD 每请求交接一次完整 KV 快照（8K、BF16，1.125 GiB）；
  AF 每次 decode 在 36 层间交接 576 KiB、共 72 次方向消息。
先用**相同总字节**的控制比较隔离启动成本，再沿同一请求累计全部 decode 调用
与 prefill 交接。不把一次 PD 与一步 AF 的时间直接作胜负比较。

本实验不重算：由 `calculations/calc.py pd-af-handoff` 现场生成。
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
MiB = 2 ** 20
GiB = 2 ** 30

BASE = dict(model='teaching-gqa', length=8192, batch=1, decode_steps=1,
            element_bytes=2, network_bandwidth=25_000_000_000,
            staging_bandwidth=25_000_000_000, startup_ns=5000, path='direct')

CASES = [
    ('基线：直连、α=5 μs、单步 decode', {}),
    ('累计 128 步 decode（同一请求）', dict(decode_steps=128)),
    ('累计 1024 步 decode（长输出）', dict(decode_steps=1024)),
    ('α=1 μs（更低启动）', dict(startup_ns=1000)),
    ('α=20 μs（跨机以太网）', dict(startup_ns=20000)),
    ('带宽减半（12.5 GB/s）', dict(network_bandwidth=12_500_000_000)),
    ('经主机暂存转发', dict(path='host-staged')),
    ('batch=64 的一步 decode', dict(batch=64)),
]


def main() -> int:
    os.makedirs(RESULTS, exist_ok=True)
    rows = []
    for i, (label, over) in enumerate(CASES):
        cfg = dict(BASE)
        cfg.update(over)
        ipath = os.path.join(RESULTS, 'input-%d.json' % i)
        opath = os.path.join(RESULTS, 'handoff-%d.json' % i)
        json.dump(cfg, open(ipath, 'w'), indent=1)
        proc = subprocess.run([sys.executable, CALC, 'pd-af-handoff', '--inputs', ipath,
                               '--format', 'json', '--output', opath],
                              capture_output=True, text=True)
        if proc.returncode != 0:
            rows.append(dict(label=label, error=(proc.stderr.strip().splitlines() or [''])[-1]))
            continue
        s = json.load(open(opath))['summary']
        rows.append(dict(label=label, scenario=cfg, summary=s,
                         pd_ns=float(F(s['pd_serialized_ns_exact'])),
                         af_ns=float(F(s['af_serialized_ns_exact'])),
                         byte_matched_extra_ns=float(F(s['byte_matched_extra_ns_exact'])),
                         equal_time_startup_ns=float(F(s['equal_time_startup_ns_exact']))))

    result = dict(schema_version=1, experiment='9-4', title='PD 与 AF 的交接频次',
                  base=BASE, rows=rows,
                  source_note='由 calculations/calc.py pd-af-handoff 现场生成。',
                  python_version=sys.version)
    json.dump(result, open(os.path.join(RESULTS, 'handoff.json'), 'w'), indent=2, ensure_ascii=False)

    lines = ['# 实验 9-4 结果：PD 与 AF 的交接频次', '',
             '同一教学 GQA 模型（%d 层、hidden %d、%d 个 KV 头）。' % (
                 rows[0]['summary']['layers'], rows[0]['summary']['hidden_size'],
                 rows[0]['summary']['kv_heads']), '',
             '| 情形 | PD 快照 | AF 单向字节 | AF 总字节 | AF 方向消息数 | PD 串行 | AF 串行 | 相同字节的额外启动 | 等时启动阈值 |',
             '| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |']
    for r in rows:
        if 'error' in r:
            lines.append('| %s | 调用失败：%s | — | — | — | — | — | — | — |' % (r['label'], r['error']))
            continue
        s = r['summary']
        lines.append('| %s | %.3f GiB | %.1f KiB | %.1f KiB | %d | %.3f ms | %.3f ms | %.1f μs | %.1f μs |' % (
            r['label'], s['pd_snapshot_bytes'] / GiB,
            s['af_one_direction_bytes'] / 1024, s['af_total_bytes'] / 1024,
            s['af_directional_messages'],
            r['pd_ns'] / 1e6, r['af_ns'] / 1e6,
            r['byte_matched_extra_ns'] / 1000,
            r['equal_time_startup_ns'] / 1000))
    lines.append('')
    open(os.path.join(RESULTS, 'handoff.md'), 'w').write('\n'.join(lines))
    print('\n'.join(lines))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
