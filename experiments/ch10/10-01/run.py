#!/usr/bin/env python3
"""实验 10-1：训练状态的容量预算。

一张卡到底少了多少空间？给 Qwen3-8B 同一序列长度和全参数训练任务逐项算容量，
比较 24 GB 4090 与 80 GB A100／H100；再换 Qwen3-235B 与 V4-Flash 检查
总状态与活跃计算。ZeRO 分片阶段（stage 0/1/2/3）逐级列出。

本实验不重算：由 `calculations/calc.py training-state` 现场生成。
本目录另有三份实跑：fsdp-cpu/、deepspeed-offload/、transfer-buffering/。
"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
CALC = os.path.join(ROOT, 'calculations', 'calc.py')
RESULTS = os.path.join(HERE, 'results')
GB = 10 ** 9
GiB = 2 ** 30

CAPACITIES = [('4090 24 GB', 24 * GB), ('A100/H100 80 GB', 80 * GB),
              ('B200 180 GB', 180 * GB)]
MODELS = ['qwen3-8b', 'qwen3-32b', 'qwen3-235b-a22b']
PARTICIPANTS = [8, 64]


def main() -> int:
    os.makedirs(RESULTS, exist_ok=True)
    rows = []
    for model in MODELS:
        for participants in PARTICIPANTS:
            for cap_name, cap in CAPACITIES:
                cfg = dict(model=model, participants=participants, gradient_bytes=2,
                           partition='flat', extra_live_bytes=0, capacity_bytes=cap)
                tag = '%s-p%d-c%d' % (model, participants, cap // GB)
                ipath = os.path.join(RESULTS, 'input-%s.json' % tag)
                opath = os.path.join(RESULTS, 'state-%s.json' % tag)
                json.dump(cfg, open(ipath, 'w'), indent=1)
                proc = subprocess.run([sys.executable, CALC, 'training-state', '--inputs', ipath,
                                       '--format', 'json', '--output', opath],
                                      capture_output=True, text=True)
                if proc.returncode != 0:
                    rows.append(dict(model=model, participants=participants, capacity=cap_name,
                                     error=(proc.stderr.strip().splitlines() or [''])[-1]))
                    continue
                doc = json.load(open(opath))
                stages = []
                for st in doc['training_state_stages']:
                    per_rank = sum(c['per_rank_bytes'] for c in st['components'])
                    stages.append(dict(stage=st['stage'], per_rank_bytes=per_rank,
                                       fits=per_rank <= cap))
                rows.append(dict(model=model, participants=participants, capacity=cap_name,
                                 capacity_bytes=cap, stages=stages,
                                 summary=doc['summary']))

    result = dict(schema_version=1, experiment='10-1', title='训练状态的容量预算',
                  capacities=[c[0] for c in CAPACITIES], models=MODELS,
                  participants=PARTICIPANTS, rows=rows,
                  source_note='由 calculations/calc.py training-state 现场生成。',
                  python_version=sys.version)
    json.dump(result, open(os.path.join(RESULTS, 'budget.json'), 'w'), indent=2, ensure_ascii=False)

    lines = ['# 实验 10-1 结果：训练状态的容量预算', '',
             'BF16 权重与梯度、FP32 主权重与两个 Adam 动量；逐 rank 字节按 ZeRO 阶段分列。', '',
             '| 模型 | rank 数 | 设备 | stage 0 | stage 1 | stage 2 | stage 3 | 最低可行阶段 |',
             '| --- | ---: | --- | ---: | ---: | ---: | ---: | --- |']
    for r in rows:
        if 'error' in r:
            lines.append('| %s | %d | %s | 调用失败：%s | — | — | — | — |' % (
                r['model'], r['participants'], r['capacity'], r['error']))
            continue
        cells = []
        first_ok = None
        for st in r['stages']:
            mark = '' if st['fits'] else '✗'
            cells.append('%.1f GiB%s' % (st['per_rank_bytes'] / GiB, mark))
            if st['fits'] and first_ok is None:
                first_ok = st['stage']
        while len(cells) < 4:
            cells.append('—')
        lines.append('| %s | %d | %s | %s | **%s** |' % (
            r['model'], r['participants'], r['capacity'], ' | '.join(cells[:4]),
            ('stage %d' % first_ok) if first_ok is not None else '全部放不下'))
    lines += ['', '（✗ 表示该阶段逐 rank 状态超出设备容量。）', '']
    open(os.path.join(RESULTS, 'budget.md'), 'w').write('\n'.join(lines))
    print('\n'.join(lines))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
