#!/usr/bin/env python3
"""Offline byte, source identity, version and fresh abstract extraction checks."""
from pathlib import Path
import hashlib,json,re,subprocess
from bs4 import BeautifulSoup
P=Path(__file__).resolve().parent;ROOT=P.parents[4]
D=json.loads((P/'reading-records.json').read_text());checked=set()
def digest(b):return hashlib.sha256(b).hexdigest()
def file(name):
 f=(ROOT/name).resolve();assert f.is_relative_to(P),name;return f
def proof(x):
 f=file(x['file']);b=f.read_bytes();assert len(b)==x['bytes'] and digest(b)==x['sha256'],str(f);checked.add(str(f));return f
def walk(x):
 if isinstance(x,dict):
  if all(k in x for k in ['file','bytes','sha256']):proof(x)
  for v in x.values():walk(v)
 elif isinstance(x,list):
  for v in x:walk(v)
def soup(f):return BeautifulSoup(f.read_bytes(),'html.parser')
def norm(x):return re.sub('[^a-z0-9]','',x.lower())
def pdftext(f,*args):return subprocess.check_output(['pdftotext',*args,str(f),'-']).decode('utf-8')
def arxiv(s):
 a=s.select_one('blockquote.abstract');assert a is not None and a.select_one('.descriptor');a.select_one('.descriptor').decompose();return a.get_text(' ',strip=True)
def compare_abstract(r,t):
 assert r['abstract']==t and digest(t.encode())==r['abstract_sha256']
 assert file(r['abstract_text_file']['file']).read_text()==t+'\n'
walk(D)
M={r['doi']:r for r in json.loads((ROOT/'references/proceedings/ASPLOS/2025/manifest.json').read_text())['papers']}
C={r['doi']:r for r in json.loads((ROOT/'references/proceedings/ASPLOS/2025/reading-coverage.json').read_text())['records']}
assert [r['program_order'] for r in D['records']]==[146,147,148,149,153]
assert len({r['doi'] for r in D['records']})==5
statuses=[]
for s in D['sources']:
 f=proof(s);statuses.append(s['status_code']);assert s['retrieved_at'] and s['url'].startswith('https://') and s['final_url'].startswith('https://')
 if s['status_code'] in [403,404]:assert not f.read_bytes().startswith(b'%PDF')
 else:assert s['status_code']==200
bad=next(s for s in D['sources'] if s['id']=='153-author');assert bad['status_code']==200 and bad['disposition'].startswith('excluded_wrong_person')
assert "Hui Xu" in soup(file(bad['file'])).get_text(' ',strip=True)
pagecount=0;pdfcount=0;viewed=0
for r in D['records']:
 f=M[r['doi']];assert r['program_order']==f['program_order'] and r['title']==f['title']
 authors=[' '.join([a.get('given',''),a.get('family','')]).strip() for a in f['author_metadata']]
 assert authors==r['authors']==r['identity']['publisher_author_names']
 src=file(r['source_file']);assert digest(src.read_bytes())==r['source_sha256']
 n=r['program_order']
 if n in [146,148]:
  s=soup(src);compare_abstract(r,arxiv(s));assert r['history']==s.select_one('.submission-history').get_text(' ',strip=True)
  assert r['version'].split(':',1)[1] in s.get_text(' ',strip=True)
  assert all(a in s.select_one('.authors').get_text(' ',strip=True) for a in authors)
  title=s.select_one('h1.title').get_text(' ',strip=True).removeprefix('Title: ')
  assert norm(r['title']).startswith(norm(title))
  if n==146:assert r['doi'] in s.select_one('.metatable').get_text(' ',strip=True)
 elif n==147:
  t=pdftext(src,'-f','1','-l','1');begin=t.index('Abstract')+len('Abstract');end=t.index('CCS Concepts:',begin);compare_abstract(r,' '.join(t[begin:end].split()))
  g=r['git_identity'];tree=json.loads(proof(g['tree_file']).read_text());assert tree['sha']==g['commit'] and not tree['truncated'];blob=next(x for x in tree['tree'] if x['path']==g['path']);assert blob['sha']==g['blob_sha1']
  raw=src.read_bytes();gitsha=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest();assert gitsha==g['blob_sha1']
  assert g['commit'] in r['source_url'] and g['path'] in r['source_url']
 elif n==149:
  # Parse literal data; this is intentionally not eval/JS execution.
  webpage=soup(proof(r['static_identity']['website_file']));assert any(x.get('component-url')==r['static_identity']['component_path'] for x in webpage.find_all('astro-island'))
  raw=src.read_text();start=raw.index('ps=[{id:1,')+len('ps=[{id:1,');end=raw.index('},{id:2,',start);item=raw[start:end]
  def literal(key):return json.loads(re.search(r'\b'+key+r':("(?:[^"\\]|\\.)*")',item).group(1))
  assert literal('title')==r['title'] and literal('url')=='https://doi.org/'+r['doi']
  assert json.loads(re.search(r'authors:(\[[^\]]*\])',item).group(1))==authors
  compare_abstract(r,literal('abstract'));assert r['representative_pdf'] is None
 elif n==153:
  s=soup(src);a=s.select('.rendering_abstractportal .textblock > p');assert len(a)==1;compare_abstract(r,a[0].get_text(' ',strip=True))
  visible=s.get_text(' ',strip=True);assert r['title'] in visible and r['doi'] in visible and all(a in visible for a in authors)
  author=soup(proof(r['author_bridge']));link=author.find('a',href='https://arxiv.org/abs/2407.00326');row=link.find_parent(class_='pub-row');assert row is not None
  assert any(r['doi'] in a['href'] for a in row.find_all('a',href=True));assert r['title'] in row.get_text(' ',strip=True)
  pre=r['related_preprint_abstract'];ps=soup(proof(pre['source']));assert ps.select_one('h1.title').get_text(' ',strip=True).removeprefix('Title: ')==pre['title'];assert pre['title'].startswith('Teola:')
  assert pre['version'].split(':',1)[1] in ps.get_text(' ',strip=True);assert pre['history']==ps.select_one('.submission-history').get_text(' ',strip=True)
  compare_abstract(pre,arxiv(ps));assert pre['count_as_additional_paper'] is False
 assert r['selected_reading']['physical_pdf_pages']==[] and r['selected_reading']['page_text']=={} and r['reading_status']=='full_abstract_read'
 rep=r['representative_pdf']
 if rep:
  pdf=proof(rep);assert pdf.read_bytes().startswith(b'%PDF');pdfcount+=1
  p=int(subprocess.check_output(['pdfinfo',str(pdf)],text=True).split('Pages:')[1].splitlines()[0]);assert p==rep['pages'];pagecount+=p
  for args,key in [([], 'text'),(['-layout'],'layout_text'),(['-f','1','-l','1'],'first_page_text')]:assert file(rep[key]['file']).read_text()==pdftext(pdf,*args),key
  first=pdftext(pdf,'-f','1','-l','1');assert all(norm(a) in norm(first) for a in authors)
  title=r['related_preprint_abstract']['title'] if n==153 else r['title'];assert norm(title) in norm(first)
  assert r['identity']['pdf_title_authors_visually_verified'] is True
  if n in [147,148]:assert r['doi'] in first and r['identity']['pdf_official_doi_visually_verified'] is True
  else:assert r['identity']['pdf_official_doi_visually_verified'] is False
  for p,x in r['selected_reading']['viewed_page_images'].items():assert p=='1' and x['actually_viewed'] is True and proof(x).read_bytes().startswith(b'\x89PNG\r\n\x1a\n');viewed+=1
 else:assert r['selected_reading']['viewed_page_images']=={}
