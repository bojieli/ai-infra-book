#!/usr/bin/env python3
"""实验 6-2：Qwen3-8B 的并行组合。

在同一组八卡资源上比较副本、TP=1／2／4／8 与若干 TP×PP 组合：
逐卡权重、KV、计算及每层通信，扫描 batch 与长度，给出各服务目标下的候选区间。

本实验不重算：由 `calculations/calc.py dense-placement|dense-communication` 现场生成。
本目录另有一份实跑：[jax-tp-sp/](jax-tp-sp/README.md) 给出 TP 与 SP 两条路径的实际执行与逐位核对。
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
GB = 10 ** 9
GiB = 2 ** 30

CARDS = 8
PLANS = [(1, 1, 8), (2, 1, 4), (4, 1, 2), (8, 1, 1), (2, 4, 1), (4, 2, 1), (2, 2, 2)]
SCANS = [(8192, 1), (8192, 8), (32768, 1), (32768, 8)]
BANDWIDTH = 450_000_000_000
STARTUP_NS = 3000
CAPACITY = 80 * GB


def run(args, out):
    path = os.path.join(RESULTS, out)
    proc = subprocess.run([sys.executable, CALC] + args + ['--format', 'json', '--output', path],
                          capture_output=True, text=True)
    if proc.returncode != 0:
        return None, (proc.stderr.strip().splitlines() or ['failed'])[-1]
    return json.load(open(path)), None


def main() -> int:
    os.makedirs(RESULTS, exist_ok=True)
    rows = []
    for tp, pp, dp in PLANS:
        for history, batch in SCANS:
            tag = 'tp%d-pp%d-dp%d-h%d-b%d' % (tp, pp, dp, history, batch)
            place, err = run(['dense-placement', '--model', 'qwen3-8b',
                              '--tp', str(tp), '--pp', str(pp), '--dp', str(dp),
                              '--batch-per-replica', str(batch), '--history', str(history),
                              '--tokens', '1', '--capacity-bytes', str(CAPACITY)],
                             'place-%s.json' % tag)
            if place is None:
                rows.append(dict(tp=tp, pp=pp, dp=dp, history=history, batch=batch, error=err))
                continue
            comm, cerr = run(['dense-communication', '--model', 'qwen3-8b',
                              '--tp', str(tp), '--pp', str(pp), '--dp', str(dp),
                              '--batch-per-replica', str(batch), '--tokens', '1',
                              '--bandwidth-bytes-per-second', str(BANDWIDTH),
                              '--startup-ns', str(STARTUP_NS)],
                             'comm-%s.json' % tag)
            ps = place['summary']
            cs = (comm or {}).get('summary', {})
            rows.append(dict(tp=tp, pp=pp, dp=dp, history=history, batch=batch,
                             cards=ps['cards'], global_requests=ps['global_requests'],
                             physical_weight_bytes=ps['physical_weight_bytes'],
                             physical_kv_bytes=ps['physical_kv_bytes'],
                             max_card_resident_bytes=ps['maximum_card_resident_bytes'],
                             all_fit=ps['all_cards_fit_declared_budget'],
                             physical_matrix_flops=ps['physical_matrix_flops'],
                             pipeline_send_bytes=ps['pipeline_network_send_payload_bytes'],
                             comm_summary=cs, comm_error=cerr))

    result = dict(schema_version=1, experiment='6-2', title='Qwen3-8B 的并行组合',
                  cards=CARDS, capacity_bytes=CAPACITY,
                  link=dict(bandwidth_bytes_per_second=BANDWIDTH, startup_ns=STARTUP_NS,
                            note='α 与带宽为声明输入，需要实测校正。'),
                  rows=rows,
                  next_measurement='最值得补测的一项：TP=8 时每层 all-reduce 的实际启动开销 α。'
                                   '本表的通信项按声明 α 计算；实验 6-5 已证明通信与计算共享资源时'
                                   '两者都变慢，因此 α 的实测值会同时改变通信项与计算项。',
                  source_note='由 calculations/calc.py dense-placement|dense-communication 现场生成。',
                  python_version=sys.version)
    json.dump(result, open(os.path.join(RESULTS, 'parallel.json'), 'w'), indent=2, ensure_ascii=False)

    lines = ['# 实验 6-2 结果：Qwen3-8B 的并行组合', '',
             '八卡、逐卡 %.0f GB；互联单向 %.0f GB/s、启动 %.1f μs（声明输入）。' % (
                 CAPACITY / GB, BANDWIDTH / 1e9, STARTUP_NS / 1000), '',
             '| TP×PP×DP | 历史 | 每副本 batch | 全局并发 | 最忙卡驻留 | 容量 | 逐卡矩阵 GFLOPs | 流水交接 |',
             '| --- | ---: | ---: | ---: | ---: | :---: | ---: | ---: |']
    for r in rows:
        if 'error' in r:
            lines.append('| %d×%d×%d | %d | %d | — | 调用失败 | — | — | — |' % (
                r['tp'], r['pp'], r['dp'], r['history'], r['batch']))
            continue
        lines.append('| %d×%d×%d | %d | %d | %d | %.2f GiB | %s | %.2f | %.2f MiB |' % (
            r['tp'], r['pp'], r['dp'], r['history'], r['batch'], r['global_requests'],
            r['max_card_resident_bytes'] / GiB, '通过' if r['all_fit'] else '不通过',
            r['physical_matrix_flops'] / 1e9,
            r['pipeline_send_bytes'] / 2 ** 20))
    lines += ['', '## 每层通信（decode 单步）', '',
              '| TP×PP×DP | 通信摘要 |', '| --- | --- |']
    seen = set()
    for r in rows:
        if 'error' in r or (r['tp'], r['pp'], r['dp']) in seen:
            continue
        seen.add((r['tp'], r['pp'], r['dp']))
        cs = r['comm_summary'] or {}
        items = []
        for k, v in cs.items():
            if isinstance(v, (int, float)) and v:
                items.append('%s %.4g' % (k, v))
            elif isinstance(v, str) and '/' in v:
                try:
                    items.append('%s %.4g' % (k, float(F(v))))
                except Exception:
                    pass
        lines.append('| %d×%d×%d | %s |' % (r['tp'], r['pp'], r['dp'],
                                            '；'.join(items[:5]) or '（见 JSON）'))
    lines += ['', '## 最值得补测的一项', '', result['next_measurement'], '']
    open(os.path.join(RESULTS, 'parallel.md'), 'w').write('\n'.join(lines))
    print('\n'.join(lines[:20]))
    print('...\n完整表见 results/parallel.md')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
