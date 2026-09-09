"""Independent offline verifier for the ninth MICRO2024 abstract package."""
from pathlib import Path
import json,hashlib,datetime,re,subprocess,unicodedata
from bs4 import BeautifulSoup
D=Path(__file__).resolve().parent
load=lambda f:json.loads((D/f).read_text())
sha=lambda b:hashlib.sha256(b).hexdigest()
def html_text(f):
 s=BeautifulSoup((D/f).read_bytes(),'html.parser')
 for tag in s(['script','style']):tag.decompose()
 return s.get_text('\n',strip=True)+'\n'
def norm(s):return ''.join(c for c in unicodedata.normalize('NFKD',s) if not unicodedata.combining(c))
sources=load('sources.json');reused=load('reused-sources.json')
for rows in [sources,reused]:
 for r in rows:
  raw=(D/r['file']).read_bytes();assert len(raw)==r['bytes'] and sha(raw)==r['sha256'],r['file']
assert len(sources)==10 and sum(r['status']==200 for r in sources)==8 and sum(r['status']==202 for r in sources)==2
assert len(reused)==10
for f in ['ringroad-publisher.response','compass-publisher.response']:assert (D/f).read_bytes()==b''
record=load('abstracts.json');coverage={r['program_order']:r for r in load('input-reading-coverage.json')['records']};manifest={p['program_order']:p for p in load('input-manifest.json')['papers']}
read={n for n,r in coverage.items() if r['abstract_read']};assert len(read)==80;blocked=set()
assert len(record['prior_batch_snapshots'])==8
for p in record['prior_batch_snapshots']:
 assert sha((D/p['file']).read_bytes())==p['sha256'];old=load(p['file']);read|={r['program_order'] for r in old['papers']};blocked|={r['program_order'] for r in old.get('unavailable',[])}
assert blocked=={13,19,26,32,38,40,51,57,97}
chosen=[p['program_order'] for p in load('input-manifest.json')['papers'] if p['program_order'] not in read|blocked][:6]
assert chosen==record['locked_program_orders']==[65,76,77,79,80,82]
assert record['input_manifest_sha256']==sha((D/'input-manifest.json').read_bytes())
assert record['input_reading_coverage_sha256']==sha((D/'input-reading-coverage.json').read_bytes())
papers=record['papers'];assert [p['program_order'] for p in papers]==[76,77,79,80]
assert [p['program_order'] for p in record['unavailable']]==[65,82]
assert [p['pdf_pages'] for p in papers]==[14,17,0,0]
for p in papers:
 n=p['program_order']
 for k in ['doi','program_title','program_authors','publisher_title','publisher_authors','publication_date','page']:assert p[k]==manifest[n][k]
 raw=(D/p['source_file']).read_bytes();assert sha(raw)==p['source_sha256']
 src=next(r for r in sources if r['file']==p['source_file']);assert src['status']==200 and src['url']==p['source_url'] and src['retrieved_at']==p['source_retrieved_at']
 if p['pdf_pages']:
  assert raw.startswith(b'%PDF')
  info=subprocess.run(['pdfinfo',str(D/p['source_file'])],check=True,capture_output=True).stdout.decode()
  assert int(re.search(r'^Pages:\s+(\d+)',info,re.M).group(1))==p['pdf_pages']
  cmd=p['extraction']['command'][:];cmd[-2]=str(D/p['source_file']);text_raw=subprocess.run(cmd,check=True,capture_output=True).stdout
  assert text_raw==(D/p['abstract_text_file']).read_bytes()
 else:
  assert p['extraction']['kind']=='bs4_visible_text' and html_text(p['source_file'])==(D/p['abstract_text_file']).read_text()
  assert not raw.startswith(b'%PDF')
 text_raw=(D/p['abstract_text_file']).read_bytes();t=text_raw.decode();a,z=p['abstract_char_range']
 assert sha(text_raw)==p['abstract_text_sha256'] and t[a:z]==p['abstract'] and a<z
 assert sha(p['abstract'].encode())==p['abstract_sha256'] and (D/p['abstract_file']).read_text()==p['abstract']+'\n'
 assert len(p['abstract'].split())>100 and p['extraction']['corrections']==[]
 assert p['read_scope']['complete_abstract'] and not p['read_scope']['body_read'] and not p['read_scope']['figures_read']
for n,names in [(76,['Aaron Barnes','Fangjia Shen','Timothy G. Rogers']),(77,['Dongho Ha','Lufei Liu','Yuan Hsi Chou','Seokjin Go','Won Woo Ro','Hung-Wei Tseng','Tor M. Aamodt'])]:
 t=norm((D/f'paper-{n:03d}-first-page.txt').read_text())
 for name in names:assert norm(name) in t,(n,name)
