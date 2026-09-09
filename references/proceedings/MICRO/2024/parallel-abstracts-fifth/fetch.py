from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from datetime import datetime,timezone
import requests,json,hashlib,sys
D=Path(__file__).resolve().parent
jobs=json.loads(Path(sys.argv[1]).read_text())
def fetch(j):
 name,url=j;t=datetime.now(timezone.utc).isoformat();r=requests.get(url,timeout=45);b=r.content;(D/name).write_bytes(b)
 return dict(file=name,url=url,final_url=r.url,status=r.status_code,retrieved_at=t,bytes=len(b),sha256=hashlib.sha256(b).hexdigest(),content_type=r.headers.get('Content-Type'))
rows=list(ThreadPoolExecutor(max_workers=6).map(fetch,jobs));p=D/'sources.json';prev=json.loads(p.read_text()) if p.exists() else [];p.write_text(json.dumps(prev+rows,ensure_ascii=False,indent=2)+'\n');print([(r['file'],r['status'],r['bytes']) for r in rows])
