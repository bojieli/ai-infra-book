"""Independent offline source/identity/extraction/count checks for the seventh batch."""
from pathlib import Path
import datetime,hashlib,json,re,subprocess,unicodedata
from bs4 import BeautifulSoup
D=Path(__file__).resolve().parent
def load(f):return json.loads((D/f).read_text())
def sha(b):return hashlib.sha256(b).hexdigest()
def html_text(f):
 s=BeautifulSoup((D/f).read_bytes(),'html.parser')
 for tag in s(['script','style']):tag.decompose()
 return (s.get_text('\n',strip=True)+'\n').replace('\r\n','\n').replace('\r','\n')
sources=load('sources.json')
for rows in [sources,load('reused-sources.json')]:
 for r in rows:
  raw=(D/r['file']).read_bytes();assert len(raw)==r['bytes'] and sha(raw)==r['sha256'],r['file']
assert len(sources)==11 and sum(r['status']==200 for r in sources)==9 and sum(r['status']==202 for r in sources)==2
assert len(load('reused-sources.json'))==8
assert all((D/f).read_bytes()==b'' for f in ['wakeup-publisher.response','srender-publisher.response'])
record=load('abstracts.json');coverage={r['program_order']:r for r in load('input-reading-coverage.json')['records']};manifest={r['program_order']:r for r in load('input-manifest.json')['papers']}
read={n for n,r in coverage.items() if r['abstract_read']};assert len(read)==67
blocked={13,19,26,32,51,97}
for old in record['prior_batch_snapshots']:
 assert old['sha256']==sha((D/old['file']).read_bytes());data=load(old['file'])
 read|={r['program_order'] for r in data['papers']};blocked|={r['program_order'] for r in data.get('unavailable',[])}
chosen=[r['program_order'] for r in load('input-manifest.json')['papers'] if r['program_order'] not in read|blocked][:6]
assert chosen==record['locked_program_orders']==[38,39,40,44,48,49]
assert all(not coverage[n]['abstract_read'] for n in chosen)
assert record['input_manifest_sha256']==sha((D/'input-manifest.json').read_bytes())
assert record['input_reading_coverage_sha256']==sha((D/'input-reading-coverage.json').read_bytes())
papers=record['papers'];assert [p['program_order'] for p in papers]==[39,44,48,49]
assert [p['program_order'] for p in record['unavailable']]==[38,40]
for p in papers:
 n=p['program_order']
 for k in ['doi','program_title','program_authors','publisher_title','publisher_authors','publication_date','page']:assert p[k]==manifest[n][k]
 raw=(D/p['source_file']).read_bytes();assert raw.startswith(b'%PDF') and sha(raw)==p['source_sha256']
 info=subprocess.run(['pdfinfo',str(D/p['source_file'])],check=True,capture_output=True).stdout.decode()
 assert int(re.search(r'^Pages:\s+(\d+)',info,re.M).group(1))==p['pdf_pages']
 cmd=p['extraction']['command'][:];cmd[-2]=str(D/p['source_file'])
 extraction=subprocess.run(cmd,check=True,capture_output=True);assert extraction.stdout==(D/p['abstract_text_file']).read_bytes()
 assert p['extraction']['corrections']==[]
 text=(D/p['abstract_text_file']).read_text();a,z=p['abstract_char_range'];assert text[a:z]==p['abstract'] and a<z
 assert sha((D/p['abstract_text_file']).read_bytes())==p['abstract_text_sha256']
 assert sha(p['abstract'].encode())==p['abstract_sha256'] and (D/p['abstract_file']).read_text()==p['abstract']+'\n'
 assert p['read_scope']['complete_abstract'] and not p['read_scope']['body_read'] and not p['read_scope']['figures_read']
 assert not p['screening']['outline_changed'] and len(p['abstract'].split())>100
for p in record['unavailable']:
 assert not p['abstract_read'] and not p['body_read'] and p['pdf_pages']==0
 assert p['doi']==manifest[p['program_order']]['doi'] and all((D/f).is_file() for f in p['evidence_files'])

