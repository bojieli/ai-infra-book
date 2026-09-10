#!/usr/bin/env python3
"""与 calculations/ 的 decode-budget 场景交叉核对实验 1-3。"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
OWN = os.path.join(HERE, 'results', 'sensitivity.json')
CALC = os.path.join(ROOT, 'calculations', 'results')

PAIRS = [('基线：8 bit 权重，batch=1', 'decode-budget-base.json'),
         ('翻倍算力', 'decode-budget-double-compute.json'),
         ('翻倍带宽', 'decode-budget-double-bandwidth.json'),
         ('位宽 8→4 bit', 'decode-budget-four-bit.json'),
         ('batch=64', 'decode-budget-b64.json')]


def close(a, b, tol=1e-9):
    return abs(a - b) <= tol * max(1.0, abs(a), abs(b))


def main() -> int:
    if not os.path.exists(OWN):
        print('先运行 python3 run.py', file=sys.stderr)
        return 1
    own = {row['label']: row for row in json.load(open(OWN))['scans']}
    failed = 0
    checked = 0
    for label, name in PAIRS:
        path = os.path.join(CALC, name)
        if not os.path.exists(path):
            print('跳过（未找到 %s）  %s' % (name, label))
            continue
        other = json.load(open(path))['summary']
        mine = own[label]
        for field, key in (('compute_seconds', 'compute_service_seconds'),
                           ('memory_seconds', 'memory_service_seconds'),
                           ('weight_bytes', 'weight_payload_bytes')):
            ok = close(mine[field], other[key])
            checked += 1
            failed += 0 if ok else 1
            print(('通过  ' if ok else '失败  ') + '%s · %s：%.12g vs %.12g' % (label, field, mine[field], other[key]))
    print('核对 %d 项，失败 %d 项' % (checked, failed))
    return 1 if failed else 0


if __name__ == '__main__':
    raise SystemExit(main())
