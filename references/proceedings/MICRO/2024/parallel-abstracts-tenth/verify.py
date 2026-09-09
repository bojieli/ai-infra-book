"""Independent offline source, identity, extraction and scope checks."""
from pathlib import Path
import json,hashlib,datetime,re,subprocess
from bs4 import BeautifulSoup
D=Path(__file__).resolve().parent
load=lambda f:json.loads((D/f).read_text());sha=lambda b:hashlib.sha256(b).hexdigest()
def html_text(f):
 s=BeautifulSoup((D/f).read_bytes(),'html.parser')
 for tag in s(['script','style']):tag.decompose()
 return s.get_text('\n',strip=True)+'\n'
sources=load('sources.json');inputs=load('reused-sources.json')
for r in sources+inputs:
 raw=(D/r['file']).read_bytes();assert len(raw)==r['bytes'] and sha(raw)==r['sha256'],r['file']
assert len(sources)==10 and len(inputs)==11
assert [sum(r['status']==v for r in sources) for v in [200,202,None]]==[5,4,1]
for r in sources:
 if r['status'] in [202,None]:assert r['bytes']==0
assert 'CERTIFICATE_VERIFY_FAILED' in next(r['error'] for r in sources if r['status'] is None)
m={p['program_order']:p for p in load('input-manifest.json')['papers']};coverage=load('input-reading-coverage.json');read={r['program_order'] for r in coverage['records'] if r['abstract_read']};assert len(read)==84
record=load('abstracts.json');blocked=set();assert len(record['prior_batch_snapshots'])==9
for r in record['prior_batch_snapshots']:
 assert r['sha256']==sha((D/r['file']).read_bytes());old=load(r['file']);read|={p['program_order'] for p in old['papers']};blocked|={p['program_order'] for p in old.get('unavailable',[])}
assert blocked=={13,19,26,32,38,40,51,57,65,82,97}
chosen=[p['program_order'] for p in load('input-manifest.json')['papers'] if p['program_order'] not in read|blocked][:6]
assert chosen==record['locked_program_orders']==[84,85,86,91,95,96]
assert record['input_manifest_sha256']==sha((D/'input-manifest.json').read_bytes())
assert record['input_reading_coverage_sha256']==sha((D/'input-reading-coverage.json').read_bytes())
assert [p['program_order'] for p in record['papers']]==[85,86]
for p in record['papers']:
 n=p['program_order']
 for k in ['doi','program_title','program_authors','publisher_title','publisher_authors','publication_date','page']:assert p[k]==m[n][k]
 src=next(r for r in sources if r['file']==p['source_file']);assert src['status']==200 and src['sha256']==p['source_sha256'] and src['url']==p['source_url'] and src['retrieved_at']==p['source_retrieved_at']
 info=subprocess.run(['pdfinfo',str(D/p['source_file'])],check=True,capture_output=True).stdout.decode();assert int(re.search(r'^Pages:\s+(\d+)',info,re.M).group(1))==p['pdf_pages']=={85:16,86:15}[n]
 cmd=p['extraction']['command'][:];cmd[-2]=str(D/p['source_file']);raw=subprocess.run(cmd,check=True,capture_output=True).stdout;assert raw==(D/p['abstract_text_file']).read_bytes()
 a,z=p['abstract_char_range'];assert raw.decode()[a:z]==p['abstract'] and sha(raw)==p['abstract_text_sha256']
 assert sha(p['abstract'].encode())==p['abstract_sha256'] and (D/p['abstract_file']).read_text()==p['abstract']+'\n'
 assert len(p['abstract'].split())>100 and p['extraction']['corrections']==[] and p['read_scope']['complete_abstract'] and not p['read_scope']['body_read'] and not p['read_scope']['figures_read']
 assert p['screening']['decision']=='reference' and not p['screening']['body_reading_candidate'] and not p['screening']['outline_changed']
