#!/usr/bin/env python3
"""Archive this survey's primary sources without changing the main reference store.

Existing originals are referenced with their original retrieval date and hash.
New downloads are immutable on rerun; text is a derived reading aid.
"""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
import subprocess
import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[2]
DEST = ROOT / 'references/token-cost/2026-09-07'
PLAN = Path(__file__).with_name('source-plan.json')

def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def archive(item):
    item = dict(item)
    if 'reuse' in item:
        source = json.loads((ROOT / item.pop('reuse')).read_text())
        original = next(x for x in source if x['id'] == item.pop('reuse_id', item['id']))
        p = ROOT / original['file']
        if not p.exists():
            p = ROOT / 'references' / original['file']
        assert digest(p) == original['sha256'], p
        item.update(file=str(p.relative_to(ROOT)), url=original['url'],
                    final_url=original.get('final_url', original.get('resolved_url', original['url'])),
                    retrieved_at=original['retrieved_at'], acquisition='existing-original',
                    version=original.get('version_in_text'))
    else:
        p = DEST / item.pop('filename')
        record = p.with_suffix(p.suffix + '.meta.json')
        if p.exists():
            previous = json.loads(record.read_text())
            assert digest(p) == previous['sha256'], p
            item.update(previous)
        else:
            response = requests.get(item['url'], timeout=(20, 180), headers={'User-Agent': 'AI-Infra-Book-Research/1.0'})
            response.raise_for_status()
            if p.suffix == '.pdf':
                assert response.content.startswith(b'%PDF-'), item['url']
            p.write_bytes(response.content)
            item.update(file=str(p.relative_to(ROOT)), final_url=response.url,
                        retrieved_at=datetime.now(timezone.utc).isoformat(),
                        content_type=response.headers.get('content-type'), acquisition='new-download')
            item.update(bytes=p.stat().st_size, sha256=digest(p))
            record.write_text(json.dumps(item, ensure_ascii=False, indent=2)+'\n')
    item.update(bytes=p.stat().st_size, sha256=digest(p))
    target = DEST / 'text' / (item['id'] + '.txt')
    if p.suffix == '.pdf':
        subprocess.run(['pdftotext', '-layout', str(p), str(target)], check=True, capture_output=True)
        info = subprocess.check_output(['pdfinfo', str(p)], text=True)
        item['pages'] = int(next(x.split(':')[1] for x in info.splitlines() if x.startswith('Pages:')))
    elif p.suffix in ('.html', '.htm'):
        soup = BeautifulSoup(p.read_bytes(), 'html.parser')
        for tag in soup(['script', 'style', 'nav', 'footer']):
            tag.decompose()
        target.write_text(soup.get_text('\n', strip=True))
    else:
        target.write_text(p.read_text())
    item['text_file'] = str(target.relative_to(ROOT))
    item['text_sha256'] = digest(target)
    assert len(target.read_text().strip()) > 100, p
    print(item['id'], item['acquisition'], item['bytes'], flush=True)
    return item

def main():
    DEST.mkdir(parents=True, exist_ok=True)
    (DEST / 'text').mkdir(exist_ok=True)
    plan = json.loads(PLAN.read_text())
    results, failures = [], []
    def attempt(x):
        try:
            return archive(x), None
        except Exception as e:
            return None, dict(id=x['id'], error=repr(e))
    with ThreadPoolExecutor(max_workers=6) as pool:
        for item, error in pool.map(attempt, plan):
            if error:
                failures.append(error)
            else:
                results.append(item)
    (DEST / 'manifest.json').write_text(json.dumps(results, ensure_ascii=False, indent=2)+'\n')
    (DEST / 'download-errors.json').write_text(json.dumps(failures, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps(dict(archived=len(results), failed=failures), ensure_ascii=False))
    if failures:
        raise SystemExit(1)

if __name__ == '__main__':
    main()
