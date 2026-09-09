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
    assert len(sources) == len({s['id'] for s in sources}) == 117
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
    assert len(orders) == manifest['public_abstracts_available'] == manifest['abstracts_screened'] == 68
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
            if a['identity'].get('publisher_author_names_in_pdf_page'):
                if a['identity'].get('doi_not_printed_in_author_preprint'):
                    assert a['program_order'] in {75, 76}
                    identity = a['identity']; landing = byid[identity['landing_source_id']]
                    assert landing['sha256'] == identity['landing_sha256']
                    soup = BeautifulSoup((ROOT / landing['file']).read_text(), 'html.parser')
                    assert norm(soup.select_one('meta[name=citation_title]')['content']) == norm(p['title'])
                    assert {norm(x['content'].split(',')[0]) for x in soup.select('meta[name=citation_author]')} == {norm(x['family']) for x in p['author_metadata']}
                    assert ' '.join(soup.select_one('.submission-history').get_text(' ', strip=True).split()) == identity['history']
                    assert identity['arxiv_version'] in raw and s['url'].endswith(identity['arxiv_version'])
                    assert norm(p['title']) in norm(raw)
                else:
                    assert norm(p['doi']) in norm(raw)
                assert all(norm(name) in norm(raw) for name in a['authors'])
                assert list(map(norm, a['authors'])) == [norm(' '.join([x.get('given', ''), x['family']])) for x in p['author_metadata']]
        elif 'html_abstract' in a:
            soup = BeautifulSoup((ROOT / s['file']).read_text(), 'html.parser')
            h = a['html_abstract']; blocks = soup.select(h['css_selector'])
            assert len(blocks) == h['expected_matches'] == 1
            text = ' '.join(blocks[0].get_text(' ', strip=True).split())
            assert norm(soup.select_one(h['citation_title_selector'])['content']) == norm(a['title'])
            assert [x['content'] for x in soup.select(h['citation_author_selector'])] == a['authors']
            assert list(map(norm, a['authors'])) == [norm(' '.join([x.get('given', ''), x['family']])) for x in p['author_metadata']]
            assert soup.select_one(h['citation_doi_selector'])['content'].lower() == p['doi']
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
    assert len(pdfs) == manifest['public_pdfs_archived'] == 65
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
    assert len(selected) == manifest['selected_sections_read'] == 15
    assert {p['program_order'] for p in selected} == {3, 21, 22, 27, 28, 35, 39, 40, 44, 49, 73, 74, 75, 76, 94}
    expected_pages = {3: range(1, 14), 21: range(2, 14), 22: range(2, 15), 27: range(2, 15), 28: range(2, 13), 35: range(1, 14), 39: range(2, 13), 40: range(2, 14), 44: list(range(2, 13)) + [16, 17], 49: range(1, 14), 94: range(1, 14)}
    expected_pages[74] = range(1, 16)
    expected_pages[73] = range(2, 16)
    expected_pages[75] = list(range(2, 14)) + [17]
    expected_pages[76] = list(range(2, 14)) + [18, 19, 20]
    for order, filename in [(3, 'iks-reading.json'), (21, 'diffuse-reading.json'), (22, 'cxlfork-reading.json'), (27, 'ascend-components-reading.json'), (28, 'picachu-reading.json'), (35, 'darwingame-reading.json'), (39, 'streamgrid-reading.json'), (40, 'arc-reading.json'), (44, 'apophenia-reading.json'), (49, 'pipellm-reading.json'), (73, 'llm-npu-reading.json'), (74, 'helix-reading.json'), (75, 'flexsp-reading.json'), (76, 'spindle-reading.json'), (94, 'fsmoe-reading.json')]:
        proof = json.loads((D / filename).read_text()); reading = proof['reading']
        assert reading == papers[order]['selected_reading']
        assert reading['physical_pdf_pages'] == list(expected_pages[order])
        selected_pdf = papers[order].get('selected_reading_pdf', papers[order]['pdf'])
        assert reading['individual_pdf'] == selected_pdf['file']
        if 'selected_reading_pdf' in papers[order]:
            data = (ROOT / selected_pdf['file']).read_bytes()
            assert len(data) == selected_pdf['bytes'] and hashlib.sha256(data).hexdigest() == selected_pdf['sha256']
            assert all(selected_pdf[k] == v for k, v in proof['paper']['pdf'].items())
        for page, expected in reading['page_text_sha256'].items():
            data = subprocess.check_output(['pdftotext', '-f', page, '-l', page, str(ROOT / reading['individual_pdf']), '-'])
            assert hashlib.sha256(data).hexdigest() == expected
        for f in proof['figures']:
            assert f['actually_viewed'] and hashlib.sha256((ROOT / f['file']).read_bytes()).hexdigest() == f['sha256']
    middle = json.loads((D / 'middle-screening-notes.json').read_text())
    assert len(middle['new_source_ids']) == 16
    assert middle['new_abstract_orders'] == [36, 37, 38, 39, 40, 41, 43, 44, 46, 48, 49, 55, 60]
    assert set(middle['new_abstract_orders']).issubset(orders)
    assert sum(byid[i].get('pdf_pages', 0) for i in middle['new_source_ids']) == middle['new_pdf_pages'] == 260
    assert {v['program_order'] for v in middle['abstract_page_views']} == {38, 40, 43, 55}
    for view in middle['abstract_page_views']:
        data = (ROOT / view['file']).read_bytes()
        assert len(data) == view['bytes'] and hashlib.sha256(data).hexdigest() == view['sha256']
        source = byid[view['source_id']]
        assert source['sha256'] == view['source_sha256'] and source['program_order'] == view['program_order']
        assert view['actually_viewed'] and view['physical_page'] == 1
    storage = json.loads((D / 'storage-screening-notes.json').read_text())
    assert len(storage['new_source_ids']) == 14
    assert storage['new_abstract_orders'] == [50, 51, 52, 53, 54, 56, 58, 61, 63, 64]
    assert set(storage['new_abstract_orders']).issubset(orders)
    assert sum(byid[i].get('pdf_pages', 0) for i in storage['new_source_ids']) == storage['new_pdf_pages'] == 130
    assert sum('pdf_pages' in byid[i] for i in storage['new_source_ids']) == storage['new_pdfs'] == 8
    assert {x['program_order'] for x in storage['unresolved']} == {57, 59, 62}
    assert not {57, 59, 62} & set(orders)
    assert len(storage['transport_errors']) == 1
    assert storage['selected_body_orders'] == [39, 40]
    assert sum(len(papers[n]['selected_reading']['physical_pdf_pages']) for n in [39, 40]) == storage['selected_body_pages'] == 23
    assert {v['program_order'] for v in storage['abstract_page_views']} == {54, 64}
    for view in storage['abstract_page_views']:
        data = (ROOT / view['file']).read_bytes()
        assert len(data) == view['bytes'] and hashlib.sha256(data).hexdigest() == view['sha256']
        source = byid[view['source_id']]
        assert source['sha256'] == view['source_sha256'] and source['program_order'] == view['program_order']
        assert view['actually_viewed'] and view['physical_page'] == 1
    for n in storage['new_abstract_orders']:
        assert storage['decisions'][str(n)] == {k: papers[n]['screening'][k] for k in ['decision', 'reason']}
        assert storage['version_notes'][str(n)] == papers[n]['public_version_note']
    batch = json.loads((D / 'heterogeneous-screening-notes.json').read_text())
    assert len(batch['new_source_ids']) == 16
    assert batch['new_abstract_orders'] == list(range(67, 77))
    assert set(batch['new_abstract_orders']).issubset(orders)
    assert sum(byid[i].get('pdf_pages', 0) for i in batch['new_source_ids']) == batch['new_pdf_pages'] == 169
    assert sum('pdf_pages' in byid[i] for i in batch['new_source_ids']) == batch['new_pdfs'] == 10
    assert {x['program_order'] for x in batch['unresolved']} == {65, 66}
    assert not {65, 66} & set(orders)
    assert len(batch['transport_errors']) == 1 and batch['transport_errors'][0]['program_order'] == 67
    assert batch['selected_body_orders'] == [74] and batch['selected_body_pages'] == 15
    assert {(v['program_order'], v['physical_page']) for v in batch['abstract_page_views']} == {(70, 2), (73, 1), (75, 1)}
    for v in batch['abstract_page_views']:
        data = (ROOT / v['file']).read_bytes(); source = byid[v['source_id']]
        assert len(data) == v['bytes'] and hashlib.sha256(data).hexdigest() == v['sha256']
        assert source['sha256'] == v['source_sha256'] and source['program_order'] == v['program_order'] and v['actually_viewed']
    for n in batch['new_abstract_orders']:
        # Keep the original abstract-screening decision when later body reading changes adoption.
        if n in {73, 75, 76}:
            filename = {73:'llm-npu-reading.json', 75:'flexsp-reading.json', 76:'spindle-reading.json'}[n]
            historical = json.loads((D / filename).read_text())['prior_abstract_screening']
        else:
            historical = papers[n]['screening']
        assert batch['decisions'][str(n)] == {k: historical[k] for k in ['decision', 'reason']}
        assert batch['version_notes'][str(n)] == papers[n]['public_version_note']
    report = dict(verified_at=datetime.now(timezone.utc).isoformat(), status='passed', scope='Public sources and declared reading only; not full proceedings completion.', responses=len(sources), failed_responses=sum(s['status_code'] != 200 for s in sources), location_dois=184, public_pdfs=len(pdfs), public_pdf_pages=sum(s['pdf_pages'] for s in pdfs), primary_abstracts_screened=len(abstracts), remaining_abstracts=184-len(abstracts), selected_sections_read=len(selected), middle_abstract_page_views=4, storage_abstract_page_views=2, storage_transport_errors=1, heterogeneous_abstract_page_views=3, heterogeneous_transport_errors=1)
    (D / 'public-audit.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    return report


if __name__ == '__main__':
    print(json.dumps(verify(), ensure_ascii=False))
