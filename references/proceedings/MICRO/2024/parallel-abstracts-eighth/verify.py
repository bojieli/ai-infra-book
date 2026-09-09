"""Independent offline identity, source, extraction and count checks for batch eight."""
from pathlib import Path
import json,hashlib,datetime,re,subprocess,base64,unicodedata
from bs4 import BeautifulSoup
D=Path(__file__).resolve().parent
load=lambda f:json.loads((D/f).read_text())
sha=lambda b:hashlib.sha256(b).hexdigest()
def html_text(f):
 s=BeautifulSoup((D/f).read_bytes(),'html.parser')
 for tag in s(['script','style']):tag.decompose()
 return s.get_text('\n',strip=True)+'\n'
def norm(s):
 return ''.join(c for c in unicodedata.normalize('NFKD',s.replace('ı','i')) if not unicodedata.combining(c))
sources=load('sources.json');reused=load('reused-sources.json')
for rows in [sources,reused]:
 for r in rows:
  raw=(D/r['file']).read_bytes();assert len(raw)==r['bytes'] and sha(raw)==r['sha256'],r['file']
assert len(sources)==12 and sum(r['status']==200 for r in sources)==10
assert sum(r['status']==404 for r in sources)==sum(r['status']==418 for r in sources)==1
assert len(reused)==9 and (D/'failed-surf-amazon.response').read_bytes()==b''
record=load('abstracts.json');coverage={r['program_order']:r for r in load('input-reading-coverage.json')['records']};manifest={p['program_order']:p for p in load('input-manifest.json')['papers']}
read={n for n,r in coverage.items() if r['abstract_read']};assert len(read)==75;blocked=set()
assert len(record['prior_batch_snapshots'])==7
for p in record['prior_batch_snapshots']:
 assert sha((D/p['file']).read_bytes())==p['sha256'];old=load(p['file']);read|={r['program_order'] for r in old['papers']};blocked|={r['program_order'] for r in old.get('unavailable',[])}
assert blocked=={13,19,26,32,38,40,51,97}
chosen=[p['program_order'] for p in load('input-manifest.json')['papers'] if p['program_order'] not in read|blocked][:6]
assert chosen==record['locked_program_orders']==[56,57,58,61,62,63]
assert record['input_manifest_sha256']==sha((D/'input-manifest.json').read_bytes())
assert record['input_reading_coverage_sha256']==sha((D/'input-reading-coverage.json').read_bytes())
papers=record['papers'];assert [p['program_order'] for p in papers]==[56,58,61,62,63]
assert [p['program_order'] for p in record['unavailable']]==[57]
assert [p['pdf_pages'] for p in papers]==[16,13,13,17,16]
for p in papers:
 n=p['program_order']
 for k in ['doi','program_title','program_authors','publisher_title','publisher_authors','page','publication_date']:assert p[k]==manifest[n][k]
 raw=(D/p['source_file']).read_bytes();assert raw.startswith(b'%PDF') and sha(raw)==p['source_sha256']
 assert next(s['url'] for s in sources if s['file']==p['source_file'])==p['source_url']
 info=subprocess.run(['pdfinfo',str(D/p['source_file'])],check=True,capture_output=True).stdout.decode()
 assert int(re.search(r'^Pages:\s+(\d+)',info,re.M).group(1))==p['pdf_pages']
 cmd=p['extraction']['command'][:];cmd[-2]=str(D/p['source_file'])
 raw=subprocess.run(cmd,check=True,capture_output=True).stdout;assert raw==(D/p['abstract_text_file']).read_bytes()
 a,z=p['abstract_char_range'];t=raw.decode();assert t[a:z]==p['abstract'] and a<z
 assert sha(raw)==p['abstract_text_sha256'] and sha(p['abstract'].encode())==p['abstract_sha256']
 assert (D/p['abstract_file']).read_text()==p['abstract']+'\n' and len(p['abstract'].split())>100
 assert p['extraction']['corrections']==[] and p['read_scope']['complete_abstract'] and not p['read_scope']['body_read'] and not p['read_scope']['figures_read']
