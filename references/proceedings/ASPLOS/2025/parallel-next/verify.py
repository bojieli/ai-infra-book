#!/usr/bin/env python3
"""Offline verifier for this packet; run from any directory. No shared writes."""
from pathlib import Path
import hashlib,json,math,re,subprocess
from bs4 import BeautifulSoup
P=Path(__file__).resolve().parent
ROOT=P.parents[4]
D=json.loads((P/'reading-records.json').read_text())
checked=set()
def digest(b):return hashlib.sha256(b).hexdigest()
def path(name):
 p=(ROOT/name).resolve();assert p.is_relative_to(P),f'Proof outside packet: {name}';return p
def check(proof):
 p=path(proof['file']);b=p.read_bytes();assert len(b)==proof['bytes'],str(p);assert digest(b)==proof['sha256'],str(p);checked.add(str(p));return p
def walk(x):
 if isinstance(x,dict):
  if all(k in x for k in ['file','bytes','sha256']):check(x)
  for v in x.values():walk(v)
 elif isinstance(x,list):
  for v in x:walk(v)
def norm(s):return re.sub('[^a-z0-9]','',s.lower())
def extract_pdf(pdf,args):return subprocess.check_output(['pdftotext',*args,str(pdf),'-']).decode('utf-8')
def check_text(expected,actual):assert path(expected['file']).read_text()==actual,expected['file']
walk(D)
M={r['doi']:r for r in json.loads((ROOT/'references/proceedings/ASPLOS/2025/manifest.json').read_text())['papers']}
C={r['doi']:r for r in json.loads((ROOT/'references/proceedings/ASPLOS/2025/reading-coverage.json').read_text())['records']}
assert len({r['doi'] for r in D['records']})==2
statuses=[]
for s in D['sources']:
 f=check(s);statuses.append(s['status_code'])
 assert s['url'].startswith('https://') and s['retrieved_at'] and s['final_url'].startswith('https://')
 if s['status_code']==403:
  assert not f.read_bytes().startswith(b'%PDF'),f
  assert any(t in f.read_text().lower() for t in ['challenge','forbidden','just a moment','cloudflare']),f
 else:assert s['status_code']==200,f
pages=0;body=0;images=0
for r in D['records']:
 formal=M[r['doi']]
 assert formal['program_order']==r['program_order'] and formal['title']==r['title']
 authornames=[' '.join([a.get('given',''),a.get('family','')]).strip() for a in formal['author_metadata']]
 assert r['authors']==authornames==r['identity']['publisher_author_names']
 html=path(r['source_file']);assert digest(html.read_bytes())==r['source_sha256']
 s=BeautifulSoup(html.read_bytes(),'html.parser');a=s.select_one('blockquote.abstract');assert a and a.select_one('.descriptor');a.select_one('.descriptor').decompose();text=a.get_text(' ',strip=True)
 assert text==r['abstract'] and digest(text.encode())==r['abstract_sha256']
 assert path(r['abstract_text_file']['file']).read_text()==text+'\n'
 assert r['version'].split(':',1)[1] in s.get_text(' ',strip=True)
 assert s.select_one('.submission-history').get_text(' ',strip=True)==r['history']
 assert norm(s.select_one('h1.title').get_text(' ',strip=True).removeprefix('Title: '))==norm(r['title'])
 htmlauthors=s.select_one('.authors').get_text(' ',strip=True)
 assert all(n in htmlauthors for n in authornames)
 pdf=check(r['representative_pdf']);assert pdf.read_bytes().startswith(b'%PDF')
 pagecount=int(subprocess.check_output(['pdfinfo',str(pdf)],text=True).split('Pages:')[1].splitlines()[0]);assert pagecount==r['representative_pdf']['pages'];pages+=pagecount
 for args,k in [([], 'text'),(['-layout'],'layout_text'),(['-f','1','-l','1'],'first_page_text')]:check_text(r['representative_pdf'][k],extract_pdf(pdf,args))
 first=extract_pdf(pdf,['-f','1','-l','1']);assert r['doi'] in first
 fixedfirst=first.replace('Aqa','Aqua') if r['program_order']==175 else first
 assert norm(r['title']) in norm(fixedfirst) and all(norm(n) in norm(first) for n in authornames)
 assert 'Abstract' in first and 'ASPLOS' in first
 if r['program_order']==145:
  assert r['doi'] in s.select_one('.metatable').get_text(' ',strip=True)
  assert r['selected_reading']['physical_pdf_pages']==[]
 else:
  home=BeautifulSoup((P/'175-author-home.html').read_bytes(),'html.parser')
  assert any(r['doi'] in a['href'] for a in home.find_all('a',href=True))
  assert r['selected_reading']['physical_pdf_pages']==[4,8,9,11]
  p8=extract_pdf(pdf,['-f','8','-l','8']);assert 'vLLM v0.5.3' in p8 and '50 GB/s' in p8 and '200 GB/s' in p8
  p9=extract_pdf(pdf,['-f','9','-l','9']);assert 'dummy http server' in p9 and 'H100' in p9 and 'A100' in p9
  assert 'cache grows quadratically' in first
 for n,pr in r['selected_reading']['page_text'].items():
  check_text(pr,extract_pdf(pdf,['-f',n,'-l',n]));body+=1
 for n,pr in r['selected_reading']['viewed_page_images'].items():
  assert pr['actually_viewed'] is True;assert check(pr).read_bytes().startswith(b'\x89PNG\r\n\x1a\n');images+=1
 assert r['reading_status']==('full_abstract_and_selected_sections_read' if r['program_order']==175 else 'full_abstract_read')
