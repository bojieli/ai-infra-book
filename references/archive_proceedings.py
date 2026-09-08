#!/usr/bin/env python3
"""Archive public proceedings, preserving per-paper evidence and resumable state.
MLSys: --years 2024 2025 2026. Download status never implies reading status.
"""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from urllib.parse import urljoin
import argparse,csv,hashlib,json,re,subprocess,time
import requests
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parent
UA={'User-Agent':'AI-Infra-Book-Literature-Archive/1.0'}
def now():return datetime.now(timezone.utc).isoformat()
def save_json(path,obj):
 tmp=path.with_suffix(path.suffix+'.tmp');tmp.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n');tmp.replace(path)
def get(url):
 for n in range(3):
  try:
   r=requests.get(url,headers=UA,timeout=(10,40));r.raise_for_status()
   if not r.content:raise ValueError('empty response')
   return r
  except Exception:
   if n==2:raise
   time.sleep(1+n)
def record(path,data,url,final):
 path.parent.mkdir(parents=True,exist_ok=True);tmp=path.with_suffix(path.suffix+'.tmp');tmp.write_bytes(data);tmp.replace(path)
 return dict(file=str(path.relative_to(ROOT)),url=url,final_url=final,bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),retrieved_at=now())
def valid(x):
 p=ROOT/x.get('file','MISSING')
 return p.is_file() and p.stat().st_size==x.get('bytes') and hashlib.sha256(p.read_bytes()).hexdigest()==x.get('sha256')
def paper(row,d):
 row=dict(row)
 try:
  if row.get('status')=='downloaded' and valid(row.get('pdf',{})) and valid(row.get('landing',{})) and (ROOT/row['text']).is_file():return row
  response=get(row['source_page']);soup=BeautifulSoup(response.content,'html.parser')
  row['landing']=record(d/'pages'/(row['id']+'.html'),response.content,row['source_page'],response.url)
  for node in soup(['script','style','nav','footer']):node.decompose()
  clean=soup.get_text('\n',strip=True)
  txt=d/'pages'/(row['id']+'.txt');txt.write_text(clean)
  row['landing_text']=str(txt.relative_to(ROOT))
  abstract=re.search(r'\nAbstract\n(.*?)(?:\nName Change Policy|\nReport an Issue|\Z)',clean,re.S)
  row['abstract']=abstract[1].strip() if abstract else ''
  href=next(a['href'] for a in soup.select('a[href]') if a.get_text(' ',strip=True)=='Paper')
  u=urljoin(response.url,href);pdf=get(u)
  if not pdf.content.startswith(b'%PDF-'):raise ValueError('not a PDF')
  p=d/'papers'/(row['id']+'.pdf');row['pdf']=record(p,pdf.content,u,pdf.url)
  text=d/'text'/(row['id']+'.txt');text.parent.mkdir(exist_ok=True)
  subprocess.run(['pdftotext','-layout',str(p),str(text)],check=True,capture_output=True,timeout=40)
  info=subprocess.run(['pdfinfo',str(p)],check=True,capture_output=True,text=True,timeout=15).stdout
  match=re.search(r'^Pages:\s+(\d+)',info,re.M)
  row.update(text=str(text.relative_to(ROOT)),pages=int(match[1]) if match else None,status='downloaded',updated_at=now())
  if len(text.read_text(errors='replace').strip())<600:row['status']='text_incomplete'
  row.pop('error',None)
 except Exception as e:row.update(status='failed',error=f'{type(e).__name__}: {e}',updated_at=now())
 return row

def archive(year,workers):
 d=ROOT/'proceedings'/'MLSys'/str(year);d.mkdir(parents=True,exist_ok=True)
 u=f'https://proceedings.mlsys.org/paper_files/paper/{year}'
 old=json.loads((d/'manifest.json').read_text()) if (d/'manifest.json').exists() else {}
 if valid(old.get('index',{})):
  index=old['index'];data=(ROOT/index['file']).read_bytes()
 else:
  r=get(u);data=r.content;index=record(d/'index.html',data,u,r.url)
 s=BeautifulSoup(data,'html.parser')
 links=[a for a in s.select('a[href]') if '-Abstract' in a['href']]
 stated=re.search(r'(\d+) papers',s.get_text(' ',strip=True));expected=int(stated[1]) if stated else len(links)
 if len(links)!=expected:raise ValueError(f'Index has {len(links)} links, states {expected}')
 oldrows={x['id']:x for x in old.get('papers',[])}
 rows=[]
 for a in links:
  digest=re.search(r'/hash/([^/]+)-Abstract',a['href'])[1];pid=f'mlsys{year}-{digest}'
  row=dict(oldrows.get(pid,{}));row.update(id=pid,venue='MLSys',year=year,title=a.get_text(' ',strip=True),source_page=urljoin(u,a['href']))
  row.setdefault('reading_status','unread');row.setdefault('status','pending');rows.append(row)
 state=dict(venue='MLSys',year=year,index=index,expected_papers=expected,papers=rows)
 save_json(d/'manifest.json',state);print(f'MLSys {year}: {expected} official entries',flush=True)
 with ThreadPoolExecutor(max_workers=workers) as pool:
  pending={pool.submit(paper,row,d):i for i,row in enumerate(rows)}
  for n,f in enumerate(as_completed(pending),1):
   i=pending[f];rows[i]=f.result();state['updated_at']=now();save_json(d/'manifest.json',state)
   if n%20==0 or n==len(rows):print(f'{year}: {n}/{len(rows)} processed, {sum(x["status"]=="downloaded" for x in rows)} PDFs ready',flush=True)
 with (d/'sources.tsv').open('w') as f:
  w=csv.writer(f,delimiter='\t');w.writerow(['id','title','source_page','pdf_url','status','reading_status'])
  for x in rows:w.writerow([x['id'],x['title'],x['source_page'],x.get('pdf',{}).get('url',''),x['status'],x['reading_status']])
 lines=[f'# MLSys {year} 论文集','',f'官方目录共 {expected} 项；下载与阅读状态分别记录。','',f'[原目录]({u}) · [归档目录](index.html) · [校验清单](manifest.json) · [来源表](sources.tsv)','']
 for x in rows:
  local=Path(x['pdf']['file']).relative_to(d.relative_to(ROOT)) if 'pdf' in x else None
  lines.append(f'- {x["title"]} — '+(f'[PDF]({local})' if local else x['status']))
 (d/'README.md').write_text('\n'.join(lines)+'\n')
 print(f'{year}: archived {sum(x["status"]=="downloaded" for x in rows)}/{expected}; errors {[x["id"] for x in rows if x["status"]!="downloaded"]}',flush=True)
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--years',type=int,nargs='+',required=True);ap.add_argument('--workers',type=int,default=4);args=ap.parse_args()
 for year in args.years:archive(year,args.workers)