for n,names in [(56,['Keyi Yin','Xiang Fang','Travis Humble','Ang Li','Yunong Shi','Yufei Ding']),(58,['Ali Mosallaei','Katherine E. Isaacs','Yifan Sun']),(61,['Juan M. Cebrian','Magnus Jahre','Alberto Ros']),(62,['Vipin Patel','Swarnendu Biswas','Mainak Chaudhuri']),(63,['Víctor Nicolás-Conesa','Rubén Titos-Gil','Ricardo Fernández-Pascual','Manuel E. Acacio','Alberto Ros'])]:
 t=norm((D/f'paper-{n:03d}-first-page.txt').read_text())
 for name in names:assert norm(name) in t,(n,name)
assert 'arXiv:2405.06941v3' in (D/'paper-056-first-page.txt').read_text()
assert 'MICRO61859.2024.00066' in (D/'paper-062-first-page.txt').read_text()
assert '2025' in (D/'paper-058-info.txt').read_text()
# Author publication entry links the exact current PDF but does not establish VoR equality.
s=BeautifulSoup((D/'akitartm-author-publications.html').read_bytes(),'html.parser')
card=next(x for x in s.select('div.pub-card') if 'Looking into the Black Box' in x.get_text())
assert 'MICRO 2024' in card.get_text() and card.find('a')['href']=='/akitartm.pdf'
# A fixed Git blob proves README identity, not implementation reading or a complete abstract.
r=load('hestia-readme-blob.json');raw=base64.b64decode(r['content']);assert raw==(D/'hestia-readme.md').read_bytes()
gitsha=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest();assert gitsha==r['sha']=='f52f839222d6a6c3b946c995fbcf1e1f574e59ce'
assert next(x['sha'] for x in load('hestia-repo-contents.json') if x['name']=='README.md')==gitsha
assert '55th' in raw.decode() and 'Yanwen' in raw.decode()
f=record['unavailable'][0];assert not f['abstract_read'] and not f['body_read'] and f['pdf_pages']==0
assert all((D/x).is_file() for x in f['evidence_files'])
reading=load('reading.json');assert reading['full_primary_abstracts_read']==5
assert reading['matching_pdf_documents']==5 and reading['matching_pdf_pages_available']==sum(p['pdf_pages'] for p in papers)==75
assert reading['body_pages_read']==reading['paper_figures_read']==0 and not reading['source_code_read'] and not reading['downloaded_code_executed']
assert [r['program_order'] for r in reading['images_actually_viewed']]==[56,58,61,62,63]
for r in reading['images_actually_viewed']:
 assert r['actually_viewed'] and r['physical_page']==1 and sha((D/r['file']).read_bytes())==r['sha256']
for r in reading['auxiliary_text_scopes']:
 raw=(D/r['file']).read_bytes();t=raw.decode();a,z=r['char_range'];assert sha(raw)==r['sha256'] and t[a:z]==r['text']
 assert [t.count('\n',0,a)+1,t.count('\n',0,z)+1]==r['line_range']
 if r['source_file'].endswith('.html'):assert html_text(r['source_file'])==t
assert all(r['returncode']==0 for r in load('extraction-log.json'))
assert [p['program_order'] for p in papers if p['screening']['decision']=='reference']==[58,61,62]
assert [p['program_order'] for p in papers if p['screening']['decision']=='exclude']==[56,63]
assert not any(p['screening']['body_reading_candidate'] or p['screening']['outline_changed'] for p in papers)
result={'status':'PASS','verified_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'http_response_files':12,'http_200':10,'http_404':1,'http_418':1,'reused_input_files':9,'canonical_abstracts_at_snapshot':75,'locked':chosen,'full_primary_abstracts':5,'unavailable_full_abstracts':[57],'matching_pdf_documents':5,'matching_pdf_physical_pages':75,'images_actually_viewed':5,'body_pages_read':0,'candidate':0,'reference':3,'exclude':2,'checks':['source bytes/status/hash','earliest unread selection against canonical75 and seven sealed batches','formal identities and author/PDF version differences','fixed Git blob README','byte-exact complete-abstract extraction/ranges','actual-image declarations and metadata-only boundaries','failure/candidate/coverage counting']}
(D/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result,ensure_ascii=False))
