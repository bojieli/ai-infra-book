#!/usr/bin/env python3
"""实验 3-7：RL 循环的资源供给。

按 V4 的阶段组织构造明确标注的教学输入，计算 rollout（prefill／decode）、
验证、教师前向、更新和权重交接各自的工作与数据量；再改变样本接受比例，
比较在**同一有效样本目标**下各阶段增加的需求。

输出的需求表交给第 10 章讨论资源池配比，本实验不给硬件推荐。
本实验不重算：由 `calculations/calc.py rl-supply|rl-cycle` 现场生成。
"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
CALC = os.path.join(ROOT, 'calculations', 'calc.py')
RESULTS = os.path.join(HERE, 'results')

TARGET_ACCEPTED = 16     # 固定的有效样本目标
PROMPTS = 8
# 接受比例：每个 prompt 生成 samples_per_prompt 个候选，其中 accepted 比例被采纳
ACCEPT_CASES = [
    ('接受 1/2（基线）', 4, 16),
    ('接受 1/4', 8, 16),
    ('接受 1/8', 16, 16),
    ('接受 全部', 2, 16),
]

BASE_SUPPLY = {
    'matrix': {
        'rollout_prefill': {'pool': 'actor', 'flops_per_second': 2.0e14},
        'rollout_decode': {'pool': 'actor', 'flops_per_second': 2.0e13},
        'reference_scoring': {'pool': 'reference', 'flops_per_second': 2.0e14},
        'teacher_scoring': {'pool': 'teacher', 'flops_per_second': 2.0e14},
        'policy_update': {'pool': 'learner', 'flops_per_second': 2.0e14},
    },
    'verifier': {'pool': 'verifier', 'seconds_per_candidate': 0.05, 'workers': 8},
    'synchronization': {'pool': 'weight_link', 'bytes_per_second': 5.0e10},
}


def run(args, out):
    path = os.path.join(RESULTS, out)
    proc = subprocess.run([sys.executable, CALC] + args + ['--format', 'json', '--output', path],
                          capture_output=True, text=True)
    if proc.returncode != 0:
        sys.exit('调用失败：%s\n%s' % (' '.join(args), proc.stderr[-900:]))
    return json.load(open(path))


def main() -> int:
    os.makedirs(RESULTS, exist_ok=True)
    rows = []
    for label, samples_per_prompt, accepted in ACCEPT_CASES:
        inputs = dict(cycle=dict(prompts=PROMPTS, samples_per_prompt=samples_per_prompt,
                                 accepted_samples=accepted),
                      supply=BASE_SUPPLY, pool_speedups={})
        ipath = os.path.join(RESULTS, 'input-spp%d.json' % samples_per_prompt)
        json.dump(inputs, open(ipath, 'w'), indent=1)
        doc = run(['rl-supply', '--inputs', ipath], 'supply-spp%d.json' % samples_per_prompt)
        s = doc['summary']
        rows.append(dict(label=label, samples_per_prompt=samples_per_prompt,
                         candidates=PROMPTS * samples_per_prompt,
                         accepted=accepted,
                         stages={st['stage']: st['service_seconds'] for st in doc['service_stages']},
                         serial_batch_seconds=s['serial_component_batch_seconds'],
                         ideal_pipeline_interval_seconds=s['ideal_pipeline_interval_lower_seconds'],
                         limiting_pools=s['limiting_pools'],
                         serial_accepted_per_second=s['conditional_serial_accepted_samples_per_second'],
                         pipeline_accepted_per_second=s['ideal_pipeline_accepted_samples_per_second_upper']))

    # 资源池扩容对照：actor 池加速 2 倍
    inputs = dict(cycle=dict(prompts=PROMPTS, samples_per_prompt=4, accepted_samples=16),
                  supply=BASE_SUPPLY, pool_speedups={'actor': 2})
    ipath = os.path.join(RESULTS, 'input-actor2.json')
    json.dump(inputs, open(ipath, 'w'), indent=1)
    actor2 = run(['rl-supply', '--inputs', ipath], 'supply-actor2.json')

    cycle = run(['rl-cycle'], 'rl-cycle.json')

    result = dict(schema_version=1, experiment='3-7', title='RL 循环的资源供给',
                  target_accepted_samples=TARGET_ACCEPTED, prompts=PROMPTS,
                  supply_note='供给速率是明确标注的教学输入，不是任何设备的实测值。',
                  source_note='由 calculations/calc.py rl-supply|rl-cycle 现场生成。',
                  rows=rows,
                  actor_speedup_2=actor2['summary'],
                  cycle_summary=cycle.get('summary'),
                  python_version=sys.version)
    json.dump(result, open(os.path.join(RESULTS, 'rl.json'), 'w'), indent=2, ensure_ascii=False)

    stage_names = ['rollout_prefill', 'rollout_decode', 'reference_scoring',
                   'teacher_scoring', 'policy_update', 'verification', 'weight_synchronization']
    lines = ['# 实验 3-7 结果：RL 循环的资源供给', '',
             '固定有效样本目标 %d，prompts %d。供给速率是教学输入。' % (TARGET_ACCEPTED, PROMPTS), '',
             '## 各阶段服务时间（秒）', '',
             '| 接受比例 | 候选数 | ' + ' | '.join(stage_names) + ' |',
             '| --- | ---: | ' + ' | '.join(['---:'] * len(stage_names)) + ' |']
    for r in rows:
        cells = ['%.3f' % r['stages'].get(n, 0.0) for n in stage_names]
        lines.append('| %s | %d | %s |' % (r['label'], r['candidates'], ' | '.join(cells)))
    lines += ['', '## 同一有效样本目标下的整体需求', '',
              '| 接受比例 | 串行一轮 | 理想流水间隔 | 受限池 | 串行有效样本/秒 | 流水上界 |',
              '| --- | ---: | ---: | --- | ---: | ---: |']
    for r in rows:
        lines.append('| %s | %.3f s | %.3f s | %s | %.4f | %.4f |' % (
            r['label'], r['serial_batch_seconds'], r['ideal_pipeline_interval_seconds'],
            '、'.join(r['limiting_pools']), r['serial_accepted_per_second'],
            r['pipeline_accepted_per_second']))
    a2 = result['actor_speedup_2']
    lines += ['', '## 扩容对照：actor 池加速 2 倍（接受 1/2）', '',
              '- 理想流水间隔：%.3f s（基线 %.3f s）' % (
                  a2['ideal_pipeline_interval_lower_seconds'],
                  rows[0]['ideal_pipeline_interval_seconds']),
              '- 受限池变为：%s' % '、'.join(a2['limiting_pools']),
              '- 流水有效样本/秒上界：%.4f（基线 %.4f）' % (
                  a2['ideal_pipeline_accepted_samples_per_second_upper'],
                  rows[0]['pipeline_accepted_per_second']), '']
    open(os.path.join(RESULTS, 'rl.md'), 'w').write('\n'.join(lines))
    print('\n'.join(lines))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
