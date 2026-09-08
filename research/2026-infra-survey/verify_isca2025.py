#!/usr/bin/env python3
"""Verify ISCA 2025 identities, public copies, and declared abstract readings."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import math
import re
import subprocess
import sys
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[2]
DEST = ROOT / 'references/proceedings/ISCA/2025'
sys.path.insert(0, str(ROOT / 'references'))
from reconcile_isca2025 import normalized


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_mesh_arithmetic():
    a = json.loads((ROOT / 'research/2026-infra-survey/arithmetic.json').read_text())['mesh_slicing_teaching']
    config = json.loads((ROOT / a['config']).read_text())
    m, k, n = a['tokens'], config['hidden_size'], config['intermediate_size']
    assert (m, k, n) == (8192, 4096, 12288)
    sizes = [m*k*2, k*n*2, m*n*2]
    assert [a[key] for key in ['x_mib', 'w_mib', 'y_mib']] == [s/2**20 for s in sizes]
    flops = 2*m*k*n//16
    assert flops == a['flops_per_chip'] == 51539607552
    for row in a['shapes']:
        r, c = row['rows'], row['cols']
        assert r*c == a['chips'] == 16
        # Explicit ring rounds, each with the initial local shard's bytes.
        assert sum(sizes[0]//16 for _ in range(c-1))/2**20 == row['horizontal_mib']
        assert sum(sizes[1]//16 for _ in range(r-1))/2**20 == row['vertical_mib']
    def schedule(s, throughput):
        comm_ends, compute_ends = [], []
        durations = [a['launch_s'] + sum(a['sync_s']+size/16/s/a['bandwidth_bytes_s'] for _ in range(3)) for size in sizes[:2]]
        g = flops/s/throughput
        # Two communication directions; double buffering prevents unbounded prefetch.
        for i in range(s):
            ready = max(comm_ends[-1] if i else 0, compute_ends[i-2] if i>=2 else 0)
            comm_ends.append(ready+max(durations))
            compute_ends.append(max(comm_ends[-1], compute_ends[-1] if i else 0)+g)
        return compute_ends[-1]*1000, max(durations)*1e6, g*1e6
    for row in a['slices']:
        s = row['count']
        assert (k//4) % (8*s) == 0
        elapsed, q, g = schedule(s, a['effective_flops_s'])
        for actual, stored in [(elapsed, row['pipeline_ms']), (q, row['comm_us']), (g, row['compute_us']), ((q+g)*s/1000, row['no_overlap_ms'])]:
            assert math.isclose(actual, stored, rel_tol=1e-12)
    assert math.isclose(schedule(16, 70e12)[0], a['s16_at_70tflops_ms'], rel_tol=1e-12)
    assert min(a['slices'], key=lambda x:x['pipeline_ms'])['count'] == 16
    # Validate block-slicing's global contraction indices on a small rectangular grid.
    # A and B start with different local K extents; local chunk numbers alone are insufficient.
    for s in [1, 2, 4]:
        seen = []
        for step in range(s):
            indices = []
            for partitions in [4, 2]:
                local = 32//partitions
                indices.append([p*local+b+lane for p in range(partitions) for b in range(step*2, local, s*2) for lane in range(2)])
            assert indices[0] == indices[1]
            seen += indices[0]
        assert sorted(seen) == list(range(32))
        # Integer products have exact equality; no floating-point associativity claim.
        for i in range(8):
            for j in range(12):
                assert sum((i+2*t)*(3*t-j) for t in seen) == sum((i+2*t)*(3*t-j) for t in range(32))
    return dict(matrix_sizes=True, ring_bytes=True, pipeline_event_schedule=True, blocked_contraction_indices=True, selected_slices=16)


def verify():
    manifest = json.loads((DEST / 'manifest.json').read_text())
    for key in ['program', 'query']:
        assert digest(ROOT / manifest[key + '_file']) == manifest[key + '_sha256']
    query = json.loads((ROOT / manifest['query_file']).read_text())['message']
    papers = manifest['papers']
    assert len(papers) == len({p['doi'] for p in papers}) == 135
    assert len(query['items']) == manifest['query_returned_items'] == 1000
    assert sum(x['DOI'].startswith('10.1145/3695053.') for x in query['items']) == 135
    volume = json.loads((DEST / 'volume-3695053.json').read_text())['message']
    assert volume['DOI'] == manifest['volume_doi'] == '10.1145/3695053'
    assert volume['ISBN'] == ['9798400712616'] and volume['published']['date-parts'] == [[2025, 6, 20]]
    isbn_query = json.loads((DEST / 'isbn-query.json').read_text())['message']
    assert isbn_query['total-results'] == len(isbn_query['items']) == 1
    assert isbn_query['items'][0]['DOI'] == volume['DOI']
    variants = json.loads((DEST / 'title-variants.json').read_text())
    assert variants['query_sha256'] == manifest['query_sha256']
    assert variants['program_sha256'] == manifest['program_sha256']
    assert len(variants['records']) == 1
    for p in papers:
        item = query['items'][p['metadata_source_index']]
        assert p['doi'] == item['DOI'] and p['publisher_title'] == item['title'][0]
        assert p['publisher_authors'] == item['author'] and not item.get('abstract')
        if p['program_order'] == 117:
            v = variants['records'][0]
            assert p['identity_method'] == 'reviewed_title_and_authors'
            assert v['doi'] == p['doi'] and v['publisher_authors'] == item['author']
            assert normalized(p['publisher_title'] + p['publisher_subtitle'][0]) == normalized(p['program_title'])
            assert normalized(', '.join(' '.join([a['given'], a['family']]) for a in item['author'])) == normalized(p['program_authors'])
        else:
            assert p['identity_method'] == 'normalized_title_exact'
            assert normalized(p['program_title']) == normalized(p['publisher_title'])
    sources = {s['id']: s for s in json.loads((DEST / 'selected-sources.json').read_text())}
    for source in sources.values():
        data = (ROOT / source['file']).read_bytes()
        assert hashlib.sha256(data).hexdigest() == source['sha256'] and len(data) == source['bytes']
    locations = json.loads((DEST / 'public-location-map.json').read_text())['papers']
    assert len(locations) == 135 and {p['doi'] for p in locations} == {p['doi'] for p in papers}
    for row in locations:
        original = json.loads((ROOT / row['source_file']).read_text())['results'][row['item_index']]
        assert original['doi'] == 'https://doi.org/' + row['doi']
        assert original['id'] == row['openalex_id']
    proof = json.loads((DEST / 'public-abstracts.json').read_text())
    readings = proof['papers']
    expected_orders = {3, 5, 9, 10, 11, 13, 14, 18, 20, 21, 31, 32, 33, 34, 35, 37, 53, 54, 55, 57, 64, 65, 66, 70, 77, 79, 86, 91, 95, 98, 101, 109, 112, 113, 115, 117, 122, 129, 132}
    assert {p['program_order'] for p in readings} == expected_orders and len(readings) == 39
    assert not proof['downloaded_code_executed']
    for item in readings:
        p = next(p for p in papers if p['doi'] == item['doi'])
        assert (p['program_order'], p['publisher_title']) == (item['program_order'], item['publisher_title'])
        expected_status = 'selected_sections_read' if p['program_order'] in {33, 55} else 'abstract_screened'
        assert p['reading_status'] == item['reading_status'] == expected_status
        assert p['abstract'] == item['abstract'] and p['screening'] == item['screening']
        assert p['reading_proof'] == 'public-abstracts.json'
        assert item['read_scope']['complete_abstract'] and not item['read_scope']['body_read']
        n = p['program_order']
        if item['source_kind'] == 'public_pdf':
            for key in ['pdf', 'text']:
                data = (ROOT / item[key + '_file']).read_bytes()
                assert hashlib.sha256(data).hexdigest() == item[key + '_sha256']
                assert len(data) == item[key + '_bytes']
            pdf = ROOT / item['pdf_file']
            assert pdf.read_bytes().startswith(b'%PDF-')
            info = subprocess.check_output(['pdfinfo', str(pdf)], text=True, stderr=subprocess.PIPE)
            assert int(re.search(r'^Pages:\s+(\d+)', info, re.M)[1]) == item['pdf_pages'] == p['pdf_pages']
            args = ['pdftotext'] + (['-raw'] if item['text_extraction']['raw'] else []) + ['-f', '1', '-l', '2', str(pdf), '-']
            fresh = subprocess.check_output(args, text=True, stderr=subprocess.PIPE)
            assert fresh == (ROOT / item['text_file']).read_text()
            assert normalized(item['public_copy_title']) in normalized(fresh)
            aliases = item.get('reviewed_author_aliases', {})
            assert aliases == ({'Ajit Matthews': 'Ajit Mathews'} if n == 112 else {})
            assert all(normalized(aliases.get(name, name)) in normalized(fresh) for a in p['publisher_authors'] for name in [' '.join([a.get('given', ''), a['family']])])
            if n == 112:
                assert p['doi'] == '10.1145/3695053.3731409' and p['doi'] in fresh
                alt = item['alternate_public_copy']
                alt_pdf, alt_text = ROOT / alt['pdf_file'], ROOT / alt['text_file']
                assert digest(alt_pdf) == alt['pdf_sha256'] and alt_pdf.stat().st_size == alt['pdf_bytes']
                assert digest(alt_text) == alt['text_sha256']
                alt_fresh = subprocess.check_output(['pdftotext', '-raw', '-f', '1', '-l', '2', str(alt_pdf), '-'], text=True)
                assert alt_fresh == alt_text.read_text() and normalized(p['publisher_title']) in normalized(alt_fresh)
                assert alt['pdf_pages'] == int(re.search(r'^Pages:\s+(\d+)', subprocess.check_output(['pdfinfo', str(alt_pdf)], text=True), re.M)[1]) == 12
                assert alt['publisher_authors_absent_in_copy'] == ['Xun Jiao', 'Jiyuan Zhang']
                assert all(normalized(name) not in normalized(alt_fresh) for name in alt['publisher_authors_absent_in_copy'])
                assert sources[alt['source_id']]['sha256'] == alt['pdf_sha256']
            spans = item['abstract_char_ranges']
            extracted = '\n'.join(fresh[lo:hi].strip() for lo, hi in spans)
            assert len(spans) == (2 if n in {14, 32, 53, 101, 115} else 1)
            for (lo, hi), marker in zip(spans, item['abstract_end_markers']):
                assert fresh[hi:].startswith(marker)
                assert fresh[:lo].count('\f') + 1 == (2 if n in {20, 57} else 1)
            assert item['read_scope']['physical_pages'] == ([2] if n in {20, 57} else [1])
            assert 'Permission to make' not in extracted and 'CCS Concepts' not in extracted
            source_records = json.loads((ROOT / item['source_manifest']).read_text())
            source = next(s for s in source_records if s['id'] == item['source_id'])
            assert source['sha256'] == item['pdf_sha256'] and source['bytes'] == item['pdf_bytes']
            if n == 115:
                assert item['reused_existing_pdf'] and source['version_in_text'] == '2505.09343v2'
            else:
                assert source['status_code'] == 200 and source['file'] == item['pdf_file']
                assert source['reading_status'] == expected_status
        else:
            data = (ROOT / item['source_file']).read_bytes()
            assert hashlib.sha256(data).hexdigest() == item['source_sha256']
            assert 'pdf_file' not in p and 'pdf_pages' not in p
            if n == 37:
                doc = BeautifulSoup(data, 'html.parser')
                extracted = doc.select_one(item['abstract_selector']).get_text(' ', strip=True)
                assert doc.select_one('main h1').get_text(' ', strip=True) == item['source_title']
                assert any(a['href'] == 'https://dl.acm.org/doi/full/' + p['doi'] for a in doc.select('a[href]'))
                authors = doc.select_one('.publication-authors__content').get_text(' ', strip=True).replace('*', '').split(', ')
                assert authors == [' '.join([a['given'], a['family']]) for a in p['publisher_authors']]
            elif n == 54:
                doc = BeautifulSoup(data, 'html.parser')
                extracted = doc.select_one(item['abstract_selector']).get_text(' ', strip=True)
                meta = lambda name: doc.select_one(f'meta[name="{name}"]')['content']
                assert meta('citation_doi') == p['doi']
                assert normalized(meta('citation_title')) == normalized(p['publisher_title'])
                assert [normalized(x['content']) for x in doc.select('meta[name="citation_author"]')] == [normalized(' '.join([a['given'], a['family']])) for a in p['publisher_authors']]
                assert meta('citation_publication_date') == '2025/06/21'
            else:
                assert n == 86
                entity = json.loads(data)['entityDescription']
                extracted = entity['abstract']
                assert entity['mainTitle'] == p['publisher_title']
                assert entity['reference']['doi'] == 'https://doi.org/' + p['doi']
                assert entity['publicationDate']['year'] == '2025'
                assert [c['identity']['name'] for c in entity['contributors']] == [' '.join([a['given'], a['family']]) for a in p['publisher_authors']]
            assert hashlib.sha256(extracted.encode()).hexdigest() == item['abstract_sha256']
        assert extracted == item['abstract'] and len(extracted) > 500
    assert {(p['program_order'], p['physical_page']) for p in proof['first_page_visual_checks']} == {(14, 1), (20, 2), (32, 1), (33, 1), (53, 1), (57, 1), (57, 2), (95, 1), (98, 1), (101, 1), (112, 1), (115, 1)}
    for image in proof['first_page_visual_checks']:
        assert image['actually_viewed'] and image['physical_page'] in {1, 2}
        assert digest(ROOT / image['file']) == image['sha256']
    assert sum('screening' in p for p in papers) == 39
    assert sum('pdf_file' in p for p in papers) == 36
    assert sum(p.get('pdf_pages', 0) for p in papers) == 549
    expanded = json.loads((DEST / 'expanded-abstracts.json').read_text())
    assert len(expanded['papers']) == expanded['new_complete_abstracts'] == 20
    assert expanded['new_representative_pdfs'] == 19 and expanded['new_representative_pdf_pages'] == 284
    assert expanded['additional_version_copies'] == 1 and expanded['additional_version_pages'] == 12
    for row in expanded['papers']:
        current = next(x for x in readings if x['doi'] == row['doi'])
        # Expanded batch is the historical abstract decision, before selected body reading.
        omitted = {'selected_reading', 'reading_status', 'screening'} if row['program_order'] == 55 else set()
        assert {k:v for k,v in current.items() if k not in omitted} == {k:v for k,v in row.items() if k not in omitted}
    selected = [p for p in papers if 'selected_reading' in p]
    assert [p['program_order'] for p in selected] == [33, 55]
    for order, stem, first, last, figure_pages in [(33, 'oaken', 2, 12, {6, 7, 11, 12}), (55, 'meshslice', 3, 13, {5, 6, 12})]:
        body = json.loads((DEST / (stem + '-reading.json')).read_text())
        reading = body['reading']
        p = next(p for p in selected if p['program_order'] == order)
        assert p['selected_reading'] == reading == next(p['selected_reading'] for p in readings if p['program_order'] == order)
        assert body['doi'] == p['doi'] and not body['downloaded_code_executed']
        assert reading['physical_pdf_pages'] == list(range(first, last+1))
        pdf = ROOT / reading['individual_pdf']
        assert digest(pdf) == reading['pdf_sha256']
        fresh = subprocess.check_output(['pdftotext', '-raw', '-f', str(first), '-l', str(last), str(pdf), '-'], text=True)
        assert fresh == (ROOT / reading['text_file']).read_text()
        assert digest(ROOT / reading['text_file']) == reading['text_sha256']
        for n in reading['physical_pdf_pages']:
            page = subprocess.check_output(['pdftotext', '-raw', '-f', str(n), '-l', str(n), str(pdf), '-'])
            assert hashlib.sha256(page).hexdigest() == reading['page_text_sha256'][str(n)]
        assert {x['physical_page'] for x in body['figures']} == figure_pages
        for figure in body['figures']:
            assert figure['actually_viewed'] and digest(ROOT / figure['file']) == figure['sha256']
    arithmetic = verify_mesh_arithmetic()
    report = dict(verified_at=datetime.now(timezone.utc).isoformat(), program_papers=135, normalized_title_matches=134, reviewed_title_subtitle_variant=1, primary_abstracts_screened=39, primary_abstracts_remaining=96, public_pdfs=36, newly_downloaded_pdfs=35, reused_existing_pdfs=1, pdf_pages=549, additional_version_copies=1, additional_version_pages=12, institutional_abstracts_without_pdf=3, selected_sections_read=2, selected_pages=22, mesh_slicing_arithmetic=arithmetic, source_responses=len(sources), failed_responses=sum(s['status_code'] >= 400 for s in sources.values()), scope='Program identities, declared complete abstracts, Oaken physical pages 2–12 and MeshSlice pages 3–13; representative PDFs exclude the additional MTIA version; not a complete public volume or whole-paper reading claim.')
    (Path(__file__).parent / 'isca2025-audit.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    return report


if __name__ == '__main__':
    print(json.dumps(verify(), ensure_ascii=False, indent=2))
