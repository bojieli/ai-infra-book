#!/usr/bin/env python3
"""Reconcile the archived MICRO 2024 program with deposited metadata offline."""
from pathlib import Path
from datetime import datetime, timezone
from bs4 import BeautifulSoup
import hashlib
import html
import json
import re
import unicodedata

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / 'references/proceedings/MICRO/2024'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def normalized(s):
    s = BeautifulSoup(s, 'html.parser').get_text() if '<' in s else html.unescape(s)
    return re.sub('[^a-z0-9]', '', unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode().lower())


def reconcile():
    program = next(p for p in json.loads((ROOT / 'references/proceedings/discovery/2026-09-08/program-index.json').read_text())['programs']
                   if p['source_id'] == 'micro2024-program')
    assert digest(ROOT / program['source_file']) == program['source_sha256']
    # The original site itself puts title continuations in two author fields.
    soup = BeautifulSoup((ROOT / program['source_file']).read_text(), 'html.parser')
    nodes = soup.select('.paper')
    assert len(nodes) == len(program['entries']) == 123
    for node, e in zip(nodes, program['entries']):
        assert node.select_one('.paper-title').get_text(' ', strip=True) == e['title']
    query_path = DEST / 'container-query.json'
    q = json.loads(query_path.read_text())['message']
    items = [(i, x) for i, x in enumerate(q['items']) if x['DOI'].lower().startswith('10.1109/micro61859.2024.')]
    assert len(items) == 124
    variants = json.loads((DEST / 'title-variants.json').read_text())
    assert variants['program_sha256'] == program['source_sha256']
    assert variants['query_sha256'] == digest(query_path)
    reviews = {x['program_order']: x for x in variants['records']}
    old_path = DEST / 'manifest.json'
    old = {p['doi']: p for p in json.loads(old_path.read_text())['papers']} if old_path.exists() else {}
    excluded, papers = [], []
    for e in program['entries']:
        if 'Posters' in e['title'] or 'PhD Forum' in e['title']:
            excluded.append(dict(program_order=e['program_order'], title=e['title'], reason='Poster-session or PhD-forum event, not an individual proceedings paper.'))
            continue
        found = [(i, x) for i, x in items if normalized(e['title']) == normalized(x['title'][0])]
        if found:
            assert len(found) == 1
            i, x = found[0]
            method = 'normalized_title_exact'
        else:
            review = reviews[e['program_order']]
            assert (review['program_title'], review['program_authors']) == (e['title'], e['authors'])
            i, x = next((i, x) for i, x in items if x['DOI'] == review['doi'])
            assert review['publisher_title'] == x['title'][0] and review['publisher_authors'] == x['author']
            method = 'reviewed_title_and_authors'
        paper = dict(program_order=e['program_order'], program_title=e['title'], program_authors=e['authors'],
                     doi=x['DOI'], publisher_title=x['title'][0], publisher_authors=x.get('author', []),
                     page=x.get('page'), publication_date=x.get('published'), identity_method=method,
                     metadata_source_index=i, publisher_links=x.get('link', []), reading_status='metadata_matched_not_screened')
        for key in ['reading_status', 'abstract', 'screening', 'reading_proof', 'pdf_file', 'pdf_pages', 'selected_reading', 'public_copy', 'source_followup']:
            if key in old.get(paper['doi'], {}):
                paper[key] = old[paper['doi']][key]
        papers.append(paper)
    assert len(excluded) == 10 and len(papers) == len({p['doi'] for p in papers}) == 113
    assert sum(p['identity_method'] == 'normalized_title_exact' for p in papers) == 101
    used = {p['doi'] for p in papers}
    front = [dict(doi=x['DOI'], title=x['title'][0], page=x.get('page'), metadata_source_index=i)
             for i, x in items if x['DOI'] not in used]
    assert len(front) == 11
    path = DEST / 'public-abstracts.json'
    if path.exists():
        proofs = {p['doi']: p for p in json.loads(path.read_text())['papers']}
        for p in papers:
            if p['doi'] not in proofs:
                continue
            r = proofs[p['doi']]
            assert (p['program_order'], p['publisher_title']) == (r['program_order'], r['publisher_title'])
            p.update(abstract=r['abstract'], screening=r['screening'], reading_proof='public-abstracts.json')
            for key in ['pdf_file', 'pdf_pages', 'selected_reading']:
                if key in r:
                    p[key] = r[key]
            p['reading_status'] = 'selected_sections_read' if 'selected_reading' in p else r['reading_status']
    result = dict(generated_at=datetime.now(timezone.utc).isoformat(),
                  scope='113 papers among 123 original official-program items matched to publisher-deposited DOI metadata. Ten non-paper events and eleven deposited front/back-matter items separated. Ranked query is not an exhaustive volume API; metadata is not abstract/body reading.',
                  program_file=program['source_file'], program_sha256=program['source_sha256'],
                  query_file=str(query_path.relative_to(ROOT)), query_sha256=digest(query_path),
                  query_returned_items=len(q['items']), query_reported_total=q['total-results'],
                  doi_prefix='10.1109/micro61859.2024.', excluded_program_events=excluded, front_back_matter=front, papers=papers)
    old_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    return result


if __name__ == '__main__':
    r = reconcile()
    print(json.dumps(dict(papers=len(r['papers']), excluded_events=len(r['excluded_program_events']), screened=sum('screening' in p for p in r['papers']))))
