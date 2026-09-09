"""Independent offline verification of raw bytes, identity, extraction, and scope."""
from pathlib import Path
from bs4 import BeautifulSoup
import json,hashlib,datetime,subprocess,re
D=Path(__file__).resolve().parent
load=lambda f:json.loads((D/f).read_text());sha=lambda b:hashlib.sha256(b).hexdigest()
def html_text(f):
 s=BeautifulSoup((D/f).read_bytes(),'html.parser')
 for tag in s(['script','style']):tag.decompose()
 return s.get_text('\n',strip=True)+'\n'
sources=load('sources.json');inputs=load('reused-sources.json')
assert len(sources)==11 and len(inputs)==12
for r in sources+inputs:
 raw=(D/r['file']).read_bytes();assert len(raw)==r['bytes'] and sha(raw)==r['sha256'],r['file']
assert [sum(r['status']==v for r in sources) for v in [200,202]]==[9,2]
assert all(r['bytes']==0 for r in sources if r['status']==202)
m={p['program_order']:p for p in load('input-manifest.json')['papers']};coverage=load('input-reading-coverage.json');read={r['program_order'] for r in coverage['records'] if r['abstract_read']};assert len(read)==86
record=load('abstracts.json');blocked=set();assert len(record['prior_batch_snapshots'])==10
for r in record['prior_batch_snapshots']:
 assert r['sha256']==sha((D/r['file']).read_bytes());old=load(r['file']);read|={p['program_order'] for p in old['papers']};blocked|={p['program_order'] for p in old.get('unavailable',[])}
assert blocked=={13,19,26,32,38,40,51,57,65,82,84,91,95,96,97}
chosen=[p['program_order'] for p in load('input-manifest.json')['papers'] if p['program_order'] not in read|blocked][:6]
assert chosen==record['locked_program_orders']==[98,102,104,106,110,113]
assert record['input_manifest_sha256']==sha((D/'input-manifest.json').read_bytes()) and record['input_reading_coverage_sha256']==sha((D/'input-reading-coverage.json').read_bytes())
assert [p['program_order'] for p in record['papers']]==[98,102,106,113]
for p in record['papers']:
 n=p['program_order']
 for k in ['doi','program_title','program_authors','publisher_title','publisher_authors','publication_date','page']:assert p[k]==m[n][k]
 src=next(r for r in sources if r['file']==p['source_file']);assert src['status']==200 and src['sha256']==p['source_sha256'] and src['url']==p['source_url'] and src['retrieved_at']==p['source_retrieved_at']
 if p['pdf_pages']:
  info=subprocess.run(['pdfinfo',str(D/p['source_file'])],check=True,capture_output=True).stdout.decode();assert int(re.search(r'^Pages:\s+(\d+)',info,re.M).group(1))==p['pdf_pages']==15
  cmd=p['extraction']['command'][:];cmd[-2]=str(D/p['source_file']);raw=subprocess.run(cmd,check=True,capture_output=True).stdout;assert raw==(D/p['abstract_text_file']).read_bytes()
 else:raw=html_text(p['source_file']).encode();assert raw==(D/p['abstract_text_file']).read_bytes()
 t=raw.decode();a,z=p['abstract_char_range'];assert t[a:z]==p['abstract'] and sha(raw)==p['abstract_text_sha256']
 assert [t.count('\n',0,a)+1,t.count('\n',0,z)+1]==p['abstract_line_range']
 assert sha(p['abstract'].encode())==p['abstract_sha256'] and (D/p['abstract_file']).read_text()==p['abstract']+'\n'
 assert len(p['abstract'].split())>100 and p['extraction']['corrections']==[] and p['read_scope']['complete_abstract'] and not p['read_scope']['body_read'] and not p['read_scope']['figures_read']
 assert not p['screening']['body_reading_candidate'] and not p['screening']['outline_changed']
 assert p['screening']['decision']==('exclude' if n==113 else 'reference')
