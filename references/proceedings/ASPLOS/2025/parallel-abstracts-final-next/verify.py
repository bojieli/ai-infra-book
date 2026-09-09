#!/usr/bin/env python3
"""Offline source bytes, formal identity and primary abstract re-extraction. No network."""
from pathlib import Path
import hashlib
import json
import re
import struct
import subprocess
import unicodedata
from bs4 import BeautifulSoup

P = Path(__file__).resolve().parent
ROOT = P.parents[4]
data = json.loads((P / 'reading-records.json').read_text())
official = {p['program_order']: p for p in json.loads((P.parent / 'manifest.json').read_text())['papers']}
seen = set()

def check(obj):
    f = (ROOT / obj['file']).resolve()
    assert f.is_relative_to(P), f
    b = f.read_bytes()
    assert len(b) == obj['bytes'] and hashlib.sha256(b).hexdigest() == obj['sha256'], f
    seen.add(obj['file']); return b

def walk(obj):
    if isinstance(obj, dict):
        if {'file', 'bytes', 'sha256'} <= obj.keys(): check(obj)
        for v in obj.values(): walk(v)
    elif isinstance(obj, list):
        for v in obj: walk(v)

def norm(s):
    s = BeautifulSoup(s, 'html.parser').get_text(' ', strip=True) if '<' in s else s
    return re.sub(r'[^a-z0-9]', '', unicodedata.normalize('NFKD', s).lower())

walk(data)
selected = json.loads(check(data['selection']))
assert {r['program_order'] for r in selected} == {1, 2, 5, 10, 14, 16}
assert all(not r['abstract_read'] and r['representative_pdf'] is None for r in selected)
assert {r['program_order'] for r in data['records']} == {10, 14, 16}
assert {r['program_order'] for r in data['gaps']} == {1, 2, 5}
assert len({r['doi'] for r in data['records'] + data['gaps']}) == 6
assert data['new_full_abstracts'] == len(data['records']) == 3
assert data['selected_body_reading_records'] == data['selected_body_physical_pages'] == 0
assert data['actual_rendered_pages_viewed'] == data['abstract_identity_pages_read_separately'] == 2
assert not data['body_reading_is_full_paper']

prov = json.loads(check(data['local_copy_provenance']))
registry_path = P / 'registry-original.json'
registry_bytes = registry_path.read_bytes()
assert len(registry_bytes) == prov['bytes'] == 2011764
assert hashlib.sha256(registry_bytes).hexdigest() == prov['sha256'] == '0443b8c7f441a3390c5b68300ee9474b7dc5f84517656c65ca77efb21a567553'
assert prov['status_code'] == 200 and prov['url'].startswith('https://api.crossref.org/works?')
assert registry_bytes == (ROOT / prov['source_archive_path']).read_bytes()
registry = json.loads(registry_bytes)['message']['items']
assert len(registry) == 1000

identity_checks = []
for r in data['records'] + data['gaps']:
    n = r['program_order']; e = official[n]
    assert e['doi'] == r['doi'] and norm(e['title']) == norm(r['title'])
    names = [a['given'] + ' ' + a['family'] for a in e['author_metadata']]
    assert names == r['authors']
    matches = [a for a in registry if a['DOI'] == r['doi']]
    assert len(matches) == 1
    cr = matches[0]
    assert norm(cr['title'][0]) == norm(r['title']) and cr['page'] == e['page']
    assert [a['given'] + ' ' + a['family'] for a in cr['author']] == names
    assert not cr.get('abstract')
    identity_checks.append({'program_order': n, 'doi': r['doi'], 'authors_checked': len(names), 'formal_registry_identity': 'pass', 'full_abstract_read': n in [10, 14, 16]})

