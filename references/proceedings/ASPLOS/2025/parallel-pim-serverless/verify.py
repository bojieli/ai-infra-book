#!/usr/bin/env python3
"""Portable offline verification; no source execution, network, or shared writes."""
from pathlib import Path
import json,hashlib,re,subprocess,unicodedata
from bs4 import BeautifulSoup
P=Path(__file__).resolve().parent;ROOT=P.parents[4];D=json.loads((P/'reading-records.json').read_text());checked=set()
def digest(b):return hashlib.sha256(b).hexdigest()
def fpath(name):
 f=(ROOT/name).resolve();assert f.is_relative_to(P),name;return f
def check(x):
 f=fpath(x['file']);b=f.read_bytes();assert len(b)==x['bytes'] and digest(b)==x['sha256'],str(f);checked.add(str(f));return f
def walk(x):
 if isinstance(x,dict):
  if all(k in x for k in ['file','bytes','sha256']):check(x)
  for v in x.values():walk(v)
 elif isinstance(x,list):
  for v in x:walk(v)
def norm(x):return re.sub('[^a-z0-9]','',unicodedata.normalize('NFKD',x).encode('ascii','ignore').decode().lower())
def pdftext(pdf,args):return subprocess.check_output(['pdftotext',*args,str(pdf),'-']).decode('utf-8')
walk(D)
M={r['doi']:r for r in json.loads((ROOT/'references/proceedings/ASPLOS/2025/manifest.json').read_text())['papers']}
C={r['doi']:r for r in json.loads((ROOT/'references/proceedings/ASPLOS/2025/reading-coverage.json').read_text())['records']}
assert [r['program_order'] for r in D['records']]==[154,156,158,170,171,172];assert len({r['doi'] for r in D['records']})==6
# Recorded source status is cross-checked against retained original download logs.
logs={}
for log in P.glob('sources-*.json.results.json'):
 for s in json.loads(log.read_text()):logs[s['id']]=s
statuses=[]
for s in D['sources']:
 f=check(s);old=logs[s['id']];assert all(s[k]==old[k] for k in ['url','final_url','status_code','bytes','sha256','retrieved_at']);statuses.append(s['status_code'])
 assert s['url'].startswith('https://') and s['final_url'].startswith('https://') and s['retrieved_at']
 if s['status_code']==429:assert not f.read_bytes().startswith(b'%PDF')
 else:assert s['status_code']==200