g=D['gaps'][0];assert g['doi']=='10.1145/3676641.3716265' and g['abstract_read'] is False and g['representative_pdf'] is None
formal=M[g['doi']];assert formal['program_order']==23 and formal['title']==g['title']
cross=json.loads((P/'023-crossref.html').read_text())['message'];assert cross['DOI']==g['doi'] and not cross.get('abstract')
assert cross['title'][0]==g['title'];assert [' '.join([a.get('given',''),a.get('family','')]).strip() for a in cross['author']]==g['authors']
home=BeautifulSoup((P/'023-author-publications.html').read_bytes(),'html.parser');home_text=home.get_text(' ',strip=True)
assert g['title'] in home_text and all(n in home_text for n in g['authors'])
assert any(g['doi'] in a['href'] for a in home.find_all('a',href=True))
calcs=json.loads((P/'calculations.json').read_text());a=calcs['assumptions']
per=2*a['layers']*a['kv_heads']*a['head_dim']*a['bytes_per_element']
small=a['coalesced_copy_bytes']/a['small_copy_bytes']*a['small_copy_bytes']/a['small_copy_bytes_per_second']*1000
big=a['coalesced_copy_bytes']/a['coalesced_copy_bytes_per_second']*1000
expected={'serialization_ns':a['payload_bytes']*8/a['hypothetical_link_bits_per_second']*1e9,'small_copy_count':a['coalesced_copy_bytes']/a['small_copy_bytes'],'individual_copies_ms':small,'coalesced_copy_ms':big,'remaining_gather_scatter_budget_ms':small-big,'kv_bytes_per_token':per,'kv_8192_bytes':per*8192,'kv_16384_bytes':per*16384,'kv_length_doubling_capacity_ratio':(per*16384)/(per*8192)}
assert expected.keys()==calcs['results'].keys()
for k,v in expected.items():assert math.isclose(v,calcs['results'][k],rel_tol=1e-12,abs_tol=1e-12),k
assert pages==D['representative_pdf_pages']==33 and body==D['selected_body_physical_pages']==4 and images==D['actual_rendered_pages_viewed']==6
assert D['new_full_abstracts']==len(D['records'])==2 and D['representative_pdfs']==2 and D['abstract_identity_pages_read_separately']==2 and D['body_reading_is_full_paper'] is False
assert len(statuses)==10 and statuses.count(200)==7 and statuses.count(403)==3
result={'status':'pass','file_proof_unique_paths':len(checked),'source_responses':len(statuses),'successful_sources':statuses.count(200),'retained_http_403':statuses.count(403),'independently_reextracted_full_primary_abstracts':2,'formal_manifest_dois_matched':3,'archived_representative_pdfs':2,'archived_pdf_pages':pages,'fresh_pdf_body_pages_reextracted':body,'abstract_identity_pages_separate':2,'actual_image_views_recorded':images,'independent_arithmetic_checks':len(expected),'current_coverage_already_abstract_read':[r['doi'] for r in D['records'] if C[r['doi']]['abstract_read']],'current_coverage_missing_abstract':[r['doi'] for r in D['records'] if not C[r['doi']]['abstract_read']],'unresolved_primary_abstract_dois':[g['doi']],'note':'Offline byte/text/identity verification does not itself prove human/model reading or rerun experiments. Current coverage dedup status is informational; no shared index written.'}
print(json.dumps(result,ensure_ascii=False,indent=2))
