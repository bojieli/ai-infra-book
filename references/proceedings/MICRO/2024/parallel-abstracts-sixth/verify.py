"""Offline provenance, identity and reading-boundary checks; no network or artifact execution."""
from pathlib import Path
import datetime
import hashlib
import json
import re
import subprocess
from bs4 import BeautifulSoup

D=Path(__file__).resolve().parent


def load(f):
    return json.loads((D/f).read_text())


def sha(b):
    return hashlib.sha256(b).hexdigest()


def html_text(f):
    soup=BeautifulSoup((D/f).read_bytes(),'html.parser')
    for tag in soup(['script','style']):
        tag.decompose()
    return (soup.get_text('\n',strip=True)+'\n').replace('\r\n','\n').replace('\r','\n')


sources=load('sources.json')
for rows in [sources,load('reused-sources.json')]:
    for r in rows:
        raw=(D/r['file']).read_bytes()
        assert len(raw)==r['bytes'] and sha(raw)==r['sha256'],r['file']
assert len(sources)==16
assert sum(r['status']==200 for r in sources)==12
assert sum(r['status']==202 for r in sources)==3
assert sum(r['status']==504 for r in sources)==1
assert len(load('reused-sources.json'))==7
for f in ['ufc-publisher.response','ufc-publisher-slash.response','fpga-publisher.response']:
    assert (D/f).read_bytes()==b''
assert 'Making sure you' in (D/'fpga-discovery-dblp-challenge.html').read_text()
assert not (D/'fpga-discovery-dblp-challenge.html').read_text().lstrip().startswith('<?xml')

record=load('abstracts.json')
coverage={r['program_order']:r for r in load('input-reading-coverage.json')['records']}
manifest={r['program_order']:r for r in load('input-manifest.json')['papers']}
read={n for n,r in coverage.items() if r['abstract_read']}
assert len(read)==67
for snapshot in record['prior_batch_snapshots']:
    assert snapshot['sha256']==sha((D/snapshot['file']).read_bytes())
    read|={r['program_order'] for r in load(snapshot['file'])['papers']}
blocked={13,19,51,97}
chosen=[r['program_order'] for r in load('input-manifest.json')['papers'] if r['program_order'] not in read|blocked][:6]
assert chosen==record['locked_program_orders']==[26,28,32,35,36,37]
assert all(coverage[n]['abstract_read'] is False for n in chosen)
assert record['input_manifest_sha256']==sha((D/'input-manifest.json').read_bytes())
assert record['input_reading_coverage_sha256']==sha((D/'input-reading-coverage.json').read_bytes())
papers=record['papers']
assert [p['program_order'] for p in papers]==[28,35,36,37]
assert [p['program_order'] for p in record['unavailable']]==[26,32]
for p in papers:
    n=p['program_order']
    for key in ['doi','program_title','program_authors','publisher_title','publisher_authors','publication_date']:
        assert p[key]==manifest[n][key]
    assert p['source_sha256']==sha((D/p['source_file']).read_bytes())
    assert p['read_scope']['complete_abstract'] and not p['read_scope']['body_read']
    assert not p['screening']['outline_changed'] and not p['screening']['body_followup_recommended']
    if p['pdf_pages']:
        assert (D/p['source_file']).read_bytes().startswith(b'%PDF')
        info=subprocess.run(['pdfinfo',str(D/p['source_file'])],check=True,capture_output=True).stdout.decode()
        assert int(re.search(r'^Pages:\s+(\d+)',info,re.M).group(1))==p['pdf_pages']
        cmd=p['extraction']['command'][:];cmd[-2]=str(D/p['source_file'])
        extracted=subprocess.run(cmd,check=True,capture_output=True)
        assert extracted.stdout==(D/p['abstract_text_file']).read_bytes()
        assert p['extraction']['corrections']==[]
    else:
        assert html_text(p['source_file'])==(D/p['abstract_text_file']).read_text()
    raw=(D/p['abstract_text_file']).read_bytes();text=raw.decode();a,z=p['abstract_char_range']
    assert text[a:z]==p['abstract'] and a<z
    assert sha(raw)==p['abstract_text_sha256'] and sha(p['abstract'].encode())==p['abstract_sha256']
    assert (D/p['abstract_file']).read_text()==p['abstract']+'\n'
    assert len(p['abstract'].split())>100
for p in record['unavailable']:
    assert p['abstract_read'] is False and p['body_read'] is False and p['pdf_pages']==0
    assert p['doi']==manifest[p['program_order']]['doi']
    assert all((D/f).is_file() for f in p['evidence_files'])

# Independently check paper identity and known differences against preserved bytes.
for n,names in [(35,['Kevin Weston','Avery Johnson','Vahid Janfaza','Farabi Mahmud','Abdullah Muzahid']),(36,['David Schall','Andreas Sandberg','Boris Grot']),(37,['Aniket Deshmukh','Lingzhe(Chester) Cai','Yale N. Patt'])]:
    text=(D/f'paper-{n:03d}-first-page.txt').read_text()
    assert all(name in text for name in names)
