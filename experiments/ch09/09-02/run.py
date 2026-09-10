#!/usr/bin/env python3
"""实验 9-2：A100＋H20 的 PD 分离。

分开 prefill 和 decode 的收益何时被抵消？以 A100 80GB SXM 做 prefill、
H20 SXM5 96GB 做 decode，比较共置、同构 PD、异构 PD 与角色对换；
沿同一 Qwen3-8B 扫描输入长度、输出长度、缓存命中、到达率与池规模，
分别评价首 token、逐 token 延迟及费用。

本实验不重算：由 `calculations/calc.py pd-pool` 现场生成。
设备效率是**标明的假设**（本文件顶部），不是实测记录。
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

# 声明的每 worker 服务速率（假设，不是实测）：A100 计算强、H20 带宽强
A100 = dict(name='A100-80GB-prefill', prefill_tokens_per_second=16384, decode_tokens_per_second=64)
H20 = dict(name='H20-96GB-decode', prefill_tokens_per_second=4096, decode_tokens_per_second=256)
LINK = 25_000_000_000

LAYOUTS = [
    ('共置（8 张 A100 都做两件事）', [dict(A100, count=8)]),
    ('同构 PD（A100 4＋4）', [dict(A100, count=8)]),
    ('异构 PD（A100 4 做 prefill，H20 4 做 decode）', [dict(A100, count=4), dict(H20, count=4)]),
    ('全 H20（8 张）', [dict(H20, count=8)]),
]

SCANS = [
    ('输入 2K／输出 128／无命中', 2048, 129, 0, '4'),
    ('输入 8K／输出 128／无命中', 8192, 129, 0, '4'),
    ('输入 8K／输出 1024／无命中', 8192, 1025, 0, '4'),
    ('输入 8K／输出 128／命中 6K 前缀', 8192, 129, 6144, '4'),
    ('输入 32K／输出 128／无命中', 32768, 129, 0, '2'),
    ('输入 8K／输出 128／到达率 8', 8192, 129, 0, '8'),
]


def main() -> int:
    os.makedirs(RESULTS, exist_ok=True)
    rows = []
    for li, (layout_name, workers) in enumerate(LAYOUTS):
        for si, (scan_name, prompt, outputs, cached, arrival) in enumerate(SCANS):
            cfg = dict(model='qwen3-8b', prompt_tokens=prompt, output_tokens=outputs,
                       cached_prefix_tokens=cached, workers=workers,
                       network_bytes_per_second=LINK,
                       arrival_requests_per_second=arrival)
            ipath = os.path.join(RESULTS, 'input-%d-%d.json' % (li, si))
            opath = os.path.join(RESULTS, 'pool-%d-%d.json' % (li, si))
            json.dump(cfg, open(ipath, 'w'), indent=1)
            proc = subprocess.run([sys.executable, CALC, 'pd-pool', '--inputs', ipath,
                                   '--format', 'json', '--output', opath],
                                  capture_output=True, text=True)
            if proc.returncode != 0:
                rows.append(dict(layout=layout_name, scan=scan_name,
                                 error=(proc.stderr.strip().splitlines() or [''])[-1]))
                continue
            s = json.load(open(opath))['summary']
            rows.append(dict(layout=layout_name, scan=scan_name, summary=s,
                             pd_bound=float(F(s['best_pd_bound_requests_per_second_exact'])),
                             colocated_bound=float(F(s['colocated_bound_requests_per_second_exact'])),
                             ratio=float(F(s['pd_to_colocated_bound_ratio_exact'])),
                             network_capacity=float(F(s['network_capacity_requests_per_second_exact'])),
                             transfer_bytes=s['pd_transfer_bytes_per_request'],
                             bottlenecks=s['best_bottlenecks'],
                             best_prefill_workers=s['best_prefill_workers'],
                             best_decode_workers=s['best_decode_workers']))

    result = dict(schema_version=1, experiment='9-2', title='A100＋H20 的 PD 分离',
                  worker_rates=dict(a100=A100, h20=H20,
                                    note='每 worker 服务速率是声明假设，不是实测。'),
                  link_bytes_per_second=LINK, rows=rows,
                  source_note='由 calculations/calc.py pd-pool 现场生成。',
                  python_version=sys.version)
    json.dump(result, open(os.path.join(RESULTS, 'pd.json'), 'w'), indent=2, ensure_ascii=False)

    lines = ['# 实验 9-2 结果：A100＋H20 的 PD 分离', '',
             '每 worker 速率为声明假设：A100 prefill 16,384 tok/s／decode 64 tok/s；'
             'H20 prefill 4,096／decode 256。链路 %.0f GB/s。' % (LINK / 1e9), '',
             '| 布局 | 场景 | 每请求交接 | PD 上界 | 共置上界 | PD/共置 | 链路容量 | 瓶颈 |',
             '| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |']
    for r in rows:
        if 'error' in r:
            lines.append('| %s | %s | 调用失败：%s | — | — | — | — | — | — |' % (
                r['layout'], r['scan'], r['error']))
            continue
        assign = 'P:' + ','.join('%s×%d' % (k, v) for k, v in r['best_prefill_workers'].items() if v)
        assign += ' D:' + ','.join('%s×%d' % (k, v) for k, v in r['best_decode_workers'].items() if v)
        lines.append('| %s | %s | %.3f GiB | %.3f req/s | %.3f req/s | %.2f× | %.3f req/s | %s | %s |' % (
            r['layout'], r['scan'], r['transfer_bytes'] / 2 ** 30,
            r['pd_bound'], r['colocated_bound'], r['ratio'],
            r['network_capacity'], '、'.join(r['bottlenecks']), assign))
    lines.append('')
    open(os.path.join(RESULTS, 'pd.md'), 'w').write('\n'.join(lines))
    print('\n'.join(lines))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
