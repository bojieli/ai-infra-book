#!/usr/bin/env python3
"""Verify public-copy identities, complete abstract spans and selected reading."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, html, json, re, subprocess, unicodedata
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[2]
DEST = ROOT / 'references/proceedings/ISCA/2024'

def verify():
    m = json.loads((DEST / 'manifest.json').read_text())
    for key in ['program', 'query']:
        assert hashlib.sha256((ROOT / m[key + '_file']).read_bytes()).hexdigest() == m[key + '_sha256']
    papers = m['papers']
    assert len(papers) == len({p['doi'] for p in papers}) == 87
    assert len(m['excluded_records']) == 11
    query = json.loads((ROOT / m['query_file']).read_text())['message']
    assert len(query['items']) == m['query_returned_items'] == 1000
    for p in papers:
        record = query['items'][p['source_item_index']]
        assert p['doi'] == record['DOI'].lower()
        assert p['publisher_title'] == record['title'][0]
        assert p['publisher_authors'] == record['author']
        assert record.get('abstract') is None
    reviews = json.loads((DEST / 'title-variants.json').read_text())['records']
    assert len(reviews) == sum(p['identity_method'] == 'reviewed_title_and_author_variant' for p in papers) == 17
    for v in reviews:
        p = next(x for x in papers if x['doi'] == v['doi'])
        assert p['program_title'] == v['program_title'] and p['publisher_title'] == v['publisher_title']
    reading = json.loads((DEST / 'ghost-abstract-reading.json').read_text())
    for key in ['pdf', 'text']:
        assert hashlib.sha256((ROOT / reading[key + '_file']).read_bytes()).hexdigest() == reading[key + '_sha256']
    pdf = ROOT / reading['pdf_file']
    info = subprocess.check_output(['pdfinfo', str(pdf)], text=True)
    assert int(re.search(r'^Pages:\s+(\d+)', info, re.M)[1]) == reading['pdf_pages'] == 16
    fresh = subprocess.check_output(['pdftotext', '-f', '1', '-l', '1', str(pdf), '-'], text=True)
    assert fresh == (ROOT / reading['text_file']).read_text()
    lo, hi = reading['abstract_char_range']
    assert fresh[lo:hi].strip() == reading['abstract'] and fresh[hi:].startswith('Index Terms—')
    assert '10.1109/ISCA59077.2024.00011' in fresh
    public = json.loads((DEST / 'public-manifest.json').read_text())['papers']
    earlier_orders = {9, 11, 13, 14, 16, 17, 21, 22, 23, 25, 40, 65, 67, 68, 72, 80, 82}
    batch_paths = ['screening-batch-2026-09-08.json', 'screening-batch-models-2026-09-08.json', 'screening-batch-remainder-2026-09-08.json']
    batches = [json.loads((DEST / name).read_text()) for name in batch_paths]
    batch_orders = set().union(*(set(b['program_orders']) for b in batches))
    assert len(batch_orders) == sum(len(b['program_orders']) for b in batches) == 52
    assert len(public) == len({p['doi'] for p in public}) == 69
    assert {p['program_order'] for p in public} == earlier_orders | batch_orders
    sources = {s['id']: s for s in json.loads((DEST / 'selected-sources.json').read_text())}
    institution_proof = json.loads((DEST / 'institutional-abstracts.json').read_text())
    institutional = institution_proof['papers']
    assert not institution_proof['downloaded_code_executed']
    assert {p['program_order'] for p in institutional} == {4, 5, 33, 39, 61, 76, 87}
    assert len(institutional) == len({p['doi'] for p in institutional}) == 7
    assert not {p['doi'] for p in institutional} & {p['doi'] for p in public}
    def normalize_identity(value):
        return re.sub('[^a-z0-9]', '', unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode().lower())
    for item in institutional:
        p = next(p for p in papers if p['doi'] == item['doi'])
        source = sources[item['source_id']]
        data = (ROOT / item['source_file']).read_bytes()
        assert hashlib.sha256(data).hexdigest() == item['source_sha256'] == source['sha256']
        assert source['file'] == item['source_file'] and source['status_code'] == 200
        assert len(data) == source['bytes'] and source['reading_status'] == 'abstract_screened'
        assert p['reading_proof'] == 'institutional-abstracts.json'
        assert p['abstract_source_kind'] == item['source_kind']
        assert p['screening'] == item['screening'] and p['abstract'] == item['abstract']
        assert (p['program_order'], p['publisher_title']) == (item['program_order'], item['publisher_title'])
        assert p['reading_status'] == item['reading_status'] == 'abstract_screened'
        assert 'pdf_file' not in p and 'pdf_pages' not in p and 'selected_reading' not in p
        n = p['program_order']
        if n == 33:
            doc = json.loads(data)
            entity = doc['entityDescription']
            extracted = entity['abstract']
            identity = dict(title=entity['mainTitle'], doi=entity['reference']['doi'], authors=[a['identity']['name'] for a in entity['contributors']], publication_year=entity['publicationDate']['year'])
            assert identity['publication_year'] == '2024'
            assert identity['authors'] == ['Joseph Charles Pandl Rogers', 'Taha Soliman', 'Magnus Jahre']
            assert [' '.join([a['given'], a['family']]) for a in p['publisher_authors']] == ['Joseph Rogers', 'Taha Soliman', 'Magnus Jahre']
            assert doc['associatedArtifacts'][0]['name'] == 'aio-isca24-author-copy.pdf'
            assert doc['associatedArtifacts'][0]['type'] == 'OpenFile'
            assert 'download' in doc['associatedArtifacts'][0]['allowedOperations']
        else:
            doc = BeautifulSoup(data, 'html.parser')
            if n == 4:
                node = doc.select_one('#abstract-head').parent
                extracted = ' '.join(x.get_text(' ', strip=True) if hasattr(x, 'get_text') else str(x).strip() for x in node.contents if getattr(x, 'name', None) != 'h2').strip()
                identity = dict(title=doc.select_one('.feature-title').get_text(' ', strip=True), doi=doc.select_one('a[href*="doi.org"]')['href'], citation=doc.select_one('#citation-head').parent.get_text(' ', strip=True))
                assert '2024' in identity['citation'] and '45-57' in identity['citation']
                assert doc.select_one('.citation-authors').get_text(' ', strip=True) == 'Song R., C. Wu, C. Liu, A. Li, M. Huang, and T. Geng. 2024.'
                author_source = sources[item['identity_source_id']]
                author_data = (ROOT / author_source['file']).read_bytes()
                assert hashlib.sha256(author_data).hexdigest() == author_source['sha256']
                author_text = BeautifulSoup(author_data, 'html.parser').get_text(' ', strip=True)
                lo = author_text.index('DS-GL:')
                author_entry = author_text[lo:author_text.index('Extending Power of Nature', lo)]
                assert normalize_identity(p['publisher_title']) in normalize_identity(author_entry)
                assert all(normalize_identity(a['family']) in normalize_identity(author_entry) for a in p['publisher_authors'])
            else:
                extracted = doc.select_one(item['abstract_selector']).get_text(' ', strip=True)
                identity = dict(title=doc.select_one('meta[name="citation_title"]')['content'], doi=doc.select_one('meta[name="citation_doi"]')['content'], authors=[x['content'] for x in doc.select('meta[name="citation_author"]')])
                expected_authors = [' '.join([a['given'], a['family']]) for a in p['publisher_authors']]
                assert [normalize_identity(a) for a in identity['authors']] == [normalize_identity(a) for a in expected_authors]
        assert identity == item['identity']
        assert identity['doi'].lower().endswith(p['doi'])
        if n != 4:
            assert normalize_identity(identity['title']) == normalize_identity(p['publisher_title'])
        assert extracted == item['abstract'] and len(extracted) > 500
        assert hashlib.sha256(extracted.encode()).hexdigest() == item['abstract_sha256']
    for p in public:
        paper = next(x for x in papers if x['doi'] == p['doi'])
        assert paper['abstract'] == p['abstract'] and paper['screening'] == p['screening']
        assert paper['reading_status'] == p['reading_status']
        assert (ROOT / p['pdf_file']).read_bytes().startswith(b'%PDF-')
        if 'source_id' in p:
            src = sources[p['source_id']]
            assert (src['file'], src['sha256'], src['status_code']) == (p['pdf_file'], p['pdf_sha256'], 200)
        for key in ['pdf', 'text']:
            data = (ROOT / p[key + '_file']).read_bytes()
            assert hashlib.sha256(data).hexdigest() == p[key + '_sha256']
            assert len(data) == p[key + '_bytes']
        info = subprocess.check_output(['pdfinfo', str(ROOT / p['pdf_file'])], text=True)
        assert int(re.search(r'^Pages:\s+(\d+)', info, re.M)[1]) == p['pdf_pages']
        text = subprocess.check_output(['pdftotext', '-f', '1', '-l', '2', str(ROOT / p['pdf_file']), '-'], text=True)
        assert text == (ROOT / p['text_file']).read_text()
        lo, hi = p['abstract_char_range']
        assert text[lo:hi].strip() == p['abstract'] and len(p['abstract']) > 500
        if p['program_order'] in batch_orders:
            assert text[hi:].startswith(p['abstract_end_marker'])
            assert '\f' not in p['abstract']
            assert p['read_scope']['physical_pages'] == [text[:lo].count('\f') + 1]
            assert 'Index Terms' not in p['abstract']
            def normalized(s):
                s = re.sub(r'<[^>]*>', '', html.unescape(s))
                return re.sub('[^a-z0-9]', '', unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode().lower())
            assert normalized(p['publisher_title']) in normalized(text)
            assert all(normalized(a['family']) in normalized(text) for a in paper['publisher_authors'])
            expected_status = 'selected_sections_read' if 'selected_reading' in p else 'abstract_screened'
            assert p['reading_status'] == expected_status
    layout_pages = [{(7, 1), (15, 1), (31, 1), (32, 1)}, {(58, 1), (63, 1)}, {(37, 1), (37, 2), (47, 1), (64, 1), (74, 1), (78, 1)}]
    for batch, counts, expected_layout in zip(batches, [(16, 249, 7), (17, 259, 0), (19, 299, 0)], layout_pages):
        assert batch['new_public_pdfs'] == len(batch['program_orders']) == counts[0]
        assert batch['new_physical_pdf_pages'] == sum(p['pdf_pages'] for p in public if p['program_order'] in batch['program_orders']) == counts[1]
        assert not batch['downloaded_code_executed']
        assert len(batch['no_response_attempts']) == counts[2]
        for attempt in batch['no_response_attempts']:
            assert not attempt['response_body_received']
            assert sources[attempt['recovered_by']]['status_code'] == 200
        assert {(x['program_order'], x['physical_page']) for x in batch['first_page_layout_checks']} == expected_layout
        assert len(batch['first_page_layout_checks']) == len(expected_layout)
        for check in batch['first_page_layout_checks']:
            assert check['actually_viewed'] and check['physical_page'] in {1, 2}
            assert hashlib.sha256((ROOT / check['file']).read_bytes()).hexdigest() == check['sha256']
    tartan = next(p for p in public if p['program_order'] == 37)
    assert tartan['read_scope']['physical_pages'] == [2]
    tartan_text = (ROOT / tartan['text_file']).read_text()
    assert '23 July 2025' in tartan_text and '19 March 2026' in tartan_text
    assert '2024' in tartan_text.split('\f')[1]
    amd = next(p for p in public if p['program_order'] == 58)
    deposited = next(p['publisher_authors'] for p in papers if p['program_order'] == 58)
    assert len(deposited) == 12 and len(amd['author_names_on_public_copy']) == 13
    assert any(a['given'] == 'Mark Fowler Nathan' and a['family'] == 'Kalyanasundharam' for a in deposited)
    assert amd['author_names_on_public_copy'][6:8] == ['Mark Fowler', 'Nathan Kalyanasundharam']
    author_source = sources[amd['identity_source_id']]
    assert author_source['status_code'] == 200
    author_page = BeautifulSoup((ROOT / author_source['file']).read_text(), 'html.parser')
    author_text = []
    for node in author_page.select_one('#authors').next_siblings:
        if getattr(node, 'name', None) == 'h2':
            break
        author_text.append(node.get_text(' ', strip=True) if hasattr(node, 'get_text') else str(node))
    assert [a.strip() for a in ' '.join(' '.join(author_text).split()).split(',')] == amd['author_names_on_public_copy']
    assert any(a.get_text(strip=True) == 'PDF' and a['href'] == './pdfs/isca2024_exascale.pdf' for a in author_page.select('a[href]'))
    # A differently titled early preprint needs an explicit publication identity.
    institution = BeautifulSoup((DEST / 'isca24-llmcompass-institution.html').read_text(), 'html.parser')
    compass = next(p for p in papers if p['program_order'] == 72)
    assert institution.select_one('meta[name="citation_title"]')['content'] == compass['publisher_title']
    assert institution.select_one('meta[name="citation_doi"]')['content'].lower() == compass['doi']
    assert [x['content'] for x in institution.select('meta[name="citation_author"]')] == [' '.join([x['given'], x['family']]) for x in compass['publisher_authors']]
    author = BeautifulSoup((DEST / 'isca24-orojenesis-author-index.html').read_text(), 'html.parser')
    node = author.find(string=lambda t: t and 'Mind the Gap:' in t).parent.parent
    assert node.select_one('a.pub_pdf')['href'] == 'papers/2024ISCA/2024ISCA_Orojensis.pdf'
    selected = [p for p in papers if 'selected_reading' in p]
    assert [p['program_order'] for p in selected] == [11, 14, 54]
    proof = json.loads((DEST / 'orojenesis-reading.json').read_text())
    r = proof['reading']
    assert r == selected[0]['selected_reading']
    assert r == next(p['selected_reading'] for p in public if p['program_order'] == 11)
    assert r['physical_pdf_pages'] == list(range(1, 15))
    assert not proof['downloaded_code_executed']
    pdf = ROOT / r['individual_pdf']
    for page, expected in r['page_text_sha256'].items():
        data = subprocess.check_output(['pdftotext', '-f', page, '-l', page, str(pdf), '-'])
        assert hashlib.sha256(data).hexdigest() == expected
    data = subprocess.check_output(['pdftotext', '-f', '1', '-l', '14', str(pdf), '-'])
    assert data == (ROOT / r['text_file']).read_bytes()
    assert hashlib.sha256(data).hexdigest() == r['text_sha256']
    for fig in proof['figures']:
        assert fig['actually_viewed']
        assert hashlib.sha256((ROOT / fig['file']).read_bytes()).hexdigest() == fig['sha256']
    feather = json.loads((DEST / 'feather-reading.json').read_text())
    fr = feather['reading']
    assert fr == selected[1]['selected_reading'] == next(p['selected_reading'] for p in public if p['program_order'] == 14)
    assert fr['physical_pdf_pages'] == list(range(2, 14)) and not feather['downloaded_code_executed']
    for page, expected in fr['page_text_sha256'].items():
        data = subprocess.check_output(['pdftotext', '-f', page, '-l', page, str(ROOT / fr['individual_pdf']), '-'])
        assert hashlib.sha256(data).hexdigest() == expected
    data = subprocess.check_output(['pdftotext', '-f', '2', '-l', '13', str(ROOT / fr['individual_pdf']), '-'])
    assert data == (ROOT / fr['text_file']).read_bytes()
    assert hashlib.sha256(data).hexdigest() == fr['text_sha256']
    assert {f['physical_page'] for f in feather['figures']} == {4, 5, 11, 12}
    for fig in feather['figures']:
        assert fig['actually_viewed'] and hashlib.sha256((ROOT / fig['file']).read_bytes()).hexdigest() == fig['sha256']
    doc = feather['reused_document']
    data = (ROOT / doc['file']).read_bytes()
    assert hashlib.sha256(data).hexdigest() == doc['sha256']
    section = BeautifulSoup(data, 'html.parser').find(id=doc['section_id']).get_text('\n', strip=True)
    extracted = (section[:section.index('Explanation.')].strip() + '\n').encode()
    assert extracted == (ROOT / doc['selected_text_file']).read_bytes()
    assert hashlib.sha256(extracted).hexdigest() == doc['selected_text_sha256']
    madmax = json.loads((DEST / 'madmax-reading.json').read_text())
    mr = madmax['reading']
    assert mr == selected[2]['selected_reading'] == next(p['selected_reading'] for p in public if p['program_order'] == 54)
    assert mr['physical_pdf_pages'] == [5, 6, 7, 8] and not madmax['downloaded_code_executed']
    for page, expected in mr['page_text_sha256'].items():
        data = subprocess.check_output(['pdftotext', '-f', page, '-l', page, str(ROOT / mr['individual_pdf']), '-'])
        assert hashlib.sha256(data).hexdigest() == expected
    data = subprocess.check_output(['pdftotext', '-f', '5', '-l', '8', str(ROOT / mr['individual_pdf']), '-'])
    assert data == (ROOT / mr['text_file']).read_bytes()
    assert hashlib.sha256(data).hexdigest() == mr['text_sha256']
    assert {f['physical_page'] for f in madmax['figures']} == {7, 8}
    for fig in madmax['figures']:
        assert fig['actually_viewed'] and hashlib.sha256((ROOT / fig['file']).read_bytes()).hexdigest() == fig['sha256']
    assert sum('screening' in p for p in papers) == 77
    assert 16 + sum(p['pdf_pages'] for p in public) == 1081
    report = dict(verified_at=datetime.now(timezone.utc).isoformat(), program_papers=87, normalized_title_matches=70, reviewed_variants=17, excluded_front_back_matter=11, public_pdfs=70, reused_existing_pdfs=1, pdf_pages=16 + sum(p['pdf_pages'] for p in public), institutional_abstracts_without_pdf=7, primary_abstracts_screened=77, primary_abstracts_remaining=10, selected_sections_read=3, selected_physical_pages=30, scope='Public copies and declared abstract/selected-page readings; institutional abstracts do not imply public PDF coverage. Not complete volume or full-text coverage.')
    (Path(__file__).parent / 'isca2024-audit.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    return report

if __name__ == '__main__':
    print(json.dumps(verify(), ensure_ascii=False, indent=2))