pages = 0; reextracted = []
for r in data['records']:
    n = r['program_order']; names = r['authors']
    assert r['identity']['official_program_doi'] == r['doi']
    assert r['identity']['formal_page_range'] == official[n]['page']
    assert r['identity']['publisher_author_names'] == names
    assert r['selected_reading']['physical_pdf_pages'] == []
    assert r['selected_reading']['page_text'] == {}
    assert r['body_reading_candidate_priority'] == 'not_selected'
    sf = ROOT / r['source_file']
    assert hashlib.sha256(sf.read_bytes()).hexdigest() == r['source_sha256']
    if n == 10:
        assert r['representative_pdf'] is None
        assert r['selected_reading']['viewed_page_images'] == {}
        soup = BeautifulSoup(sf.read_text(), 'html.parser')
        nodes = soup.select('.rendering_researchoutput_abstractportal .textblock > p')
        assert len(nodes) == 1
        abstract = ' '.join(nodes[0].get_text(' ', strip=True).split())
        assert norm(soup.select_one('meta[name="citation_title"]')['content']) == norm(r['title'])
        assert [m['content'] for m in soup.select('meta[name="citation_author"]')] == names
        assert soup.select_one('meta[name="citation_doi"]')['content'] == r['doi']
        assert soup.select_one('meta[name="citation_firstpage"]')['content'] == '16'
        assert soup.select_one('meta[name="citation_lastpage"]')['content'] == '31'
        assert soup.select_one('meta[name="citation_publication_date"]')['content'] == '2025/03/30'
        assert soup.select_one('meta[name="citation_online_date"]')['content'] == '2025/09/26'
        assert abstract.startswith('Processing-in-memory (PIM) architectures')
        assert abstract.endswith('4.24-209× for real-world benchmarks.')
    else:
        pdf = r['representative_pdf']; f = ROOT / pdf['file']
        count = int(re.search(r'^Pages:\s+(\d+)', subprocess.check_output(['pdfinfo', str(f)], text=True), re.M).group(1))
        assert count == pdf['pages'] == {14: 17, 16: 16}[n]; pages += count
        first_bytes = subprocess.check_output(['pdftotext', '-f', '1', '-l', '1', str(f), '-'])
        assert first_bytes == check(pdf['first_page_text'])
        assert subprocess.check_output(['pdftotext', str(f), '-']) == check(pdf['text'])
        assert subprocess.check_output(['pdftotext', '-layout', str(f), '-']) == check(pdf['layout_text'])
        first = first_bytes.decode()
        assert norm(r['title']) in norm(first) and norm(r['doi']) in norm(first)
        for name in names: assert norm(name) in norm(first), (n, name)
        assert r['identity']['pdf_title_authors_visually_verified']
        assert r['identity']['pdf_official_doi_visually_verified']
        abstract = ' '.join(first.split('Abstract', 1)[1].split('CCS Concepts:', 1)[0].split())
        png = r['selected_reading']['viewed_page_images']['1']; b = check(png)
        assert b[:8] == b'\x89PNG\r\n\x1a\n' and min(struct.unpack('>II', b[16:24])) >= 1000
        assert png['actually_viewed']
        if n == 14:
            assert '17 pages.' in first and official[n]['page'] == '79-94'
            assert abstract.startswith('Quantum circuit simulation (QCS)')
            assert abstract.endswith('311.42× faster on average.')
        else:
            assert '16 pages.' in first and official[n]['page'] == '339-354'
            assert abstract.startswith('Modern energy-harvesting devices [23]')
            assert 'endto-end latency' in abstract
            assert abstract.endswith('up to 4.2× compared to several baselines.')
    assert abstract == r['abstract']
    assert hashlib.sha256(abstract.encode()).hexdigest() == r['abstract_sha256']
    assert check(r['abstract_text_file']) == (abstract + '\n').encode()
    reextracted.append(n)
assert pages == data['representative_pdf_pages'] == 33
assert sum(r['representative_pdf'] is not None for r in data['records']) == data['representative_pdfs'] == 2

sources = {s['id']: s for s in data['sources']}
assert len(sources) == len(data['sources']) == 25
statuses = {}
for s in sources.values():
    assert s['retrieved_at'] and s['url'] and s['final_url']
    statuses[s['status_code']] = statuses.get(s['status_code'], 0) + 1
    if s['file'].endswith('.pdf'): assert s['status_code'] == 200 and check(s).startswith(b'%PDF')
    if s['status_code'] == 429: assert check(s) == b''
