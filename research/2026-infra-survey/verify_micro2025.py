#!/usr/bin/env python3
"""Verify MICRO 2025 catalog identities and declared primary abstract scopes."""
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter, deque
from fractions import Fraction
from bs4 import BeautifulSoup
import csv, hashlib, json, re, subprocess, sys

ROOT = Path(__file__).resolve().parents[2]
DEST = ROOT/'references/proceedings/MICRO/2025'
sys.path.insert(0,str(ROOT/'references'))
from reconcile_micro2024 import normalized


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_handoffs():
    """Check declared page evidence and teaching arithmetic independently."""
    records = []
    for name, order, pages in [('streamtensor', 14, list(range(3, 15))),
                               ('llm265', 30, list(range(4, 14)))]:
        r = json.loads((DEST / f'{name}-reading.json').read_text())
        assert r['program_order'] == order and r['physical_pages'] == pages
        assert not r['downloaded_code_executed'] and not r['hardware_experiments_run']
        assert sha(ROOT / r['pdf_file']) == r['pdf_sha256']
        assert [x['page'] for x in r['page_texts']] == pages
        texts = []
        for page in r['page_texts']:
            path = ROOT / page['file']
            assert sha(path) == page['sha256']
            fresh = subprocess.check_output(['pdftotext', '-layout', '-f', str(page['page']),
                '-l', str(page['page']), str(ROOT / r['pdf_file']), '-'], text=True, stderr=subprocess.PIPE)
            assert fresh == path.read_text()
            texts.append(fresh)
        assert ''.join(texts) == (ROOT / r['text_file']).read_text()
        assert sha(ROOT / r['text_file']) == r['text_sha256']
        for im in r['viewed_pages']:
            assert im['actually_viewed'] and im['physical_page'] in pages
            assert sha(ROOT / im['file']) == im['sha256']
        assert (ROOT / r['adoption']['case']).exists() and not r['adoption']['new_numbered_items']
        records.append(r)
    capabilities = json.loads((DEST / 'codec-capabilities-reading.json').read_text())
    for source in capabilities:
        path = ROOT / source['file']; assert sha(path) == source['sha256']
        tables = BeautifulSoup(path.read_text(), 'html.parser').select('table')
        for selected in source['tables']:
            rows = tables[selected['table_index']].select('tr')
            cells = lambda row: [c.get_text(' ', strip=True) for c in row.find_all(['th', 'td'], recursive=False)]
            assert cells(rows[0]) == selected['header']
            assert cells(rows[selected['row_index']]) == selected['cells']
    matrix = capabilities[1]['tables']
    for board, encoders in [('NVIDIA A100', '0'), ('NVIDIA H100 SXM', '0'), ('GeForce RTX 3090', '1')]:
        found = [r for r in matrix if r['cells'][0] == board and 'Total # of NVENC' in r['header']]
        assert len(found) == 1
        assert found[0]['cells'][found[0]['header'].index('Total # of NVENC')] == encoders

    x = json.loads((ROOT / 'research/2026-infra-survey/tensor-handoffs-arithmetic.json').read_text())
    config = json.loads((ROOT / 'references/outline-checks/2026-09-07/scaling-history/qwen3-8b-config.json').read_text())
    S = config['hidden_size'] * config['intermediate_size'] * 2
    w = x['weight']; assert w['shape'] == [config['hidden_size'], config['intermediate_size']]
    assert S == w['original_bytes'] == 96 * 2**20
    ratio = Fraction(1, 4); decode = Fraction(10**9)
    assert S * ratio == w['compressed_bytes'] == 24 * 2**20
    threshold = (1-ratio)*decode
    assert threshold == w['serial_break_even_link_bytes_per_second']
    for row in w['rows']:
        B = Fraction(row['link_bytes_per_second'])
        assert abs(float(S/B*1000) - row['raw_ms']) < 1e-9
        assert abs(float((ratio*S/B+S/decode)*1000) - row['preencoded_transfer_decode_ms']) < 1e-9
    for factor in [Fraction(1,2), Fraction(1), Fraction(2)]:
        B = threshold * factor
        saving = S/B-(ratio*S/B+S/decode)
        assert (saving > 0) == (factor < 1)
        assert (saving == 0) == (factor == 1)
    assert w['single_output_peak_bytes'] == 120*2**20
    assert w['double_output_peak_bytes'] == 216*2**20
    a = x['activation']; assert a['original_bytes'] == a['shape'][0]*config['hidden_size']*2 == 16*2**20
    online_threshold = (1-ratio)/(1/Fraction(a['encoding_original_bytes_per_second'])+1/decode)
    assert online_threshold == a['serial_break_even_link_bytes_per_second'] == 375_000_000
    f = x['fifo']; queue = deque(); peak = 0; consumed = []
    for time in range(max(f['consumption_times'])+1):
        if time in f['consumption_times']:
            assert queue, ('consumer has no ready input', time)
            consumed.append(queue.popleft())
        if time in f['production_times']:
            queue.append(f['production_times'].index(time))
        peak = max(peak, len(queue))
        assert len(queue) == sum(t <= time for t in f['production_times'])-sum(t <= time for t in f['consumption_times'])
    assert not queue and consumed == list(range(5)) and peak == f['peak_tiles'] == 3
    tile = f['tile_shape'][0]*f['tile_shape'][1]*f['dtype_bytes']
    assert tile == f['tile_bytes'] == 16*1024
    assert peak*tile == f['peak_fifo_bytes'] == 48*1024
    assert f['layout_converter_slots']*tile == f['layout_converter_bytes'] == 32*1024
    assert f['combined_bytes'] == f['layout_converter_bytes']+f['peak_fifo_bytes'] == 80*1024
    assert f['combined_bytes'] > f['available_handoff_bytes'] >= f['peak_fifo_bytes']
    return records


