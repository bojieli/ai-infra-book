#!/usr/bin/env python3
"""实验 6-7：功率预算下的超节点规模。

同一功率预算下，怎样组成一个超节点？分别计入设备、网络与散热配套，
求候选规模并比较模型服务能力。

设备功率与规格取自统一计算项目的官方硬件表；网络与散热按显式声明的
系数换算，不使用任何厂商未公布的整机数字。模型服务能力用第 2 章已算好的
权重与 KV 载荷判断（容量是否放得下、带宽给出的 decode 下界）。

只依赖 Python 3 标准库。
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

POWER_BUDGETS = [120_000, 250_000, 500_000, 1_000_000]   # W，机柜到机房级
NETWORK_W_PER_DEVICE = 150      # 每设备分摊的交换与光模块功率（声明输入）
COOLING_OVERHEAD = 0.30         # 散热配套按 IT 功率的比例（声明输入）
HOST_W_PER_8_DEVICES = 800      # 每 8 个设备一台主机（声明输入）

CANDIDATES = ['a100-80gb-sxm', 'h100-sxm', 'b200-sxm', 'rtx-pro6000-blackwell-ws']
MODELS = [('qwen3-8b', 8192, 64), ('qwen3-235b-a22b', 8192, 64)]


def load_devices():
    raw = json.load(open(HARDWARE))
    devs = raw['devices'] if isinstance(raw, dict) and 'devices' in raw else raw
    devs = devs if isinstance(devs, list) else list(devs.values())
    out = []
    for cid in CANDIDATES:
        d = next((x for x in devs if x.get('id') == cid), None)
        if d is None or not d.get('power_watts'):
            continue
        out.append(dict(id=cid, name=d['name'], power=d['power_watts'],
                        capacity_bytes=int(d['memory']['nominal_capacity'] * GB),
                        bandwidth=d['memory']['bandwidth_bytes_per_second']))
    return out


def model_demand(model, length, batch):
    path = os.path.join(RESULTS, 'capacity-%s.json' % model)
    proc = subprocess.run([sys.executable, CALC, 'capacity-scan', '--model', model,
                           '--length', str(length), '--capacities', '80000000000',
                           '--format', 'json', '--output', path],
                          capture_output=True, text=True)
    if proc.returncode != 0:
        sys.exit('调用失败：%s\n%s' % (model, proc.stderr[-600:]))
    doc = json.load(open(path))
    c = next(x for x in doc['capacity_comparisons'] if x['matrix_bits'] == 16)
    return dict(model=model, length=length, batch=batch,
                weight_bytes=c['weight_bytes'],
                kv_bytes_per_request=c['kv_bytes_per_request'],
                resident_bytes=c['weight_bytes'] + batch * c['kv_bytes_per_request'],
                step_read_bytes=c['weight_bytes'] + batch * c['kv_bytes_per_request'])


def main() -> int:
    os.makedirs(RESULTS, exist_ok=True)
    devices = load_devices()
    demands = [model_demand(*m) for m in MODELS]

    rows = []
    for budget in POWER_BUDGETS:
        for d in devices:
            # 每设备的完整功率份额：设备 ＋ 网络 ＋ 主机分摊，再按散热系数放大
            it_per_device = d['power'] + NETWORK_W_PER_DEVICE + HOST_W_PER_8_DEVICES / 8
            total_per_device = it_per_device * (1 + COOLING_OVERHEAD)
            n = int(budget // total_per_device)
            if n <= 0:
                continue
            for dem in demands:
                total_capacity = n * d['capacity_bytes']
                # 一份模型副本要多少张卡（只看权重＋该 batch 的 KV）
                cards_per_replica = math.ceil(dem['resident_bytes'] / d['capacity_bytes'])
                replicas = n // cards_per_replica if cards_per_replica else 0
                # 满副本下的 decode 步下界：每卡读自己那一份
                per_card_read = dem['step_read_bytes'] / cards_per_replica if cards_per_replica else 0
                step_seconds = per_card_read / d['bandwidth'] if per_card_read else None
                rows.append(dict(
                    budget_w=budget, device=d['id'], device_name=d['name'],
                    device_power_w=d['power'], per_device_total_w=total_per_device,
                    devices=n, total_capacity_bytes=total_capacity,
                    model=dem['model'], batch=dem['batch'],
                    cards_per_replica=cards_per_replica, replicas=replicas,
                    decode_step_seconds=step_seconds,
                    tokens_per_second=(replicas * dem['batch'] / step_seconds)
                    if step_seconds and replicas else 0.0))

    result = dict(schema_version=1, experiment='6-7', title='功率预算下的超节点规模',
                  assumptions=dict(network_w_per_device=NETWORK_W_PER_DEVICE,
                                   cooling_overhead=COOLING_OVERHEAD,
                                   host_w_per_8_devices=HOST_W_PER_8_DEVICES,
                                   note='网络、主机与散热系数是声明输入，不是厂商公布的整机数字。'),
                  devices=devices, demands=demands, rows=rows,
                  source_note='设备规格取自 calculations/configs/hardware.json；'
                              '模型载荷由 calc.py capacity-scan 现场生成。',
                  python_version=sys.version)
    json.dump(result, open(os.path.join(RESULTS, 'power.json'), 'w'), indent=2, ensure_ascii=False)

    lines = ['# 实验 6-7 结果：功率预算下的超节点规模', '',
             '每设备完整功率份额＝设备 ＋ 网络 %d W ＋ 主机分摊 %d W，再乘散热系数 %.2f（均为声明输入）。' % (
                 NETWORK_W_PER_DEVICE, HOST_W_PER_8_DEVICES // 8, 1 + COOLING_OVERHEAD), '',
             '## 候选规模', '',
             '| 功率预算 | 设备 | 单设备 TDP | 完整份额 | 可容纳设备数 | 总容量 |',
             '| ---: | --- | ---: | ---: | ---: | ---: |']
    seen = set()
    for r in rows:
        key = (r['budget_w'], r['device'])
        if key in seen:
            continue
        seen.add(key)
        lines.append('| %d kW | %s | %d W | %.0f W | %d | %.1f TB |' % (
            r['budget_w'] // 1000, r['device_name'], r['device_power_w'],
            r['per_device_total_w'], r['devices'], r['total_capacity_bytes'] / 1e12))
    lines += ['', '## 同一预算下的模型服务能力', '',
              '| 功率预算 | 设备 | 模型 | 每副本卡数 | 副本数 | 每步下界 | 满配吞吐 |',
              '| ---: | --- | --- | ---: | ---: | ---: | ---: |']
    for r in rows:
        lines.append('| %d kW | %s | %s | %d | %d | %s | %s |' % (
            r['budget_w'] // 1000, r['device'], r['model'],
            r['cards_per_replica'], r['replicas'],
            '%.2f ms' % (r['decode_step_seconds'] * 1e3) if r['decode_step_seconds'] else '—',
            '%.0f tok/s' % r['tokens_per_second'] if r['tokens_per_second'] else '—'))
    lines.append('')
    open(os.path.join(RESULTS, 'power.md'), 'w').write('\n'.join(lines))
    print('\n'.join(lines))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
