#!/usr/bin/env python3
"""实验 4-3：存储容量与解码带宽。

相同容量为什么有不同的解码速度？用 Qwen3-8B／235B 的真实权重和 KV 工作集，
在 A100、H100／H200、B200 与 M2 Max 上分别计算：
  1. 驻留（能放下多少并发）；
  2. 一步 decode 的读取时间；
  3. 只替换容量 → 只替换带宽 → 代入真实产品，三步分开看收益来源。

权重与 KV 由 `calculations/calc.py capacity-scan` 现场生成；设备容量与带宽
直接取自统一计算项目的官方硬件表 `calculations/configs/hardware.json`。
本实验不重算模型侧公式。只依赖 Python 3 标准库。
"""
import json
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

DEVICE_IDS = ['a100-80gb-sxm', 'h100-sxm', 'h200-sxm', 'b200-sxm', 'm2-max-38gpu-96gb']
MODELS = ['qwen3-8b', 'qwen3-235b-a22b']
LENGTHS = [8192, 32768]
BITS = 16


def load_devices():
    raw = json.load(open(HARDWARE))
    devs = raw['devices'] if isinstance(raw, dict) and 'devices' in raw else raw
    devs = devs if isinstance(devs, list) else list(devs.values())
    out = []
    for d in devs:
        if d.get('id') in DEVICE_IDS:
            mem = d['memory']
            out.append(dict(id=d['id'], name=d['name'],
                            capacity_bytes=int(mem['nominal_capacity'] * GB),
                            bandwidth=mem['bandwidth_bytes_per_second']))
    out.sort(key=lambda r: DEVICE_IDS.index(r['id']))
    return out


def run(args, out):
    path = os.path.join(RESULTS, out)
    proc = subprocess.run([sys.executable, CALC] + args + ['--format', 'json', '--output', path],
                          capture_output=True, text=True)
    if proc.returncode != 0:
        sys.exit('调用失败：%s\n%s' % (' '.join(args), proc.stderr[-800:]))
    return json.load(open(path))


def main() -> int:
    os.makedirs(RESULTS, exist_ok=True)
    devices = load_devices()
    caps = [str(d['capacity_bytes']) for d in devices]

    rows = []
    for model in MODELS:
        for length in LENGTHS:
            doc = run(['capacity-scan', '--model', model, '--length', str(length),
                       '--capacities'] + caps, 'capacity-%s-n%d.json' % (model, length))
            byte_cap = {c['capacity_bytes']: c for c in doc['capacity_comparisons']
                        if c['matrix_bits'] == BITS}
            for dev in devices:
                c = byte_cap.get(dev['capacity_bytes'])
                if c is None:
                    continue
                per_request_kv = c['kv_bytes_per_request']
                n = c['maximum_requests']
                # 一步 decode 的读取：整份权重 ＋ 每个在跑请求的历史
                read_bytes = c['weight_bytes'] + n * per_request_kv
                rows.append(dict(
                    model=model, length=length, device=dev['id'], device_name=dev['name'],
                    capacity_bytes=dev['capacity_bytes'], bandwidth=dev['bandwidth'],
                    weight_bytes=c['weight_bytes'], kv_bytes_per_request=per_request_kv,
                    weights_fit=c['weights_and_workspace_fit'], maximum_requests=n,
                    decode_read_bytes=read_bytes,
                    decode_read_seconds=read_bytes / dev['bandwidth'],
                    tokens_per_second=(n * dev['bandwidth'] / read_bytes) if read_bytes else None))

    # 只替换容量 / 只替换带宽：以 A100 为基准，逐项换成 H100 的对应值
    base = next(d for d in devices if d['id'] == 'a100-80gb-sxm')
    target = next(d for d in devices if d['id'] == 'h200-sxm')
    big = next(d for d in devices if d['id'] == 'b200-sxm')
    swap = []
    ref = next(r for r in rows if r['model'] == 'qwen3-8b' and r['length'] == 8192
               and r['device'] == 'a100-80gb-sxm')
    for label, cap, bw in [('A100 基线', base['capacity_bytes'], base['bandwidth']),
                           ('只替换容量→H200 的 141 GB', target['capacity_bytes'], base['bandwidth']),
                           ('只替换带宽→H200 的 4800 GB/s', base['capacity_bytes'], target['bandwidth']),
                           ('真实 H200', target['capacity_bytes'], target['bandwidth']),
                           ('只替换容量→B200 的 180 GB', big['capacity_bytes'], base['bandwidth']),
                           ('只替换带宽→B200 的 8000 GB/s', base['capacity_bytes'], big['bandwidth']),
                           ('真实 B200', big['capacity_bytes'], big['bandwidth'])]:
        headroom = cap - ref['weight_bytes'] - 2 * GiB
        n = max(0, int(headroom // ref['kv_bytes_per_request']))
        read = ref['weight_bytes'] + n * ref['kv_bytes_per_request']
        swap.append(dict(step=label, capacity_bytes=cap, bandwidth=bw,
                         maximum_requests=n, decode_read_bytes=read,
                         decode_read_seconds=read / bw,
                         tokens_per_second=n * bw / read if read else None))

    result = dict(schema_version=1, experiment='4-3', title='存储容量与解码带宽',
                  bits=BITS, devices=devices, rows=rows, swap=swap,
                  source_note='模型侧由 calculations/calc.py capacity-scan 现场生成；'
                              '设备容量与带宽取自 calculations/configs/hardware.json 的官方记录。',
                  python_version=sys.version)
    json.dump(result, open(os.path.join(RESULTS, 'capacity-bandwidth.json'), 'w'),
              indent=2, ensure_ascii=False)

    lines = ['# 实验 4-3 结果：存储容量与解码带宽', '',
             'BF16 权重；工作区按 capacity-scan 的声明值；KV 按 BF16。', '',
             '## 驻留与一步 decode 的读取时间', '',
             '| 模型 | 历史 | 设备 | 容量 | 带宽 | 权重 | 最大并发 | 一步读取 | 读取时间 | 满并发吞吐 |',
             '| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |']
    for r in rows:
        lines.append('| %s | %d | %s | %.0f GB | %.0f GB/s | %.1f GB | %s | %.1f GB | %.2f ms | %s |' % (
            r['model'], r['length'], r['device'], r['capacity_bytes'] / GB,
            r['bandwidth'] / GB, r['weight_bytes'] / GB,
            r['maximum_requests'] if r['weights_fit'] else '权重放不下',
            r['decode_read_bytes'] / GB, r['decode_read_seconds'] * 1e3,
            '%.0f tok/s' % r['tokens_per_second'] if r['tokens_per_second'] else '—'))
    lines += ['', '## 逐项替换：只换容量／只换带宽／真实产品（Qwen3-8B，历史 8192）', '',
              '| 步骤 | 容量 | 带宽 | 最大并发 | 一步读取 | 读取时间 | 满并发吞吐 |',
              '| --- | ---: | ---: | ---: | ---: | ---: | ---: |']
    for s in swap:
        lines.append('| %s | %.0f GB | %.0f GB/s | %d | %.1f GB | %.2f ms | %.0f tok/s |' % (
            s['step'], s['capacity_bytes'] / GB, s['bandwidth'] / GB,
            s['maximum_requests'], s['decode_read_bytes'] / GB,
            s['decode_read_seconds'] * 1e3, s['tokens_per_second']))
    lines.append('')
    open(os.path.join(RESULTS, 'capacity-bandwidth.md'), 'w').write('\n'.join(lines))
    print('\n'.join(lines))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
