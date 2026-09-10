#!/usr/bin/env python3
"""实验 6-9：内存池的容量收益与访问代价。

四台机器的总内存够用，为什么仍有任务放不下？
四个 64 GiB 节点分别承接 80、48、32、32 GiB 的工作集，比较三条路径：
  迁移任务、增加本地容量、向池借用 16 GiB。
对同一份工作集只改变访问频次，求借用路径必须提供的能力。

本实验不重算：由 `calculations/calc.py memory-pool-access` 现场生成。
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


def main() -> int:
    os.makedirs(RESULTS, exist_ok=True)
    rows = []
    for copies in (1, 2):
        path = os.path.join(RESULTS, 'pool-copies%d.json' % copies)
        proc = subprocess.run([sys.executable, CALC, 'memory-pool-access',
                               '--copies', str(copies), '--format', 'json', '--output', path],
                              capture_output=True, text=True)
        if proc.returncode != 0:
            sys.exit('调用失败：\n' + proc.stderr[-800:])
        rows.append(dict(copies=copies, doc=json.load(open(path))))

    base = rows[0]['doc']
    feasible = [a for a in base['access_scenarios'] if a.get('deterministic_serial_queue_bounded')]
    infeasible = [a for a in base['access_scenarios'] if not a.get('deterministic_serial_queue_bounded')]

    result = dict(schema_version=1, experiment='6-9', title='内存池的容量收益与访问代价',
                  source_note='由 calculations/calc.py memory-pool-access 现场生成。',
                  capacity=base['capacity'], failure_sets=base['failure_sets'],
                  access_scenarios=base['access_scenarios'],
                  replicated=rows[1]['doc'].get('failure_sets'),
                  feasible_count=len(feasible), infeasible_count=len(infeasible),
                  python_version=sys.version)
    json.dump(result, open(os.path.join(RESULTS, 'pool.json'), 'w'), indent=2, ensure_ascii=False)

    cap = base['capacity']
    GiB = 2 ** 30
    lines = ['# 实验 6-9 结果：内存池的容量收益与访问代价', '',
             '## 容量：总量够，仍然放不下', '',
             '| 节点 | 容量 | 任务需求 | 本地缺口 |',
             '| ---: | ---: | ---: | ---: |']
    for i, (c, d) in enumerate(zip(cap['node_capacity_bytes'], cap['job_demand_bytes'])):
        lines.append('| %d | %.0f GiB | %.0f GiB | %.0f GiB |' % (
            i, c / GiB, d / GiB, cap['local_deficit_bytes'][i] / GiB))
    lines += ['', '- 总容量 %.0f GiB，总需求 %.0f GiB，**总量够**。' % (
        cap['total_capacity_bytes'] / GiB, cap['total_demand_bytes'] / GiB),
        '- 整任务迁移：%s' % cap['whole_job_migration_infeasibility'],
        '- 增加本地容量：需要 %.0f GiB。' % (cap['added_local_capacity_bytes'] / GiB),
        '- 向池借用：唯一借用 %.0f GiB；池外仍有 %.0f GiB 本地余量无法被这个任务使用。' % (
            cap['borrowed_unique_bytes'] / GiB,
            cap['unusable_local_slack_before_pool_bytes'] / GiB)]
    lines += ['', '## 访问频次决定借用路径必须提供的能力', '',
              '| 接口带宽 | 延迟 | 在途事务 | 读/秒 | 一次读取服务时间 | 负载 | 队列有界 | 可承受读频上限 |',
              '| ---: | ---: | ---: | ---: | ---: | ---: | :---: | ---: |']
    for a in base['access_scenarios']:
        lines.append('| %.0f GB/s | %.0f μs | %d | %.4g | %.4g s | %.4g | %s | %.4g /s |' % (
            a['interface_bandwidth_bytes_per_second'] / 1e9, a['latency_ns'] / 1000,
            a['active_transactions'], float(F(a['reads_per_second_exact'])),
            float(F(a['serialized_read_service_seconds_exact'])),
            float(F(a['load_exact'])),
            '是' if a['deterministic_serial_queue_bounded'] else '否',
            float(F(a['max_read_frequency_exact']))))
    lines += ['', '可行 %d 项／不可行 %d 项。' % (len(feasible), len(infeasible)), '']
    open(os.path.join(RESULTS, 'pool.md'), 'w').write('\n'.join(lines))
    print('\n'.join(lines[:14]))
    print('...')
    print('可行 %d 项／不可行 %d 项，完整表见 results/pool.md' % (len(feasible), len(infeasible)))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
