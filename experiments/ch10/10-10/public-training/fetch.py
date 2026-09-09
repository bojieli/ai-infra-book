"""Small public-source downloads only; no model, dataset or GPU work."""
import datetime,hashlib,json,pathlib,sys,urllib.request
B=pathlib.Path(__file__).resolve().parent
url,name=sys.argv[1:3];p=B/name;p.parent.mkdir(parents=True,exist_ok=True)
with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'ai-infra-book-source-readiness'}),timeout=45) as r:
 body=r.read(10*1024*1024+1);assert len(body)<=10*1024*1024,'Large download refused';meta=dict(url=url,resolved_url=r.url,status=r.status,bytes=len(body),sha256=hashlib.sha256(body).hexdigest(),retrieved_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),headers={k:v for k,v in r.headers.items() if k.lower() in ['content-type','etag','last-modified']})
p.write_bytes(body);(B/(name+'.source.json')).write_text(json.dumps(meta,indent=2)+'\n');print(json.dumps(dict(file=name,bytes=len(body),sha256=meta['sha256'])))
