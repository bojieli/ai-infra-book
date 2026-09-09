"""Offline verification of primary byte provenance and selected-read accounting."""
from pathlib import Path
import datetime
import hashlib
import json
import re
import subprocess
from bs4 import BeautifulSoup

D = Path(__file__).resolve().parent


def load(f):
    return json.loads((D / f).read_text())


def sha(b):
    return hashlib.sha256(b).hexdigest()


def html_text(f):
    soup = BeautifulSoup((D / f).read_bytes(), 'html.parser')
    for tag in soup(['script', 'style']):
        tag.decompose()
    return (soup.get_text('\n', strip=True) + '\n').replace('\r\n', '\n').replace('\r', '\n')


sources = load('sources.json')
for rows in [sources, load('reused-sources.json')]:
    for r in rows:
        raw = (D / r['file']).read_bytes()
        assert len(raw) == r['bytes'] and sha(raw) == r['sha256'], r['file']
assert len(sources) == 13
assert sum(r['status'] == 200 for r in sources) == 10
assert sum(r['status'] == 202 for r in sources) == 2
assert sum(r['status'] == 404 for r in sources) == 1
assert all((D / f).read_bytes() == b'' for f in ['hyfiss-publisher.response', 'drctl-publisher.response'])
assert not (D / 'delayavf-author-404.response').read_bytes().startswith(b'%PDF')
light = next(r for r in load('fourth-batch-sources.json') if r['file'] == 'identity-mismatch-nsf-10590071.pdf')
assert light['url'] == 'https://par.nsf.gov/servlets/purl/10590071' and light['status'] == 200
assert light['sha256'] == sha((D / 'paper-016.pdf').read_bytes())

record = load('abstracts.json')
locked = [13, 16, 17, 18, 19, 24]
assert record['locked_program_orders'] == locked
coverage = {r['program_order']: r for r in load('input-reading-coverage.json')['records']}
manifest = {r['program_order']: r for r in load('input-manifest.json')['papers']}
assert all(coverage[n]['abstract_read'] is False for n in locked)
assert record['input_manifest_sha256'] == sha((D / 'input-manifest.json').read_bytes())
assert record['input_reading_coverage_sha256'] == sha((D / 'input-reading-coverage.json').read_bytes())
for old in record['prior_batch_snapshots']:
    assert old['sha256'] == sha((D / old['file']).read_bytes())
    already = {r['program_order'] for r in load(old['file'])['papers']}
    assert not already.intersection(locked)
assert not {51, 97}.intersection(locked)
papers = record['papers']
assert [p['program_order'] for p in papers] == [16, 17, 18, 24]
assert [p['program_order'] for p in record['unavailable']] == [13, 19]
assert set(p['program_order'] for p in papers + record['unavailable']) == set(locked)
for p in papers:
    n = p['program_order']
    assert p['doi'] == manifest[n]['doi'] == coverage[n]['doi']
    for key in ['program_title', 'publisher_title', 'publisher_authors', 'publication_date']:
        assert p[key] == manifest[n][key]
    assert p['read_scope']['complete_abstract'] and not p['read_scope']['body_read']
    assert not p['screening']['outline_changed'] and not p['screening']['body_followup_recommended']
    assert p['source_sha256'] == sha((D / p['source_file']).read_bytes())
    if p['pdf_pages']:
        assert (D / p['source_file']).read_bytes().startswith(b'%PDF')
        info = subprocess.run(['pdfinfo', str(D / p['source_file'])], check=True, capture_output=True).stdout.decode()
        assert int(re.search(r'^Pages:\s+(\d+)', info, re.M).group(1)) == p['pdf_pages']
        cmd = p['extraction']['command'][:]
        cmd[-2] = str(D / p['source_file'])
        extracted = subprocess.run(cmd, check=True, capture_output=True)
        assert extracted.stdout == (D / p['abstract_text_file']).read_bytes()
        assert p['extraction']['corrections'] == []
    else:
        assert html_text(p['source_file']) == (D / p['abstract_text_file']).read_text()
    text = (D / p['abstract_text_file']).read_text()
    a,z = p['abstract_char_range']
    assert text[a:z] == p['abstract']
    assert p['abstract_text_sha256'] == sha((D / p['abstract_text_file']).read_bytes())
    assert p['abstract_sha256'] == sha(p['abstract'].encode())
    assert (D / p['abstract_file']).read_text() == p['abstract'] + '\n'
    assert len(p['abstract'].split()) > 150
