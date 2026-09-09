"""Download only explicitly selected small public author sources; no model assets."""
import pathlib,json,urllib.request,hashlib,datetime
B=pathlib.Path(__file__).resolve().parent

def fetch(name,url):
 p=B/'sources'/name
 if p.exists():return json.loads(p.read_text()) if name.endswith('.json') else (p.read_bytes() if p.suffix=='.png' else p.read_text())
 req=urllib.request.Request(url,headers={'User-Agent':'research-source-audit'})
 with urllib.request.urlopen(req,timeout=45) as r:
  data=r.read(8000001)
  assert len(data)<=8000000,'small-source cap exceeded'
 p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
 reg=B/'sources.json';rows=json.loads(reg.read_text()) if reg.exists() else []
 rows.append(dict(path='sources/'+name,url=url,sha256=hashlib.sha256(data).hexdigest(),bytes=len(data),downloaded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat()))
 reg.write_text(json.dumps(rows,indent=2)+'\n')
 return json.loads(data) if name.endswith('.json') else (data if p.suffix=='.png' else data.decode())
if __name__=='__main__':
 import sys
 fetch(sys.argv[1],sys.argv[2])
