"""Seal all delivery files and the authorized status file, excluding this manifest."""
import hashlib,json
from pathlib import Path
R=Path(__file__).resolve().parent
status=R.parents[2]/'parallel-workers/agentquality/status.md'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
files={str(p.relative_to(R)):dict(sha256=sha(p),bytes=p.stat().st_size) for p in sorted(R.rglob('*')) if p.is_file() and p.name!='manifest.json'}
assert sum(v['bytes'] for k,v in files.items() if k.startswith('raw/'))<=100*1024**2
(R/'manifest.json').write_text(json.dumps(dict(files=files,status=dict(path='experiments/parallel-workers/agentquality/status.md',sha256=sha(status),bytes=status.stat().st_size),self_excluded=True),indent=2)+'\n')
print(json.dumps(dict(files=len(files),total_bytes=sum(x['bytes'] for x in files.values()),raw_bytes=sum(v['bytes'] for k,v in files.items() if k.startswith('raw/')))))
