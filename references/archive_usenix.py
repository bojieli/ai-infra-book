#!/usr/bin/env python3
"""Archive public USENIX volumes and program entries; reading is tracked separately.

The program is not assumed to contain only refereed papers. Its entries must be
checked against the archived table of contents before claiming paper coverage.
Only publicly linked proceedings, contents and errata are downloaded.
"""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import urljoin, urlparse
import argparse
import hashlib
import json
import re
import subprocess
import time

import requests
from bs4 import BeautifulSoup
from archive_proceedings import ROOT, UA, get, now, record, save_json


def valid(item):
    path = ROOT / item.get('file', 'MISSING')
    if not path.is_file() or path.stat().st_size != item.get('bytes'):
        return False
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest() == item.get('sha256')


def pdf(url, dest, old):
    if valid(old) and old.get('text') and (ROOT / old['text']).is_file():
        return old
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix('.pdf.part')
    if valid(old):
        item = dict(old)
    else:
        for attempt in range(3):
            try:
                digest = hashlib.sha256()
                size = 0
                with requests.get(url, headers=UA, stream=True, timeout=(15, 60)) as response:
                    response.raise_for_status()
                    with tmp.open('wb') as out:
                        for chunk in response.iter_content(1024 * 1024):
                            if not chunk:
                                continue
                            if size == 0 and not chunk.startswith(b'%PDF-'):
                                raise ValueError('Response is not a PDF')
                            out.write(chunk)
                            digest.update(chunk)
                            size += len(chunk)
                    if size == 0:
                        raise ValueError('Empty PDF')
                    declared = response.headers.get('Content-Length')
                    if declared and not response.headers.get('Content-Encoding') and int(declared) != size:
                        raise ValueError('Incomplete response')
                    item = dict(file=str(dest.relative_to(ROOT)), url=url,
                                final_url=response.url, bytes=size,
                                sha256=digest.hexdigest(), retrieved_at=now())
                tmp.replace(dest)
                break
            except Exception:
                tmp.unlink(missing_ok=True)
                if attempt == 2:
                    raise
                time.sleep(attempt + 1)
    info = subprocess.run(['pdfinfo', str(dest)], check=True, capture_output=True,
                          text=True, timeout=60).stdout
    item['pages'] = int(re.search(r'^Pages:\s+(\d+)', info, re.M)[1])
    text = dest.with_suffix('.txt')
    subprocess.run(['pdftotext', '-layout', str(dest), str(text)], check=True,
                   capture_output=True, timeout=240)
    if text.stat().st_size < 100:
        raise ValueError('Searchable text missing')
    item['text'] = str(text.relative_to(ROOT))
    return item


