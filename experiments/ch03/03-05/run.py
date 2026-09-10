#!/usr/bin/env python3
"""实验 3-5：实时语音的响应预算。

对同一条固定语音记录计算三项：首次播放时刻、块间抖动（欠载与迟到）和
打断响应；再分别改变模型、网络与缓冲，判断哪一项能改善对话。

本实验不重算：由 `calculations/calc.py audio-timing` 现场生成。
本目录另有两个已交付的资料子目录：`historical-arrivals/`（历史到达记录）
与 `source-contract/`（来源核对）。只依赖 Python 3 标准库。
"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
CALC = os.path.join(ROOT, 'calculations', 'calc.py')
RESULTS = os.path.join(HERE, 'results')
MS = 1e6

FRAME_NS = 20_000_000        # 20 ms 一帧
CHUNKS = 8


def base(**over):
    cfg = dict(frame_ns=FRAME_NS,
               model_ns=[12_000_000] * CHUNKS,
               network_delay_ns=[5_000_000] * CHUNKS,
               send_ns=1_000_000,
               jitter_buffer_ns=40_000_000,
               sample_rate=24000, channels=1, sample_bytes=2,
               interrupt_ns=None, control_delay_ns=5_000_000,
               device_quantum_ns=10_000_000)
    cfg.update(over)
    return cfg


CASES = [
    ('基线（模型 12 ms、网络 5 ms、缓冲 40 ms）', base()),
    ('网络第 3 块抖动到 50 ms', base(network_delay_ns=[5_000_000, 5_000_000, 50_000_000] + [5_000_000] * 5)),
    ('模型变慢到 25 ms/块', base(model_ns=[25_000_000] * CHUNKS)),
    ('模型加速到 6 ms/块', base(model_ns=[6_000_000] * CHUNKS)),
    ('缓冲取消（0 ms）', base(jitter_buffer_ns=0)),
    ('缓冲加大到 100 ms', base(jitter_buffer_ns=100_000_000)),
    ('网络整体降到 2 ms', base(network_delay_ns=[2_000_000] * CHUNKS)),
    ('抖动 ＋ 缓冲加大到 100 ms',
     base(network_delay_ns=[5_000_000, 5_000_000, 50_000_000] + [5_000_000] * 5,
          jitter_buffer_ns=100_000_000)),
    ('打断：第 60 ms 发出停止', base(interrupt_ns=60_000_000)),
    ('打断 ＋ 缓冲 100 ms', base(interrupt_ns=60_000_000, jitter_buffer_ns=100_000_000)),
    ('播放中打断：第 150 ms（缓冲 40 ms）', base(interrupt_ns=150_000_000)),
    ('播放中打断：第 150 ms（缓冲 100 ms）', base(interrupt_ns=150_000_000, jitter_buffer_ns=100_000_000)),
    ('播放中打断：第 150 ms（缓冲 0 ms）', base(interrupt_ns=150_000_000, jitter_buffer_ns=0)),
]


def run(cfg, name):
    ipath = os.path.join(RESULTS, 'input-%s.json' % name)
    opath = os.path.join(RESULTS, 'timing-%s.json' % name)
    json.dump(cfg, open(ipath, 'w'), indent=1)
    proc = subprocess.run([sys.executable, CALC, 'audio-timing', '--inputs', ipath,
                           '--format', 'json', '--output', opath],
                          capture_output=True, text=True)
    if proc.returncode != 0:
        sys.exit('调用失败：%s\n%s' % (name, proc.stderr[-900:]))
    return json.load(open(opath))


def main() -> int:
    os.makedirs(RESULTS, exist_ok=True)
    rows = []
    for i, (label, cfg) in enumerate(CASES):
        doc = run(cfg, 'c%d' % i)
        s = doc['summary']
        rows.append(dict(label=label, case='c%d' % i, summary=s))

    result = dict(schema_version=1, experiment='3-5', title='实时语音的响应预算',
                  frame_ns=FRAME_NS, chunks=CHUNKS,
                  source_note='由 calculations/calc.py audio-timing 现场生成；时序输入是明确标注的教学值。',
                  rows=rows, python_version=sys.version)
    json.dump(result, open(os.path.join(RESULTS, 'voice.json'), 'w'), indent=2, ensure_ascii=False)

    lines = ['# 实验 3-5 结果：实时语音的响应预算', '',
             '固定记录：%d 个 20 ms 块、24 kHz 单声道 16 bit。' % CHUNKS, '',
             '## 首次播放与块间抖动', '',
             '| 场景 | 首次播放 | 采集到播放 | 欠载次数 | 累计停顿 | 最大迟到 | 播放结束 |',
             '| --- | ---: | ---: | ---: | ---: | ---: | ---: |']
    for r in rows:
        s = r['summary']
        if s.get('interrupt_to_mute_ns') is not None:
            continue
        lines.append('| %s | %.1f ms | %.1f ms | %d | %.1f ms | %.1f ms | %.1f ms |' % (
            r['label'], s['first_playback_from_time_zero_ns'] / MS,
            s['first_chunk_capture_to_playback_ns'] / MS, s['deadline_misses'],
            s['total_playback_stall_ns'] / MS, s['maximum_playback_lateness_ns'] / MS,
            s['baseline_playback_finish_ns'] / MS))
    lines += ['', '## 打断响应', '',
              '| 场景 | 静音生效 | 打断到静音 | 打断后仍可听见 |', '| --- | ---: | ---: | ---: |']
    for r in rows:
        s = r['summary']
        if s.get('interrupt_to_mute_ns') is None:
            continue
        lines.append('| %s | %.1f ms | %.1f ms | %.1f ms |' % (
            r['label'], s['mute_effective_ns'] / MS, s['interrupt_to_mute_ns'] / MS,
            s['audible_after_interrupt_ns'] / MS))
    lines.append('')
    open(os.path.join(RESULTS, 'voice.md'), 'w').write('\n'.join(lines))
    print('\n'.join(lines))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
