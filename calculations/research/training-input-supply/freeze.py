from pathlib import Path
import json,hashlib
from calculate import calculate
P=Path(__file__).resolve().parent
long_samples=[dict(tokens=512,stored_bytes=8192,cpu_ns=100000) for _ in range(12)]
scenes=[dict(id='training-supply-default'),dict(id='training-supply-no-checkpoint',checkpoint_every=0),dict(id='training-supply-shared-starvation',samples=long_samples,host_slots=1,device_slots=1,snapshot_slots=8),dict(id='training-supply-independent-storage',samples=long_samples,host_slots=1,device_slots=1,snapshot_slots=8,shared_storage=False),dict(id='training-supply-cpu-bottleneck',samples=[{**s,'cpu_ns':100000000} for s in long_samples],checkpoint_every=0)]
(P/'scenarios.json').write_text(json.dumps(scenes,indent=2)+'\n')
(P/'results').mkdir(exist_ok=True)
for scene in scenes:
 r=calculate(**{k:v for k,v in scene.items() if k!='id'});assert r==calculate(**r['scenario'])
 (P/'results'/(scene['id']+'.json')).write_text(json.dumps(r,indent=2)+'\n')
 lines=['# '+scene['id'],'','Conditional finite input supply; exact rational times. See CONTRACT.md.','','| Field | Value |','|---|---|']
 def visit(x,path=''):
  if isinstance(x,dict) and x:
   for k,v in x.items():visit(v,path+'.'+k if path else k)
  elif isinstance(x,list) and x:
   for i,v in enumerate(x):visit(v,path+f'[{i}]')
  else:lines.append('| '+path+' | '+str(x).replace('|','&#124;')+' |')
 visit(r);(P/'results'/(scene['id']+'.md')).write_text('\n'.join(lines)+'\n')
files=[P/'calculate.py',P/'test_supply.py',P/'CONTRACT.md',P/'scenarios.json',*sorted((P/'results').glob('*'))]
(P/'bindings.json').write_text(json.dumps({'files':[{'file':str(f.relative_to(P)),'sha256':hashlib.sha256(f.read_bytes()).hexdigest()} for f in files]},indent=2)+'\n')
print([(s['id'],json.loads((P/'results'/(s['id']+'.json')).read_text())['summary']['training_end_exact']) for s in scenes])
