#!/usr/bin/env python3
"""Save the original figures underlying the survey's key engineering comparisons."""
from pathlib import Path
from datetime import datetime, timezone
from urllib.parse import urljoin, urlsplit
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import mimetypes
import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[2]
DEST = ROOT / 'references/token-cost/2026-09-07'

def main():
    sources = {x['id']:x for x in json.loads((DEST / 'manifest.json').read_text())}
    jobs = []
    for name in ['vllm-060','blackwell-inferencex','inferencex-gb300']:
        item = sources[name]
        soup = BeautifulSoup((ROOT/item['file']).read_text(), 'html.parser')
        seen = set()
        for img in soup.find_all('img'):
            src = img.get('src','')
            if not src or src in seen:
                continue
            if name == 'blackwell-inferencex' and '/2026/02/' not in src:
                continue
            seen.add(src)
            jobs.append((name, urljoin(item['final_url'],src)))
    (DEST / 'figures').mkdir(exist_ok=True)
    old = {x['url']:x for x in json.loads((DEST/'figures.json').read_text())} if (DEST/'figures.json').exists() else {}
    def fetch(job):
        name,url = job
        if url in old:
            x=old[url]
            if hashlib.sha256((ROOT/x['file']).read_bytes()).hexdigest()==x['sha256']:
                return x
        response = requests.get(url,timeout=(20,90));response.raise_for_status()
        assert response.headers.get('content-type','').startswith('image/'),url
        # Image optimization endpoints share a path; their query strings identify
        # different images, so the full URL must participate in the filename.
        suffix=mimetypes.guess_extension(response.headers['content-type'].split(';')[0]) or '.img'
        target = DEST/'figures'/(name+'-'+hashlib.sha256(url.encode()).hexdigest()[:12]+suffix)
        target.write_bytes(response.content)
        return dict(source_id=name,url=url,final_url=response.url,file=str(target.relative_to(ROOT)),
                    bytes=len(response.content),sha256=hashlib.sha256(response.content).hexdigest(),
                    retrieved_at=datetime.now(timezone.utc).isoformat(),publication_use='Original retained for research; no publication permission inferred.')
    with ThreadPoolExecutor(max_workers=5) as pool:
        results = list(pool.map(fetch,jobs))
    (DEST/'figures.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n')
    print(f'Saved {len(results)} original figures.')

if __name__=='__main__':
    main()
