#!/usr/bin/env python3
"""Reconcile the archived ISCA 2025 program with deposited metadata offline."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import html
import json
import re
import unicodedata
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / 'references/proceedings/ISCA/2025'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def normalized(value):
    value = BeautifulSoup(value, 'html.parser').get_text() if '<' in value else html.unescape(value)
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode()
    return re.sub('[^a-z0-9]', '', value.lower())


def reconcile():
    program = next(p for p in json.loads((ROOT / 'references/proceedings/discovery/2026-09-08/program-index.json').read_text())['programs'] if p['source_id'] == 'isca2025-program')
    assert digest(ROOT / program['source_file']) == program['source_sha256']
    query_path = DEST / 'container-query.json'
    query = json.loads(query_path.read_text())['message']
    records = [(i, x) for i, x in enumerate(query['items']) if x['DOI'].startswith('10.1145/3695053.')]
    variants = json.loads((DEST / 'title-variants.json').read_text())
    assert variants['program_sha256'] == program['source_sha256']
    assert variants['query_sha256'] == digest(query_path)
    reviewed = {v['program_order']: v for v in variants['records']}
    path = DEST / 'manifest.json'
    old = {p['doi']: p for p in json.loads(path.read_text())['papers']} if path.exists() else {}
    papers = []
    for entry in program['entries']:
        candidates = [(i, x) for i, x in records if normalized(entry['title']) == normalized(x['title'][0])]
        if candidates:
            assert len(candidates) == 1
            index, item = candidates[0]
            method = 'normalized_title_exact'
        else:
            review = reviewed[entry['program_order']]
            assert (entry['title'], entry['authors']) == (review['program_title'], review['program_authors'])
            index, item = next((i, x) for i, x in records if x['DOI'] == review['doi'])
            assert item['title'][0] == review['publisher_title'] and item['author'] == review['publisher_authors']
            method = 'reviewed_title_and_authors'
        paper = dict(program_order=entry['program_order'], program_title=entry['title'], program_authors=entry['authors'], doi=item['DOI'], publisher_title=item['title'][0], publisher_subtitle=item.get('subtitle', []), publisher_authors=item['author'], page=item.get('page'), publication_date=item.get('published'), metadata_source_index=index, identity_method=method, publisher_links=item.get('link', []), reading_status='metadata_matched_not_screened')
        for key in ['reading_status', 'abstract', 'screening', 'reading_proof', 'pdf_file', 'pdf_pages', 'selected_reading', 'public_copy', 'source_followup']:
            if key in old.get(paper['doi'], {}):
                paper[key] = old[paper['doi']][key]
        papers.append(paper)
    assert len(papers) == len({p['doi'] for p in papers}) == len(records) == 135
    assert sum(p['identity_method'] == 'normalized_title_exact' for p in papers) == 134
    proof_path = DEST / 'public-abstracts.json'
    if proof_path.exists():
        proofs = {p['doi']: p for p in json.loads(proof_path.read_text())['papers']}
        for paper in papers:
            if paper['doi'] not in proofs:
                continue
            proof = proofs[paper['doi']]
            assert (paper['program_order'], paper['publisher_title']) == (proof['program_order'], proof['publisher_title'])
            paper.update(abstract=proof['abstract'], screening=proof['screening'], reading_proof='public-abstracts.json')
            if 'selected_reading' in proof:
                paper['selected_reading'] = proof['selected_reading']
            paper['reading_status'] = 'selected_sections_read' if 'selected_reading' in paper else proof['reading_status']
            if proof['source_kind'] == 'public_pdf':
                paper.update(pdf_file=proof['pdf_file'], pdf_pages=proof['pdf_pages'])
    result = dict(generated_at=datetime.now(timezone.utc).isoformat(), scope='All 135 archived official-program entries matched to publisher-deposited metadata; ranked query is not an exhaustive volume API. Metadata matching is separate from abstract/PDF/body reading.', program_file=program['source_file'], program_sha256=program['source_sha256'], query_file=str(query_path.relative_to(ROOT)), query_sha256=digest(query_path), query_returned_items=len(query['items']), query_reported_total=query['total-results'], volume_doi='10.1145/3695053', papers=papers)
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    return result


if __name__ == '__main__':
    result = reconcile()
    print(json.dumps(dict(matched=len(result['papers']), screened=sum('screening' in p for p in result['papers']))))
