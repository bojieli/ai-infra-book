#!/usr/bin/env python3
"""实验 10-3：4090 集群的可行范围。

4090 集群的哪一项先不够？沿用 Qwen3-8B 的领域训练任务，再换成 Qwen3-235B；
对具体 4090 主机、PCIe、NIC 与 H100 系统计算逐卡容量、训练步通信和总时间。
先排除无法达到期限的组合，再指出剩余候选最需要哪项实测。

容量与工作量由 `calculations/calc.py training-matrix|training-state` 现场生成；
设备规格取自统一计算项目的官方硬件表；PCIe／NIC 是声明输入。
"""
import json
import math
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
CALC = os.path.join(ROOT, 'calculations', 'calc.py')
HARDWARE = os.path.join(ROOT, 'calculations', 'configs', 'hardware.json')
RESULTS = os.path.join(HERE, 'results')
GB = 10 ** 9
GiB = 2 ** 30

TOKEN_TARGET = 100_000_000_000
DEADLINE_DAYS = 30
EFFICIENCY = 0.35

# 具体系统：卡型、每机卡数、卡间链路、机间 NIC（声明输入）
SYSTEMS = [
    ('4090 主机（8 卡／PCIe Gen4 x16／单 100 Gb NIC）', 'rtx4090', 8, 25e9, 12.5e9),
    ('4090 主机（8 卡／PCIe Gen4 x16／4×200 Gb NIC）', 'rtx4090', 8, 25e9, 100e9),
    ('H100 系统（8 卡／NVLink／8×400 Gb NIC）', 'h100-sxm', 8, 450e9, 400e9),
]
MODELS = ['qwen3-8b', 'qwen3-235b-a22b']


def run(args, out):
    path = os.path.join(RESULTS, out)
    proc = subprocess.run([sys.executable, CALC] + args + ['--format', 'json', '--output', path],
                          capture_output=True, text=True)
    if proc.returncode != 0:
        return None, (proc.stderr.strip().splitlines() or ['failed'])[-1]
    return json.load(open(path)), None


def device(dev_id):
    raw = json.load(open(HARDWARE))
    devs = raw['devices'] if isinstance(raw, dict) and 'devices' in raw else raw
    devs = devs if isinstance(devs, list) else list(devs.values())
    d = next(x for x in devs if x.get('id') == dev_id)
    peaks = d.get('peak_rates') or []
    bf16 = next((p for p in peaks if p['input_precision'] == 'BF16'
                 and p.get('sparsity') == 'dense'), None)
    return dict(id=dev_id, name=d['name'],
                capacity=int(d['memory']['nominal_capacity'] * GB),
                bandwidth=d['memory']['bandwidth_bytes_per_second'],
                peak=(bf16['tera_ops_per_second'] * 1e12) if bf16 else None)


