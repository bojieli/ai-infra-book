from pathlib import Path
from urllib.request import Request,urlopen
from urllib.error import HTTPError
from hashlib import sha256
from datetime import datetime,timezone
from concurrent.futures import ThreadPoolExecutor
import sys,json
base=Path(__file__).resolve().parent
batch=Path(sys.argv[1]);items=json.loads(batch.read_text())
def fetch(item):
 out=base/item['file'];assert not out.exists()
 r=dict(item);r['started_at_utc']=datetime.now(timezone.utc).isoformat()
 try:
  response=urlopen(Request(item['url'],headers={'User-Agent':'Mozilla/5.0 (research archive; academic abstract screening)'}),timeout=25)
 except HTTPError as e:response=e
 except Exception as e:
  r.update({'status':None,'error':type(e).__name__+': '+str(e),'response_bytes_archived':False});return r
 with response:
  content=response.read();out.write_bytes(content)
  r.update({'status':response.code,'final_url':response.url,'headers':dict(response.headers),'bytes':len(content),'sha256':sha256(content).hexdigest(),'response_bytes_archived':True})
 r['completed_at_utc']=datetime.now(timezone.utc).isoformat()
 return r
with ThreadPoolExecutor(max_workers=6) as ex:result=list(ex.map(fetch,items))
(base/(batch.name+'.results.json')).write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps([{k:r.get(k) for k in ['file','status','bytes','error']} for r in result],ensure_ascii=False))
