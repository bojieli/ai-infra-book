#!/usr/bin/env python3
"""Check the book's current structure, generated view, links and preserved evidence."""
from collections import Counter
from pathlib import Path
from urllib.parse import unquote, urlsplit
import csv
import hashlib
import html
import json
import re
import tarfile
from outline_text import rendered_inline

ROOT = Path(__file__).resolve().parents[1]
OUTLINES = ROOT / 'outlines'
REVISION = ROOT / 'research/outline-revision-2026-09-08'
errors = []


def check(condition, message):
    if not condition:
        errors.append(message)


def anchors(path):
    text = path.read_text()
    explicit = re.findall(r'\bid=["\']([^"\']+)', text)
    if path.suffix == '.md':
        seen = Counter()
        for heading in re.findall(r'^#{1,6} (.+)', text, re.M):
            heading = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', heading)
            heading = re.sub(r'<[^>]+>', '', heading)
            slug = re.sub(r'[^\w\-\s]', '', heading.lower(), flags=re.U).replace(' ', '-')
            count = seen[slug]
            seen[slug] += 1
            explicit.append(slug + (f'-{count}' if count else ''))
    return set(explicit)


catalog = json.loads((OUTLINES / 'chapters.json').read_text())
check([c['number'] for c in catalog] == list(range(1, 14)), 'Chapter catalog order')
check({c['file'] for c in catalog} == {p.name for p in OUTLINES.glob('[0-9][0-9]-*.md')}, 'Chapter file set')
counts = Counter()
all_labs = set()
all_figures = set()
all_sections = set()
page = (ROOT / 'skeleton.html').read_text()


for c in catalog:
    n = c['number']
    p = OUTLINES / c['file']
    s = p.read_text()
    check(s.startswith(f'# 第 {n} 章 {c["title"]}\n'), f'{p.name}: title')
    check(all(0 < prior < n for prior in c['prerequisites']), f'{p.name}: forward prerequisite')
    for label in ['本章判断', '前置与交付', '阅读安排', '## 本章的设计决定', '## 写作资料']:
        check(label in s, f'{p.name}: missing {label}')
    sections = re.findall(r'^## (\d+\.\d+) ', s, re.M)
    check(sections == [f'{n}.{i}' for i in range(1, len(sections) + 1)], f'{p.name}: section numbering')
    subs = []
    for sec in sections:
        found = re.findall(r'^### (' + re.escape(sec) + r'\.\d+) ', s, re.M)
        check(found == [f'{sec}.{i}' for i in range(1, len(found) + 1)], f'{p.name}: subsection numbering {sec}')
        subs.extend(found)
    all_sections.update(sections + subs)
    for word, key, target in [('实验', 'experiments', all_labs), ('图', 'figures', all_figures)]:
        identifiers = re.findall(r'^> \*\*' + word + r' (\d+-\d+)', s, re.M)
        check(identifiers == [f'{n}-{i}' for i in range(1, len(identifiers) + 1)], f'{p.name}: {word} order')
        target.update(identifiers)
        counts[key] += len(identifiers)
    cores = re.findall(r'^> \*\*实验 (\d+-\d+)[^\n]*〔核心〕', s, re.M)
    check(cores == c['core_experiments'] and len(cores) == 3, f'{p.name}: core selection')
    check(len(re.findall(r'^> \*\*实验 [^\n]*〔(?:核心|延伸)〕', s, re.M)) == len(re.findall(r'^> \*\*实验 ', s, re.M)), f'{p.name}: lab classification')
    counts.update(sections=len(sections), subsections=len(subs), core=len(cores))
    check(f'id="ch-{n}"' in page and f'{n:02d} · {html.escape(c["title"])}' in page, f'{p.name}: HTML navigation')
    for sec in sections + subs:
        check(f'id="sec-{sec.replace(".", "-")}"' in page, f'{p.name}: HTML section {sec}')
    article = re.search(r'<article class="card" id="ch-' + str(n) + r'">(.*?)</article>', page, re.S)
    visible = html.unescape(re.sub(r'<[^>]+>', '', article[1])) if article else ''
    for paragraph in s.split('## 写作资料', 1)[0].split('\n\n')[2:]:
        if paragraph.startswith(('#', '>')):
            continue
        check(rendered_inline(paragraph.replace('\n', ' ')) in visible, f'{p.name}: stale HTML paragraph {paragraph[:45]}')
    companion = OUTLINES / 'extensions' / c['file']
    check(companion.exists(), f'{p.name}: companion')
    if n not in (1, 13):
        companion_text = companion.read_text()
        for sec in sections + subs:
            check(f'id="detail-{sec}"' in companion_text, f'{p.name}: companion anchor {sec}')

