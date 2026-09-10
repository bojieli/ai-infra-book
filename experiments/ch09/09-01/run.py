#!/usr/bin/env python3
"""实验 9-1：服务分工与缓存的基线。

复用第 6、7 章确定的并行方案，给一组 Chat／Agent 请求画完整时序，
分别估算三种组织可能省下的工作与新增流量：
  1. 共置（一切都在同一实例）；
  2. 阶段分离（PD）；
  3. 缓存复用（前缀命中）。
最后选出后续最值得验证的两项。

工作量由 `calculations/calc.py forward|generate` 现场生成；
分离与缓存的收支沿用 9-2／9-4 的口径。只依赖 Python 3 标准库。
"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
CALC = os.path.join(ROOT, 'calculations', 'calc.py')
RESULTS = os.path.join(HERE, 'results')
GiB = 2 ** 30
TFLOP = 10 ** 12
LINK = 25e9

# 一组 Chat／Agent 请求（长度取自实验 2-8 的固定画像量级）
REQUESTS = [
    ('Chat 轮 1', 256, 0, 32),
    ('Chat 轮 2', 512, 256, 32),
    ('Chat 轮 3', 800, 512, 32),
    ('Agent 轮 1', 2048, 0, 128),
    ('Agent 轮 2', 3200, 2048, 128),
    ('Agent 轮 3', 4400, 3200, 128),
]


def run(args, out):
    path = os.path.join(RESULTS, out)
    proc = subprocess.run([sys.executable, CALC] + args + ['--format', 'json', '--output', path],
                          capture_output=True, text=True)
    if proc.returncode != 0:
        sys.exit('调用失败：%s\n%s' % (' '.join(args), proc.stderr[-600:]))
    return json.load(open(path))


def main() -> int:
    os.makedirs(RESULTS, exist_ok=True)
    rows = []
    for i, (name, prompt, cached, outputs) in enumerate(REQUESTS):
        full = run(['forward', '--model', 'qwen3-8b', '--batch', '1',
                    '--tokens', str(prompt), '--history', '0'], 'full-%d.json' % i)
        suffix = run(['forward', '--model', 'qwen3-8b', '--batch', '1',
                      '--tokens', str(prompt - cached), '--history', str(cached)],
                     'suffix-%d.json' % i) if cached else full
        gen = run(['generate', '--model', 'qwen3-8b', '--batch', '1',
                   '--history', str(prompt), '--steps', str(outputs)], 'gen-%d.json' % i)
        fs, ss, gs = full['summary'], suffix['summary'], gen['summary']
        rows.append(dict(
            request=name, prompt=prompt, cached=cached, outputs=outputs,
            prefill_flops_full=fs['matrix_flops'],
            prefill_flops_cached=ss['matrix_flops'],
            prefill_flops_saved=fs['matrix_flops'] - ss['matrix_flops'],
            kv_snapshot_bytes=fs['kv_resident_after_bytes'],
            decode_flops=gs['matrix_flops'],
            decode_weight_read_bytes=gs['weight_read_once_per_step_bytes'],
            decode_history_read_bytes=gs['kv_existing_history_read_bytes'],
            pd_transfer_bytes=fs['kv_resident_after_bytes'],
            pd_transfer_seconds=fs['kv_resident_after_bytes'] / LINK,
            cache_restore_bytes=cached and int(fs['kv_resident_after_bytes'] * cached / prompt) or 0))

    totals = dict(
        prefill_flops_full=sum(r['prefill_flops_full'] for r in rows),
        prefill_flops_cached=sum(r['prefill_flops_cached'] for r in rows),
        prefill_flops_saved=sum(r['prefill_flops_saved'] for r in rows),
        decode_flops=sum(r['decode_flops'] for r in rows),
        decode_weight_read_bytes=sum(r['decode_weight_read_bytes'] for r in rows),
        pd_transfer_bytes=sum(r['pd_transfer_bytes'] for r in rows),
        pd_transfer_seconds=sum(r['pd_transfer_seconds'] for r in rows),
        cache_restore_bytes=sum(r['cache_restore_bytes'] for r in rows))

    picks = [
        '**最值得验证的第一项：前缀缓存的实际命中粒度与驻留时间。** 本基线把命中当作精确前缀且总是可用；'
        '实测（实验 8-4）显示命中按精确 token 前缀判定，首 token 一变就归零，且驻留受容量与淘汰影响。'
        '这一项决定上表 %.1f%% 的 prefill 节省能否兑现。' % (
            100.0 * totals['prefill_flops_saved'] / totals['prefill_flops_full']),
        '**最值得验证的第二项：PD 交接在真实链路上的时间与并发影响。** 本基线按 %.0f GB/s 无竞争计，'
        '整组请求要搬 %.2f GiB、耗时 %.1f ms；实际链路与在途并发（实验 7-5）以及交接期间两侧的等待'
        '（实验 9-4）都会改变这笔账。' % (
            LINK / 1e9, totals['pd_transfer_bytes'] / GiB, totals['pd_transfer_seconds'] * 1e3),
    ]

    result = dict(schema_version=1, experiment='9-1', title='服务分工与缓存的基线',
                  link_bytes_per_second=LINK, requests=rows, totals=totals, picks=picks,
                  source_note='工作量由 calculations/calc.py 现场生成；链路速率为声明输入。',
                  python_version=sys.version)
    json.dump(result, open(os.path.join(RESULTS, 'baseline.json'), 'w'), indent=2, ensure_ascii=False)

    lines = ['# 实验 9-1 结果：服务分工与缓存的基线', '',
             '一组 6 个 Chat／Agent 请求，链路 %.0f GB/s。' % (LINK / 1e9), '',
             '| 请求 | 输入 | 可复用前缀 | 输出 | 完整 prefill | 命中后 prefill | 省下 | decode 工作 | KV 快照 | PD 交接 |',
             '| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |']
    for r in rows:
        lines.append('| %s | %d | %d | %d | %.3f TF | %.3f TF | %.3f TF | %.3f TF | %.3f GiB | %.2f ms |' % (
            r['request'], r['prompt'], r['cached'], r['outputs'],
            r['prefill_flops_full'] / TFLOP, r['prefill_flops_cached'] / TFLOP,
            r['prefill_flops_saved'] / TFLOP, r['decode_flops'] / TFLOP,
            r['kv_snapshot_bytes'] / GiB, r['pd_transfer_seconds'] * 1e3))
    lines += ['', '## 三种组织的收支合计', '',
              '| 项目 | 数值 |', '| --- | ---: |',
              '| 共置：完整 prefill 工作 | %.3f TFLOPs |' % (totals['prefill_flops_full'] / TFLOP),
              '| 缓存复用：命中后 prefill 工作 | %.3f TFLOPs |' % (totals['prefill_flops_cached'] / TFLOP),
              '| 缓存复用：省下的 prefill 工作 | **%.3f TFLOPs（%.1f%%）** |' % (
                  totals['prefill_flops_saved'] / TFLOP,
                  100.0 * totals['prefill_flops_saved'] / totals['prefill_flops_full']),
              '| 缓存复用：需要取回／保留的 KV | %.3f GiB |' % (totals['cache_restore_bytes'] / GiB),
              '| 阶段分离：新增交接字节 | **%.3f GiB** |' % (totals['pd_transfer_bytes'] / GiB),
              '| 阶段分离：新增交接时间 | **%.1f ms** |' % (totals['pd_transfer_seconds'] * 1e3),
              '| 全部 decode 工作 | %.3f TFLOPs |' % (totals['decode_flops'] / TFLOP),
              '| 全部 decode 权重读取 | %.1f GiB |' % (totals['decode_weight_read_bytes'] / GiB),
              '', '## 后续最值得验证的两项', ''] + ['- ' + p for p in picks] + ['']
    open(os.path.join(RESULTS, 'baseline.md'), 'w').write('\n'.join(lines))
    print('\n'.join(lines))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
