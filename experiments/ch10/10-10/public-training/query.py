"""Anonymous read-only public W&B query; never uses account/share credentials."""
import json,urllib.request,urllib.error,sys,hashlib,datetime
from pathlib import Path
root=Path(__file__).absolute().parent;name=sys.argv[1];body=sys.stdin.buffer.read();query=json.loads(body)['query'];assert query.lstrip().startswith('query')
req=urllib.request.Request('https://api.wandb.ai/graphql',data=body,headers={'Content-Type':'application/json','User-Agent':'ai-infra-book-public-record-review'})
try:
 with urllib.request.urlopen(req,timeout=45) as r:raw=r.read(20*1024*1024+1);status=r.status
except urllib.error.HTTPError as e:raw=e.read();status=e.code
assert len(raw)<=20*1024*1024
p=root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw);p.with_suffix(p.suffix+'.query.json').write_bytes(body);p.with_suffix(p.suffix+'.source.json').write_text(json.dumps(dict(url=req.full_url,status=status,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),retrieved_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),authentication='none',method='POST read-only query'),indent=2)+'\n');print(status,len(raw));j=json.loads(raw);print('errors',j.get('errors'))