for n,suffix in [(36,'00042'),(37,'00043')]:
    assert f'MICRO61859.2024.{suffix}' in (D/f'paper-{n:03d}-first-page.txt').read_text()
assert '10.1109/MICRO61859.2024.00041' in html_text('cache-index-nsf.html')
assert '10.1109/MICRO61859.2024.00036' in html_text('bigint-institution.html')
assert [p['family'] for p in manifest[35]['publisher_authors']][:3]==['Weston','Johnson','Janfaza']
assert manifest[35]['program_authors'].index('Vahid Janfaza')<manifest[35]['program_authors'].index('Avery Johnson')
assert (D/'paper-035-first-page.txt').read_text().index('Avery Johnson')<(D/'paper-035-first-page.txt').read_text().index('Vahid Janfaza')
assert 'Branch Pre-computation' in manifest[37]['program_title']
assert 'Branch Precomputation' in manifest[37]['publisher_title']
assert 'LLBP_MICRO24.pdf' in (D/'llbp-author.html').read_text()
assert not any('LLBPX' in r['file'] or 'LLBPX' in r['url'] for r in sources)

reading=load('reading.json')
assert reading['full_primary_abstracts_read']==len(papers)==4
assert reading['body_pages_read']==reading['paper_figures_read']==0
assert not reading['research_source_code_read'] and not reading['downloaded_code_executed']
assert reading['author_site_metadata_js_read'] is True
assert reading['matching_pdf_documents']==sum(bool(p['pdf_pages']) for p in papers)==3
assert reading['matching_pdf_pages_available']==sum(p['pdf_pages'] for p in papers)==42
assert [r['program_order'] for r in reading['images_actually_viewed']]==[35,36,37]
for r in reading['images_actually_viewed']:
    assert r['physical_page']==1 and r['actually_viewed']
    assert sha((D/r['file']).read_bytes())==r['sha256']
for r in reading['auxiliary_text_scopes']:
    raw=(D/r['file']).read_bytes();text=raw.decode().replace('\r\n','\n').replace('\r','\n')
    assert sha(raw)==r['sha256']
    if r['source_file'].endswith('.html'):
        assert html_text(r['source_file'])==text
    a,z=r['char_range']
    assert text[a:z]==r['text'] and a<z
    assert [text.count('\n',0,a)+1,text.count('\n',0,z)+1]==r['line_range']
js=next(r for r in reading['auxiliary_text_scopes'] if r['source_file'].endswith('.js'))
assert js['text'].startswith('{title:"A Scalable, Efficient') and js['text'].endswith('selected:!0}')
assert '10.1109/MICRO61859.2024.00040' in js['text']

observed=load('tool-observations.json')
for r in observed['tool_outputs']:
    raw=(D/r['file']).read_bytes()
    assert len(raw)==r['bytes'] and sha(raw)==r['sha256']
    assert not r['http_status_available'] and not r['is_original_http_response']
    assert not any(s['file']==r['file'] for s in sources)
u=observed['observations'][0]
assert u['program_order']==26 and not u['counted_as_primary_abstract_read']
assert u['complete_looking_abstract_observed']
a,z=u['char_range'];text=(D/u['source_file']).read_text()
assert text[a:z]==u['observed_abstract_text'] and sha((D/u['source_file']).read_bytes())==u['source_sha256']
assert '6.0' in u['observed_abstract_text'] and '1.6' in u['observed_abstract_text']
assert 'verify that you' in (D/'ufc-open-tool-output.txt').read_text()
assert all(r['returncode']==0 for r in load('extraction-log.json'))
assert sum(p['screening']['decision']=='candidate' for p in papers)==0
assert sum(p['screening']['decision']=='reference' for p in papers)==2
assert sum(p['screening']['decision']=='exclude' for p in papers)==2

result={'status':'PASS','verified_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'http_response_files':16,'http_200':12,'http_202_empty':3,'http_504':1,'http_200_challenge_pages':1,'reused_input_files':7,'locked':chosen,'full_primary_abstracts':4,'unavailable_primary_archival_paths':[26,32],'tool_only_indexed_abstract_observed':[26],'matching_pdf_documents':3,'matching_pdf_physical_pages':42,'images_actually_viewed':3,'body_pages_read':0,'candidate':0,'reference':2,'exclude':2,'checks':['raw HTTP and reused byte lengths/SHA256','earliest unread selection against canonical and five prior batches','title/author/DOI identity and preserved author-order difference','PDF page counts and byte-exact first-page extraction','HTML text and full abstract ranges','exact auxiliary text/JS metadata ranges','tool-indexed text kept distinct from original publisher HTTP','200 challenge and 202/504 failures excluded','reading and screening counts']}
(D/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(result,ensure_ascii=False))