def verify():
    m = json.loads((DEST/'manifest.json').read_text())
    for key in ['program','query']:
        assert sha(ROOT/m[key+'_file']) == m[key+'_sha256']
    nodes = BeautifulSoup((ROOT/m['program_file']).read_text(),'html.parser').select('.paper')
    q = json.loads((ROOT/m['query_file']).read_text())['message']
    assert len(q['items']) == m['query_returned_items'] == 300
    assert q['total-results'] == m['query_reported_total']
    relevant = [x for x in q['items'] if x['DOI'].startswith(m['doi_prefix'])]
    papers = {p['program_order']:p for p in m['papers']}
    assert len(nodes) == len(papers) == len(relevant) == 123
    assert {p['doi'] for p in papers.values()} == {x['DOI'] for x in relevant}
    assert not any(x.get('abstract') for x in relevant)
    v = json.loads((DEST/'title-variants.json').read_text())
    assert v['program_sha256'] == m['program_sha256'] and v['query_sha256'] == m['query_sha256']
    reviews = {x['program_order']:x for x in v['records']}
    assert set(reviews) == {1,9,21,32,49,88,93}
    for n,p in papers.items():
        x = q['items'][p['metadata_source_index']]
        assert (p['doi'],p['publisher_title'],p['publisher_authors']) == (x['DOI'],x['title'][0],x['author'])
        assert p['program_title'] == nodes[n-1].select_one('.paper-title').get_text(' ',strip=True)
        assert p['program_authors'] == nodes[n-1].select_one('.paper-authors').get_text(' ',strip=True)
        if n in reviews:
            r = reviews[n]
            for key in ['doi','publisher_title','publisher_authors','program_title','program_authors']:
                assert p[key] == r[key]
            assert p['identity_method'] == 'reviewed_title_and_authors'
        else:
            assert normalized(p['program_title']) == normalized(p['publisher_title'])
            assert p['identity_method'] == 'normalized_title_exact'
    sources = json.loads((DEST/'sources.json').read_text())
    assert len(sources) == len({s['id'] for s in sources}) == 26
    assert sum(s['status_code'] != 200 for s in sources) == 2
    for s in sources:
        f = ROOT/s['file']
        assert f.stat().st_size == s['bytes'] and sha(f) == s['sha256']
        assert (s['reading_status'] == 'failed_response_not_evidence') == (s['status_code'] != 200)
    tls = [x for x in json.loads((DEST/'fetch-supplement.json').read_text()) if not x.get('response_body_received',True)]
    assert len(tls) == 1 and 'CertificateError' in tls[0]['error']
    locations = json.loads((DEST/'public-location-map.json').read_text())
    records = locations['records']; doIs = {r['doi'] for r in records}
    assert len(records) == 66 and len(doIs) == 65
    assert set(locations['missing_dois']) == {p['doi'] for p in papers.values()}-doIs
    assert len(locations['missing_dois']) == 58
    for r in records:
        assert sha(ROOT/r['source_file']) == r['source_sha256']
        x = json.loads((ROOT/r['source_file']).read_text())['results'][r['source_index']]
        assert r['doi'] == x['doi'].removeprefix('https://doi.org/').lower()
        assert r['openalex_id'] == x['id'] and r['locations'] == x['locations']
        assert papers[r['program_order']]['doi'] == r['doi']
    proof = json.loads((DEST/'public-abstracts.json').read_text())
    assert not proof['downloaded_code_executed']
    readings = proof['papers']; expected = {1,2,14,25,30,36,38,39,76,77,94,102,118}
    assert len(readings) == 13 and {p['program_order'] for p in readings} == expected
    with (ROOT/'research/2026-infra-survey/screening-micro-2025.tsv').open() as f:
        rows = {int(x['program_order']):x for x in csv.DictReader(f,delimiter='\t')}
    assert set(rows) == expected
    images = 0
    for p in readings:
        n = p['program_order']; mrow = papers[n]
        for key in ['doi','publisher_title','abstract','screening','reading_status','pdf_file','pdf_pages']:
            assert p[key] == mrow[key]
        assert p['read_scope']['complete_abstract']
        assert p['read_scope']['body_read'] == ('selected_reading' in p)
        assert p['screening']['basis'] == 'title_and_full_abstract'
        for key in ['decision','reason','basis']:assert rows[n][key] == p['screening'][key]
        for key in ['pdf','full_text','screen_text']:
            assert sha(ROOT/p[key+'_file']) == p[key+'_sha256']
        pdf = ROOT/p['pdf_file']; assert pdf.read_bytes().startswith(b'%PDF-') and pdf.stat().st_size == p['pdf_bytes']
        info = subprocess.check_output(['pdfinfo',str(pdf)],text=True,stderr=subprocess.PIPE)
        assert int(re.search(r'^Pages:\s+(\d+)',info,re.M)[1]) == p['pdf_pages']
        t = subprocess.check_output(['pdftotext','-raw','-f','1','-l','2',str(pdf),'-'],text=True,stderr=subprocess.PIPE)
        assert t == (ROOT/p['screen_text_file']).read_text()
        assert normalized(p['public_copy_title']) == normalized(p['publisher_title'])
        assert normalized(p['public_copy_title']) in normalized(t)
        authors = [' '.join(x.get(k,'') for k in ['given','family']) for x in mrow['publisher_authors']]
        assert authors == p['public_copy_authors'] and all(normalized(x) in normalized(t) for x in authors)
        ranges = p['abstract_ranges']
        a = p['abstract_join'].join(t[start:end] for start,end in ranges)
        assert a == p['abstract'] and hashlib.sha256(a.encode()).hexdigest() == p['abstract_sha256']
        page = 2 if n == 102 else 1
        assert p['abstract_physical_pages'] == [page]
        assert all(t[:start].count('\f')+1 == page for start,end in ranges)
        assert len(ranges) == (2 if n == 1 else 1)
        if n == 1:
            omitted = t[ranges[0][1]:ranges[1][0]]
            assert 'Equal contribution' in omitted and 'ACM ISBN' in omitted
        assert 'ACM Reference Format' not in a and 'This work is licensed' not in a
        if 'additional_abstract_source' in p:
            r = p['additional_abstract_source']; f = ROOT/r['file']; assert sha(f) == r['sha256']
            soup = BeautifulSoup(f.read_text(),'html.parser')
            extra = soup.select_one(r['selector']).get_text(' ',strip=True)
            assert extra == r['abstract'] and hashlib.sha256(extra.encode()).hexdigest() == r['abstract_sha256']
            assert normalized(extra) == normalized(a)
            assert soup.select_one('meta[name="citation_doi"]')['content'] == r['citation_doi'] == p['doi']
            assert r['complete_abstract_read'] and r['not_additional_paper']
        if 'visual_identity_check' in p:
            im = p['visual_identity_check']; assert im['actually_viewed'] and im['physical_page'] == page and sha(ROOT/im['file']) == im['sha256']; images += 1
        if 'additional_version' in p:
            r = p['additional_version']; assert n == 25 and not r['representative_copy']
            assert sha(ROOT/r['pdf_file']) == r['pdf_sha256']
            early = subprocess.check_output(['pdftotext','-raw','-f','1','-l','1',str(ROOT/r['pdf_file']),'-'],text=True,stderr=subprocess.PIPE)
            assert r['public_title'] in early and r['arxiv_version'] in early
            assert int(re.search(r'^Pages:\s+(\d+)',subprocess.check_output(['pdfinfo',str(ROOT/r['pdf_file'])],text=True,stderr=subprocess.PIPE),re.M)[1]) == r['pdf_pages'] == 15
    assert images == 7 and sum(p['pdf_pages'] for p in readings) == 208
    assert Counter(p['screening']['decision'] for p in readings) == dict(candidate=5,reference=4,exclude=4)
    selected = verify_handoffs()
    for r in selected:
        n = r['program_order']
        abstract = next(p for p in readings if p['program_order'] == n)
        assert r == abstract['selected_reading'] == papers[n]['selected_reading']
    assert {p['program_order'] for p in readings if 'selected_reading' in p} == {14,30}
    report = dict(verified_at=datetime.now(timezone.utc).isoformat(),program_papers=123,normalized_title_matches=116,reviewed_title_author_variants=7,source_responses=26,failed_http_responses=2,tls_failures_without_response=1,secondary_location_records=66,secondary_location_dois=65,primary_abstracts_screened=13,remaining_abstracts=110,public_pdfs=13,pdf_pages=208,additional_version_copies=1,additional_version_pages=15,abstract_identity_images_viewed=7,selected_sections_read=0,screening_decisions=dict(Counter(p['screening']['decision'] for p in readings)),scope='Official program identities and declared primary abstract reading only; not a complete proceedings download or body/evaluation reading.',errors=[])
    report.update(selected_sections_read=len(selected), selected_physical_pages=sum(len(r['physical_pages']) for r in selected), selected_page_images_viewed=sum(len(r['viewed_pages']) for r in selected), selected_source_responses=2, arithmetic='passed', scope='Official catalog, primary abstracts, selected physical pages and teaching arithmetic; not complete proceedings or implementation/performance verification.')
    (ROOT/'research/2026-infra-survey/micro2025-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    return report


if __name__ == '__main__':
    print(json.dumps(verify(),ensure_ascii=False,indent=2))
