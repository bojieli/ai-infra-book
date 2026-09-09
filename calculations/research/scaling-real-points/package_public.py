"""Assemble only required frozen evidence; no network or shared writes."""
import json,hashlib,shutil
from pathlib import Path
from adapt_statistical import records
HERE=Path(__file__).resolve().parent
OUT=HERE/'public'
SRC=OUT/'sources/scaling-real-points'
SRC.mkdir(parents=True,exist_ok=True)
locks={x['file']:x for x in json.loads((HERE/'adapter-inputs.lock.json').read_text())}
locks.update({x['file']:x for x in json.loads((HERE/'sources.lock.json').read_text())})
rows=records();strict=json.loads((HERE/'adapted.json').read_text())['records'];required={'README.md','utils/parametric_fit.ipynb'}
for r in rows:
 old=next(x for x in strict if x['record_id']==r['id']);required.add(r['evaluation']['file'])
 r['evaluation']['file']='sources/scaling-real-points/'+r['evaluation']['file']
 r['budget_source']=None
 if old.get('training_budget'):
  f=old['training_budget']['file'];required.add(f);r['budget_source']='sources/scaling-real-points/'+f
entries=[]
for f in sorted(required):
 target=SRC/f;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(HERE/f,target)
 b=target.read_bytes();e=dict(locks.get(f,{}));e.update(file=str(target.relative_to(OUT)),bytes=len(b),sha256=hashlib.sha256(b).hexdigest());entries.append(e)
for f in ['supplement.pdf','supplement.txt','STATISTICAL-C4-REVIEW.md','statistical-C4-eight-point-evidence.json','n-loss-sources.lock.json']:
 source=HERE.parent/'scaling-real-points-independent'/f;target=SRC/'independent'/f;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target);b=target.read_bytes();entries.append(dict(file=str(target.relative_to(OUT)),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b),origin='Independent extraction/review; official supplement URL in n-loss-sources.lock.json'))
config=OUT/'configs/scaling-real-points';config.mkdir(parents=True,exist_ok=True)
(config/'data.json').write_text(json.dumps(rows,indent=2)+'\n');b=(config/'data.json').read_bytes();entries.append(dict(file=str((config/'data.json').relative_to(OUT)),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b),origin='Derived eight rows; public records() verifies notebook and logs'))
(OUT/'configs/scaling-real-points.lock.json').write_text(json.dumps(entries,indent=2)+'\n')
