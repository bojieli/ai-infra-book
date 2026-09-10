#!/usr/bin/env python3
"""实验 10-2：从训练任务反推资源。

按 Qwen3-8B 的具体矩阵求每 token 训练工作，再由 100B token／30 天推设备需求。
先声明算法 FLOPs 的统计范围，再用 30%／40%／50% 效率作敏感性输入，
与容量下界交叉检查；换 235B MoE 或改变更新范围后重新计算。
区分理想估算、实际训练步与全部日历时间。

本实验不重算：由 `calculations/calc.py training-matrix|training-state|dense-training-scale`
现场生成。只依赖 Python 3 标准库。
"""
import json
import math
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
CALC = os.path.join(ROOT, 'calculations', 'calc.py')
RESULTS = os.path.join(HERE, 'results')
GiB = 2 ** 30

TOKEN_TARGET = 100_000_000_000
CALENDAR_DAYS = 30
EFFICIENCIES = [0.30, 0.40, 0.50]
DEVICES = [('A100 80GB SXM', 312e12, 80e9), ('H100 SXM', 989.4e12, 80e9),
           ('B200 SXM', 2250e12, 180e9)]
MODELS = [('qwen3-8b', 4096, None), ('qwen3-8b', 4096, 1024),
          ('qwen3-235b-a22b', 4096, None)]


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
    for model, tokens, supervised in MODELS:
        args = ['training-matrix', '--model', model, '--tokens', str(tokens)]
        tag = '%s-t%d%s' % (model, tokens, '-sft' if supervised else '')
        if supervised:
            args += ['--supervised-tokens', str(supervised), '--head-strategy', 'compact']
        doc, err = run(args, 'matrix-%s.json' % tag)
        if doc is None:
            rows.append(dict(model=model, error=err))
            continue
        s = doc['summary']
        per_token = s['training_matrix_flops'] / s['input_tokens']
        total = per_token * TOKEN_TARGET
        state_bytes = s['unsharded_parameter_state_bytes']
        for name, peak, capacity in DEVICES:
            for eff in EFFICIENCIES:
                device_seconds = total / (peak * eff)
                devices = device_seconds / (CALENDAR_DAYS * 86400)
                rows.append(dict(
                    model=model, supervised=supervised, per_token_flops=per_token,
                    total_flops=total, device=name, peak=peak, capacity=capacity,
                    efficiency=eff, device_seconds=device_seconds,
                    devices_needed=devices, devices_ceil=math.ceil(devices),
                    unsharded_state_bytes=state_bytes,
                    min_devices_for_state=math.ceil(state_bytes / capacity),
                    capacity_binding=math.ceil(state_bytes / capacity) > math.ceil(devices)))

    result = dict(schema_version=1, experiment='10-2', title='从训练任务反推资源',
                  token_target=TOKEN_TARGET, calendar_days=CALENDAR_DAYS,
                  flops_scope='算法 FLOPs 的统计范围＝训练矩阵子账（前向＋反向的矩阵乘，'
                              '含注意力，按所声明的输出头范围）；不含非矩阵、优化器、'
                              '重计算、通信与格式转换。效率因此按同一子账定义，'
                              '不能直接套用完整训练步口径的 MFU。',
                  rows=rows,
                  source_note='由 calculations/calc.py training-matrix 现场生成。',
                  python_version=sys.version)
    json.dump(result, open(os.path.join(RESULTS, 'demand.json'), 'w'), indent=2, ensure_ascii=False)

    lines = ['# 实验 10-2 结果：从训练任务反推资源', '',
             '目标：%.0fB token／%d 天。' % (TOKEN_TARGET / 1e9, CALENDAR_DAYS), '',
             '**算法 FLOPs 的统计范围**：' + result['flops_scope'], '',
             '| 模型 | 更新范围 | 每 token 训练矩阵 | 总量 | 设备 | 效率 | 需要设备数 | 容量下界设备数 | 谁支配 |',
             '| --- | --- | ---: | ---: | --- | ---: | ---: | ---: | --- |']
    for r in rows:
        if 'error' in r:
            lines.append('| %s | — | 调用失败：%s | — | — | — | — | — | — |' % (r['model'], r['error']))
            continue
        lines.append('| %s | %s | %.3g FLOPs | %.3g FLOPs | %s | %.0f%% | **%d** | %d | %s |' % (
            r['model'], 'SFT（1/4 计损失）' if r['supervised'] else '全 token',
            r['per_token_flops'], r['total_flops'], r['device'], r['efficiency'] * 100,
            r['devices_ceil'], r['min_devices_for_state'],
            '容量' if r['capacity_binding'] else '算力'))
    lines.append('')
    open(os.path.join(RESULTS, 'demand.md'), 'w').write('\n'.join(lines))
    print('\n'.join(lines))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
