#!/usr/bin/env python3
"""实验 12-5：ACK 频率与空口效率。

减少 ACK 一定有利吗？按语音块与视觉帧的速率建立空口模型，扫描 ACK 频率，
比较线上字节、输入过期、反馈延迟与完成时刻；再改变编码码率重算。

本实验不重算：由 `calculations/calc.py transport-closed-loop` 现场生成
（该实现逐包重放上下行、拥塞控制与 ACK 策略）。
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

# 两类媒体：语音块（小而密）与视觉帧（大而疏）；速率是声明输入
MEDIA = [
    ('语音块（20 ms、低码率）', 2336, 32),
    ('语音块（20 ms、高码率）', 9344, 32),
    ('视觉帧（低码率）', 35000, 128),
    ('视觉帧（高码率）', 140000, 128),
]
ACK_POLICIES = [
    ('每包 ACK', dict(mode='count_or_timer', every=1, max_delay=10)),
    ('每 2 包 ACK', dict(mode='count_or_timer', every=2, max_delay=10)),
    ('每 4 包 ACK', dict(mode='count_or_timer', every=4, max_delay=10)),
    ('每 8 包 ACK', dict(mode='count_or_timer', every=8, max_delay=10)),
    ('每 16 包 ACK', dict(mode='count_or_timer', every=16, max_delay=10)),
    ('每 8 包或 2 单位超时', dict(mode='count_or_timer', every=8, max_delay=2)),
]
LINKS = dict(up=dict(rate_bps=9824, propagation=1), down=dict(rate_bps=736, propagation=1))


def main() -> int:
    os.makedirs(RESULTS, exist_ok=True)
    rows = []
    for mi, (media, upload, response) in enumerate(MEDIA):
        for pi, (policy, ack) in enumerate(ACK_POLICIES):
            cfg = dict(upload_bytes=upload, response_bytes=response, model_seconds='1',
                       until='400', links=LINKS,
                       sender=dict(initial_cwnd=2400,
                                   rtt_seed=dict(latest_rtt=4, smoothed_rtt=4,
                                                 rttvar=2, min_rtt=4)),
                       ack_policy=ack)
            ipath = os.path.join(RESULTS, 'input-%d-%d.json' % (mi, pi))
            opath = os.path.join(RESULTS, 'loop-%d-%d.json' % (mi, pi))
            json.dump(cfg, open(ipath, 'w'), indent=1)
            proc = subprocess.run([sys.executable, CALC, 'transport-closed-loop',
                                   '--inputs', ipath, '--format', 'json', '--output', opath],
                                  capture_output=True, text=True)
            if proc.returncode != 0:
                rows.append(dict(media=media, policy=policy,
                                 error=(proc.stderr.strip().splitlines() or [''])[-1]))
                continue
            doc = json.load(open(opath))
            s = doc['summary']
            waits = doc.get('waits') or []
            events = doc.get('application_events') or []
            last_event = max((float(F(str(e.get('at', 0)))) for e in events), default=None)
            rows.append(dict(media=media, policy=policy,
                             upload_bytes=upload, wire_bytes=s['wire_bytes'],
                             unique_received=s['unique_received_bytes'],
                             overhead_ratio=s['wire_bytes'] / max(1, s['unique_received_bytes']),
                             complete=s['complete'],
                             waits=len(waits),
                             last_application_event=last_event))

    result = dict(schema_version=1, experiment='12-5', title='ACK 频率与空口效率',
                  media=[m[0] for m in MEDIA], policies=[p[0] for p in ACK_POLICIES],
                  links=LINKS, rows=rows,
                  source_note='由 calculations/calc.py transport-closed-loop 现场生成；'
                              '链路速率与传播时延是声明输入。',
                  python_version=sys.version)
    json.dump(result, open(os.path.join(RESULTS, 'ack.json'), 'w'), indent=2, ensure_ascii=False)

    lines = ['# 实验 12-5 结果：ACK 频率与空口效率', '',
             '上行 %d bps／下行 %d bps，单向传播各 1 单位（声明输入）。' % (
                 LINKS['up']['rate_bps'], LINKS['down']['rate_bps']), '',
             '| 媒体 | ACK 策略 | 载荷 B | 线上字节 | 线上/载荷 | 等待次数 | 最后应用事件 | 完成 |',
             '| --- | --- | ---: | ---: | ---: | ---: | ---: | :---: |']
    for r in rows:
        if 'error' in r:
            lines.append('| %s | %s | — | 调用失败：%s | — | — | — | — |' % (
                r['media'], r['policy'], r['error']))
            continue
        lines.append('| %s | %s | %d | %d | %.4f | %d | %s | %s |' % (
            r['media'], r['policy'], r['upload_bytes'], r['wire_bytes'],
            r['overhead_ratio'], r['waits'],
            '%.2f' % r['last_application_event'] if r['last_application_event'] is not None else '—',
            '是' if r['complete'] else '否'))
    lines.append('')
    open(os.path.join(RESULTS, 'ack.md'), 'w').write('\n'.join(lines))
    print('\n'.join(lines))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
