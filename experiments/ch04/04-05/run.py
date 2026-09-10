#!/usr/bin/env python3
"""实验 4-5：batch 与架构性能。

把 batch 变大，会改变芯片比较的结果吗？

用 Qwen3-8B 与 DeepSeek-V4-Flash 的真实形状，在三家架构的选定代际上生成
Roofline 点；再分别只改变矩阵吞吐、存储带宽和非矩阵（向量／特殊函数）能力，
最后代入真实组合。prefill 与 decode、不同 batch 分开看。

工作量与设备规格全部由 `calculations/calc.py forward|v4-forward|roofline` 现场生成；
本实验只做本题的组织、判断与自绘 SVG。只依赖 Python 3 标准库。
"""
import json
import math
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
CALC = os.path.join(ROOT, 'calculations', 'calc.py')
RESULTS = os.path.join(HERE, 'results')
GiB = 2 ** 30

DEVICES = [
    ('a100-80gb-sxm', 'A100', 'BF16', 'FP32', 'tensor'),
    ('h100-sxm', 'H100', 'BF16', 'FP32', 'tensor'),
    ('b200-sxm', 'B200', 'BF16', 'FP32', 'tensor'),
    ('rtx-pro6000-blackwell-ws', 'RTX PRO 6000', 'BF16', 'FP32', 'tensor'),
]

# 场景：模型、阶段、batch、tokens、history
CASES = [
    ('qwen3-8b', 'prefill', 1, 8192, 0),
    ('qwen3-8b', 'decode', 1, 1, 8192),
    ('qwen3-8b', 'decode', 8, 1, 8192),
    ('qwen3-8b', 'decode', 64, 1, 8192),
    ('qwen3-8b', 'decode', 256, 1, 8192),
    ('deepseek-v4-flash', 'prefill', 1, 8192, 0),
    ('deepseek-v4-flash', 'decode', 1, 1, 8192),
    ('deepseek-v4-flash', 'decode', 64, 1, 8192),
]

# 统一计算项目把这两个参数定义为“效率”，不允许超过 1；因此单因子改动用“减半”表达，
# 与“另一项翻倍”在比值上等价。
VARIANTS = [('真实组合', 1.0, 1.0),
            ('只把矩阵吞吐减半', 0.5, 1.0),
            ('只把存储带宽减半', 1.0, 0.5)]


def run(args, out):
    path = os.path.join(RESULTS, out)
    proc = subprocess.run([sys.executable, CALC] + args + ['--format', 'json', '--output', path],
                          capture_output=True, text=True)
    if proc.returncode != 0:
        return None, (proc.stderr.strip().splitlines() or ['failed'])[-1]
    return json.load(open(path)), None


def work_of(model, batch, tokens, history):
    """取该场景的矩阵工作与必须的读写字节（各模型按自己的口径）。"""
    if model == 'qwen3-8b':
        doc, err = run(['forward', '--model', model, '--batch', str(batch),
                        '--tokens', str(tokens), '--history', str(history)],
                       'work-%s-b%d-t%d-h%d.json' % (model, batch, tokens, history))
        if doc is None:
            return None, err
        s = doc['summary']
        traffic = (s['weight_read_once_per_operator_bytes'] +
                   s['kv_attention_unique_payload_bytes'] + s['kv_new_write_bytes'])
        return dict(matrix_flops=s['matrix_flops'], traffic_bytes=traffic,
                    scalar_flops=s['scalar_flops'],
                    special_ops=sum(s['special_ops'].values())), None
    doc, err = run(['v4-forward', '--model', model, '--batch', str(batch),
                    '--tokens', str(tokens), '--history', str(history)],
                   'work-%s-b%d-t%d-h%d.json' % (model, batch, tokens, history))
    if doc is None:
        return None, err
    s = doc['summary']
    return dict(matrix_flops=s['matrix_flops_effective_attention'],
                traffic_bytes=s['uniform_bf16_parameter_bytes'] + s['state_resident_after_bytes'],
                scalar_flops=s['accounted_scalar_flops'],
                special_ops=sum(s['accounted_special_ops'].values())), None