for n,names in [(98,['Cheng Tan','Miaomiao Jiang','Deepak Patil','Yanghui Ou','Zhaoying Li','Lei Ju','Tulika Mitra','Hyunchul Park','Antonino Tumeo','Jeff Zhang']),(102,['Roman Brunner','Rakesh Kumar'])]:
 t=(D/f'paper-{n:03d}-first-page.txt').read_text()
 for name in names:assert name in t,(n,name)
assert 'DVFS-Aware Acceleration' in (D/'paper-098-first-page.txt').read_text() and 'DFVS' in m[98]['program_title']
assert 'Aug 16' in (D/'paper-098-info.txt').read_text() and 'Sep 16' in (D/'paper-102-info.txt').read_text()
assert '32 percentage points' in record['papers'][1]['abstract']
v=html_text('vga-publications.html');a=v.index('VGA:');assert v.index('Jihoon Hong',a)<v.index('Hyunseung Lee',a)
assert m[106]['publisher_authors'][1]['given']=='Hyunseung'
assert 'https://ieeexplore.ieee.org/document/10764661' in (D/'vga-publications.html').read_text()
s=html_text('supercore-institution.html');assert m[113]['doi'].lower() in s.lower() and '1532-1547' in s and '4K.' in record['papers'][3]['abstract']
assert [p['program_order'] for p in record['unavailable']]==[104,110]
for p in record['unavailable']:
 assert p['doi']==m[p['program_order']]['doi'] and not p['abstract_read'] and not p['body_read'] and p['pdf_pages']==0
 assert all((D/f).is_file() for f in p['evidence_files'])
assert 'Ares-Flash' not in html_text('ares-computerorg.html') and '<csdl-app>' in (D/'ares-computerorg.html').read_text()
assert 'VGA' not in html_text('vga-author.html')
links=load('selected-links.json')
assert any(x['href']=='' for r in links if r['source_file']=='ares-group.html' for x in r['links'])
assert any(x['href']=='https://dl.acm.org/doi/pdf/10.1109/MICRO61859.2024.00109' for r in links if r['source_file']=='ares-coauthor.html' for x in r['links'])
assert not any('dl.acm.org' in r['url'] for r in sources)
r=load('reading.json');assert r['full_primary_abstracts_read']==4 and r['matching_pdf_documents']==2 and r['matching_pdf_pages_available']==30
assert r['body_pages_read']==r['paper_figures_read']==0 and not r['source_code_read'] and not r['downloaded_code_executed']
assert [x['program_order'] for x in r['images_actually_viewed']]==[98,102]
for x in r['images_actually_viewed']:assert x['actually_viewed'] and x['physical_page']==1 and sha((D/x['file']).read_bytes())==x['sha256']
for x in r['auxiliary_text_scopes']:
 raw=(D/x['file']).read_bytes();t=raw.decode();a,z=x['char_range'];assert sha(raw)==x['sha256'] and t==html_text(x['source_file']) and t[a:z]==x['text'] and a>=0 and z>a
 assert [t.count('\n',0,a)+1,t.count('\n',0,z)+1]==x['line_range']
assert all(x['returncode']==0 for x in load('extraction-log.json'))
result={'status':'PASS','verified_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'fetch_attempts':11,'http_response_files':11,'http_200':9,'http_202_empty':2,'reused_input_files':12,'canonical_abstracts_at_snapshot':86,'locked':chosen,'full_primary_abstracts':4,'unavailable_full_abstracts':[104,110],'matching_pdf_documents':2,'matching_pdf_physical_pages':30,'images_actually_viewed':2,'body_pages_read':0,'candidate':0,'reference':3,'exclude':1,'checks':['raw source/reused-input bytes/hash','earliest unread selection against canonical86 and ten sealed packages','formal identities and explicit author-order/title discrepancies','byte-exact complete abstract extraction/ranges','HTML-only papers contribute zero PDF pages','human reading/image scope declarations','HTTP202 empty and HTTP200 shell not counted as abstracts']}
(D/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result,ensure_ascii=False))