for f,names in [('bci-institution.html',['Hunjun Lee','Yeongwoo Jang','Daye Jung','Seunghyun Song','Jangwoo Kim']),('activen-lab.html',['Xiaoyi Liu','Zhongzhu Pu','Peng Qu','Weimin Zheng','Youhui Zhang'])]:
 t=html_text(f)
 for name in names:assert name in t,(f,name)
# Check metadata separately: webpage dates are not conference or manuscript revision dates.
for f in ['activen-lab.html','bci-institution.html']:
 s=BeautifulSoup((D/f).read_bytes(),'html.parser');rows=[]
 for tag in s.find_all('meta'):
  key=tag.get('name') or tag.get('property') or ''
  if key.startswith('citation_') or key in ['article:published_time','article:modified_time']:rows.append({'key':key,'value':tag.get('content')})
 assert rows==load(f+'-metadata.json')
m=load('activen-lab.html-metadata.json');assert {'key':'article:published_time','value':'2024-07-02T00:00:00+00:00'} in m
assert {'key':'article:modified_time','value':'2025-08-11T15:46:36+08:00'} in m
m=load('bci-institution.html-metadata.json');assert {'key':'citation_doi','value':'10.1109/MICRO61859.2024.00082'} in m
assert {'key':'citation_author_institution','value':'Hanyang University'} in m
assert 'July, 2024' in html_text('activen-lab.html') and 'Oct. 2024' in html_text('bci-author.html')
s=BeautifulSoup((D/'compass-liu-author.html').read_bytes(),'html.parser');title=next(a for a in s.find_all('a',href=True) if a.get_text().startswith('COMPASS:'))
assert title['href']=='#' and all(a['href']=='#' for a in title.parent.find_all('a',href=True))
s=BeautifulSoup((D/'ringroad-author.html').read_bytes(),'html.parser');a=next(a for a in s.find_all('a',href=True) if 'Ring Road:' in a.get_text());assert a['href']=='https://ieeexplore.ieee.org/document/10764681'
for p in record['unavailable']:
 assert not p['abstract_read'] and not p['body_read'] and p['pdf_pages']==0 and p['doi']==manifest[p['program_order']]['doi']
 assert all((D/f).is_file() for f in p['evidence_files'])
reading=load('reading.json');assert reading['full_primary_abstracts_read']==4
assert reading['matching_pdf_documents']==2 and reading['matching_pdf_pages_available']==31 and reading['html_complete_abstracts']==2
assert reading['body_pages_read']==reading['paper_figures_read']==0 and not reading['source_code_read'] and not reading['downloaded_code_executed']
assert [r['program_order'] for r in reading['images_actually_viewed']]==[76,77]
for r in reading['images_actually_viewed']:assert r['actually_viewed'] and r['physical_page']==1 and sha((D/r['file']).read_bytes())==r['sha256']
for r in reading['auxiliary_text_scopes']:
 raw=(D/r['file']).read_bytes();t=raw.decode();a,z=r['char_range'];assert sha(raw)==r['sha256'] and html_text(r['source_file'])==t and t[a:z]==r['text']
 assert a>=0 and z>a and [t.count('\n',0,a)+1,t.count('\n',0,z)+1]==r['line_range']
assert all(r['returncode']==0 for r in load('extraction-log.json'))
assert [p['program_order'] for p in papers if p['screening']['decision']=='reference']==[76,77,80]
assert [p['program_order'] for p in papers if p['screening']['decision']=='exclude']==[79]
assert not any(p['screening']['body_reading_candidate'] or p['screening']['outline_changed'] for p in papers)
result={'status':'PASS','verified_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'http_response_files':10,'http_200':8,'http_202_empty':2,'reused_input_files':10,'canonical_abstracts_at_snapshot':80,'locked':chosen,'full_primary_abstracts':4,'unavailable_full_abstracts':[65,82],'matching_pdf_documents':2,'matching_pdf_physical_pages':31,'html_complete_abstracts':2,'images_actually_viewed':2,'body_pages_read':0,'candidate':0,'reference':3,'exclude':1,'checks':['original HTTP/reused-input bytes and hashes','earliest unread selection against canonical80 and eight sealed batches','formal/PDF/HTML identity and version boundaries','byte-exact PDF/HTML extraction and full abstract ranges','institution/lab metadata and placeholder links','human read/image scope declarations','failure and coverage counting']}
(D/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result,ensure_ascii=False))