g=D['gaps'][0];assert g['program_order']==150 and not g['abstract_read'] and g['representative_pdf'] is None
assert g['doi'] in M and M[g['doi']]['title']==g['title'];s=soup(P/'150-author-pubs.html');row=s.select_one('#BlockDepend');assert row and g['title'] in row.get_text(' ',strip=True) and all(a in row.get_text(' ',strip=True) for a in g['authors']);assert any(g['doi'] in a['href'] for a in row.find_all('a',href=True))
x=json.loads((P/'150-crossref.html').read_text())['message'];assert x['DOI']==g['doi'] and not x.get('abstract')
tree=json.loads((P/'150-author-tree.html').read_text());assert not tree['truncated'];assert any(x['path']=='assets/pdf/asplos2025-presentation.pdf' for x in tree['tree'])
assert pdfcount==D['representative_pdfs']==4 and pagecount==D['representative_pdf_pages']==65 and viewed==D['actual_rendered_pages_viewed']==4
assert D['new_full_abstracts']==5 and D['selected_body_reading_records']==D['selected_body_physical_pages']==0 and D['abstract_identity_pages_read_separately']==4 and D['body_reading_is_full_paper'] is False
assert len(statuses)==29 and statuses.count(200)==24 and statuses.count(403)==3 and statuses.count(404)==2
result={'status':'pass','file_proof_unique_paths':len(checked),'source_responses':len(statuses),'http_200':statuses.count(200),'retained_http_403':statuses.count(403),'retained_http_404':statuses.count(404),'excluded_wrong_person_http_200':1,'freshly_reextracted_unique_doi_primary_abstracts':5,'related_preprint_abstracts_reextracted_not_extra_doi':1,'formal_manifest_identities_matched':6,'archived_representative_pdfs':pdfcount,'archived_pdf_pages':pagecount,'selected_body_pages':0,'abstract_identity_pages_separate':4,'actual_image_views_recorded':viewed,'current_coverage_already_abstract_read':[r['doi'] for r in D['records'] if C[r['doi']]['abstract_read']],'current_coverage_missing_abstract':[r['doi'] for r in D['records'] if not C[r['doi']]['abstract_read']],'unresolved_primary_abstract_dois':[g['doi']],'notes':['No downloaded JavaScript/code executed. Static author record parsed as string literals.','Ayo formal abstract and renamed Teola related preprint kept distinct.','No shared records written. Verification is not paper-body reading or benchmark reproduction.']}
print(json.dumps(result,ensure_ascii=False,indent=2))
