#!/usr/bin/env python3
"""Reconcile the cached MICRO 2025 program and preserve explicit reading scopes."""
from pathlib import Path
from datetime import datetime, timezone
from bs4 import BeautifulSoup
import hashlib, json
from reconcile_micro2024 import normalized

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT/'references/proceedings/MICRO/2025'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def reconcile():
    program = next(p for p in json.loads((ROOT/'references/proceedings/discovery/2026-09-08/program-index.json').read_text())['programs'] if p['source_id'] == 'micro2025-program')
    assert digest(ROOT/program['source_file']) == program['source_sha256']
    nodes = BeautifulSoup((ROOT/program['source_file']).read_text(), 'html.parser').select('.paper')
    assert len(nodes) == len(program['entries']) == 123
    query_file = DEST/'container-query.json'
    query = json.loads(query_file.read_text())['message']
    items = [(i,x) for i,x in enumerate(query['items']) if x['DOI'].startswith('10.1145/3725843.')]
    assert len(items) == 123
    variants = json.loads((DEST/'title-variants.json').read_text())
    assert variants['program_sha256'] == program['source_sha256'] and variants['query_sha256'] == digest(query_file)
    reviews = {r['program_order']:r for r in variants['records']}
    manifest = DEST/'manifest.json'
    old = {p['doi']:p for p in json.loads(manifest.read_text())['papers']} if manifest.exists() else {}
    proof_file = DEST/'public-abstracts.json'
    proof = {p['doi']:p for p in json.loads(proof_file.read_text())['papers']} if proof_file.exists() else {}
    papers = []
    for e,node in zip(program['entries'],nodes):
        assert e['title'] == node.select_one('.paper-title').get_text(' ',strip=True)
        assert e['authors'] == node.select_one('.paper-authors').get_text(' ',strip=True)
        found = [(i,x) for i,x in items if normalized(e['title']) == normalized(x['title'][0])]
        if found:
            assert len(found) == 1 and e['program_order'] not in reviews
            i,x = found[0]; method = 'normalized_title_exact'
        else:
            r = reviews[e['program_order']]
            assert (e['title'],e['authors']) == (r['program_title'],r['program_authors'])
            i,x = next((i,x) for i,x in items if x['DOI'] == r['doi'])
            assert (x['title'][0],x['author']) == (r['publisher_title'],r['publisher_authors'])
            method = 'reviewed_title_and_authors'
        p = dict(program_order=e['program_order'],program_title=e['title'],program_authors=e['authors'],doi=x['DOI'],publisher_title=x['title'][0],publisher_authors=x['author'],page=x.get('page'),publication_date=x.get('published'),identity_method=method,metadata_source_index=i,publisher_links=x.get('link',[]),reading_status='metadata_matched_not_screened')
        for key in ['reading_status','abstract','screening','reading_proof','pdf_file','pdf_pages','selected_reading','public_copy','source_followup']:
            if key in old.get(p['doi'],{}):p[key] = old[p['doi']][key]
        if p['doi'] in proof:
            r = proof[p['doi']]
            assert (p['program_order'],p['publisher_title']) == (r['program_order'],r['publisher_title'])
            p.update(abstract=r['abstract'],screening=r['screening'],reading_proof='public-abstracts.json')
            for key in ['pdf_file','pdf_pages','selected_reading']:
                if key in r:p[key] = r[key]
            p['reading_status'] = 'selected_sections_read' if 'selected_reading' in p else r['reading_status']
        papers.append(p)
    assert len(papers) == len({p['doi'] for p in papers}) == 123
    assert sum(p['identity_method'] == 'normalized_title_exact' for p in papers) == 116
    result = dict(generated_at=datetime.now(timezone.utc).isoformat(),scope='123 official program papers matched to publisher-deposited DOI metadata. Ranked query is not an exhaustive volume API; metadata is not abstract or body reading.',program_file=program['source_file'],program_sha256=program['source_sha256'],query_file=str(query_file.relative_to(ROOT)),query_sha256=digest(query_file),query_returned_items=len(query['items']),query_reported_total=query['total-results'],doi_prefix='10.1145/3725843.',papers=papers)
    manifest.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    return result


if __name__ == '__main__':
    r = reconcile()
    print(json.dumps(dict(papers=len(r['papers']),screened=sum('screening' in p for p in r['papers']))))
