#!/usr/bin/env python3
"""Verify official TOC membership and first-page titles, without marking papers read."""
from pathlib import Path
from datetime import datetime, timezone
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import hashlib
import json
import re
import subprocess
import unicodedata

ROOT = Path(__file__).resolve().parents[2]
REF = ROOT / 'references'
EXPECTED = {'OSDI': {2024: (53, 12), 2025: (53, 12), 2026: (136, 20)},
            'NSDI': {2024: (112, 17), 2025: (83, 16), 2026: (150, 24)}}
# These title variants were checked on physical PDF first pages.
PDF_TITLES = {
    'osdi24-li': 'Data-flow Availability: Achieving Timing Assurance on Autonomous Systems',
    'osdi25-guan': 'KPerfIR: Towards an Open and Compiler-centric Ecosystem for GPU Kernel Performance Tooling on Modern AI Workloads',
    'nsdi24-peng': 'UFO: The Ultimate QoS-Aware CPU Core Management for Virtualized and Oversubscribed Public Clouds',
    'osdi26-teguia': 'Inside Out: A Paradigm Shift In Live VM Introspection',
    'osdi26-leonhardi': 'PIMS: Fleet-wide Datacenter Maintenance with Minimal Capacity Buffer and Predictable Latency (Operational System)',
    'osdi26-sang': 'Unleash All Cores: Scalable Asymmetry-aware DNN Inference on Mobile CPUs',
}
NON_PAPERS = {'osdi26-keynote', 'nsdi26-keynote-vahdat'}
TEXT_VARIANTS = {'osdi26-athlur': 'Scaling the IO wall with eclarative IO'}


def norm(text):
    return ''.join(c.lower() for c in unicodedata.normalize('NFKD', text) if c.isalnum())


def checksum(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def verify(venue, year, expected, offset):
    directory = REF / f'proceedings/{venue}/{year}'
    path = directory / 'manifest.json'
    state = json.loads(path.read_text())
    assert state['status'] == 'downloaded'
    for item in [state['index'], *state['documents'].values()]:
        local = REF / item['file']
        assert local.stat().st_size == item['bytes'] and checksum(local) == item['sha256']
        if local.suffix == '.pdf':
            with local.open('rb') as stream:
                assert stream.read(5) == b'%PDF-'
            info = subprocess.check_output(['pdfinfo', str(local)], text=True,
                                           stderr=subprocess.PIPE, timeout=30)
            assert int(re.search(r'^Pages:\s+(\d+)', info, re.M)[1]) == item['pages']
            assert (REF / item['text']).stat().st_size > 100
    soup = BeautifulSoup((REF / state['index']['file']).read_bytes(), 'html.parser')
    public = {urljoin(state['index']['url'], a['href']) for a in soup.select('a[href]')}
    assert all(x['url'] in public for x in state['documents'].values())
    conference = venue.lower() + str(year)[-2:]
    program = {urljoin(state['index']['url'], a['href'])
               for a in soup.select('article.node-paper h2 a[href]')
               if a.get_text(' ', strip=True) and f'/conference/{conference}/presentation/' in a['href']}
    assert program == {x['source_page'] for x in state['entries']}
    contents = (REF / state['documents']['contents']['text']).read_text()
    chunks = list(re.finditer(r'([\s\S]*?)(?:\.\s*){3,}(\d+)\s*$', contents, re.M))
    assert len(chunks) == expected
    mapping = {}
    for chunk in chunks:
        matches = [x for x in state['entries'] if norm(x['title']) in norm(chunk[1])]
        assert len(matches) == 1, (venue, year, chunk[2], matches)
        assert matches[0]['id'] not in mapping
        mapping[matches[0]['id']] = int(chunk[2])
    assert len(mapping) == expected
    volume = state['documents']['volume']
    text = (REF / volume['text']).read_text()
    use_physical_extraction = text.count('\f') != volume['pages']
    pages = text.split('\f') if not use_physical_extraction else None
    notes = []
    if use_physical_extraction:
        notes.append(f'PDF has {volume["pages"]} pages but text has {text.count(chr(12))} formfeeds; '
                     'first pages verified by physical -f/-l extraction, not text offsets.')
    mismatches = []
    for entry in state['entries']:
        if entry['id'] not in mapping:
            assert entry['id'] in NON_PAPERS, entry
            entry.update(entry_type='keynote', paper_membership='not_in_proceedings_contents')
            continue
        printed = mapping[entry['id']]
        physical = printed + offset
        assert 1 <= physical <= volume['pages']
        if use_physical_extraction:
            page = subprocess.check_output(['pdftotext', '-raw', '-f', str(physical), '-l', str(physical),
                                            str(REF / volume['file']), '-'], text=True,
                                           stderr=subprocess.PIPE, timeout=30)
        else:
            page = pages[physical - 1]
        title = PDF_TITLES.get(entry['id'], entry['title'])
        searchable_title = TEXT_VARIANTS.get(entry['id'], title)
        if norm(searchable_title) not in norm(page):
            mismatches.append((entry['id'], physical, title, page[:240]))
            continue
        entry.update(entry_type='paper', paper_membership='verified_in_official_contents',
                     printed_start_page=printed, volume_start_page=physical,
                     first_page_title_verified=True)
        if title != entry['title']:
            entry['pdf_title'] = title
            notes.append(f'{entry["id"]}: official program/contents title differs from PDF; both retained.')
        if entry['id'] in TEXT_VARIANTS:
            notes.append(f'{entry["id"]}: decorative D in Declarative is absent from extracted text; '
                         'visually verified in qa/osdi26-athlur-title.png.')
    assert not mismatches, (venue, year, mismatches)
    state.update(expected_papers=expected, coverage_status='catalog_and_volume_first_pages_verified')
    state['coverage'] = {'verified_at': datetime.now(timezone.utc).isoformat(),
                         'index_sha256': state['index']['sha256'],
                         'contents_sha256': state['documents']['contents']['sha256'],
                         'volume_sha256': volume['sha256'], 'verified_papers': expected,
                         'non_paper_entries': len(state['entries']) - expected,
                         'physical_page_offset': offset, 'notes': notes,
                         'reading_scope': 'Archive coverage only; abstracts and full texts remain unread.'}
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + '\n')
    readme = directory / 'README.md'
    value = readme.read_text()
    value = re.sub(r'已归档整卷、目录及官方页面列出的勘误。.*?\n',
                   f'已归档整卷、目录及官方页面列出的勘误。官方目录 {expected} 篇与日程和整卷正文首页逐项核对；'
                   f'另有 {len(state["entries"]) - expected} 场 keynote 不计入论文数。尚未逐篇阅读。\n', value)
    readme.write_text(value)
    result = {'venue': venue, 'year': year, 'papers': expected, 'volume_pages': volume['pages'],
              'pdf_documents': len(state['documents']), 'pdf_bytes': sum(x['bytes'] for x in state['documents'].values()),
              'notes': notes}
    print(json.dumps(result, ensure_ascii=False), flush=True)
    return result


if __name__ == '__main__':
    rows = [verify(v, y, n, offset) for v, years in EXPECTED.items() for y, (n, offset) in years.items()]
    report = {'verified_at': datetime.now(timezone.utc).isoformat(), 'volumes': rows,
              'papers_covered': sum(x['papers'] for x in rows),
              'scope': 'Public volumes, official TOCs and first-page titles; not full-paper reading.'}
    (Path(__file__).parent / 'usenix-archive-audit.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
