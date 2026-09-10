#!/usr/bin/env python3
"""实验 8-5（本目录编号 08-07）容量分析：MacBook 上的 Qwen3-235B。

对 Qwen3-235B-A22B 的**实际量化文件逐片求和**，再用 M2 Max 96 GB 的可用内存、
8K／32K 上下文与不同并发计算驻留，判断何时需要主存／磁盘换入。

本实验不重算：由 `calculations/calc.py gguf-inventory` 现场生成（该实现读取
官方发布仓库的分片清单与 LFS SHA256，逐片求和）。同目录的实跑记录见上级 README。
"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
CALC = os.path.join(ROOT, 'calculations', 'calc.py')
RESULTS = os.path.join(HERE, 'results')
GB = 10 ** 9
GiB = 2 ** 30

VARIANTS = ['Q2_K', 'UD-Q2_K_XL', 'Q3_K_S', 'Q4_K_M', 'Q8_0', 'BF16']
CASES = [
    ('M2 Max 96 GB、8K 上下文、预留 8 GiB', 8192, 96 * GB, 8 * GiB),
    ('M2 Max 96 GB、32K 上下文、预留 8 GiB', 32768, 96 * GB, 8 * GiB),
    ('M2 Max 96 GB、8K 上下文、不预留', 8192, 96 * GB, 0),
    ('M3 Ultra 192 GB、32K 上下文、预留 8 GiB', 32768, 192 * GB, 8 * GiB),
]


def main() -> int:
    os.makedirs(RESULTS, exist_ok=True)
    rows = []
    for i, (label, ctx, budget, reserved) in enumerate(CASES):
        cfg = dict(context_tokens=ctx, memory_budget_bytes=budget,
                   reserved_bytes=reserved, variants=VARIANTS)
        ipath = os.path.join(RESULTS, 'input-%d.json' % i)
        opath = os.path.join(RESULTS, 'inventory-%d.json' % i)
        json.dump(cfg, open(ipath, 'w'), indent=1)
        proc = subprocess.run([sys.executable, CALC, 'gguf-inventory', '--inputs', ipath,
                               '--format', 'json', '--output', opath],
                              capture_output=True, text=True)
        if proc.returncode != 0:
            rows.append(dict(label=label, error=(proc.stderr.strip().splitlines() or [''])[-1]))
            continue
        doc = json.load(open(opath))
        rows.append(dict(label=label, context=ctx, budget=budget, reserved=reserved,
                         summary=doc['summary'],
                         variants=doc.get('gguf_variants') or doc.get('variants')))

    result = dict(schema_version=1, experiment='8-5（目录 08-07）容量分析',
                  title='MacBook 大模型的容量与速度：Qwen3-235B 文件逐片求和',
                  cases=[c[0] for c in CASES], rows=rows,
                  source_note='由 calculations/calc.py gguf-inventory 现场生成，'
                              '读取官方发布仓库的分片清单与 LFS SHA256。',
                  python_version=sys.version)
    json.dump(result, open(os.path.join(RESULTS, 'capacity.json'), 'w'),
              indent=2, ensure_ascii=False)

    base = next(r for r in rows if 'summary' in r)
    s = base['summary']
    lines = ['# 8-5 容量分析结果：Qwen3-235B 的量化文件与 Mac 驻留', '',
             '仓库 `%s`，revision `%s`；树中完整变体 %d 个、完整 GGUF 文件 %d 份。' % (
                 s['repository'], s['revision'][:12], s['complete_variants_in_tree'],
                 s['complete_gguf_files']), '',
             'BF16 KV 每 token %d B，每个独立请求（%d token）%.2f GiB。' % (
                 s['bf16_kv_bytes_per_token'], base['context'],
                 s['bf16_kv_bytes_per_independent_request'] / GiB), '']
    for r in rows:
        if 'error' in r:
            lines += ['## %s' % r['label'], '', '调用失败：%s' % r['error'], '']
            continue
        lines += ['## %s' % r['label'], '',
                  '可用 %.2f GiB。' % (r['summary']['declared_available_bytes'] / GiB), '',
                  '| 变体 | 分片 | 文件合计 | 装入后剩余 | 可容纳独立 BF16 KV 请求 | 文件放得下 | 再加 1 个 KV |',
                  '| --- | ---: | ---: | ---: | ---: | :---: | :---: |']
        for v in (r['variants'] or []):
            lines.append('| %s | %d | %.2f GiB | %.2f GiB | %d | %s | %s |' % (
                v['variant'], v['shards'], v['file_bytes'] / GiB,
                v['budget_after_files_bytes'] / GiB,
                v['max_independent_bf16_kv_requests'],
                '是' if v['files_fit_budget'] else '否',
                '是' if v['files_plus_one_kv_fit'] else '否'))
        lines.append('')
    open(os.path.join(RESULTS, 'capacity.md'), 'w').write('\n'.join(lines))
    print('\n'.join(lines))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
