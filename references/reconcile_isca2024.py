#!/usr/bin/env python3
"""Reconcile the archived ISCA 2024 program, without network access."""
from pathlib import Path
from datetime import datetime, timezone
from bs4 import BeautifulSoup
import hashlib, json, re, unicodedata

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / 'references/proceedings/ISCA/2024'

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def normalized(title):
    text = BeautifulSoup(title, 'html.parser').get_text()
    text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode()
    return re.sub('[^a-z0-9]', '', text.lower())

def reconcile():
    program = next(x for x in json.loads((ROOT / 'references/proceedings/discovery/2026-09-08/program-index.json').read_text())['programs'] if x['source_id'] == 'isca2024-program')
    query_path = DEST / 'isca24-container-query.json'
    query = json.loads(query_path.read_text())['message']
    records = [(i, x) for i, x in enumerate(query['items']) if x['DOI'].lower().startswith('10.1109/isca59077.2024.')]
    by_doi = {x['DOI'].lower(): (i, x) for i, x in records}
    reviewed = json.loads((DEST / 'title-variants.json').read_text())
    assert reviewed['program_sha256'] == digest(ROOT / program['source_file'])
    assert reviewed['query_sha256'] == digest(query_path)
    variants = {x['program_order']: x for x in reviewed['records']}
    reading = json.loads((DEST / 'ghost-abstract-reading.json').read_text())
    assert digest(ROOT / reading['pdf_file']) == reading['pdf_sha256']
    assert digest(ROOT / reading['text_file']) == reading['text_sha256']
    papers = []
    for e in program['entries']:
        candidates = [(i, x) for i, x in records if normalized(e['title']) == normalized(x['title'][0])]
        if candidates:
            assert len(candidates) == 1
            i, x = candidates[0]
            method = 'normalized_title_exact'
        else:
            v = variants[e['program_order']]
            assert (e['title'], e['authors']) == (v['program_title'], v['program_authors'])
            i, x = by_doi[v['doi']]
            assert (x['title'][0], x.get('author', [])) == (v['publisher_title'], v['publisher_authors'])
            method = 'reviewed_title_and_author_variant'
        paper = dict(program_order=e['program_order'], program_title=e['title'], program_authors=e['authors'], doi=x['DOI'].lower(), publisher_title=x['title'][0], publisher_authors=x.get('author', []), page=x.get('page'), source_item_index=i, identity_method=method, publisher_url=x.get('resource', {}).get('primary', {}).get('URL'), reading_status='metadata_matched_not_screened')
        if paper['doi'] == reading['doi']:
            paper.update(reading_status='abstract_screened', abstract=reading['abstract'], screening=reading['screening'], reading_proof='ghost-abstract-reading.json', pdf_file=reading['pdf_file'], pdf_pages=reading['pdf_pages'])
        papers.append(paper)
    assert len(papers) == len({p['doi'] for p in papers}) == 87
    assert sum(p['identity_method'] == 'normalized_title_exact' for p in papers) == 70
    used = {p['doi'] for p in papers}
    excluded = [dict(doi=x['DOI'].lower(), title=x['title'][0], reason='Proceedings front/back matter absent from the 87-paper program') for _, x in records if x['DOI'].lower() not in used]
    result = dict(generated_at=datetime.now(timezone.utc).isoformat(), scope='All 87 archived program entries matched; query is ranked and not exhaustive. One public PDF and one full abstract screened, not an archived/read complete volume.', program_file=program['source_file'], program_sha256=program['source_sha256'], query_file=str(query_path.relative_to(ROOT)), query_sha256=digest(query_path), query_returned_items=len(query['items']), query_reported_total=query['total-results'], matching_prefix_records=len(records), excluded_records=excluded, papers=papers)
    path = DEST / 'manifest.json'
    if path.exists():
        old = json.loads(path.read_text())
        # Keep future readings on a cached resume. Identity must still match.
        old_papers = {p['doi']: p for p in old['papers']}
        for p in result['papers']:
            previous = old_papers.get(p['doi'], {})
            for key in ['reading_status', 'abstract', 'screening', 'reading_proof', 'pdf_file', 'pdf_pages', 'selected_reading', 'abstract_source_kind']:
                if key in previous:
                    p[key] = previous[key]
    public_path = DEST / 'public-manifest.json'
    public = {}
    if public_path.exists():
        public = {p['doi']: p for p in json.loads(public_path.read_text())['papers']}
        for p in result['papers']:
            if p['doi'] in public:
                item = public[p['doi']]
                assert p['publisher_title'] == item['publisher_title']
                p.update(reading_status=item['reading_status'], abstract=item['abstract'], screening=item['screening'], reading_proof='public-manifest.json', pdf_file=item['pdf_file'], pdf_pages=item['pdf_pages'])
                if 'selected_reading' in item:
                    p['selected_reading'] = item['selected_reading']
    institution_path = DEST / 'institutional-abstracts.json'
    if institution_path.exists():
        institutional = {p['doi']: p for p in json.loads(institution_path.read_text())['papers']}
        for p in result['papers']:
            if p['doi'] in institutional:
                item = institutional[p['doi']]
                assert (p['program_order'], p['publisher_title']) == (item['program_order'], item['publisher_title'])
                # An HTML/JSON abstract adds reading coverage, never PDF pages.
                # A subsequent public PDF/selected reading takes precedence.
                if p['doi'] not in public and 'selected_reading' not in p:
                    p.update(reading_status=item['reading_status'], abstract=item['abstract'], screening=item['screening'], reading_proof='institutional-abstracts.json', abstract_source_kind=item['source_kind'])
    result['scope'] = 'All 87 archived program entries matched; query is ranked and not exhaustive. Public PDF and abstract coverage are counted separately; not an archived/read complete volume.'
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    return result

if __name__ == '__main__':
    manifest = reconcile()
    print(json.dumps({'matched': len(manifest['papers']), 'excluded': len(manifest['excluded_records']), 'abstracts_screened': sum('screening' in x for x in manifest['papers'])}))
