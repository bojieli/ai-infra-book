"""Make isolated copies; never remove files from the sealed baseline."""
import hashlib,json,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parent
base=ROOT.parent
trace=[json.loads(l) for l in (base/'results/consumer-v6/storage.jsonl').read_text().splitlines()]
gets=[x for x in trace if x['method']=='get'];assert len(gets)==64
source={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (base/'storage-v3').glob('*.bin')}
assert len(source)==65
cases=[]
for name,index in [('first',0),('middle',32)]:
 path=ROOT/f'storage-{name}';assert not path.exists()
 omitted=Path(gets[index]['file']).name
 path.mkdir()
 for filename in source:
  if filename!=omitted:shutil.copy2(base/'storage-v3'/filename,path/filename)
 cases.append(dict(case=name,missing_page_index=index,omitted=omitted,before_files={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in path.glob('*.bin')}))
(ROOT/'preparation.json').write_text(json.dumps(dict(source_files=source,cases=cases),indent=2)+'\n')