assert (P/'154-crossref.html').read_bytes()==b''
pages=0;images=0;pdfdoi=0
for r in D['records']:
 m=M[r['doi']];assert m['program_order']==r['program_order'] and m['title']==r['title'];n=r['program_order']
 authors=[' '.join([a.get('given',''),a.get('family','')]).strip() for a in m['author_metadata']]
 assert authors==r['authors']==r['identity']['publisher_author_names'];assert r['identity']['formal_page_range']==m['page'] and r['identity']['presentation_year']==m['presentation_year'] and r['identity']['volume_doi']==m['volume_doi']
 source=fpath(r['source_file']);assert digest(source.read_bytes())==r['source_sha256']
 if r['extraction_kind']=='arxiv_html':
  s=BeautifulSoup(source.read_bytes(),'html.parser');a=s.select_one('blockquote.abstract');assert a and a.select_one('.descriptor');a.select_one('.descriptor').decompose();text=a.get_text(' ',strip=True)
  assert s.select_one('.submission-history').get_text(' ',strip=True)==r['history'];assert r['version'] in s.get_text(' ',strip=True)
  assert norm(s.select_one('h1.title').get_text(' ',strip=True).removeprefix('Title: '))==norm(r['title'])
  assert all(norm(a) in norm(s.select_one('.authors').get_text(' ',strip=True)) for a in authors)
 else:
  raw=pdftext(source,['-f','1','-l','1']);start=raw.index('Abstract')+len('Abstract')
  if n==156:end=raw.index('Keywords:',start)
  elif n==170:end=raw.index('CCS Concepts:',start)
  elif n==172:
   terminal='TTFT) by 53.0%.';end=raw.index(terminal,start)+len(terminal)
  else:raise AssertionError(n)
  text=' '.join(raw[start:end].split())
  if n==172:assert 'Figure 1' not in text and 'Loading phase' not in text and text.endswith('TTFT) by 53.0%.')
 assert text==r['abstract'] and digest(text.encode())==r['abstract_sha256'];assert fpath(r['abstract_text_file']['file']).read_text()==text+'\n'
 rep=r['representative_pdf'];pdf=check(rep);assert pdf.read_bytes().startswith(b'%PDF')
 p=int(subprocess.check_output(['pdfinfo',str(pdf)],text=True).split('Pages:')[1].splitlines()[0]);assert p==rep['pages'];pages+=p
 for args,key in [([],'text'),(['-layout'],'layout_text'),(['-f','1','-l','1'],'first_page_text')]:assert fpath(rep[key]['file']).read_text()==pdftext(pdf,args),rep[key]['file']
 first=pdftext(pdf,['-f','1','-l','1']);assert norm(r['title']) in norm(first)
 aliases=r['identity']['author_aliases'];assert aliases==({'Karl Friedrich Alexander Friebel':'Karl F. A. Friebel'} if n==156 else {})
 assert all(norm(aliases.get(a,a)) in norm(first) for a in authors)
 assert r['identity']['pdf_title_authors_visually_verified'] is True
 if n in [156,170,171,172]:assert r['doi'] in first and r['identity']['pdf_official_doi_visually_verified'] is True;pdfdoi+=1
 else:assert r['identity']['pdf_official_doi_visually_verified'] is False
 if n==154:
  assert p==13 and '2502.15470v2' in first;lo,hi=[int(x) for x in m['page'].split('-')];assert hi-lo+1==17
  assert r['identity']['doi_bridge'].startswith('Existing official-program/publisher manifest')
 if n==158:
  c=json.loads(check(r['identity']['publisher_identity_source']).read_text())['message'];assert c['DOI']==r['doi'] and c['title'][0]==r['title'];assert [' '.join([a.get('given',''),a.get('family','')]).strip() for a in c['author']]==authors
 if n==156:
  assert 'ASPLOS ’24' in first and r['identity']['presentation_year']==2025
  v=r['related_version_metadata'];s=BeautifulSoup(check(v['source']).read_bytes(),'html.parser');assert v['version'].split(':',1)[1] in s.get_text(' ',strip=True) and s.select_one('.submission-history').get_text(' ',strip=True)==v['history'];assert v['canonical_abstract_from_this_source'] is False
 assert r['reading_status']=='full_abstract_read' and r['selected_reading']['physical_pdf_pages']==[] and r['selected_reading']['page_text']=={}
 for page,pr in r['selected_reading']['viewed_page_images'].items():assert page=='1' and pr['actually_viewed'] is True and check(pr).read_bytes().startswith(b'\x89PNG\r\n\x1a\n');images+=1
assert pages==D['representative_pdf_pages']==91 and images==D['actual_rendered_pages_viewed']==D['abstract_identity_pages_read_separately']==6
assert D['new_full_abstracts']==D['representative_pdfs']==6 and D['selected_body_physical_pages']==D['selected_body_reading_records']==0 and D['gaps']==[] and D['body_reading_is_full_paper'] is False
assert len(statuses)==13 and statuses.count(200)==11 and statuses.count(429)==2
result={'status':'pass','file_proof_unique_paths':len(checked),'source_responses':len(statuses),'http_200':statuses.count(200),'retained_http_429':statuses.count(429),'retained_zero_byte_http_429':1,'freshly_reextracted_unique_doi_primary_abstracts':6,'formal_manifest_identities_matched':6,'pdf_first_page_official_dois_verified':pdfdoi,'preprints_without_printed_official_doi':2,'archived_representative_pdfs':6,'archived_pdf_pages':pages,'selected_body_pages':0,'abstract_identity_pages_separate':6,'actual_image_views_recorded':images,'current_coverage_already_abstract_read':[r['doi'] for r in D['records'] if C[r['doi']]['abstract_read']],'current_coverage_missing_abstract':[r['doi'] for r in D['records'] if not C[r['doi']]['abstract_read']],'unresolved_primary_abstract_dois':[],'notes':['PAPI 13-page arXiv preprint is not the formal 17-page version.','CINM retains ASPLOS 2024 volume 4 versus 2025 programme presentation and explicit author abbreviation.','No body reading, source execution, benchmark reproduction, or shared-index writes.']}
print(json.dumps(result,ensure_ascii=False,indent=2))