for logpath in P.glob('*-jobs.json.results.json'):
    logs = json.loads(logpath.read_text())
    jobs = json.loads((P / logpath.name.removesuffix('.results.json')).read_text())
    assert {x['id'] for x in logs} == {x['id'] for x in jobs}
    for log in logs:
        s = sources[log['id']]
        for k in ['url', 'final_url', 'status_code', 'bytes', 'sha256', 'retrieved_at']: assert s[k] == log[k]
        assert Path(s['file']).name == Path(log['file']).name
assert statuses == {200: 14, 429: 4, 403: 7}, statuses

artifact_checks = []
for gap in data['gaps']:
    n = gap['program_order']
    assert gap['full_abstract_read'] is False and gap['representative_pdf'] is None and gap['body_pages_read'] == []
    assert gap['body_reading_candidate_priority'] == 'undetermined_until_primary_abstract'
    assert set(gap['failed_source_ids']) == {s['id'] for s in sources.values() if s['id'].startswith(f'{n:03d}-') and s['status_code'] != 200}
    if n == 1:
        cr = json.loads(check(gap['single_crossref']))['message']
        assert cr['DOI'] == gap['doi'] and not cr.get('abstract')
        text = BeautifulSoup(check(gap['author_publication_pages'][0]).decode(), 'html.parser').get_text(' ', strip=True)
        assert norm(gap['title']) in norm(text)
        for name in gap['authors']: assert norm(name) in norm(text), name
    else:
        a = gap['artifact_locator']
        commit = json.loads(check(a['commit_metadata']))
        tree = json.loads(check(a['tree']))
        assert commit['sha'] == tree['sha'] == a['commit']
        assert not tree.get('truncated')
        assert not any(t['path'].lower().endswith('.pdf') for t in tree['tree'])
        readme = check(a['readme'])
        blob = hashlib.sha1(b'blob ' + str(len(readme)).encode() + b'\0' + readme).hexdigest()
        assert next(t for t in tree['tree'] if t['path'] == 'README.md')['sha'] == blob
        assert f"/{a['commit']}/README.md" in sources[f'{n:03d}-artifact-readme']['url']
        if n == 2:
            assert norm(gap['title']) in norm(readme.decode())
            for name in gap['authors']: assert norm(name) in norm(readme.decode()), name
        else:
            assert 'ASPLOS 2025 RASSM Artifact' in readme.decode()
        artifact_checks.append({'program_order': n, 'repository': a['repository'], 'commit': a['commit'], 'readme_git_blob': blob, 'pdf_absent_in_complete_tree_snapshot': True, 'code_executed': False})

result = {'status': 'pass', 'file_proofs_checked': len(seen), 'formal_identity_checks': identity_checks, 'full_primary_abstracts_reextracted': len(reextracted), 'reextracted_orders': reextracted, 'representative_pdfs': 2, 'representative_pdf_pages': 33, 'actual_viewed_first_page_images_verified': 2, 'selected_body_pages': 0, 'body_candidates': 0, 'http_responses': 25, 'http_statuses': statuses, 'genuine_zero_byte_failed_responses': 4, 'local_primary_registry_copy': 'byte-identical previous archive, no new HTTP request', 'artifact_locator_checks': artifact_checks, 'unresolved_original_abstracts': [1, 2, 5], 'version_limits': ['10 original institution HTML abstract only; no PDF.', '14 author PDF17 pages versus formal16; no publisher-byte equivalence.', '16 author publication-layout PDF16 pages, revision unlabelled; exact archived bytes pinned.'], 'verification_limits': 'Offline sources/status/identity and three complete abstract re-extractions; two full PDF text extractions are mechanical archive verification, not body reading. PNG/record checks cannot prove reading independently; actual two-page visual review recorded. No downloaded code executed.'}
(P / 'validation.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
print(json.dumps(result, ensure_ascii=False, indent=2))
