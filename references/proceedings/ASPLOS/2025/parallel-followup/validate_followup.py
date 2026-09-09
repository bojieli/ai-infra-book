from pathlib import Path
from bs4 import BeautifulSoup
import json,hashlib,subprocess,re
p=Path(__file__).resolve().parent;repo=p.parents[4];b=json.loads((p/'reading-records.json').read_text());sha=lambda x:hashlib.sha256(x).hexdigest();errors=[];proofs=[]
def walk(o):
 if isinstance(o,dict):
  if all(k in o for k in ['file','bytes','sha256']):
   f=repo/o['file'];data=f.read_bytes();ok=len(data)==o['bytes'] and sha(data)==o['sha256'];proofs.append(dict(file=o['file'],ok=ok))
   if not ok:errors.append(o['file'])
  for v in o.values():walk(v)
 elif isinstance(o,list):
  for v in o:walk(v)
walk(b);details=[];norm=lambda x:re.sub('[^a-z0-9]','',x.lower())
for r in b['records']:
 n=r['program_order'];s=BeautifulSoup((repo/r['source_file']).read_bytes(),'html.parser');e=s.select_one('blockquote.abstract');e.select_one('.descriptor').extract();a=e.get_text(' ',strip=True);abstractok=a==r['abstract'] and sha(a.encode())==r['abstract_sha256'];d=r['representative_pdf'];first=subprocess.check_output(['pdftotext','-f','1','-l','1',str(repo/d['file']),'-']);txt=first.decode();titleok=norm(r['identity']['publisher_title']) in norm(txt);doiok=norm(r['doi']) in norm(txt)
 names=r['identity']['publisher_author_names'];names=[x.replace('Ramachandran Ramjee','Ramchandran Ramjee') for x in names];authorsok=all(norm(x) in norm(txt) for x in names)
 pagechecks=[]
 for k,pf in r['selected_reading']['page_text'].items():
  raw=subprocess.check_output(['pdftotext','-f',k,'-l',k,str(repo/d['file']),'-']);pagechecks.append(dict(page=int(k),reextracted_sha256=sha(raw),matches=sha(raw)==pf['sha256']))
 detail=dict(program_order=n,complete_html_abstract_reextract_matches=abstractok,pdf_title_normalized_matches=titleok,pdf_doi_matches=doiok,all_pdf_author_names_present_with_explicit_variants=authorsok,page_reextractions=pagechecks)
 details.append(detail)
 if not all([abstractok,titleok,doiok,authorsok]+[v['matches'] for v in pagechecks]):errors.append('record '+str(n))
assert b['new_full_abstracts']==3 and b['representative_pdf_pages']==51 and b['selected_body_physical_pages']==16
v=dict(passed=not errors,file_proofs_checked=len(proofs),unique_paths=len({v['file'] for v in proofs}),details=details,failures=errors,scope='Fresh HTML full-abstract re-extraction, PDF title/DOI/author presence with explicitly recorded spelling variants, all 16 selected page re-extractions, file hashes and count consistency. No benchmark reproduction or full-paper claim.')
(p/'validation.json').write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n');print(json.dumps(v,ensure_ascii=False))