for n,names in [(85,['Md Hafizul Islam Chowdhuryy','Fan Yao']),(86,['Yuanqing Miao','Yingtian Zhang','Dinghao Wu','Danfeng Zhang','Gang Tan','Rui Zhang','Mahmut Taylan Kandemir'])]:
 t=(D/f'paper-{n:03d}-first-page.txt').read_text()
 for name in names:assert name in t,(n,name)
assert 'we IvLeague-Invert' in record['papers'][0]['abstract']
assert 'Nov 21' in (D/'paper-086-info.txt').read_text()
assert [p['program_order'] for p in record['unavailable']]==[84,91,95,96]
for p in record['unavailable']:
 assert p['doi']==m[p['program_order']]['doi'] and not p['abstract_read'] and not p['body_read'] and p['pdf_pages']==0
 assert all((D/f).is_file() for f in p['evidence_files'])
# Decode already-returned state as data, inspect matching keys only; never execute scripts.
s=BeautifulSoup((D/'pointcim-institution.html').read_bytes(),'html.parser');raw=s.find('script',id='dspace-angular-state').string
state=json.loads(raw.replace('&q;','"').replace('&s;',"'").replace('&l;','<').replace('&g;','>').replace('&a;','&'));assert state==load('pointcim-angular-state.json')
found=[]
def walk(x,path=[]):
 if isinstance(x,dict):
  for k,v in x.items():
   if 'abstract' in k.lower():found.append({'path':path+[k],'value':v})
   walk(v,path+[k])
 elif isinstance(x,list):
  for i,v in enumerate(x):walk(v,path+[i])
walk(state);assert found==load('pointcim-abstract-key-search.json') and len(found)==23 and all(r['path'][0]=='NGX_TRANSLATE_STATE' for r in found)
assert '10.1109/micro61859.2024.00097' in html_text('pointcim-institution.html')
assert 'Ghost Arbitration: Mitigating Interconnect Side-Channel Timing Attacks in GPU' in html_text('ghost-author-publications.html')
assert 'Hans Kasan' in html_text('ghost-author-publications.html') and 'to appear' in html_text('terminus-author.html')
r=load('reading.json');assert r['full_primary_abstracts_read']==2 and r['matching_pdf_documents']==2 and r['matching_pdf_pages_available']==31
assert r['body_pages_read']==r['paper_figures_read']==0 and not r['source_code_read'] and not r['downloaded_code_executed']
assert [x['program_order'] for x in r['images_actually_viewed']]==[85,86]
for x in r['images_actually_viewed']:assert x['actually_viewed'] and x['physical_page']==1 and sha((D/x['file']).read_bytes())==x['sha256']
for x in r['auxiliary_text_scopes']:
 raw=(D/x['file']).read_bytes();t=raw.decode();a,z=x['char_range'];assert sha(raw)==x['sha256'] and t==html_text(x['source_file']) and t[a:z]==x['text'] and a>=0 and z>a
 assert [t.count('\n',0,a)+1,t.count('\n',0,z)+1]==x['line_range']
assert all(x['returncode']==0 for x in load('extraction-log.json'))
result={'status':'PASS','verified_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'fetch_attempts':10,'http_response_files':9,'http_200':5,'http_202_empty':4,'tls_failures_without_http_response':1,'reused_input_files':11,'canonical_abstracts_at_snapshot':84,'locked':chosen,'full_primary_abstracts':2,'unavailable_full_abstracts':[84,91,95,96],'matching_pdf_documents':2,'matching_pdf_physical_pages':31,'images_actually_viewed':2,'body_pages_read':0,'candidate':0,'reference':2,'exclude':0,'checks':['raw source/reused-input bytes/hash','earliest unread selection against canonical84 and nine sealed packages','formal identity and author PDF dates','byte-exact complete abstract extraction/ranges','PointCIM static state decoding: UI labels are not abstracts','human reading/image declarations','HTTP versus TLS failure and coverage counting']}
(D/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result,ensure_ascii=False))
