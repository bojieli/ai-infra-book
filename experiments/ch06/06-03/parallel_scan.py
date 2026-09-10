#!/usr/bin/env python3
"""实验 6-3：MoE 结构与并行选择。

对 Qwen3-235B-A22B（第一组）与 V4-Flash／V4-Pro／Kimi K3（第二组）扫描
EP、TP、PP 与副本：逐项统计权重驻留、每 token 的专家读取、dispatch／combine
与最忙设备；再分别改变 prefill 长度、decode batch、互联带宽与延迟。

本实验不重算：由 `calculations/calc.py qwen235-placement|all-to-all|moe-dedup|experts`
现场生成。本目录另有一份**真实路由采集**：见下方“实际路由观测”。
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

PLACEMENTS = [dict(tp=1, ep=8, pp=1), dict(tp=2, ep=4, pp=1), dict(tp=4, ep=2, pp=1),
              dict(tp=8, ep=1, pp=1), dict(tp=2, ep=2, pp=2)]
LINKS = [(450_000_000_000, 3000, '机内 450 GB/s'),
         (50_000_000_000, 5000, 'scale-out 50 GB/s'),
         (50_000_000_000, 20000, 'scale-out 50 GB/s、启动 20 μs')]
TOKENS_PER_RANK = [1, 8, 64, 1024]


def run(args, out):
    path = os.path.join(RESULTS, out)
    proc = subprocess.run([sys.executable, CALC] + args + ['--format', 'json', '--output', path],
                          capture_output=True, text=True)
    if proc.returncode != 0:
        return None, (proc.stderr.strip().splitlines() or ['failed'])[-1]
    return json.load(open(path)), None


def run_inputs(cmd, cfg, out):
    ipath = os.path.join(RESULTS, 'input-%s.json' % out)
    json.dump(cfg, open(ipath, 'w'), indent=1)
    return run([cmd, '--inputs', ipath], '%s.json' % out)


def main() -> int:
    os.makedirs(RESULTS, exist_ok=True)

    placements = []
    for p in PLACEMENTS:
        cfg = dict(p, length=8192, capacity_bytes=80 * GB, workspace_bytes=2 * 1024 ** 3,
                   group_size=128, scale_bytes=2)
        doc, err = run_inputs('qwen235-placement', cfg,
                              'place-tp%d-ep%d-pp%d' % (p['tp'], p['ep'], p['pp']))
        if doc is None:
            placements.append(dict(**p, error=err))
            continue
        placements.append(dict(**p, cohort=doc['cohort'], ranks=len(doc['ranks'])))

    dispatch = []
    for bw, startup, label in LINKS:
        for tpr in TOKENS_PER_RANK:
            for routing in ('balanced', 'hotspot'):
                doc, err = run(['all-to-all', '--model', 'qwen3-235b-a22b',
                                '--tokens-per-rank', str(tpr), '--participants', '8',
                                '--bandwidth-bytes-per-second', str(bw),
                                '--startup-ns', str(startup), '--routing', routing],
                               'a2a-%d-%d-%s-%d.json' % (bw, startup, routing, tpr))
                if doc is None:
                    dispatch.append(dict(link=label, tokens_per_rank=tpr, routing=routing, error=err))
                    continue
                dispatch.append(dict(link=label, tokens_per_rank=tpr, routing=routing,
                                     summary=doc['summary']))

    dedup = []
    for pattern in ('clustered', 'spread'):
        doc, err = run(['moe-dedup', '--model', 'qwen3-235b-a22b', '--pattern', pattern,
                        '--tokens-per-rank', '64', '--participants', '8',
                        '--bandwidth-bytes-per-second', '450000000000',
                        '--startup-ns', '3000'], 'dedup-%s.json' % pattern)
        dedup.append(dict(pattern=pattern, summary=(doc or {}).get('summary'), error=err))

    experts = []
    for model in ('deepseek-v4-flash', 'deepseek-v4-pro', 'kimi-k3'):
        for routing in ('balanced', 'concentrated'):
            doc, err = run(['experts', '--model', model, '--batch', '64', '--routing', routing],
                           'experts-%s-%s.json' % (model, routing))
            experts.append(dict(model=model, routing=routing,
                                summary=(doc or {}).get('summary'), error=err))

    result = dict(schema_version=1, experiment='6-3', title='MoE 结构与并行选择',
                  placements=placements, dispatch=dispatch, dedup=dedup, experts=experts,
                  source_note='由 calculations/calc.py 现场生成；互联速率为声明输入。',
                  python_version=sys.version)
    json.dump(result, open(os.path.join(RESULTS, 'moe-parallel.json'), 'w'),
              indent=2, ensure_ascii=False)

    lines = ['# 实验 6-3 结果：MoE 结构与并行选择', '',
             '## 第一组：Qwen3-235B-A22B 的八卡切分', '',
             '| TP×EP×PP | 位宽 | 八卡物理权重 | 逐卡通过 | 最大并发 | 受限的卡 |',
             '| --- | ---: | ---: | :---: | ---: | --- |']
    for p in placements:
        if 'error' in p:
            lines.append('| %d×%d×%d | — | 调用失败：%s | — | — | — |' % (
                p['tp'], p['ep'], p['pp'], p['error']))
            continue
        for c in p['cohort']:
            lines.append('| %d×%d×%d | %d bit | %.1f GB | %s | %d | %s |' % (
                p['tp'], p['ep'], p['pp'], c['bits'],
                c['physical_weight_bytes'] / GB,
                '是' if c['all_weights_workspace_fit'] else '否',
                c['maximum_requests'],
                '全部' if len(c['limiting_ranks']) == p['tp'] * p['ep'] * p['pp']
                else '、'.join(str(x) for x in c['limiting_ranks'])))
    lines += ['', '## dispatch／combine：路由分布与互联条件', '',
              '| 互联 | 每 rank token | 路由 | 本地/远端分派 | dispatch 发送 | 最忙接收 | dispatch+combine |',
              '| --- | ---: | --- | ---: | ---: | ---: | ---: |']
    for d in dispatch:
        if 'error' in d:
            lines.append('| %s | %d | %s | 调用失败：%s | — | — | — |' % (
                d['link'], d['tokens_per_rank'], d['routing'], d['error']))
            continue
        s = d['summary']
        lines.append('| %s | %d | %s | %d/%d | %.2f MiB | %.2f MiB | %.3f ms |' % (
            d['link'], d['tokens_per_rank'], d['routing'],
            s['local_assignments'], s['remote_assignments'],
            s['dispatch_network_send_bytes'] / 2 ** 20,
            s['dispatch_maximum_receive_bytes'] / 2 ** 20,
            s['dispatch_plus_combine_modeled_seconds'] * 1e3))
    lines += ['', '## 第二组：V4-Flash／V4-Pro／K3 的专家台账（batch=64）', '',
              '| 模型 | 路由 | FFN TFLOPs | 每层专家并集 | 批内权重载荷 |',
              '| --- | --- | ---: | ---: | ---: |']
    for e in experts:
        if not e['summary']:
            lines.append('| %s | %s | 调用失败：%s | — | — |' % (e['model'], e['routing'], e['error']))
            continue
        s = e['summary']
        lines.append('| %s | %s | %.4f | %s | %.1f GiB |' % (
            e['model'], e['routing'], s['ffn_matrix_flops'] / 1e12,
            s.get('expert_union_per_moe_layer', '—'),
            s.get('uniform_matrix_weight_payload_bytes', 0) / GiB))
    lines.append('')
    open(os.path.join(RESULTS, 'moe-parallel.md'), 'w').write('\n'.join(lines))
    print('\n'.join(lines[:22]))
    print('...\n完整表见 results/moe-parallel.md')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