for p in record['unavailable']:
    assert not p['abstract_read'] and not p['body_read'] and p['pdf_pages'] == 0
    assert p['doi'] == manifest[p['program_order']]['doi']
    assert all((D / f).is_file() for f in p['evidence_files'])

# Identity evidence is independent of any generated summary.
assert 'MICRO61859.2024.00025' in (D / 'paper-016-first-page.txt').read_text()
for n, names in [(16,['Yuchen Zhou','Jianping Zeng','Changhee Jung']), (17,['Peter W. Deutsch','Vincent Quentin Ulitzsch','Sudhanva Gurumurthi','Vilas Sridharan','Joel S. Emer','Mengjia Yan']), (18,['Evgeny Manzhosov','Simha Sethumadhavan'])]:
    text = (D / f'paper-{n:03d}-first-page.txt').read_text()
    assert all(name in text for name in names)
assert '10.1109/MICRO61859.2024.00032' in html_text('cachecraft-institution.html')
assert '10764566' in (D / 'cachecraft-author-pubs.html').read_text()
assert '10764631' in (D / 'drctl-author-pubs.md').read_text()
assert '10764651' in (D / 'hyfiss-author.html').read_text()
for f in ['hyfiss-record.json', 'delayavf-record.json']:
    assert load(f)['metadata']['resource_type']['type'] == 'software'
assert 'description' not in load('hyfiss-record.json')['metadata']
assert load('hyfiss-record.json')['metadata']['version'] == 'v1.1.4'
assert len(load('delayavf-record.json')['metadata']['description']) < 160

reading = load('reading.json')
assert reading['full_primary_abstracts_read'] == len(papers) == 4
assert reading['body_pages_read'] == 0 and not reading['source_code_read'] and not reading['downloaded_code_executed']
assert reading['matching_pdf_documents'] == sum(bool(p['pdf_pages']) for p in papers) == 3
assert reading['matching_pdf_pages_available'] == sum(p['pdf_pages'] for p in papers) == 48
assert reading['new_matching_pdf_downloads'] == 2 and reading['reused_matching_pdf_documents'] == 1
assert [r['program_order'] for r in reading['images_actually_viewed']] == [16, 17, 18]
for r in reading['images_actually_viewed']:
    assert r['actually_viewed'] and r['physical_page'] == 1
    assert r['sha256'] == sha((D / r['file']).read_bytes())
for r in reading['auxiliary_text_scopes']:
    raw = (D / r['file']).read_bytes()
    assert sha(raw) == r['sha256']
    text = raw.decode().replace('\r\n', '\n').replace('\r', '\n')
    if r['source_file'].endswith('.html'):
        assert text == html_text(r['source_file'])
    a,z = r['char_range']
    assert text[a:z] == r['text'] and a < z
    assert [text.count('\n',0,a)+1, text.count('\n',0,z)+1] == r['line_range']
assert all(p['screening']['decision'] != 'candidate' for p in papers)
assert sum(p['screening']['decision'] == 'reference' for p in papers) == 2
assert sum(p['screening']['decision'] == 'exclude' for p in papers) == 2
logs = load('extraction-log.json')
assert all(r['returncode'] == 0 for r in logs)
assert any('Illegal annotation destination' in r['stderr'] for r in logs if r['n'] == 16)

result = {'status':'PASS', 'verified_at':datetime.datetime.now(datetime.timezone.utc).isoformat(), 'http_response_files':13, 'http_200':10, 'http_202_empty':2, 'http_404':1, 'reused_input_files':8, 'locked':locked, 'full_primary_abstracts':4, 'unavailable_full_abstracts':[13,19], 'matching_pdf_documents':3, 'matching_pdf_physical_pages':48, 'new_pdf_downloads':2, 'reused_pdf_documents':1, 'images_actually_viewed':3, 'body_pages_read':0, 'candidate':0, 'reference':2, 'exclude':2, 'checks':['raw response and reused byte lengths/SHA256', 'LightWSP original NSF URL/status/hash bridge', 'input snapshots and prior-batch exclusion', 'title/author/DOI identity', 'PDF page counts and byte-exact first-page extraction', 'HTML extraction and abstract character ranges', 'exact selected auxiliary ranges', 'software artifact versus paper distinction', 'failed-response exclusion', 'reading and screening counts']}
(D / 'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(result,ensure_ascii=False))
