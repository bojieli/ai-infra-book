#!/usr/bin/env python3
"""实验 3-10：GPU 小时与系统预算。

核对公开字段：对卡数已知的案例估算日历时间，对其他案例给条件区间；
再把长期服务费用加入比较，说明哪些数据缺失会改变选择。

本实验不重算：由 `calculations/calc.py training-history|dense-training-scale|
training-deadline` 现场生成。只依赖标准库。
"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
CALC = os.path.join(ROOT, 'calculations', 'calc.py')
RESULTS = os.path.join(HERE, 'results')

# 长期服务对照的显式输入（教学值，不是任何厂商报价）
FLEET_SIZES = [1024, 2048, 4096, 8192, 16384]


def run(args, out):
    path = os.path.join(RESULTS, out)
    proc = subprocess.run([sys.executable, CALC] + args + ['--format', 'json', '--output', path],
                          capture_output=True, text=True)
    if proc.returncode != 0:
        sys.exit('调用失败：%s\n%s' % (' '.join(args), proc.stderr[-900:]))
    return json.load(open(path))


def main() -> int:
    os.makedirs(RESULTS, exist_ok=True)
    hist = run(['training-history'], 'training-history.json')
    scale = run(['dense-training-scale'], 'dense-training-scale.json')
    deadline = run(['training-deadline'], 'training-deadline.json')

    rows = []
    for r in hist['training_history_rows']:
        inp = r['input']
        d = r['duration']
        gpu_hours = inp.get('gpu_hours')
        count = inp.get('gpu_count')
        interpretation = d['interpretation']
        conditional_days = d.get('conditional_constant_count_days')
        # 卡数未知时给条件区间：按几档常见规模换算
        interval = None
        if gpu_hours and not count:
            interval = [dict(assumed_gpu_count=n, days=gpu_hours / n / 24) for n in FLEET_SIZES]
        rows.append(dict(id=inp['id'], gpu_family=inp.get('gpu_family'),
                         gpu_hours=gpu_hours, gpu_count=count,
                         gpu_count_role=inp.get('gpu_count_role'),
                         interpretation=interpretation,
                         conditional_days=conditional_days,
                         conditional_interval=interval,
                         scope_notes=inp.get('scope_notes')))

    result = dict(schema_version=1, experiment='3-10', title='GPU 小时与系统预算',
                  source_note='由 calculations/calc.py 现场生成；假设卡数是本实验声明的教学档位。',
                  rows=rows,
                  dense_scale_summary=scale.get('summary'),
                  deadline_summary=deadline.get('summary'),
                  missing_data_that_changes_choices=[
                      'GPU 小时是否与卡数覆盖同一范围：若含预热、失败重跑或评测，日历时间会被高估。',
                      '卡数是否全程恒定：真实作业常有扩缩容与故障替换，恒定假设只给条件值。',
                      'MFU：同样的 GPU 小时在不同 MFU 下对应完全不同的有效计算。',
                      '是否含数据准备、tokenize 与检查点写入的时间。',
                      '推理侧的调用量与生命周期：训练一次的成本能被多少次调用摊薄，决定训练与服务哪一侧主导总预算。',
                      '设备单价、电力与折旧年限：GPU 小时不是货币，换算需要另一组未公开输入。',
                  ],
                  python_version=sys.version)
    json.dump(result, open(os.path.join(RESULTS, 'budget.json'), 'w'), indent=2, ensure_ascii=False)

    lines = ['# 实验 3-10 结果：GPU 小时与系统预算', '',
             '## 公开字段核对与日历时间', '',
             '| 案例 | 卡型 | GPU 小时 | 卡数 | 判定 | 条件日历时间 |',
             '| --- | --- | ---: | ---: | --- | --- |']
    for r in rows:
        if r['conditional_days']:
            days = '%.1f 天（恒定卡数条件下）' % r['conditional_days']
        elif r['conditional_interval']:
            lo = r['conditional_interval'][-1]['days']
            hi = r['conditional_interval'][0]['days']
            days = '%.1f–%.1f 天（假设 %d–%d 卡）' % (lo, hi, FLEET_SIZES[0], FLEET_SIZES[-1])
        else:
            days = '未公开 GPU 小时，无法给区间'
        lines.append('| %s | %s | %s | %s | %s | %s |' % (
            r['id'], r['gpu_family'] or '—',
            '{:,}'.format(r['gpu_hours']) if r['gpu_hours'] else '未公开',
            r['gpu_count'] if r['gpu_count'] else '未公开',
            r['interpretation'], days))
    lines += ['', '## 卡数未知时的条件区间（逐档）', '',
              '| 案例 | ' + ' | '.join('%d 卡' % n for n in FLEET_SIZES) + ' |',
              '| --- | ' + ' | '.join(['---:'] * len(FLEET_SIZES)) + ' |']
    for r in rows:
        if not r['conditional_interval']:
            continue
        lines.append('| %s | %s |' % (r['id'], ' | '.join(
            '%.1f 天' % it['days'] for it in r['conditional_interval'])))
    lines += ['', '## 哪些缺失数据会改变选择', ''] + [
        '- ' + x for x in result['missing_data_that_changes_choices']] + ['']
    open(os.path.join(RESULTS, 'budget.md'), 'w').write('\n'.join(lines))
    print('\n'.join(lines))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
