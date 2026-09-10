#!/usr/bin/env python3
"""与 calculations/ 的独立实现交叉核对实验 1-2 的共同输入。

找不到那份结果时跳过并返回 0：本实验本身不依赖它。
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
OWN = os.path.join(HERE, 'results', 'resource-card.json')
OTHER = os.path.join(ROOT, 'calculations', 'results', 'decode-budget-base.json')


def main() -> int:
    if not os.path.exists(OWN):
        print('先运行 python3 run.py', file=sys.stderr)
        return 1
    own = json.load(open(OWN))
    eight_bit = next(r for r in own['capacity'] if r['weight_bits'] == 8)
    checks = [('8 bit 纯权重 = 70 GB', eight_bit['weight_bytes'] == 70_000_000_000),
              ('16 bit 纯权重 = 140 GB',
               next(r for r in own['capacity'] if r['weight_bits'] == 16)['weight_bytes'] == 140_000_000_000),
              ('400 Gb/s = 50 GB/s', own['bandwidth']['raw_bytes_per_second'] == 50_000_000_000)]
    if os.path.exists(OTHER):
        other = json.load(open(OTHER))['summary']
        checks.append(('与 calculations 的权重载荷一致',
                       other['weight_payload_bytes'] == eight_bit['weight_bytes']))
        checks.append(('与 calculations 的标称容量一致',
                       other['nominal_capacity_bytes'] == eight_bit['card_capacity_bytes']))
    else:
        print('跳过：未找到 calculations/results/decode-budget-base.json')
    failed = 0
    for name, ok in checks:
        print(('通过  ' if ok else '失败  ') + name)
        failed += 0 if ok else 1
    return 1 if failed else 0


if __name__ == '__main__':
    raise SystemExit(main())
