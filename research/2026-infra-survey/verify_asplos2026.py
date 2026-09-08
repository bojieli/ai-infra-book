#!/usr/bin/env python3
"""Verify archived identities and declared ASPLOS 2026 abstract scopes offline."""
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
import csv
import hashlib
import json
import re
import subprocess
import sys
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[2]
DEST = ROOT / 'references/proceedings/ASPLOS/2026'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify():
    manifest = json.loads((DEST / 'manifest.json').read_text())
    assert sha(ROOT / manifest['program_file']) == manifest['program_sha256']
    assert sha(ROOT / manifest['identity_map']) == manifest['identity_map_sha256']
    mapping = json.loads((ROOT / manifest['identity_map']).read_text())
    papers = manifest['papers']
    assert len(papers) == len({p['doi'] for p in papers}) == 168
    for paper, identity in zip(papers, mapping['papers']):
        for key in identity:
            if key != 'reading_status':
                assert paper[key] == identity[key], (paper['program_order'], key)
    sources = json.loads((DEST / 'sources.json').read_text())
    assert len(sources) == len({s['id'] for s in sources})
    reused = json.loads((ROOT / 'references/proceedings/catalog-review/2026-09-08/sources.json').read_text())
    by_id = {s['id']: s for s in sources + reused}
    for source in sources:
        path = ROOT / source['file']
        assert path.stat().st_size == source['bytes'] and sha(path) == source['sha256']
        assert source['reading_status'] != 'downloaded_not_read'
    locations = json.loads((DEST / 'public-location-map.json').read_text())
    for record in locations['records']:
        path = ROOT / record['source_file']
        assert sha(path) == record['source_sha256']
        row = json.loads(path.read_text())['results'][record['source_index']]
        assert record['doi'] == row['doi'].removeprefix('https://doi.org/').lower()
        assert record['locations'] == row['locations'] and record['openalex_id'] == row['id']
        assert papers[record['program_order'] - 1]['doi'] == record['doi']
    for name, count, returned in locations['query_counts']:
        response = json.loads((DEST / name).read_text())
        assert count == response['meta']['count'] and returned == len(response['results'])
    assert set(locations['missing_dois']) == {p['doi'] for p in papers} - {r['doi'] for r in locations['records']}
    proof = json.loads((DEST / 'public-abstracts.json').read_text())
    assert not proof['downloaded_code_executed'] and not proof['hardware_experiments_run']
    readings = proof['papers']
    with (ROOT / 'research/2026-infra-survey/screening-asplos-2026.tsv').open() as file:
        screens = {int(r['program_order']): r for r in csv.DictReader(file, delimiter='\t')}
    assert set(screens) == {r['program_order'] for r in readings}
    pages = images = pdfs = reused_pdfs = 0
    for record in readings:
        n = record['program_order']; paper = papers[n - 1]
        assert record['doi'] == paper['doi']
        assert record['published_title'] == paper['published_title_text']
        assert record['read_scope']['complete_abstract']
        assert record['read_scope']['body_read'] == ('selected_reading' in record)
        assert record['reading_status'] == paper['reading_status']
        assert record['abstract'] == paper['abstract']
        assert hashlib.sha256(record['abstract'].encode()).hexdigest() == record['abstract_sha256']
        assert {k: screens[n][k] for k in ('basis', 'decision', 'reason')} == paper['screening'] == record['screening']
        source = by_id[record['source_id']]
        if 'pdf_file' in record:
            pdf = ROOT / record['pdf_file']; pdfs += 1
            assert source['file'] == record['pdf_file'] and sha(pdf) == record['pdf_sha256'] == source['sha256']
            info = subprocess.check_output(['pdfinfo', str(pdf)], text=True, stderr=subprocess.PIPE)
            assert int(re.search(r'^Pages:\s+(\d+)', info, re.M)[1]) == record['pdf_pages']
            pages += record['pdf_pages']; reused_pdfs += record['source_id'].startswith('catalog-review-')
            raw = subprocess.check_output(['pdftotext', '-raw', '-f', '1', '-l', '2', str(pdf), '-'], text=True, stderr=subprocess.PIPE)
            assert raw == (ROOT / record['screen_file']).read_text()
            assert sha(ROOT / record['screen_file']) == record['screen_sha256']
            previous_end = -1
            for start, end in record['abstract_ranges']:
                assert previous_end <= start < end <= len(raw)
                assert raw.count('\f', 0, start) + 1 in record['read_scope']['physical_pages']
                assert raw.count('\f', 0, end - 1) + 1 in record['read_scope']['physical_pages']
                previous_end = end
            abstract = ''.join(raw[a:b] for a, b in record['abstract_ranges'])
            for before, after in record['extraction_glyph_corrections'].items():
                assert before in abstract
                abstract = abstract.replace(before, after)
            abstract = ' '.join(re.sub(r'(?<=\w)-\n(?=\w)', '', abstract).split())
            assert abstract == record['abstract']
            assert record['identity']['doi_present'] == (paper['doi'] in raw)
            if record['identity']['arxiv_version']:
                assert 'arXiv:' + record['identity']['arxiv_version'] in raw
            assert sha(ROOT / record['archive_text_file']) == record['archive_text_sha256']
            for viewed in record.get('viewed_pages', []):
                assert viewed['actually_viewed'] and viewed['physical_page'] in record['read_scope']['physical_pages']
                assert sha(ROOT / viewed['file']) == viewed['sha256']; images += 1
        else:
            path = ROOT / record['html_file']
            assert sha(path) == record['html_sha256'] == source['sha256']
            soup = BeautifulSoup(path.read_text(), 'html.parser')
            assert soup.select_one(record['abstract_selector']).get_text(' ', strip=True) == record['abstract']
            if record['identity'].get('metadata_scheme') == 'eprints':
                assert soup.select_one('meta[name="eprints.id_number"]')['content'] == record['doi']
                assert soup.select_one('meta[name="eprints.abstract"]')['content'] == record['abstract']
                assert soup.select_one('meta[name="eprints.title"]')['content'] == record['public_title']
                assert [s['content'] for s in soup.select('meta[name="eprints.creators_name"]')] == record['identity']['citation_authors']
            else:
                assert soup.select_one('meta[name="citation_doi"]')['content'] == record['doi']
                assert [s['content'] for s in soup.select('meta[name="citation_author"]')] == record['identity']['citation_authors']
    assert sum('screening' in p for p in papers) == len(readings)
    expanded_path = DEST / 'expanded-screening-notes.json'
    if expanded_path.exists():
        expanded = json.loads(expanded_path.read_text())
        assert not expanded['downloaded_code_executed'] and not expanded['book_outline_changed']
        expanded_readings = [r for r in readings if r['program_order'] in expanded['new_abstract_orders']]
        assert len(expanded_readings) == len(expanded['new_abstract_orders'])
        assert sum(r['pdf_pages'] for r in expanded_readings) == expanded['new_pdf_pages']
        # The expansion record describes that earlier phase; later selected readings
        # must not invalidate its historically correct zero-body scope.
        assert expanded['body_sections_read'] == 0
        for r in expanded_readings:
            if r['read_scope']['body_read']:
                later = json.loads((ROOT / r['selected_reading']['record_file']).read_text())
                assert later['recorded_at'] > expanded['recorded_at']
        for item in expanded['publication_entries']:
            path = ROOT / item['file']
            assert sha(path) == item['sha256'] == by_id[item['source_id']]['sha256']
            soup = BeautifulSoup(path.read_text(), 'html.parser')
            node = soup.select(item['selector'])[item['selector_index']]
            assert node.get_text(' ', strip=True) + '\n' == (ROOT / item['text_file']).read_text()
            assert sha(ROOT / item['text_file']) == item['text_sha256']
            assert [dict(text=a.get_text(' ', strip=True), href=a['href']) for a in node.select('a[href]')] == item['links']
        assert all('screening' not in papers[n - 1] for n in expanded['remaining_gap_orders'])
    selected = [p for p in readings if 'selected_reading' in p]
    midprogram_path = DEST / 'midprogram-screening-notes.json'
    related_pdf_pages = related_pdfs = 0
    if midprogram_path.exists():
        phase = json.loads(midprogram_path.read_text())
        assert not phase['book_outline_changed'] and not phase['downloaded_code_executed']
        assert not phase['hardware_experiments_run'] and phase['body_sections_read'] == 0
        batch = [r for r in readings if r['program_order'] in phase['new_abstract_orders']]
        assert len(batch) == phase['new_abstracts'] == 15
        assert sum(r.get('pdf_pages', 0) for r in batch) == phase['new_representative_pdf_pages']
        assert [r['program_order'] for r in batch if 'pdf_file' in r] == phase['new_representative_pdf_orders']
        assert dict(Counter(r['screening']['decision'] for r in batch)) == phase['decisions']
        assert len(phase['new_response_ids']) == len(set(phase['new_response_ids'])) == 29
        assert all(sid in by_id for sid in phase['new_response_ids'])
        for item in phase['source_followups']:
            path = ROOT / item['file']
            assert sha(path) == item['sha256'] == by_id[item['source_id']]['sha256']
            node = BeautifulSoup(path.read_text(), 'html.parser').select_one(item['selector'])
            assert node.get_text(' ', strip=True) + '\n' == (ROOT / item['text_file']).read_text()
            assert sha(ROOT / item['text_file']) == item['text_sha256']
        starc_meta = (DEST / 'starc-arxiv-metadata-selected.txt').read_text()
        assert 'Early preprint' in starc_meta and '10.1145/3779212.3790226' in starc_meta
        assert 'simulated HBM-PIM' in (DEST / 'starc-ibm-selected.txt').read_text()
        assert 'IEEE CAL), 2024' in (DEST / 'straw-arxiv-metadata-selected.txt').read_text()
        nebula = next(r for r in batch if r['program_order'] == 54)
        assert nebula['abstract'].count('1925%') == 2
        assert not nebula['extraction_glyph_corrections']
        for item in phase['related_prior_work']:
            pdf = ROOT / item['pdf_file']; related_pdfs += 1
            assert sha(pdf) == item['pdf_sha256'] == by_id[item['source_id']]['sha256']
            assert not any(r.get('pdf_file') == item['pdf_file'] for r in readings)
            info = subprocess.check_output(['pdfinfo', str(pdf)], text=True, stderr=subprocess.PIPE)
            assert int(re.search(r'^Pages:\s+(\d+)', info, re.M)[1]) == item['pdf_pages']
            related_pdf_pages += item['pdf_pages']
            raw = subprocess.check_output(['pdftotext', '-raw', '-f', '1', '-l', '2', str(pdf), '-'], text=True, stderr=subprocess.PIPE)
            assert raw == (ROOT / item['screen_file']).read_text()
            assert sha(ROOT / item['screen_file']) == item['screen_sha256']
            abstract = ''.join(raw[a:b] for a, b in item['abstract_ranges'])
            assert ' '.join(re.sub(r'(?<=\w)-\n(?=\w)', '', abstract).split()) == item['abstract']
            viewed = item['viewed_page']
            assert viewed['actually_viewed'] and sha(ROOT / viewed['file']) == viewed['sha256']
        # Gap lists describe this phase. Future completed readings may supersede them.
        assert set(phase['remaining_gap_orders']).isdisjoint(phase['new_abstract_orders'])
    program56_path = DEST / 'program56-screening-notes.json'
    if program56_path.exists():
        phase = json.loads(program56_path.read_text())
        assert not phase['book_outline_changed'] and phase['body_sections_read'] == 0
        assert not phase['downloaded_code_executed'] and not phase['hardware_experiments_run']
        batch = [r for r in readings if r['program_order'] in phase['new_abstract_orders']]
        assert len(batch) == phase['new_abstracts'] == 18
        assert sum(r['pdf_pages'] for r in batch) == phase['new_representative_pdf_pages'] == 338
        assert [r['program_order'] for r in batch] == phase['new_representative_pdf_orders']
        assert Counter(r['screening']['decision'] for r in batch) == phase['decisions']
        assert sum(len(r.get('viewed_pages', [])) for r in batch) == phase['viewed_abstract_pages'] == 11
        fetched = []
        for item in phase['fetch_batches']:
            path = ROOT / item['file']; assert sha(path) == item['sha256']
            fetched.extend(r['id'] for r in json.loads(path.read_text()) if 'id' in r)
        assert fetched == phase['new_response_ids'] and len(set(fetched)) == 30
        fetched_sources = [by_id[sid] for sid in fetched]
        assert phase['response_counts'] == dict(
            pdf=sum(s['file'].endswith('.pdf') for s in fetched_sources),
            html_success=sum(s['status_code'] == 200 and s['file'].endswith('.html') for s in fetched_sources),
            http_403=sum(s['status_code'] == 403 for s in fetched_sources))
        for item in phase['source_followups']:
            path = ROOT / item['file']
            assert sha(path) == item['sha256'] == by_id[item['source_id']]['sha256']
            node = BeautifulSoup(path.read_text(), 'html.parser').select(item['selector'])[item['selector_index']]
            assert node.get_text(' ', strip=True) + '\n' == (ROOT / item['text_file']).read_text()
            assert sha(ROOT / item['text_file']) == item['text_sha256']
            links = ([node] if node.name == 'a' else []) + node.select('a[href]')
            assert [dict(text=a.get_text(' ', strip=True), href=a['href']) for a in links] == item['links']
        assert set(phase['remaining_gap_orders']).isdisjoint(phase['new_abstract_orders'])
    program81_path = DEST / 'program81-screening-notes.json'
    if program81_path.exists():
        phase = json.loads(program81_path.read_text())
        assert not phase['book_outline_changed'] and phase['body_sections_read'] == 0
        assert not phase['downloaded_code_executed'] and not phase['hardware_experiments_run']
        assert set(phase['new_abstract_orders']) == set(range(81, 106)) - {83, 90, 93, 103}
        batch = [r for r in readings if r['program_order'] in phase['new_abstract_orders']]
        assert len(batch) == phase['new_abstracts'] == 21
        assert sum(r['pdf_pages'] for r in batch) == phase['new_representative_pdf_pages'] == 353
        assert [r['program_order'] for r in batch] == phase['new_representative_pdf_orders']
        assert Counter(r['screening']['decision'] for r in batch) == phase['decisions']
        assert sum(len(r.get('viewed_pages', [])) for r in batch) == phase['actually_viewed_page_count'] == 11
        fetched = []
        for name in ['fetch-program81.json', 'fetch-program81-followup.json']:
            fetched.extend(r['id'] for r in json.loads((DEST / name).read_text()))
        assert fetched == phase['new_response_ids'] and len(set(fetched)) == 27
        assert sum(by_id[sid]['status_code'] == 403 for sid in fetched) == 4
        for item in phase['source_followups']:
            path = ROOT / item['file']
            assert sha(path) == item['sha256'] == by_id[item['source_id']]['sha256']
            node = BeautifulSoup(path.read_text(), 'html.parser').select(item['selector'])[item['selector_index']]
            assert node.get_text(' ', strip=True) + '\n' == (ROOT / item['text_file']).read_text()
            assert sha(ROOT / item['text_file']) == item['text_sha256']
            assert [dict(text=a.get_text(' ', strip=True), href=a['href']) for a in node.select('a[href]')] == item['links']
        assert set(phase['remaining_gap_orders']).isdisjoint(phase['new_abstract_orders'])
    program106_path = DEST / 'program106-screening-notes.json'
    if program106_path.exists():
        phase = json.loads(program106_path.read_text())
        assert not phase['book_outline_changed'] and phase['body_sections_read'] == 0
        assert not phase['downloaded_code_executed'] and not phase['hardware_experiments_run']
        assert set(phase['new_abstract_orders']) == set(range(106, 131)) - set(phase['remaining_gap_orders'])
        batch = [r for r in readings if r['program_order'] in phase['new_abstract_orders']]
        assert len(batch) == phase['new_abstracts'] == 15
        assert sum(r.get('pdf_pages', 0) for r in batch) == phase['new_representative_pdf_pages'] == 242
        assert [r['program_order'] for r in batch if 'pdf_file' in r] == phase['new_representative_pdf_orders']
        assert Counter(r['screening']['decision'] for r in batch) == phase['decisions']
        assert sum(len(r.get('viewed_pages', [])) for r in batch) == phase['viewed_representative_pages'] == 7
        responses = []
        for item in phase['fetch_batches']:
            path = ROOT / item['file']; assert sha(path) == item['sha256']
            responses.extend(json.loads(path.read_text()))
        ids = [r['id'] for r in responses if 'id' in r]
        assert ids == phase['new_response_ids'] and len(ids) == len(set(ids)) == 38
        assert phase['response_counts'] == dict(
            pdf=sum(by_id[sid]['file'].endswith('.pdf') for sid in ids),
            http_403=sum(by_id[sid]['status_code'] == 403 for sid in ids),
            http_404=sum(by_id[sid]['status_code'] == 404 for sid in ids),
            successful=sum(by_id[sid]['status_code'] == 200 for sid in ids),
            errors_without_response=sum('id' not in r for r in responses))
        for item in phase['source_followups']:
            path = ROOT / item['file']
            assert sha(path) == item['sha256'] == by_id[item['source_id']]['sha256']
            node = BeautifulSoup(path.read_text(), 'html.parser').select(item['selector'])[item['selector_index']]
            assert node.get_text(' ', strip=True) + '\n' == (ROOT / item['text_file']).read_text()
            assert sha(ROOT / item['text_file']) == item['text_sha256']
            links = ([node] if node.name == 'a' else []) + node.select('a[href]')
            assert [dict(text=a.get_text(' ', strip=True), href=a['href']) for a in links] == item['links']
        for item in phase['text_followups']:
            path = ROOT / item['file']
            assert sha(path) == item['sha256'] == by_id[item['source_id']]['sha256']
            assert path.read_text()[item['start']:item['end']] == (ROOT / item['text_file']).read_text()
            assert sha(ROOT / item['text_file']) == item['text_sha256']
        for item in phase['json_followups']:
            path = ROOT / item['file']; raw = json.loads(path.read_text())
            assert sha(path) == item['sha256'] == by_id[item['source_id']]['sha256']
            assert {k: raw[k] for k in item['fields']} == json.loads((ROOT / item['selected_file']).read_text())
            assert sha(ROOT / item['selected_file']) == item['selected_sha256']
        for item in phase['related_prior_work']:
            pdf = ROOT / item['pdf_file']; related_pdfs += 1
            assert sha(pdf) == item['pdf_sha256'] == by_id[item['source_id']]['sha256']
            assert not any(r.get('pdf_file') == item['pdf_file'] for r in readings)
            info = subprocess.check_output(['pdfinfo', str(pdf)], text=True, stderr=subprocess.PIPE)
            assert int(re.search(r'^Pages:\s+(\d+)', info, re.M)[1]) == item['pdf_pages']
            related_pdf_pages += item['pdf_pages']
            raw = subprocess.check_output(['pdftotext', '-raw', '-f', '1', '-l', '2', str(pdf), '-'], text=True, stderr=subprocess.PIPE)
            assert raw == (ROOT / item['screen_file']).read_text()
            assert sha(ROOT / item['screen_file']) == item['screen_sha256']
            assert sha(ROOT / item['archive_text_file']) == item['archive_text_sha256']
            abstract = ''.join(raw[a:b] for a, b in item['abstract_ranges'])
            assert ' '.join(re.sub(r'(?<=\w)-\n(?=\w)', '', abstract).split()) == item['abstract']
            viewed = item['viewed_page']
            assert viewed['actually_viewed'] and sha(ROOT / viewed['file']) == viewed['sha256']
            assert 'arXiv:2212.05614v1' in raw
        assert phase['actually_viewed_page_count'] == phase['viewed_representative_pages'] + len(phase['related_prior_work']) == 8
    tail_path = DEST / 'program-tail-screening-notes.json'
    if tail_path.exists():
        phase = json.loads(tail_path.read_text())
        assert not phase['book_outline_changed'] and not phase['skeleton_changed']
        assert not phase['case_notes_changed'] and phase['body_sections_read'] == 0
        assert not phase['downloaded_code_executed'] and not phase['hardware_experiments_run']
        batch = [r for r in readings if r['program_order'] in phase['new_abstract_orders']]
        assert len(batch) == phase['new_abstracts'] == 21
        assert sum(r.get('pdf_pages', 0) for r in batch) == phase['new_representative_pdf_pages'] == 343
        assert [r['program_order'] for r in batch if 'pdf_file' in r] == phase['new_representative_pdf_orders']
        assert Counter(r['screening']['decision'] for r in batch) == phase['decisions']
        assert sum(len(r.get('viewed_pages', [])) for r in batch) == phase['actually_viewed_page_count'] == 9
        fetched = []
        for item in phase['fetch_batches']:
            path = ROOT / item['file']; assert sha(path) == item['sha256']
            fetched.extend(r['id'] for r in json.loads(path.read_text()))
        assert fetched == phase['new_response_ids'] and len(set(fetched)) == 34
        assert Counter('pdf' if by_id[sid]['file'].endswith('.pdf') else 'html' for sid in fetched) == phase['response_counts']
        assert Counter(str(by_id[sid]['status_code']) for sid in fetched) == phase['response_status_counts']
        for item in phase['source_followups']:
            path = ROOT / item['file']
            assert sha(path) == item['sha256'] == by_id[item['source_id']]['sha256']
            node = BeautifulSoup(path.read_text(), 'html.parser').select(item['selector'])[item['selector_index']]
            assert node.get_text(' ', strip=True) + '\n' == (ROOT / item['text_file']).read_text()
            assert sha(ROOT / item['text_file']) == item['text_sha256']
            links = ([node] if node.name == 'a' else []) + node.select('a[href]')
            assert [dict(text=a.get_text(' ', strip=True), href=a['href']) for a in links] == item['links']
        for item in phase['negative_location_searches']:
            path = ROOT / item['file']
            assert sha(path) == item['sha256'] == by_id[item['source_id']]['sha256']
            text = BeautifulSoup(path.read_text(), 'html.parser').get_text(' ', strip=True).casefold()
            assert (item['needle'] in text) == item['match_found'] == False
        assert set(phase['remaining_gap_orders']).isdisjoint(phase['new_abstract_orders'])
        morphlux = next(r for r in batch if r['program_order'] == 150)
        assert not morphlux['identity']['doi_present']
        assert morphlux['identity']['arxiv_version'] == '2508.03674v3'
        assert morphlux['public_title'] != morphlux['published_title']
        assert 'inference' in morphlux['version_note']
        assert 'HAL, 2001' not in next(r for r in batch if r['program_order'] == 162)['abstract']
    if selected:
        from verify_shift_parallel import verify as verify_shift
        from verify_superoffload import verify as verify_superoffload
        from verify_attention_tiles import verify as verify_attention
        from verify_fusion_legality import verify as verify_fusion
        from verify_history_speculation import verify as verify_history
        from verify_optimization_evaluation import verify as verify_optimization
        from verify_remote_ordering import verify as verify_ordering
        from verify_configuration_wall import verify as verify_configuration
        from verify_memory_tiering import verify as verify_memory_tiering
        from verify_torus_allocation import verify as verify_torus_allocation
        from verify_metadata_quantization import verify as verify_metadata_quantization
        from verify_smartnic_policy import verify as verify_smartnic_policy
        validators = {4: verify_shift, 23: verify_superoffload, 41: verify_attention, 68: verify_fusion, 101: verify_history, 116: verify_ordering, 127: verify_optimization, 150: verify_torus_allocation, 151: verify_configuration, 155: verify_metadata_quantization, 168: verify_smartnic_policy}
        for item in selected:
            if item['program_order'] not in (145, 147):
                validators[item['program_order']]()
        if any(item['program_order'] in (145, 147) for item in selected):
            assert {145, 147} <= {item['program_order'] for item in selected}
            verify_memory_tiering()
    return dict(verified_at=datetime.now(timezone.utc).isoformat(), status='passed',
                scope='Program catalog, declared primary abstract screens and selected paper scopes; not complete conference reading.',
                program_papers=len(papers), responses=len(sources),
                location_records=len(locations['records']), location_distinct_dois=len({r['doi'] for r in locations['records']}),
                primary_abstracts_screened=len(readings), abstracts_pending=len(papers)-len(readings),
                representative_pdfs=pdfs, representative_pages=pages, reused_pdfs=reused_pdfs,
                new_pdfs=pdfs-reused_pdfs, viewed_abstract_pages=images,
                decisions=dict(Counter(r['screening']['decision'] for r in readings)), selected_sections_read=len(selected),
                related_prior_work_pdfs_not_counted=related_pdfs, related_prior_work_pages_not_counted=related_pdf_pages)


if __name__ == '__main__':
    report = verify()
    (Path(__file__).parent / 'asplos2026-audit.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(report, ensure_ascii=False, indent=2))