def archive(conference):
    match = re.fullmatch(r'(osdi|nsdi)(24|25|26)', conference)
    if not match:
        raise ValueError('Expected osdi24..26 or nsdi24..26')
    venue, year = match[1].upper(), 2000 + int(match[2])
    directory = ROOT / 'proceedings' / venue / str(year)
    directory.mkdir(parents=True, exist_ok=True)
    manifest = directory / 'manifest.json'
    state = json.loads(manifest.read_text()) if manifest.exists() else {}
    url = f'https://www.usenix.org/conference/{conference}/technical-sessions'
    try:
        if valid(state.get('index', {})):
            data = (ROOT / state['index']['file']).read_bytes()
        else:
            response = get(url)
            data = response.content
            state['index'] = record(directory / 'index.html', data, url, response.url)
        soup = BeautifulSoup(data, 'html.parser')
        previous = {p['source_page']: p for p in state.get('entries', [])}
        entries = {}
        for article in soup.select('article.node-paper'):
            title = article.select_one('h2 a[href]')
            if not title or not title.get_text(' ', strip=True):
                continue
            if f'/conference/{conference}/presentation/' not in title['href']:
                continue
            source = urljoin(url, title['href'])
            row = dict(previous.get(source, {}))
            desc = article.select_one('.field-name-field-paper-description-long')
            authors = article.select_one('.field-name-field-paper-people-text')
            row.update(id=conference + '-' + source.rsplit('/', 1)[-1],
                       title=title.get_text(' ', strip=True), source_page=source,
                       abstract=desc.get_text('\n', strip=True) if desc else '',
                       authors=authors.get_text(' ', strip=True) if authors else '')
            row.setdefault('reading_status', 'unread')
            row.setdefault('paper_membership', 'not_yet_checked_against_contents')
            entries[source] = row
        files = {}
        for anchor in soup.select('a[href]'):
            link = urljoin(url, anchor['href'])
            name = Path(urlparse(link).path).name
            if re.search(r'full[-_]proceedings\.pdf$', name, re.I):
                files['volume'] = link
            elif re.search(r'contents\.pdf$', name, re.I):
                files['contents'] = link
            elif 'errata' in name.lower() and name.lower().endswith('.pdf'):
                files['errata-' + name.removesuffix('.pdf')] = link
        if 'volume' not in files or 'contents' not in files:
            raise ValueError('Official program lacks expected public volume/contents links')
        state.update(venue=venue, year=year, catalog_entries=len(entries),
                     entries=list(entries.values()), updated_at=now(),
                     coverage_status='program_membership_not_yet_checked_against_contents',
                     status='downloading')
        state.setdefault('documents', {})
        save_json(manifest, state)
        print(f'{conference}: {len(entries)} program entries; {len(files)} public PDFs', flush=True)
        for key, source in files.items():
            destination = directory / (key + '.pdf')
            state['documents'][key] = pdf(source, destination, state['documents'].get(key, {}))
            state['updated_at'] = now()
            save_json(manifest, state)
            item = state['documents'][key]
            print(f'{conference}: {key}, {item["pages"]} pages, {item["bytes"]} bytes', flush=True)
        state.update(status='downloaded', updated_at=now())
        coverage = state.get('coverage', {})
        if (coverage.get('index_sha256') == state['index']['sha256']
                and coverage.get('contents_sha256') == state['documents']['contents']['sha256']
                and coverage.get('volume_sha256') == state['documents']['volume']['sha256']):
            state['coverage_status'] = 'catalog_and_volume_first_pages_verified'
            description = (f'官方目录 {coverage["verified_papers"]} 篇与日程和整卷正文首页逐项核对；'
                           f'另有 {coverage["non_paper_entries"]} 场 keynote 不计入论文数。')
            papers = [p for p in state['entries'] if p.get('entry_type') == 'paper']
            screened = sum('screening' in p for p in papers)
            selected = sum('selected_reading' in p for p in papers)
            if screened:
                description += (f'已逐篇筛选 {screened} 篇完整摘要，{selected} 篇补读所列正文；'
                                f'范围见[阅读记录](../../../../research/2026-infra-survey/reading-{venue.lower()}-{year}.md)，不表示全卷全文已读。')
            else:
                description += '尚未逐篇筛选摘要。'
        else:
            state.pop('coverage', None)
            state.pop('expected_papers', None)
            for entry in state['entries']:
                for key in ['entry_type', 'printed_start_page', 'volume_start_page', 'first_page_title_verified', 'pdf_title']:
                    entry.pop(key, None)
                entry['paper_membership'] = 'not_yet_checked_against_contents'
            description = (f'日程提取到 {len(entries)} 个本会议具名条目，'
                           '尚未逐项与目录核对，不能据此宣称论文篇数或已经阅读。')
        state.pop('error', None)
        save_json(manifest, state)
        lines = [f'# {venue} {year} 公开论文集', '',
                 f'[官方日程]({url}) · [原始页面](index.html) · [清单](manifest.json)', '',
                 '已归档整卷、目录及官方页面列出的勘误。' + description, '']
        for key, item in state['documents'].items():
            lines.append(f'- [{key}]({Path(item["file"]).name})：{item["pages"]} 页；'
                         f'[文本]({Path(item["text"]).name})。')
        (directory / 'README.md').write_text('\n'.join(lines) + '\n')
        return conference, state['status']
    except Exception as exc:
        state.update(status='failed', error=f'{type(exc).__name__}: {exc}', updated_at=now())
        save_json(manifest, state)
        print(f'{conference}: {state["error"]}', flush=True)
        return conference, 'failed'


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--conferences', nargs='+', required=True)
    parser.add_argument('--workers', type=int, default=2)
    args = parser.parse_args()
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        results = list(pool.map(archive, args.conferences))
    print(results, flush=True)
    raise SystemExit(any(status != 'downloaded' for _, status in results))
