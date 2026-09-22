#!/usr/bin/env python3
"""Verify structural integrity of the Traditional Chinese edition against manuscripts."""
import re
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent.parent / 'manuscripts'
DEST = Path(__file__).resolve().parent.parent

mapping = [
    (SRC / '00-前言.md', DEST / 'introduction.md'),
    (SRC / '01-初识 AI Infra.md', DEST / 'chapter01.md'),
    (SRC / '02-模型架构.md', DEST / 'chapter02.md'),
    (SRC / '03-推理与训练负载.md', DEST / 'chapter03.md'),
    (SRC / '04-加速器架构.md', DEST / 'chapter04.md'),
    (SRC / '05-算子与运行时.md', DEST / 'chapter05.md'),
    (SRC / '06-超节点.md', DEST / 'chapter06.md'),
    (SRC / '07-数据中心网络.md', DEST / 'chapter07.md'),
    (SRC / '08-推理优化.md', DEST / 'chapter08.md'),
    (SRC / '09-分布式推理.md', DEST / 'chapter09.md'),
    (SRC / '10-训练系统.md', DEST / 'chapter10.md'),
    (SRC / '11-资源调度与运行环境.md', DEST / 'chapter11.md'),
    (SRC / '12-端边云协同.md', DEST / 'chapter12.md'),
]

all_ok = True
for s, d in mapping:
    s_text = s.read_text('utf-8')
    d_text = d.read_text('utf-8')

    s_math = len(re.findall(r'\$\$[\s\S]*?\$\$', s_text))
    d_math = len(re.findall(r'\$\$[\s\S]*?\$\$', d_text))
    s_inline_math = len(re.findall(r'\$[^\$\n]+\$', s_text))
    d_inline_math = len(re.findall(r'\$[^\$\n]+\$', d_text))
    s_code = len(re.findall(r'```[\s\S]*?```', s_text))
    d_code = len(re.findall(r'```[\s\S]*?```', d_text))
    s_imgs = len(re.findall(r'!\[.*?\]\(.*?\)', s_text))
    d_imgs = len(re.findall(r'!\[.*?\]\(.*?\)', d_text))

    diffs = []
    if s_math != d_math: diffs.append(f'display math {s_math}!={d_math}')
    if s_inline_math != d_inline_math: diffs.append(f'inline math {s_inline_math}!={d_inline_math}')
    if s_code != d_code: diffs.append(f'code blocks {s_code}!={d_code}')
    if s_imgs != d_imgs: diffs.append(f'images {s_imgs}!={d_imgs}')

    if diffs:
        all_ok = False
        print(f'MISMATCH in {d.name}: {diffs}')
    else:
        print(f'{d.name}: OK (math: {d_math}, inline_math: {d_inline_math}, code: {d_code}, imgs: {d_imgs})')

if all_ok:
    print('>>> ALL 13 CHAPTERS PERFECTLY MATCH ORIGINAL STRUCTURE!')
