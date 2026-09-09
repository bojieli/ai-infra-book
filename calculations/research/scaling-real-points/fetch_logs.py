from pathlib import Path
from urllib.request import urlopen
from concurrent.futures import ThreadPoolExecutor
import json
P=Path(__file__).resolve().parent
names={r['record_id'] for r in json.loads((P/'candidate-points.json').read_text())}
jobs=[]
for repo in (P/'hub').iterdir():
    j=json.loads((repo/'api.json').read_text())
    for row in j['siblings']:
        f=row['rfilename'];folder=f.split('/')[0]
        if (folder in names or folder.removesuffix('c4') in names) and (f.endswith('.out') or f.endswith('/transformers/config.json') or f.endswith('/latest')):
            jobs.append((repo,j['sha'],f))
def get(job):
    repo,rev,f=job;target=repo/f
    if target.exists():return
    data=urlopen(f'https://huggingface.co/datablations/{repo.name}/resolve/{rev}/{f}').read(10_000_001)
    if len(data)>10_000_000:raise ValueError('Log exceeds10MB cap:'+f)
    target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
with ThreadPoolExecutor(max_workers=6) as pool:list(pool.map(get,jobs))
print('Fetched bounded log/config/latest files:',len(jobs))
