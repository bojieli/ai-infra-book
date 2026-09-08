#!/usr/bin/env python3
"""Persist manual abstract decisions without changing archive/coverage evidence."""
import argparse
import csv
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[2]
parser = argparse.ArgumentParser()
parser.add_argument('--venue', choices=['OSDI', 'NSDI'], required=True)
parser.add_argument('--year', type=int, choices=[2024, 2025, 2026], required=True)
parser.add_argument('--date', default=datetime.now(ZoneInfo('Asia/Singapore')).date().isoformat())
args = parser.parse_args()
directory = ROOT / 'references/proceedings' / args.venue / str(args.year)
manifest = directory / 'manifest.json'
state = json.loads(manifest.read_text())
papers = [p for p in state['entries'] if p.get('entry_type') == 'paper']
stem = f'{args.venue.lower()}-{args.year}'
rows = list(csv.DictReader((Path(__file__).parent / f'screening-{stem}.tsv').open(), delimiter='\t'))
assert [int(r['number']) for r in rows] == list(range(1, len(rows) + 1))
assert len(rows) <= len(papers)
for row, paper in zip(rows, papers):
    assert paper['abstract'].strip() and paper['first_page_title_verified']
    old = paper.get('screening', {})
    paper['screening'] = dict(date=old.get('date', args.date),
                              basis='title_and_full_abstract',
                              decision=row['decision'], reason=row['reason'])
    if 'selected_reading' not in paper:
        paper['reading_status'] = 'abstract_screened'
state['updated_at'] = datetime.now(timezone.utc).isoformat()
manifest.write_text(json.dumps(state, ensure_ascii=False, indent=2) + '\n')
selected = [p for p in papers if 'selected_reading' in p]
readme = directory / 'README.md'
if readme.exists():
    summary = (f'已按正式论文顺序筛读 {len(rows)}／{len(papers)} 篇完整摘要，'
               f'{len(selected)} 篇补读所列正文；范围见'
               f'[阅读记录](../../../../research/2026-infra-survey/reading-{stem}.md)，'
               '不表示全卷全文已读。')
    updated, count = re.subn(r'(不计入论文数。)[^\n]*', lambda m: m[1] + summary,
                             readme.read_text(), count=1)
    assert count == 1, readme
    readme.write_text(updated)
lines = [f'# {args.venue} {args.year}：摘要筛选与重点阅读', '',
         f'已按官方日程中的正式论文顺序阅读 {len(rows)}／{len(papers)} 篇完整摘要；'
         f'{len(selected)} 篇补读所列正文。下载、首页核对、摘要筛选和正文阅读分别记录。', '',
         f'[逐项手工取舍](screening-{stem}.tsv)与[归档清单](../../references/proceedings/{args.venue}/{args.year}/manifest.json)同步。', '',
         '| 序号与论文 | 本轮取舍 | 原因与位置 |', '| --- | --- | --- |']
for row, paper in zip(rows, papers):
    path = f'../../references/proceedings/{args.venue}/{args.year}/volume.pdf#page={paper["volume_start_page"]}'
    title = paper['title'].replace('|', '\\|')
    lines.append(f'| {row["number"]}. [{title}]({path}) | {row["decision"]} | {row["reason"]} |')
lines += ['', '## 重点章节与采用边界', '']
for paper in selected:
    r = paper['selected_reading']
    lines.append(f'- **{paper["title"]}**：{r["scope"]}；'
                 f'原整卷物理页 {", ".join(map(str, r["volume_physical_pages"]))}。')
    if r.get('version_note'):
        lines.append(f'  {r["version_note"]}')
if not selected:
    lines.append('当前只完成上述摘要筛选，候选须与既有材料比较并补读正文；未登记任何新增全文阅读。')
lines += ['', '具体推算和采用决策另记案例笔记；新增候选不自动进入正文。历史实验的模型、软件、硬件和质量条件保持原样，本书贯穿模型继续使用 Qwen3／V4／K3。', '']
(Path(__file__).parent / f'reading-{stem}.md').write_text('\n'.join(lines))
print(json.dumps(dict(venue=args.venue, year=args.year, abstract_screens=len(rows),
                      selected_sections=len(selected)), ensure_ascii=False))
