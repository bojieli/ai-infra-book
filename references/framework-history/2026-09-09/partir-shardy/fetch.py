from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,requests
D=Path('/tmp/ai-infra-parallel-partir')
items=[('shardy-commit','https://api.github.com/repos/openxla/shardy/commits/main','json'),('shardy-repository','https://api.github.com/repos/openxla/shardy','json'),('jax-migration','https://docs.jax.dev/en/latest/shardy_jax_migration.html','html'),('shardy-overview','https://openxla.org/shardy/overview','html')]
def get(it):
 key,url,ext=it;t=datetime.now(timezone.utc).isoformat();r=requests.get(url,timeout=40);b=r.content;name=key+'.'+ext;(D/name).write_bytes(b)
 return dict(id=key,url=url,final_url=r.url,status=r.status_code,retrieved_at=t,file=name,bytes=len(b),sha256=hashlib.sha256(b).hexdigest(),content_type=r.headers.get('Content-Type'))
rows=list(ThreadPoolExecutor(max_workers=4).map(get,items));(D/'sources.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n');print([(r['id'],r['status'],r['bytes']) for r in rows])