# Verify identities and version markers independently of generated conclusions.
for n,names in [(39,['Yao Hsiao','Nikos Nikoleris','Artem Khyzha','Dominic P. Mulligan','Gustavo Petri','Christopher W. Fletcher','Caroline Trippel']),(44,['Lingxiang Yin','Sanjay Gandham','Mingjie Lin','Hao Zheng']),(48,['Axel Feldmann','Courtney Golden','Yifan Yang','Joel S. Emer','Daniel Sanchez']),(49,['Kailin Yang','José F. Martı́nez'])]:
 text=unicodedata.normalize('NFKD',(D/f'paper-{n:03d}-first-page.txt').read_text())
 for name in names:
  assert unicodedata.normalize('NFKD',name) in text,(n,name)
assert 'arXiv:2409.19478v1' in (D/'paper-039-first-page.txt').read_text()
assert '2409.19478v1' in next(r['url'] for r in sources if r['file']=='paper-039.pdf')
assert 'Authors\' version' in html_text('rtl-arxiv.html')
assert 'MICRO61859.2024.00054' in (D/'paper-048-first-page.txt').read_text()
assert '2025' in (D/'paper-044-info.txt').read_text()
assert 'assets/files/MICRO-2024.pdf' in (D/'scale-author-pubs.html').read_text()
assert "[MICRO'24]" in html_text('scale-author-pubs.html') and 'November 2-6, 2024.' in html_text('scale-author-pubs.html')
s=BeautifulSoup((D/'srender-coauthor-pubs.html').read_bytes(),'html.parser')
title=next(a for a in s.find_all('a',href=True) if a.get_text().startswith('SRender:'))
assert title['href']=='#'
assert all(a['href']=='#' for a in title.parent.find_all('a',href=True))

reading=load('reading.json');assert reading['full_primary_abstracts_read']==4
assert reading['body_pages_read']==reading['paper_figures_read']==0 and not reading['source_code_read'] and not reading['downloaded_code_executed']
assert reading['matching_pdf_documents']==len(papers)==4 and reading['matching_pdf_pages_available']==sum(p['pdf_pages'] for p in papers)==60
assert [r['program_order'] for r in reading['images_actually_viewed']]==[39,44,48,49]
for r in reading['images_actually_viewed']:
 assert r['actually_viewed'] and r['physical_page']==1 and sha((D/r['file']).read_bytes())==r['sha256']
for r in reading['auxiliary_text_scopes']:
 raw=(D/r['file']).read_bytes();text=raw.decode().replace('\r\n','\n').replace('\r','\n');a,z=r['char_range']
 assert sha(raw)==r['sha256'] and html_text(r['source_file'])==text
 assert text[a:z]==r['text'] and a<z and [text.count('\n',0,a)+1,text.count('\n',0,z)+1]==r['line_range']
assert all(r['returncode']==0 for r in load('extraction-log.json'))
assert [p['program_order'] for p in papers if p['screening']['decision']=='candidate']==[49]
assert [p['program_order'] for p in papers if p['screening']['decision']=='reference']==[44,48]
assert [p['program_order'] for p in papers if p['screening']['decision']=='exclude']==[39]
result={'status':'PASS','verified_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'http_response_files':11,'http_200':9,'http_202_empty':2,'reused_input_files':8,'locked':chosen,'full_primary_abstracts':4,'unavailable_full_abstracts':[38,40],'matching_pdf_documents':4,'matching_pdf_physical_pages':60,'images_actually_viewed':4,'body_pages_read':0,'candidate':1,'reference':2,'exclude':1,'checks':['original HTTP and reused input bytes/hash','earliest unread selection against canonical67 and six sealed batches','title/author/DOI/arXiv identity','version dates and placeholder links','PDF page counts and byte-exact extraction','complete abstract and auxiliary ranges','actual image/read boundaries','candidate and failure counting']}
(D/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result,ensure_ascii=False))
