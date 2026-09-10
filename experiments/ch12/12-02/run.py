#!/usr/bin/env python3
"""实验 12-2：远端执行的延迟收支。

并排计算三条完整路径：图片精修、ASR／TTS 与 Computer Use。
对 Computer Use 把截图由 0.8 MB 降到 0.2 MB，并加入 30 ms 编码开销，
复算单轮与多轮时间；再改变 RTT 和模型执行位置，给出在任务成功率要求下
最值得优化的一段。

图片路径由 `calculations/calc.py image-request-budget` 现场生成；
语音路径由 `calc.py audio-timing` 现场生成；Computer Use 的逐段预算在本文件内
按声明输入直接相加（每一步都可手算核对）。只依赖 Python 3 标准库。
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
MB = 10 ** 6

RTTS = [0.030, 0.080, 0.200]      # 30／80／200 ms
UPLINK_BPS = 20_000_000           # 20 Mb/s 上行
DOWNLINK_BPS = 100_000_000

# Computer Use：每轮一张截图上行、一条动作下行
CU_VARIANTS = [
    ('原始截图 0.8 MB、无编码开销', 800_000, 0.0),
    ('压到 0.2 MB、编码 30 ms', 200_000, 0.030),
    ('压到 0.2 MB、编码 100 ms', 200_000, 0.100),
]
CU_ACTION_BYTES = 2_000
CU_MODEL_SECONDS = [0.4, 1.2]
CU_ROUNDS = [1, 10, 30]


def run(cmd, cfg, out):
    ipath = os.path.join(RESULTS, 'input-%s.json' % out)
    opath = os.path.join(RESULTS, '%s.json' % out)
    json.dump(cfg, open(ipath, 'w'), indent=1)
    proc = subprocess.run([sys.executable, CALC, cmd, '--inputs', ipath,
                           '--format', 'json', '--output', opath],
                          capture_output=True, text=True)
    if proc.returncode != 0:
        return None, (proc.stderr.strip().splitlines() or ['failed'])[-1]
    return json.load(open(opath)), None


def computer_use(screenshot_bytes, encode_seconds, model_seconds, rtt, rounds):
    upload = screenshot_bytes * 8 / UPLINK_BPS
    download = CU_ACTION_BYTES * 8 / DOWNLINK_BPS
    per_round = encode_seconds + upload + rtt + model_seconds + download
    return dict(encode=encode_seconds, upload=upload, rtt=rtt,
                model=model_seconds, download=download,
                per_round=per_round, total=per_round * rounds, rounds=rounds)


def main() -> int:
    os.makedirs(RESULTS, exist_ok=True)

    # 图片精修
    image_rows = []
    for rtt in RTTS:
        cfg = dict(input_bytes=30_000_000, output_bytes=5_000_000,
                   upload_bits_per_second=UPLINK_BPS,
                   download_bits_per_second=DOWNLINK_BPS,
                   preparation_seconds='0', connection_seconds='0',
                   request_rtt_seconds=str(F(int(rtt * 1000), 1000)),
                   queue_seconds='0', input_decode_seconds='0',
                   model_seconds='3/10', output_encode_seconds='0',
                   output_use_seconds='0', local_seconds='5',
                   quality_contract='same original information and same final-image requirement',
                   metadata_kind='declared_teaching', input_format='RAW', output_format='JPEG')
        doc, err = run('image-request-budget', cfg, 'image-rtt%d' % int(rtt * 1000))
        if doc is None:
            image_rows.append(dict(rtt=rtt, error=err))
            continue
        v = doc['variants'][0]
        image_rows.append(dict(rtt=rtt,
                               complete_seconds=float(F(v['complete_final_image_seconds_exact']))))

    # ASR／TTS：固定语音记录的首播与打断
    audio_rows = []
    for rtt in RTTS:
        cfg = dict(frame_ns=20_000_000, model_ns=[12_000_000] * 8,
                   network_delay_ns=[int(rtt / 2 * 1e9)] * 8, send_ns=1_000_000,
                   jitter_buffer_ns=40_000_000, sample_rate=24000, channels=1,
                   sample_bytes=2, interrupt_ns=None, control_delay_ns=5_000_000,
                   device_quantum_ns=10_000_000)
        doc, err = run('audio-timing', cfg, 'audio-rtt%d' % int(rtt * 1000))
        if doc is None:
            audio_rows.append(dict(rtt=rtt, error=err))
            continue
        s = doc['summary']
        audio_rows.append(dict(rtt=rtt,
                               first_playback_s=s['first_playback_from_time_zero_ns'] / 1e9,
                               finish_s=s['baseline_playback_finish_ns'] / 1e9,
                               deadline_misses=s['deadline_misses']))

    # Computer Use
    cu_rows = []
    for label, shot, enc in CU_VARIANTS:
        for model_s in CU_MODEL_SECONDS:
            for rtt in RTTS:
                for rounds in CU_ROUNDS:
                    row = computer_use(shot, enc, model_s, rtt, rounds)
                    row.update(variant=label, model_seconds=model_s)
                    cu_rows.append(row)

    result = dict(schema_version=1, experiment='12-2', title='远端执行的延迟收支',
                  uplink_bps=UPLINK_BPS, downlink_bps=DOWNLINK_BPS,
                  image=image_rows, audio=audio_rows, computer_use=cu_rows,
                  source_note='图片与语音路径由 calculations/calc.py 现场生成；'
                              'Computer Use 的逐段预算按声明输入直接相加。',
                  python_version=sys.version)
    json.dump(result, open(os.path.join(RESULTS, 'latency.json'), 'w'), indent=2, ensure_ascii=False)

    lines = ['# 实验 12-2 结果：远端执行的延迟收支', '',
             '上行 %.0f Mb/s、下行 %.0f Mb/s。' % (UPLINK_BPS / 1e6, DOWNLINK_BPS / 1e6), '',
             '## 三条路径并排', '',
             '| RTT | 图片精修完整成片 | 语音首播 | 语音播放结束 | 语音欠载 |',
             '| ---: | ---: | ---: | ---: | ---: |']
    for i, rtt in enumerate(RTTS):
        im = image_rows[i]
        au = audio_rows[i]
        lines.append('| %.0f ms | %s | %s | %s | %s |' % (
            rtt * 1000,
            '%.3f s' % im['complete_seconds'] if 'complete_seconds' in im else '失败',
            '%.1f ms' % (au['first_playback_s'] * 1e3) if 'first_playback_s' in au else '失败',
            '%.1f ms' % (au['finish_s'] * 1e3) if 'finish_s' in au else '—',
            au.get('deadline_misses', '—')))
    lines += ['', '## Computer Use 的逐段与多轮', '',
              '| 截图变体 | 模型 | RTT | 编码 | 上传 | 模型 | 单轮 | 10 轮 | 30 轮 |',
              '| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |']
    seen = set()
    for r in cu_rows:
        key = (r['variant'], r['model_seconds'], r['rtt'])
        if key in seen:
            continue
        seen.add(key)
        one = next(x for x in cu_rows if (x['variant'], x['model_seconds'], x['rtt']) == key and x['rounds'] == 1)
        ten = next(x for x in cu_rows if (x['variant'], x['model_seconds'], x['rtt']) == key and x['rounds'] == 10)
        thirty = next(x for x in cu_rows if (x['variant'], x['model_seconds'], x['rtt']) == key and x['rounds'] == 30)
        lines.append('| %s | %.1f s | %.0f ms | %.0f ms | %.0f ms | %.0f ms | %.3f s | %.2f s | %.2f s |' % (
            r['variant'], r['model_seconds'], r['rtt'] * 1000,
            r['encode'] * 1000, r['upload'] * 1000, r['model'] * 1000,
            one['per_round'], ten['total'], thirty['total']))
    lines.append('')
    open(os.path.join(RESULTS, 'latency.md'), 'w').write('\n'.join(lines))
    print('\n'.join(lines))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
