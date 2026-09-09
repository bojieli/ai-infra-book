"""Self-written HTTP archiver. Reads bytes only, never executes responses."""
from pathlib import Path
import urllib.request, urllib.error, json,hashlib,datetime,concurrent.futures,sys
D=Path(__file__).resolve().parent
items=json.loads(Path(sys.argv[1]).read_text())
def fetch(r):
 now=datetime.datetime.now(datetime.timezone.utc).isoformat();out=dict(r);out['retrieved_at']=now
 try:
  req=urllib.request.Request(r['url'],headers={'User-Agent':'Mozilla/5.0'})
  with urllib.request.urlopen(req,timeout=40) as res:
   raw=res.read();out.update(status=res.status,final_url=res.url,content_type=res.headers.get('Content-Type',''))
 except urllib.error.HTTPError as e:
  raw=e.read();out.update(status=e.code,final_url=e.url,content_type=e.headers.get('Content-Type',''),error=str(e))
 except Exception as e:
  raw=b'';out.update(status=None,error=repr(e))
 (D/r['file']).write_bytes(raw);out.update(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest());return out
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:results=list(ex.map(fetch,items))
rows=json.loads((D/'sources.json').read_text())+results
(D/'sources.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n')
for r in results:print(json.dumps(r,ensure_ascii=False))