def svg(path, points, devices):
    """自绘 Roofline：横轴算术强度，纵轴可达吞吐；每台设备一条折线。"""
    w, h = 900, 560
    l, r, t, b = 80, 30, 60, 70
    xs = [p['intensity'] for p in points if p['intensity'] > 0]
    lo_x, hi_x = min(xs) / 3, max(xs) * 3
    hi_y = max(d['peak_flops'] for d in devices) * 1.4
    lo_y = min(d['bandwidth'] * lo_x for d in devices) / 3

    def X(v):
        return l + (math.log10(v) - math.log10(lo_x)) / (math.log10(hi_x) - math.log10(lo_x)) * (w - l - r)

    def Y(v):
        return h - b - (math.log10(v) - math.log10(lo_y)) / (math.log10(hi_y) - math.log10(lo_y)) * (h - t - b)

    colors = ['#3d5a80', '#c1666b', '#4c956c', '#9c6644']
    out = ['<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d" '
           'font-family="Helvetica,Arial,sans-serif">' % (w, h, w, h),
           '<rect width="%d" height="%d" fill="#ffffff"/>' % (w, h),
           '<text x="30" y="34" font-size="16" font-weight="600">Roofline：Qwen3-8B 与 V4-Flash 在四种架构上的 prefill／decode</text>']
    for i, d in enumerate(devices):
        c = colors[i % len(colors)]
        ridge = d['peak_flops'] / d['bandwidth']
        pts = [(lo_x, d['bandwidth'] * lo_x), (ridge, d['peak_flops']), (hi_x, d['peak_flops'])]
        path_d = ' '.join(('M' if j == 0 else 'L') + '%.1f,%.1f' % (X(x), Y(y))
                          for j, (x, y) in enumerate(pts))
        out.append('<path d="%s" fill="none" stroke="%s" stroke-width="2"/>' % (path_d, c))
        out.append('<text x="%.1f" y="%.1f" font-size="12" fill="%s">%s</text>'
                   % (X(hi_x) - 90, Y(d['peak_flops']) - 6, c, d['label']))
    for p in points:
        c = colors[[d['id'] for d in devices].index(p['device']) % len(colors)]
        x, y = X(p['intensity']), Y(p['attainable'])
        out.append('<circle cx="%.1f" cy="%.1f" r="4" fill="%s" opacity="0.9"/>' % (x, y, c))
        if p['label_it']:
            out.append('<text x="%.1f" y="%.1f" font-size="10" fill="#33475b">%s</text>'
                       % (x + 6, y - 4, p['tag']))
    for v in (1, 10, 100, 1000, 10000):
        if lo_x <= v <= hi_x:
            out.append('<line x1="%.1f" y1="%d" x2="%.1f" y2="%d" stroke="#e2e6ea"/>'
                       % (X(v), t, X(v), h - b))
            out.append('<text x="%.1f" y="%d" font-size="11" text-anchor="middle" fill="#5a6b7d">%d</text>'
                       % (X(v), h - b + 18, v))
    for v in (1e12, 1e13, 1e14, 1e15):
        if lo_y <= v <= hi_y:
            out.append('<line x1="%d" y1="%.1f" x2="%d" y2="%.1f" stroke="#e2e6ea"/>'
                       % (l, Y(v), w - r, Y(v)))
            out.append('<text x="%d" y="%.1f" font-size="11" text-anchor="end" fill="#5a6b7d">%g T</text>'
                       % (l - 6, Y(v) + 4, v / 1e12))
    out.append('<text x="%d" y="%d" font-size="12" fill="#33475b">算术强度（FLOPs/byte）</text>' % (w // 2 - 60, h - 20))
    out.append('<text x="18" y="%d" font-size="12" fill="#33475b" transform="rotate(-90 18 %d)">可达吞吐（FLOPs/s）</text>' % (h // 2, h // 2))
    out.append('</svg>')
    open(path, 'w').write('\n'.join(out))


def main() -> int:
    os.makedirs(RESULTS, exist_ok=True)
    works = {}
    for model, phase, batch, tokens, history in CASES:
        wk, err = work_of(model, batch, tokens, history)
        if wk is None:
            sys.exit('工作量调用失败：%s %s：%s' % (model, phase, err))
        works[(model, phase, batch)] = wk

    rows = []
    device_info = []
    for dev, label, prec, acc, unit in DEVICES:
        got_peak = False
        for (model, phase, batch), wk in works.items():
            for vname, cmul, bmul in VARIANTS:
                doc, err = run(['roofline', '--device', dev,
                                '--flops', str(int(wk['matrix_flops'])),
                                '--traffic-bytes', str(int(wk['traffic_bytes'])),
                                '--precision', prec, '--accumulator', acc,
                                '--unit', unit, '--sparsity', 'dense',
                                '--compute-efficiency', str(cmul),
                                '--bandwidth-efficiency', str(bmul)],
                               'rl-%s-%s-%s-b%d-%s.json' % (dev, model, phase, batch,
                                                            vname.replace(' ', '')))
                if doc is None:
                    continue
                s = doc['summary']
                peak = doc['selected_peak']['tera_ops_per_second'] * 1e12 * cmul
                if not got_peak and vname == '真实组合':
                    device_info.append(dict(id=dev, label=label, peak_flops=peak,
                                            bandwidth=wk['traffic_bytes'] / s['memory_service_seconds']))
                    got_peak = True
                rows.append(dict(device=dev, device_label=label, model=model, phase=phase,
                                 batch=batch, variant=vname,
                                 intensity=s['arithmetic_intensity_flops_per_byte'],
                                 ridge=s['ridge_point_flops_per_byte'],
                                 compute_seconds=s['compute_service_seconds'],
                                 memory_seconds=s['memory_service_seconds'],
                                 lower_bound_seconds=s['resource_time_lower_bound_seconds'],
                                 attainable=s['throughput_upper_bound_flops_per_second'],
                                 dominant='compute' if s['compute_service_seconds'] >= s['memory_service_seconds'] else 'memory',
                                 scalar_flops=works[(model, phase, batch)]['scalar_flops'],
                                 special_ops=works[(model, phase, batch)]['special_ops']))

    points = [dict(device=r['device'], intensity=r['intensity'], attainable=r['attainable'],
                   tag='%s b%d' % (r['phase'][:2], r['batch']),
                   label_it=(r['device'] == 'h100-sxm' and r['model'] == 'qwen3-8b'))
              for r in rows if r['variant'] == '真实组合']
    svg(os.path.join(RESULTS, 'roofline.svg'), points, device_info)

    result = dict(schema_version=1, experiment='4-5', title='batch 与架构性能',
                  source_note='由 calculations/calc.py 现场生成；倍数是假设的供给变化，不是别的型号。',
                  works={'%s|%s|%d' % k: v for k, v in works.items()},
                  rows=rows, devices=device_info, python_version=sys.version)
    json.dump(result, open(os.path.join(RESULTS, 'roofline.json'), 'w'), indent=2, ensure_ascii=False)

    lines = ['# 实验 4-5 结果：batch 与架构性能', '',
             '## 真实组合下的算术强度与主导资源', '',
             '| 模型 | 阶段 | batch | 算术强度 | H100 脊点 | A100 | H100 | B200 | RTX PRO 6000 |',
             '| --- | --- | ---: | ---: | ---: | --- | --- | --- | --- |']
    keys = sorted({(r['model'], r['phase'], r['batch']) for r in rows},
                  key=lambda k: (k[0], k[1], k[2]))
    for model, phase, batch in keys:
        sel = {r['device_label']: r for r in rows
               if r['variant'] == '真实组合' and (r['model'], r['phase'], r['batch']) == (model, phase, batch)}
        any_row = next(iter(sel.values()))
        cells = []
        for lbl in ('A100', 'H100', 'B200', 'RTX PRO 6000'):
            r = sel.get(lbl)
            cells.append('%s %.2f ms' % ('计算' if r['dominant'] == 'compute' else '访存',
                                         r['lower_bound_seconds'] * 1e3) if r else '—')
        h100 = sel.get('H100')
        lines.append('| %s | %s | %d | %.1f | %.1f | %s |' % (
            model, phase, batch, any_row['intensity'],
            h100['ridge'] if h100 else 0, ' | '.join(cells)))
    lines += ['', '## 单因子改动：只改矩阵吞吐 / 只改存储带宽（H100）', '',
              '| 模型 | 阶段 | batch | 真实组合 | 矩阵吞吐减半 | 存储带宽减半 |',
              '| --- | --- | ---: | ---: | ---: | ---: |']
    for model, phase, batch in keys:
        got = {r['variant']: r for r in rows
               if r['device'] == 'h100-sxm' and (r['model'], r['phase'], r['batch']) == (model, phase, batch)}
        if len(got) < 3:
            continue
        lines.append('| %s | %s | %d | %.2f ms | %.2f ms | %.2f ms |' % (
            model, phase, batch,
            got['真实组合']['lower_bound_seconds'] * 1e3,
            got['只把矩阵吞吐减半']['lower_bound_seconds'] * 1e3,
            got['只把存储带宽减半']['lower_bound_seconds'] * 1e3))
    lines += ['', '## 非矩阵工作（不折算成矩阵吞吐）', '',
              '| 模型 | 阶段 | batch | 标量 GFLOPs | 特殊函数原语次数 |',
              '| --- | --- | ---: | ---: | ---: |']
    for model, phase, batch in keys:
        wk = works[(model, phase, batch)]
        lines.append('| %s | %s | %d | %.2f | %.4g |' % (
            model, phase, batch, wk['scalar_flops'] / 1e9, wk['special_ops']))
    lines += ['', '![Roofline](roofline.svg)', '']
    open(os.path.join(RESULTS, 'roofline.md'), 'w').write('\n'.join(lines))
    print('\n'.join(lines))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
