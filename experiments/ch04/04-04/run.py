#!/usr/bin/env python3
"""实验 4-4：片上缓冲与数据复用。

增加一块片上缓冲值不值得？沿同一 Qwen3-8B 上投影矩阵与注意力工作：
  1. 扫描分块与缓冲容量，算每个候选的下一层访问字节（中转字节）；
  2. 比较同步加载（单缓冲）与异步搬运（双缓冲）：可行块怎样变、字节怎样变；
  3. 提高矩阵吞吐后，同一块缓冲为什么可能不够——给出收益开始变小的位置。

本实验不重算：由 `calculations/calc.py gemm-tiles|attention-tiles` 现场生成。
"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
CALC = os.path.join(ROOT, 'calculations', 'calc.py')
RESULTS = os.path.join(HERE, 'results')
MiB = 2 ** 20
KiB = 1024

CAPACITIES = [64 * KiB, 80 * KiB, 128 * KiB, 192 * KiB, 256 * KiB]
TILES = ['32', '64', '128', '256']
BUFFERS = [1, 2]        # 1＝同步加载；2＝异步双缓冲
TOKENS = 1024


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
    for cap in CAPACITIES:
        for buf in BUFFERS:
            doc, err = run(['gemm-tiles', '--model', 'qwen3-8b', '--tokens', str(TOKENS),
                            '--tiles'] + TILES + ['--tile-k', '32',
                            '--capacity-bytes', str(cap), '--input-buffers', str(buf)],
                           'gemm-c%d-b%d.json' % (cap, buf))
            if doc is None:
                rows.append(dict(capacity=cap, buffers=buf, error=err))
                continue
            feasible = [r for r in doc['gemm_tile_rows'] if r['fits_capacity']]
            best = min(feasible, key=lambda r: r['next_level_bytes']) if feasible else None
            rows.append(dict(capacity=cap, buffers=buf,
                             candidates=len(doc['gemm_tile_rows']),
                             feasible=len(feasible),
                             best_tile=[best['tile_m'], best['tile_k'], best['tile_n']] if best else None,
                             best_next_level_bytes=best['next_level_bytes'] if best else None,
                             best_arithmetic_intensity=best['arithmetic_intensity'] if best else None,
                             reserved_working_bytes=best['reserved_working_bytes'] if best else None,
                             one_read_write_payload_bytes=doc['summary']['one_read_write_payload_bytes'],
                             all_rows=doc['gemm_tile_rows']))

    attn = []
    for cap in (64 * KiB, 128 * KiB, 256 * KiB):
        doc, err = run(['attention-tiles', '--model', 'qwen3-8b', '--tokens', '8192',
                        '--capacity-bytes', str(cap), '--causal',
                        '--kv-blocks', '1', '16', '64', '128', '256'],
                       'attn-c%d.json' % cap)
        if doc is None:
            attn.append(dict(capacity=cap, error=err))
            continue
        attn.append(dict(capacity=cap, summary=doc.get('summary'),
                         rows=doc['attention_tile_rows']))

    result = dict(schema_version=1, experiment='4-4', title='片上缓冲与数据复用',
                  tokens=TOKENS, capacities=CAPACITIES, tiles=TILES,
                  source_note='由 calculations/calc.py gemm-tiles|attention-tiles 现场生成。',
                  gemm=rows, attention=attn, python_version=sys.version)
    json.dump(result, open(os.path.join(RESULTS, 'buffer.json'), 'w'), indent=2, ensure_ascii=False)

    payload = next((r['one_read_write_payload_bytes'] for r in rows if 'error' not in r), None)
    lines = ['# 实验 4-4 结果：片上缓冲与数据复用', '',
             'Qwen3-8B 上投影 `[%d,4096]×[4096,12288]`；只读写一次的最低载荷 %.1f MiB。' % (
                 TOKENS, payload / MiB if payload else 0), '',
             '## 缓冲容量 × 缓冲策略：可行块与中转字节', '',
             '| 片上容量 | 缓冲 | 可行候选 | 最佳块 (m,k,n) | 下一层访问 | 算术强度 |',
             '| ---: | --- | ---: | --- | ---: | ---: |']
    for r in rows:
        if 'error' in r:
            lines.append('| %d KiB | %s | — | 调用失败 | — | — |' % (
                r['capacity'] / KiB, '同步' if r['buffers'] == 1 else '异步双缓冲'))
            continue
        lines.append('| %d KiB | %s | %d／%d | %s | %.1f MiB | %.1f |' % (
            r['capacity'] / KiB, '同步' if r['buffers'] == 1 else '异步双缓冲',
            r['feasible'], r['candidates'],
            '×'.join(str(x) for x in r['best_tile']) if r['best_tile'] else '无可行块',
            (r['best_next_level_bytes'] or 0) / MiB,
            r['best_arithmetic_intensity'] or 0))
    lines += ['', '## 注意力侧的同一问题（8192 token，因果，单头）', '',
              '| 片上容量 | KV 块 | 可行 | Q 块 | 保留工作空间 | 接口字节 | 行状态更新 |',
              '| ---: | ---: | :---: | ---: | ---: | ---: | ---: |']
    for a in attn:
        if 'error' in a:
            lines.append('| %d KiB | — | — | — | — | 调用失败：%s | — |' % (a['capacity'] / KiB, a['error']))
            continue
        for r in a['rows']:
            lines.append('| %d KiB | %d | %s | %s | %s | %s | %s |' % (
                a['capacity'] / KiB, r['kv_block'], '是' if r['feasible'] else '否',
                r.get('query_block', '—'),
                '%.1f KiB' % (r['reserved_working_bytes'] / KiB) if 'reserved_working_bytes' in r else '—',
                '%.1f MiB' % (r['interface_bytes'] / MiB) if 'interface_bytes' in r else '—',
                '%.4g' % r['row_state_updates'] if 'row_state_updates' in r else '—'))
    lines.append('')
    open(os.path.join(RESULTS, 'buffer.md'), 'w').write('\n'.join(lines))
    print('\n'.join(lines))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
