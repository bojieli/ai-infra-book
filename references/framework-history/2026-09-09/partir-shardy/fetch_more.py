from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,requests,sys
D=Path('/tmp/ai-infra-parallel-partir');items=json.loads(Path(sys.argv[1]).read_text())
def get(it):
 key,url,ext=it;t=datetime.now(timezone.utc).isoformat();r=requests.get(url,timeout=40);b=r.content;name=key+'.'+ext;(D/name).write_bytes(b)
 return dict(id=key,url=url,final_url=r.url,status=r.status_code,retrieved_at=t,file=name,bytes=len(b),sha256=hashlib.sha256(b).hexdigest(),content_type=r.headers.get('Content-Type'))
rows=list(ThreadPoolExecutor(max_workers=min(6,len(items))).map(get,items));old=json.loads((D/'sources.json').read_text());(D/'sources.json').write_text(json.dumps(old+rows,ensure_ascii=False,indent=2)+'\n');print([(r['id'],r['status'],r['bytes']) for r in rows])
