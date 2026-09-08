#!/usr/bin/env python3
"""Check public-copy identity, primary abstracts and the declared selected pages."""
from pathlib import Path
from datetime import datetime, timezone
from bs4 import BeautifulSoup
import csv
import hashlib
import json
import re
import subprocess
import unicodedata

ROOT = Path(__file__).resolve().parents[2]
D = ROOT / 'references/proceedings/ASPLOS/2025'


def norm(text):
    return re.sub(r'[^a-z0-9]', '', unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode().lower())


def verify():
    sources = json.loads((D / 'selected-sources.json').read_text())
    assert len(sources) == len({s['id'] for s in sources}) == 56
    byid = {s['id']: s for s in sources}
    for s in sources:
        b = (ROOT / s['file']).read_bytes()
        assert len(b) == s['bytes'] and hashlib.sha256(b).hexdigest() == s['sha256']
        if 'derived_text' in s:
            t = s['derived_text']; data = (ROOT / t['file']).read_bytes()
            assert len(data) == t['bytes'] and hashlib.sha256(data).hexdigest() == t['sha256']
        for lo, hi in s.get('read_scope', {}).get('line_ranges_inclusive', []):
            assert 1 <= lo <= hi <= len(b.decode().splitlines())
    manifest = json.loads((D / 'manifest.json').read_text())
    papers = {p['program_order']: p for p in manifest['papers']}
    locations = json.loads((D / 'public-location-map.json').read_text())['records']
    assert len(locations) == 184
    for loc in locations:
        row = json.loads((ROOT / loc['source_file']).read_text())['results'][loc['result_index']]
        assert row['doi'] == 'https://doi.org/' + loc['doi']
        assert loc['doi'] == papers[loc['program_order']]['doi']
        assert row['id'] == loc['openalex_id']
        assert loc['candidate_locations'] == [x for x in row['locations'] if x.get('pdf_url') and 'dl.acm.org' not in x['pdf_url']]
    abstracts = json.loads((D / 'public-abstracts.json').read_text())['records']
    screens = list(csv.DictReader((ROOT / 'research/2026-infra-survey/screening-asplos-2025.tsv').open(), delimiter='\t'))
    orders = [a['program_order'] for a in abstracts]
    assert orders == sorted(set(orders)) == [int(s['number']) for s in screens]
    assert len(orders) == manifest['public_abstracts_available'] == manifest['abstracts_screened'] == 24
    for a, sc in zip(abstracts, screens):
        p = papers[a['program_order']]; s = byid[a['source_id']]
        assert a['source_file'] == s['file'] and a['source_sha256'] == s['sha256']
        assert a['identity']['official_program_doi'] == p['doi'] and norm(a['title']) == norm(p['title'])
        assert a['reading_status'] == 'full_abstract_read'
        if 'page_text' in a:
            t = a['page_text']; page = str(t['physical_page'])
            data = subprocess.check_output(['pdftotext', '-f', page, '-l', page, str(ROOT / s['file']), '-'])
            assert data == (ROOT / t['file']).read_bytes() and hashlib.sha256(data).hexdigest() == t['sha256']
            raw = data.decode(); spans = t['character_spans']
            assert all(0 <= lo < hi <= len(raw) for lo, hi in spans)
            text = ' '.join(' '.join(raw[lo:hi] for lo, hi in spans).split())
        else:
            soup = BeautifulSoup((ROOT / s['file']).read_text(), 'html.parser')
            block = soup.select_one('blockquote.abstract')
            if block:
                desc = block.select_one('.descriptor')
                if desc: desc.decompose()
                text = ' '.join(block.get_text(' ', strip=True).split())
                assert soup.select_one('meta[name=citation_title]')['content'] == a['title']
                assert [x['content'] for x in soup.select('meta[name=citation_author]')] == a['authors']
                assert {norm(x.split(',')[0]) for x in a['authors']} == {norm(x.get('family', '')) for x in p['author_metadata']}
            else:
                raw = soup.get_text(' ', strip=True); text = ' '.join(raw[raw.index('Thanks to the computation'):].split())
                assert p['doi'] in str(soup)
        assert text == a['abstract'] and hashlib.sha256(text.encode()).hexdigest() == a['abstract_sha256']
        assert p['public_abstract']['sha256'] == a['abstract_sha256']
        assert p['screening'] == {'basis': 'title_and_full_primary_public_abstract', 'decision': sc['decision'], 'reason': sc['reason']}
    pdfs = [s for s in sources if 'pdf_pages' in s]
    assert len(pdfs) == manifest['public_pdfs_archived'] == 23
    for s in pdfs:
        p = papers[s['program_order']]; pdf = ROOT / s['file']
        assert pdf.read_bytes().startswith(b'%PDF-') and p['pdf']['sha256'] == s['sha256']
        info = subprocess.check_output(['pdfinfo', str(pdf)], text=True, stderr=subprocess.PIPE)
        assert int(re.search(r'^Pages:\s+(\d+)', info, re.M)[1]) == s['pdf_pages'] == p['pages']
        data = subprocess.check_output(['pdftotext', '-f', '1', '-l', '1', str(pdf), '-'])
        assert data == (ROOT / s['first_page_text']['file']).read_bytes()
        assert hashlib.sha256(data).hexdigest() == s['first_page_text']['sha256']
        title = re.search(r'^Title:\s*(.+)', info, re.M)
        assert norm(p['title']) in norm(data.decode()) or (title and norm(p['title']) == norm(title[1]))
    selected = [p for p in papers.values() if p['reading_status'] == 'selected_sections_read']
    assert len(selected) == manifest['selected_sections_read'] == 2
    assert {p['program_order'] for p in selected} == {3, 94}
    for order, filename in [(3, 'iks-reading.json'), (94, 'fsmoe-reading.json')]:
        proof = json.loads((D / filename).read_text()); reading = proof['reading']
        assert reading == papers[order]['selected_reading']
        assert reading['physical_pdf_pages'] == list(range(1, 14))
        assert reading['individual_pdf'] == papers[order]['pdf']['file']
        for page, expected in reading['page_text_sha256'].items():
            data = subprocess.check_output(['pdftotext', '-f', page, '-l', page, str(ROOT / reading['individual_pdf']), '-'])
            assert hashlib.sha256(data).hexdigest() == expected
        for f in proof['figures']:
            assert f['actually_viewed'] and hashlib.sha256((ROOT / f['file']).read_bytes()).hexdigest() == f['sha256']
    report = dict(verified_at=datetime.now(timezone.utc).isoformat(), status='passed', scope='Public sources and declared reading only; not full proceedings completion.', responses=len(sources), failed_responses=sum(s['status_code'] != 200 for s in sources), location_dois=184, public_pdfs=len(pdfs), public_pdf_pages=sum(s['pdf_pages'] for s in pdfs), primary_abstracts_screened=len(abstracts), remaining_abstracts=184-len(abstracts), selected_sections_read=len(selected))
    (D / 'public-audit.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    return report


if __name__ == '__main__':
    print(json.dumps(verify(), ensure_ascii=False))
