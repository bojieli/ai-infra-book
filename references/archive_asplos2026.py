#!/usr/bin/env python3
"""Archive public ASPLOS 2026 sources; reconcile the already reviewed catalog.

Default operation is offline. Network access requires --locations or --fetch.
Program inclusion and publication year are deliberately kept separate.
"""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
import argparse
import hashlib
import json
import requests

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / 'references/proceedings/ASPLOS/2026'
MAP = ROOT / 'references/proceedings/catalog-review/2026-09-08/asplos2026-program-doi-map.json'
PROGRAM = ROOT / 'references/proceedings/discovery/2026-09-08/asplos2026-program.html'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')


def collect(urls, batch):
    DEST.mkdir(parents=True, exist_ok=True)
    target = DEST / 'sources.json'
    old = json.loads(target.read_text()) if target.exists() else []
    assert not {r['id'] for r in old} & {'asplos26-' + k for k in urls}

    def fetch(item):
        key, url = item
        try:
            response = requests.get(url, timeout=40, headers={'User-Agent': 'AI Infra Book source research'})
        except requests.RequestException as exc:
            return dict(key=key, url=url, error=repr(exc), response_body_received=False)
        content = response.content
        kind = response.headers.get('content-type', '')
        ext = 'pdf' if content.startswith(b'%PDF-') else 'json' if 'json' in kind else 'html' if 'html' in kind else 'txt'
        path = DEST / (key + '.' + ext)
        assert not path.exists(), path
        path.write_bytes(content)
        return dict(id='asplos26-' + key, title=key, url=url, final_url=response.url,
                    status_code=response.status_code, file=str(path.relative_to(ROOT)),
                    bytes=len(content), sha256=sha(path), retrieved_at=datetime.now(timezone.utc).isoformat(),
                    reading_status='downloaded_not_read' if response.status_code == 200 else 'failed_response_not_evidence')

    with ThreadPoolExecutor(max_workers=4) as pool:
        rows = list(pool.map(fetch, urls.items()))
    assert (json.loads(target.read_text()) if target.exists() else []) == old
    write(target, old + [r for r in rows if 'id' in r])
    write(DEST / batch, rows)
    return [{k: v for k, v in r.items() if k in ('id', 'status_code', 'bytes', 'error')} for r in rows]


def reconcile():
    DEST.mkdir(parents=True, exist_ok=True)
    mapping = json.loads(MAP.read_text())
    assert sha(ROOT / mapping['query_file']) == mapping['query_sha256']
    catalog = mapping['papers']
    assert len(catalog) == len({p['doi'] for p in catalog}) == 168
    target = DEST / 'manifest.json'
    old = {p['doi']: p for p in json.loads(target.read_text())['papers']} if target.exists() else {}
    proof_path = DEST / 'public-abstracts.json'
    proof = {p['doi']: p for p in json.loads(proof_path.read_text())['papers']} if proof_path.exists() else {}
    papers = []
    for entry in catalog:
        paper = dict(entry)
        for key in ('public_copy', 'pdf_file', 'pdf_pages', 'abstract', 'screening', 'reading_proof',
                    'reading_status', 'selected_reading', 'source_followup'):
            if key in old.get(paper['doi'], {}):
                paper[key] = old[paper['doi']][key]
        if paper['doi'] in proof:
            record = proof[paper['doi']]
            assert record['program_order'] == paper['program_order']
            for key in ('abstract', 'screening', 'pdf_file', 'pdf_pages', 'reading_status', 'selected_reading'):
                if key in record:
                    paper[key] = record[key]
            paper['reading_proof'] = 'public-abstracts.json'
        papers.append(paper)
    result = dict(generated_at=datetime.now(timezone.utc).isoformat(),
                  scope='168 detailed ASPLOS 2026 program entries; not a claim of complete publisher volumes. Original header says 167; discrepancy remains unresolved.',
                  program_file=str(PROGRAM.relative_to(ROOT)), program_sha256=sha(PROGRAM),
                  identity_map=str(MAP.relative_to(ROOT)), identity_map_sha256=sha(MAP),
                  papers=papers)
    write(target, result)
    return dict(papers=len(papers), screened=sum('screening' in p for p in papers))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--locations', action='store_true')
    parser.add_argument('--fetch', type=Path, help='JSON object mapping stable source keys to public URLs')
    parser.add_argument('--batch', default='fetch-public.json')
    args = parser.parse_args()
    if args.locations:
        papers = json.loads(MAP.read_text())['papers']
        urls = {'locations-%02d' % (i // 40 + 1): 'https://api.openalex.org/works?' + urlencode(
                    {'filter': 'doi:' + '|'.join(p['doi'] for p in papers[i:i + 40]), 'per-page': 50})
                for i in range(0, len(papers), 40)}
        print(json.dumps(collect(urls, 'fetch-locations.json')))
    if args.fetch:
        print(json.dumps(collect(json.loads(args.fetch.read_text()), args.batch)))
    print(json.dumps(reconcile()))
