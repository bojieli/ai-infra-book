#!/usr/bin/env python3
"""实验 12-1：图片精修的传输与计算预算。

用原图和成片的实际字节（或给定元数据）计算上传、执行与回传；
扫描上行带宽、处理速度和压缩开销，比较**减少字节、复用连接、加速模型**
各省多少时间。输入与成片的业务要求保持一致。

本实验不重算：由 `calculations/calc.py image-request-budget` 现场生成。
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

BASE = dict(input_bytes=30_000_000, output_bytes=5_000_000,
            upload_bits_per_second=20_000_000, download_bits_per_second=100_000_000,
            preparation_seconds='0', connection_seconds='1/5',
            request_rtt_seconds='1/10', queue_seconds='0',
            input_decode_seconds='0', model_seconds='3/10',
            output_encode_seconds='0', output_use_seconds='0', local_seconds='5',
            compression=dict(transmitted_bytes=15_000_000,
                             extra_encode_seconds='1/5', extra_decode_seconds='1/10',
                             comparison_authorized=True,
                             quality_contract='same original information and same final-image requirement'),
            quality_contract='same original information and same final-image requirement',
            metadata_kind='declared_teaching', input_format='RAW', output_format='JPEG')

CASES = [
    ('基线：20 Mb/s 上行、建连 0.2 s、模型 0.3 s', {}),
    ('上行 5 Mb/s', dict(upload_bits_per_second=5_000_000)),
    ('上行 100 Mb/s', dict(upload_bits_per_second=100_000_000)),
    ('上行 1 Gb/s', dict(upload_bits_per_second=1_000_000_000)),
    ('模型加速到 0.1 s', dict(model_seconds='1/10')),
    ('模型变慢到 3 s', dict(model_seconds='3')),
    ('建连开销 0（复用连接）', dict(connection_seconds='0')),
    ('压缩到 1/4（7.5 MB，编码 0.4 s）',
     dict(compression=dict(BASE['compression'], transmitted_bytes=7_500_000,
                           extra_encode_seconds='2/5'))),
]


def main() -> int:
    os.makedirs(RESULTS, exist_ok=True)
    rows = []
    for i, (label, over) in enumerate(CASES):
        cfg = dict(BASE)
        cfg.update(over)
        ipath = os.path.join(RESULTS, 'input-%d.json' % i)
        opath = os.path.join(RESULTS, 'budget-%d.json' % i)
        json.dump(cfg, open(ipath, 'w'), indent=1)
        proc = subprocess.run([sys.executable, CALC, 'image-request-budget', '--inputs', ipath,
                               '--format', 'json', '--output', opath],
                              capture_output=True, text=True)
        if proc.returncode != 0:
            rows.append(dict(label=label, error=(proc.stderr.strip().splitlines() or [''])[-1]))
            continue
        doc = json.load(open(opath))
        variants = {vv['variant']: vv for vv in doc['variants']}
        rows.append(dict(label=label, scenario=cfg, variants=variants,
                         comparison=doc.get('compression_comparison')))

    result = dict(schema_version=1, experiment='12-1', title='图片精修的传输与计算预算',
                  base=BASE, rows=rows,
                  source_note='由 calculations/calc.py image-request-budget 现场生成；'
                              '文件字节与各阶段时间均为声明输入，不执行编解码或模型。',
                  python_version=sys.version)
    json.dump(result, open(os.path.join(RESULTS, 'budget.json'), 'w'), indent=2, ensure_ascii=False)

    def secs(v, key):
        val = v.get(key)
        return float(F(val)) if isinstance(val, str) else (val if val is not None else None)

    lines = ['# 实验 12-1 结果：图片精修的传输与计算预算', '',
             '原图 %.0f MB、成片 %.0f MB；本地处理声明为 %s 秒。' % (
                 BASE['input_bytes'] / MB, BASE['output_bytes'] / MB, BASE['local_seconds']), '',
             '| 情形 | 变体 | 上传 | 模型 | 下载 | 完整成片 | 复用连接后 |',
             '| --- | --- | ---: | ---: | ---: | ---: | ---: |']
    for r in rows:
        if 'error' in r:
            lines.append('| %s | 调用失败：%s | — | — | — | — | — |' % (r['label'], r['error']))
            continue
        for name, v in r['variants'].items():
            stages = {st['stage']: st for st in v['stages']}
            lines.append('| %s | %s | %.3f s | %.3f s | %.3f s | **%.3f s** | %.3f s |' % (
                r['label'], name,
                float(F(stages['upload']['duration_seconds_exact'])),
                float(F(stages['model']['duration_seconds_exact'])),
                float(F(stages['download']['duration_seconds_exact'])),
                float(F(v['complete_final_image_seconds_exact'])),
                float(F(v['reused_connection_final_seconds_exact']))))
    lines.append('')
    open(os.path.join(RESULTS, 'budget.md'), 'w').write('\n'.join(lines))
    print('\n'.join(lines))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