def main() -> int:
    os.makedirs(RESULTS, exist_ok=True)
    rows = []
    for model in MODELS:
        doc, err = run(['training-matrix', '--model', model, '--tokens', '4096'],
                       'matrix-%s.json' % model)
        if doc is None:
            rows.append(dict(model=model, error=err))
            continue
        s = doc['summary']
        per_token = s['training_matrix_flops'] / s['input_tokens']
        total_flops = per_token * TOKEN_TARGET
        state_bytes = s['unsharded_parameter_state_bytes']
        grad_bytes = s['parameters'] * 2      # BF16 梯度 all-reduce 载荷
        for label, dev_id, per_host, intra, inter in SYSTEMS:
            dev = device(dev_id)
            if dev['peak'] is None:
                rows.append(dict(model=model, system=label, error='官方未记录该卡的 BF16 dense 峰值'))
                continue
            # 逐卡容量：状态按卡数均分（ZeRO 风格分片，通信另计）
            cards_for_compute = math.ceil(total_flops / (dev['peak'] * EFFICIENCY) /
                                          (DEADLINE_DAYS * 86400))
            cards_for_state = math.ceil(state_bytes / (dev['capacity'] * 0.7))  # 留 30% 给激活与临时量
            cards = max(cards_for_compute, cards_for_state, per_host)
            hosts = math.ceil(cards / per_host)
            # 每步梯度 all-reduce：机内环形＋机间环形，取较慢的一段
            intra_bytes = 2 * (per_host - 1) / per_host * grad_bytes
            intra_seconds = intra_bytes / intra
            inter_seconds = (2 * (hosts - 1) / hosts * grad_bytes / inter) if hosts > 1 else 0.0
            step_tokens = 4096 * cards
            step_compute = per_token * step_tokens / (cards * dev['peak'] * EFFICIENCY)
            comm = intra_seconds + inter_seconds
            step_total = step_compute + comm
            steps = TOKEN_TARGET / step_tokens
            days = steps * step_total / 86400
            rows.append(dict(model=model, system=label, device=dev['name'],
                             cards_for_compute=cards_for_compute,
                             cards_for_state=cards_for_state, cards=cards, hosts=hosts,
                             per_card_state_bytes=state_bytes / cards,
                             step_compute_seconds=step_compute,
                             intra_seconds=intra_seconds, inter_seconds=inter_seconds,
                             step_total_seconds=step_total,
                             communication_fraction=comm / step_total,
                             projected_days=days,
                             meets_deadline=days <= DEADLINE_DAYS,
                             first_short=('容量' if cards_for_state > cards_for_compute else
                                          ('机间通信' if inter_seconds > intra_seconds and
                                           inter_seconds > step_compute else
                                           ('机内通信' if intra_seconds > step_compute else '算力')))))

    result = dict(schema_version=1, experiment='10-3', title='4090 集群的可行范围',
                  token_target=TOKEN_TARGET, deadline_days=DEADLINE_DAYS,
                  efficiency=EFFICIENCY, systems=[s[0] for s in SYSTEMS], rows=rows,
                  source_note='工作量与状态由 calculations/calc.py 现场生成；'
                              '设备规格取自官方硬件表；PCIe／NIC 速率与 30% 容量余量是声明输入。',
                  next_measurement='剩余候选最需要的一项实测：4090 主机上 PCIe Gen4 x16 '
                                   '在 8 卡同时 all-reduce 时的**实际有效带宽**。'
                                   '本表按 25 GB/s 单向峰值计，但 8 卡共享上行与 P2P 受限会让实际值低得多；'
                                   '它直接决定机内通信占比，进而决定 4090 方案能否达到期限。',
                  python_version=sys.version)
    json.dump(result, open(os.path.join(RESULTS, 'feasible.json'), 'w'), indent=2, ensure_ascii=False)

    lines = ['# 实验 10-3 结果：4090 集群的可行范围', '',
             '目标 %.0fB token／%d 天，效率 %.0f%%（声明输入）。' % (
                 TOKEN_TARGET / 1e9, DEADLINE_DAYS, EFFICIENCY * 100), '',
             '| 模型 | 系统 | 算力所需卡 | 容量所需卡 | 取用卡数 | 主机数 | 步计算 | 机内通信 | 机间通信 | 通信占比 | 预计天数 | 达期限 | 先不够的是 |',
             '| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | :---: | --- |']
    for r in rows:
        if 'error' in r:
            lines.append('| %s | %s | %s | — | — | — | — | — | — | — | — | — | — |' % (
                r['model'], r.get('system', '—'), r['error']))
            continue
        lines.append('| %s | %s | %d | %d | %d | %d | %.3f s | %.3f s | %.3f s | %.1f%% | %.1f | %s | **%s** |' % (
            r['model'], r['system'], r['cards_for_compute'], r['cards_for_state'],
            r['cards'], r['hosts'], r['step_compute_seconds'],
            r['intra_seconds'], r['inter_seconds'],
            r['communication_fraction'] * 100, r['projected_days'],
            '是' if r['meets_deadline'] else '否', r['first_short']))
    lines += ['', '## 剩余候选最需要的一项实测', '', result['next_measurement'], '']
    open(os.path.join(RESULTS, 'feasible.md'), 'w').write('\n'.join(lines))
    print('\n'.join(lines))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
