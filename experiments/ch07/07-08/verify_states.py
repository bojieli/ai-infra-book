"""Full model/Adam tensor checks and same-rank trajectory checks across conditions."""
import argparse
import json
from pathlib import Path
import torch

p=argparse.ArgumentParser();p.add_argument('--run',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
a=p.parse_args();torch.set_num_threads(1);checks=0;differences=[]
for job,label in [(0,'solo-a'),(1,'solo-b')]:
    ref_path=a.run/f'r0-{label}'/f'job{job}-rank0/final.pt'
    ref=torch.load(ref_path,map_location='cpu',weights_only=True)
    for path in sorted(a.run.glob(f'*/job{job}-rank*/final.pt')):
        other=torch.load(path,map_location='cpu',weights_only=True)
        assert ref['optimizer']['param_groups']==other['optimizer']['param_groups'];checks+=1
        for key,value in ref['model'].items():
            checks+=1
            if not torch.equal(value,other['model'][key]):differences.append(dict(file=str(path),key=key,max_abs=(value-other['model'][key]).abs().max().item()))
        for key,state in ref['optimizer']['state'].items():
            for name,value in state.items():
                checks+=1;candidate=other['optimizer']['state'][key][name]
                if not torch.equal(value,candidate):differences.append(dict(file=str(path),key=f'{key}.{name}',max_abs=(value-candidate).abs().max().item()))
        rank=int(path.parent.name[-1]);reference=json.loads((a.run/f'r0-{label}'/f'job{job}-rank{rank}/steps.json').read_text())
        current=json.loads((path.parent/'steps.json').read_text());assert len(reference)==len(current);checks+=1
        for x,y in zip(reference,current):
            checks+=2;assert x['input_offsets']==y['input_offsets']
            if x['loss']!=y['loss']:differences.append(dict(file=str(path),step=x['step'],kind='loss',reference=x['loss'],actual=y['loss']))
out=dict(checks=checks,all_exact=not differences,differences=differences,
         scope='all saved final model/Adam tensors and per-rank input/loss trajectories; timing not required equal')
a.out.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'checks':checks,'all_exact':not differences,'differences':len(differences)}))