check(page.count('<h4>本章的设计决定</h4>') == 13, 'HTML chapter decisions')
ids = re.findall(r'\bid=["\']([^"\']+)', page)
check(len(ids) == len(set(ids)), 'Duplicate HTML IDs')
for p in OUTLINES.glob('[0-9][0-9]-*.md'):
    text = p.read_text()
    for word, valid in [('实验', all_labs), ('图', all_figures)]:
        for identifier in re.findall(word + r' (\d+-\d+)', text):
            check(identifier in valid, f'{p.name}: undefined {word} {identifier}')

# All current writing surfaces; source snapshots and historical reports retain their own anchors.
active = [ROOT / 'README.md', ROOT / 'skeleton.html', *OUTLINES.rglob('*.md'),
          *ROOT.glob('case-studies/*.md'), ROOT / 'references/README.md',
          ROOT / 'references/INFERENCE-PAPER-GUIDE.md', REVISION / 'README.md']
anchor_cache = {}
link_count = 0
for p in active:
    s = p.read_text()
    urls = re.findall(r'\]\(([^)]+)\)', s) if p.suffix == '.md' else re.findall(r'\bhref=["\']([^"\']+)', s)
    for url in urls:
        url = html.unescape(url).strip('<>')
        if re.match(r'\w+:|//', url):
            continue
        parts = urlsplit(url)
        target = (p.parent / unquote(parts.path)).resolve() if parts.path else p
        if target == REVISION / 'validation.json':
            continue  # This run writes the report after checking.
        link_count += 1
        if not target.exists():
            errors.append(f'{p.relative_to(ROOT)}: missing link {url}')
        elif parts.fragment and target.suffix in ('.md', '.html'):
            if target not in anchor_cache:
                anchor_cache[target] = anchors(target)
            check(unquote(parts.fragment) in anchor_cache[target], f'{p.relative_to(ROOT)}: missing anchor {url}')

with (ROOT / 'references/inference-reading-map.tsv').open() as f:
    for row in csv.DictReader(f, delimiter='\t'):
        for position in row['sections'].split(','):
            check(position in all_sections or position in {str(i) for i in range(1, 14)}, f'Reading map {row["id"]}: {position}')
with (ROOT / 'references/sources.tsv').open() as f:
    sources = {r['id']: [int(n) for n in r['chapters'].split(',')] for r in csv.DictReader(f, delimiter='\t')}
manifest = json.loads((ROOT / 'references/manifest.json').read_text())
hash_count = 0
for source in manifest:
    check(source['chapters'] == sources[source['id']], f'Catalog mismatch {source["id"]}')
    if source.get('file') and source.get('sha256'):
        p = ROOT / 'references' / source['file']
        check(hashlib.sha256(p.read_bytes()).hexdigest() == source['sha256'], f'Source changed {p}')
        hash_count += 1

before_manifest = json.loads((REVISION / 'before-manifest.json').read_text())
with tarfile.open(REVISION / 'before.tar.gz') as archive:
    for record in before_manifest:
        data = archive.extractfile(record['path']).read()
        check(hashlib.sha256(data).hexdigest() == record['sha256'], f'Before snapshot changed {record["path"]}')
    for c in catalog:
        old_name = f'outlines/{c["previous_number"]:02d}-' + c['file'][3:]
        original = archive.extractfile(old_name).read().decode()
        companion = (OUTLINES / 'extensions' / c['file']).read_text()
        for pattern, kind in [(r'^### ', 'subsections'), (r'^> \*\*实验 ', 'experiments'), (r'^> \*\*图 ', 'figures')]:
            check(len(re.findall(pattern, original, re.M)) == len(re.findall(pattern, companion, re.M)), f'{c["file"]}: incomplete companion {kind}')

report = dict(status='passed' if not errors else 'failed', chapters=len(catalog), **counts,
              local_links_checked=link_count, reference_hashes_checked=hash_count,
              snapshot_files_checked=len(before_manifest), errors=errors)
(REVISION / 'validation.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
print(json.dumps(report, ensure_ascii=False, indent=2))
raise SystemExit(bool(errors))
