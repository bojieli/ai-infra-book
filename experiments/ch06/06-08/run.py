#!/usr/bin/env python3
"""实验 6-8：超节点的历史设计选择（进阶推演）。

回到某一代 DGX／TPU 的组织，用当年公开输入复算一组 TP／EP 方案；
再把本章固定模型放到 NVIDIA、TPU 与 UB 三种资源条件下，比较选择为何改变，
并保留“实际采用”与“本推演预测”的差异。

历史锚点全部是公开规格；协作范围与通信预算由
`calculations/calc.py ub-scope|dense-placement` 现场生成。
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

# 当年公开输入（只用该时点已公开的规格）
ERAS = [
    dict(era='DGX-1（2016，P100）', devices_per_node=8, capacity_gb=16,
         scale_up='NVLink 1.0 混合立方网格', note='单机 8 卡，跨机走 InfiniBand。'),
    dict(era='DGX-2（2018，V100）', devices_per_node=16, capacity_gb=32,
         scale_up='NVSwitch 全互连', note='首次把 scale-up 范围从 8 扩到 16。'),
    dict(era='TPU v3 Pod（2018）', devices_per_node=1024, capacity_gb=32,
         scale_up='2D 环面直连', note='协作范围以 pod 为单位，拓扑固定为环面。'),
]

# 三种资源条件（互联带宽与启动时间是声明输入，用于比较选择而非复原历史性能）
RESOURCE_PROFILES = [
    ('NVIDIA 风格：机内快、跨机慢', 50_000_000_000, 2000, 25_000_000_000, 5000),
    ('TPU 风格：范围大但每跳带宽较低', 25_000_000_000, 2000, 20_000_000_000, 3000),
    ('UB 风格：把机内速率延伸到更大范围', 50_000_000_000, 2000, 45_000_000_000, 2500),
]

MODELS = ['qwen3-8b', 'qwen3-32b']


def run(cmd, inputs, out):
    ipath = os.path.join(RESULTS, 'input-%s.json' % out)
    opath = os.path.join(RESULTS, '%s.json' % out)
    json.dump(inputs, open(ipath, 'w'), indent=1)
    proc = subprocess.run([sys.executable, CALC, cmd, '--inputs', ipath,
                           '--format', 'json', '--output', opath],
                          capture_output=True, text=True)
    if proc.returncode != 0:
        return None, (proc.stderr.strip().splitlines() or ['failed'])[-1]
    return json.load(open(opath)), None


def main() -> int:
    os.makedirs(RESULTS, exist_ok=True)
    rows = []
    for model in MODELS:
        for name, lbw, lst, rbw, rst in RESOURCE_PROFILES:
            cfg = dict(model=model, batch=1, history=8192, decode_steps=32,
                       capacity_bytes=24 * GB, workspace_bytes=2 * 1024 ** 3,
                       local_bytes_per_second=lbw, local_startup_ns=lst,
                       remote_bytes_per_second=rbw, remote_startup_ns=rst)
            doc, err = run('ub-scope', cfg,
                           'ub-%s-%s' % (model, name.split('：')[0]))
            if doc is None:
                rows.append(dict(model=model, profile=name, error=err))
                continue
            rows.append(dict(model=model, profile=name,
                             candidates=doc['scope_candidates'],
                             thresholds=doc['scope_crossover']))

    result = dict(schema_version=1, experiment='6-8', title='超节点的历史设计选择',
                  eras=ERAS, resource_profiles=[dict(name=n, local_bps=a, local_startup_ns=b,
                                                     remote_bps=c, remote_startup_ns=d)
                                                for n, a, b, c, d in RESOURCE_PROFILES],
                  rows=rows,
                  reasoning=dict(
                      era_choice='当年（2016–2018）公开可见的模型远小于单机容量：'
                                 'DGX-1 的 8×16 GB＝128 GB 已经能装下当时任何公开模型的权重与状态，'
                                 '因此按当年输入复算，TP 只需要覆盖单机，跨机以数据并行为主。',
                      era_prediction='按这一输入，把 scale-up 范围从 8 扩到 16（DGX-2）在当年很难用容量论证，'
                                     '只能用“更大 batch 的同步开销”论证；'
                                     'TPU 选择 pod 级环面则说明另一条路线：'
                                     '把协作范围做大但接受每跳带宽较低与拓扑固定。',
                      actual='实际采用：NVIDIA 走 NVSwitch 把机内全互连范围扩大，'
                             'TPU 走 pod 级直连环面，两者都在 GPT-3 之前就已确定。',
                      difference='本推演与实际的差异：按当年容量输入，本推演给不出扩大 scale-up 的充分理由；'
                                 '实际选择是按未来负载下注的。差异不在算术，而在“为哪一类负载设计”。',
                      today='把本章固定模型放到三种资源条件下重算：远端带宽越接近本地，'
                            '跨服务器切分越早成为更好的选择；'
                            '这正是 UB 风格路线要改变的那一项——不是提高峰值，而是把机内速率延伸到更大范围。'),
                  source_note='协作范围与通信预算由 calculations/calc.py ub-scope 现场生成；'
                              '互联速率是声明输入，不是历史设备的实测。',
                  python_version=sys.version)
    json.dump(result, open(os.path.join(RESULTS, 'historical.json'), 'w'), indent=2, ensure_ascii=False)

    lines = ['# 实验 6-8 结果：超节点的历史设计选择', '',
             '## 当年公开输入', '',
             '| 代际 | scale-up 范围 | 逐卡容量 | 组织 |', '| --- | ---: | ---: | --- |']
    for e in ERAS:
        lines.append('| %s | %d 设备 | %d GB | %s |' % (
            e['era'], e['devices_per_node'], e['capacity_gb'], e['scale_up']))
    lines += ['', '## 同一模型在三种资源条件下的选择', '',
              '| 模型 | 资源条件 | 通信更优候选 | 单机 TP8 通信/前向 | 双机 TP4×PP2 通信/前向 | 远端带宽阈值 | 远端启动阈值 |',
              '| --- | --- | --- | ---: | ---: | ---: | ---: |']
    for r in rows:
        if 'error' in r:
            lines.append('| %s | %s | 调用失败：%s | — | — | — | — |' % (r['model'], r['profile'], r['error']))
            continue
        cands = {c['name']: c for c in r['candidates']}
        th = r['thresholds'] or {}
        def ms(c):
            summ = c.get('summary') or {}
            v = summ.get('serial_communication_seconds_per_forward_exact')
            return '%.3f ms' % (float(F(v)) * 1e3) if v else '—'
        one = cands.get('single_server_tp8', {})
        two = cands.get('two_servers_tp4_pp2', {})
        thr = th.get('remote_bandwidth_threshold_bytes_per_second_exact')
        sthr = th.get('remote_startup_threshold_seconds_exact')
        lines.append('| %s | %s | %s | %s | %s | %s | %s |' % (
            r['model'], r['profile'],
            th.get('communication_only_preference', '—'), ms(one), ms(two),
            '%.1f MB/s' % (float(F(thr)) / 1e6) if thr else '—',
            '%.1f μs' % (float(F(sthr)) * 1e6) if sthr else '—'))
    rea = result['reasoning']
    lines += ['', '## 推演', '',
              '**当年的选择**：' + rea['era_choice'], '',
              '**当年能给出的预测**：' + rea['era_prediction'], '',
              '**实际采用**：' + rea['actual'], '',
              '**差异**：' + rea['difference'], '',
              '**放到今天**：' + rea['today'], '']
    open(os.path.join(RESULTS, 'historical.md'), 'w').write('\n'.join(lines))
    print('\n'.join(lines))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
