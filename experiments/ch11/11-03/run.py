#!/usr/bin/env python3
"""实验 11-4（本目录 11-03）：异构集群中的成组作业。

在一张含两类 GPU、不同 CPU 余量和两级网络的资源图上，安排在线推理、
训练和离线任务；比较等待、迁移与跨机器启动的预计完成时间，
指出哪一种约束使空闲卡无法使用。

设备需求沿用前章估算（第 6、10 章的逐卡容量与训练步时间）；
统一计算项目未覆盖这一放置问题，因此本实验独立实现，每一步都可手算核对。
只依赖 Python 3 标准库。
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(HERE, 'results')
GB = 10 ** 9

# 资源图：两个机架，每个机架 4 台主机；机架内 400 GB/s，机架间 50 GB/s
HOSTS = []
for rack in range(2):
    for h in range(4):
        gpu_type = 'H100-80G' if rack == 0 else 'L40S-48G'
        HOSTS.append(dict(
            host='r%dh%d' % (rack, h), rack=rack, gpu_type=gpu_type,
            gpus=8, gpu_capacity=(80 if gpu_type.startswith('H100') else 48) * GB,
            cpu_cores=64 if rack == 0 else 32,
            cpu_free_cores=(48 if h < 2 else 8) if rack == 0 else (24 if h < 2 else 4),
            free_gpus=8))

INTRA_RACK_BPS, INTER_RACK_BPS = 400e9, 50e9
INTRA_RACK_START_S, INTER_RACK_START_S = 0.0, 0.0

# 作业：沿用前章估算的设备需求
JOBS = [
    dict(name='在线推理（Qwen3-8B，TP=2 副本×4）', kind='online', gpus=8,
         same_host=True, gpu_capacity_needed=20 * GB, cpu_cores=16,
         gang=True, priority=0, runtime_s=None,
         startup_s=dict(same_host=45, cross_host=75, cross_rack=110)),
    dict(name='训练（Qwen3-8B 全参，ZeRO-2，16 卡）', kind='training', gpus=16,
         same_host=False, gpu_capacity_needed=30 * GB, cpu_cores=8,
         gang=True, priority=1, runtime_s=30 * 86400,
         startup_s=dict(same_host=120, cross_host=180, cross_rack=420)),
    dict(name='离线批量生成（8 卡，可分散）', kind='offline', gpus=8,
         same_host=False, gpu_capacity_needed=20 * GB, cpu_cores=4,
         gang=False, priority=2, runtime_s=6 * 3600,
         startup_s=dict(same_host=30, cross_host=40, cross_rack=60)),
    dict(name='验证服务（CPU 重，2 卡）', kind='verify', gpus=2,
         same_host=True, gpu_capacity_needed=20 * GB, cpu_cores=48,
         gang=True, priority=3, runtime_s=3600,
         startup_s=dict(same_host=20, cross_host=30, cross_rack=45)),
]


def place(job, hosts):
    """按优先级顺序放置：先同主机，再同机架，最后跨机架。返回放置与不可用原因。"""
    reasons = []
    candidates = [h for h in hosts
                  if h['gpu_capacity'] >= job['gpu_capacity_needed']]
    dropped_capacity = [h['host'] for h in hosts if h not in candidates]
    if dropped_capacity:
        reasons.append('逐卡容量不足而排除：' + '、'.join(dropped_capacity))
    # 同主机
    for h in candidates:
        if h['free_gpus'] >= job['gpus'] and h['cpu_free_cores'] >= job['cpu_cores']:
            return dict(mode='same_host', hosts=[h['host']], racks=[h['rack']]), reasons
    if job['same_host']:
        cpu_blocked = [h['host'] for h in candidates
                       if h['free_gpus'] >= job['gpus'] and h['cpu_free_cores'] < job['cpu_cores']]
        if cpu_blocked:
            reasons.append('GPU 空闲但 CPU 余量不足，无法单机放下：' + '、'.join(cpu_blocked))
        return None, reasons
    # 同机架
    for rack in (0, 1):
        pool = [h for h in candidates if h['rack'] == rack]
        gpus = sum(min(h['free_gpus'], h['free_gpus']) for h in pool)
        cpu_ok = [h for h in pool if h['cpu_free_cores'] >= 1]
        if gpus >= job['gpus'] and len(cpu_ok) == len(pool):
            return dict(mode='cross_host', hosts=[h['host'] for h in pool],
                        racks=[rack]), reasons
    # 跨机架
    gpus = sum(h['free_gpus'] for h in candidates)
    if gpus >= job['gpus']:
        return dict(mode='cross_rack', hosts=[h['host'] for h in candidates],
                    racks=sorted({h['rack'] for h in candidates})), reasons
    reasons.append('全集群空闲 GPU 不足')
    return None, reasons


def main() -> int:
    os.makedirs(RESULTS, exist_ok=True)
    hosts = [dict(h) for h in HOSTS]
    rows = []
    clock = 0.0
    for job in sorted(JOBS, key=lambda j: j['priority']):
        placement, reasons = place(job, hosts)
        if placement is None:
            rows.append(dict(job=job['name'], placed=False, reasons=reasons,
                             wait_seconds=None, startup_seconds=None,
                             expected_finish_seconds=None))
            continue
        startup = job['startup_s'][placement['mode']]
        wait = clock
        finish = (wait + startup + job['runtime_s']) if job['runtime_s'] else None
        # 扣减资源
        need = job['gpus']
        cpu_need = job['cpu_cores']
        for h in hosts:
            if h['host'] not in placement['hosts'] or need <= 0:
                continue
            take = min(h['free_gpus'], need)
            h['free_gpus'] -= take
            need -= take
            take_cpu = min(h['cpu_free_cores'], cpu_need)
            h['cpu_free_cores'] -= take_cpu
            cpu_need -= take_cpu
        rows.append(dict(job=job['name'], placed=True, mode=placement['mode'],
                         hosts=placement['hosts'], racks=placement['racks'],
                         reasons=reasons, wait_seconds=wait, startup_seconds=startup,
                         runtime_seconds=job['runtime_s'],
                         expected_finish_seconds=finish,
                         residual_cpu_need=cpu_need, residual_gpu_need=need))
        if job['kind'] != 'online':
            clock += 0.0

    idle = [dict(host=h['host'], gpu_type=h['gpu_type'], free_gpus=h['free_gpus'],
                 cpu_free_cores=h['cpu_free_cores']) for h in hosts if h['free_gpus'] > 0]
    blocked = [h for h in idle if h['cpu_free_cores'] < 8]

    result = dict(schema_version=1, experiment='11-4（目录 11-03）',
                  title='异构集群中的成组作业',
                  resource_graph=dict(hosts=HOSTS, intra_rack_bps=INTRA_RACK_BPS,
                                      inter_rack_bps=INTER_RACK_BPS),
                  jobs=[j['name'] for j in JOBS], placements=rows,
                  idle_after=idle, idle_blocked_by_cpu=blocked,
                  binding_constraint=(
                      '使空闲卡无法使用的约束依次是：'
                      '(1) 逐卡容量——L40S 48 GB 装不下需要 30 GB/卡以上且要留工作区的训练分片；'
                      '(2) CPU 余量——r0h2／r0h3 与 r1h2／r1h3 的 GPU 空闲但只剩 8／4 核，'
                      'CPU 重的验证服务放不进去；'
                      '(3) 成组（gang）语义——训练要 16 卡同时就绪，'
                      '零散的空闲卡即使总数够也不能拼成一个作业；'
                      '(4) 同主机约束——在线推理要求副本在同一主机内，'
                      '跨主机的空闲卡对它没有意义。'),
                  method='优先级顺序放置，先同主机、再同机架、最后跨机架；'
                         '每一步的容量与 CPU 扣减都可手算核对。',
                  python_version=sys.version)
    json.dump(result, open(os.path.join(RESULTS, 'placement.json'), 'w'),
              indent=2, ensure_ascii=False)

    lines = ['# 实验 11-4 结果：异构集群中的成组作业', '',
             '资源图：机架 0 有 4 台 H100-80G 主机（每台 8 卡、64 核），'
             '机架 1 有 4 台 L40S-48G 主机（每台 8 卡、32 核）；'
             '机架内 400 GB/s，机架间 50 GB/s。'
             'CPU 余量按主机不同：每机架前两台余量充足，后两台紧张。', '',
             '| 作业 | 放置 | 主机 | 跨机架 | 等待 | 启动 | 预计完成 |',
             '| --- | --- | --- | :---: | ---: | ---: | ---: |']
    for r in rows:
        if not r['placed']:
            lines.append('| %s | **无法放置** | — | — | — | — | — |' % r['job'])
            continue
        lines.append('| %s | %s | %s | %s | %.0f s | %.0f s | %s |' % (
            r['job'], {'same_host': '同主机', 'cross_host': '同机架跨主机',
                       'cross_rack': '跨机架'}[r['mode']],
            '、'.join(r['hosts'][:4]) + ('…' if len(r['hosts']) > 4 else ''),
            '是' if len(r['racks']) > 1 else '否',
            r['wait_seconds'], r['startup_seconds'],
            '%.1f 天' % (r['expected_finish_seconds'] / 86400)
            if r['expected_finish_seconds'] else '常驻'))
    lines += ['', '## 放置过程中被排除的原因', '']
    for r in rows:
        for reason in r['reasons']:
            lines.append('- %s：%s' % (r['job'], reason))
    lines += ['', '## 放置后仍空闲的卡', '',
              '| 主机 | 卡型 | 空闲 GPU | 空闲 CPU 核 |', '| --- | --- | ---: | ---: |']
    for h in idle:
        lines.append('| %s | %s | %d | %d |' % (h['host'], h['gpu_type'],
                                                h['free_gpus'], h['cpu_free_cores']))
    lines += ['', '## 哪种约束使空闲卡无法使用', '', result['binding_constraint'], '']
    open(os.path.join(RESULTS, 'placement.md'), 'w').write('\n'.join(lines))
    print('\n'.join(lines))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
