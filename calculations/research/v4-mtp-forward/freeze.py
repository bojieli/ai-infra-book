from pathlib import Path
import hashlib
import json
from calculate import calculate, markdown
from infra_calc.sources import provenance
P=Path(__file__).resolve().parent
PROJECT=P.parents[1]
scenes=[dict(id='v4-mtp-first-call'),dict(id='v4-mtp-b2-prefill16',batch=2,tokens=16),dict(id='v4-mtp-prefill129',tokens=129),dict(id='v4-mtp-history128',start_pos=128)]
(P/'results').mkdir(exist_ok=True)
summary=[]
for scene in scenes:
    r=calculate(**{k:v for k,v in scene.items() if k!='id'})
    assert r==calculate(**r['scenario'])
    (P/'results'/(scene['id']+'.json')).write_text(json.dumps(r,indent=2,allow_nan=False)+'\n')
    (P/'results'/(scene['id']+'.md')).write_text(markdown(r))
    summary.append(dict(id=scene['id'],summary=r['summary'],state=r['state']))
(P/'scenarios.json').write_text(json.dumps(scenes,indent=2)+'\n')
(P/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
(P/'sources.lock.subset.json').write_text(json.dumps(provenance('deepseek-v4-flash'),indent=2)+'\n')
deps=['sources.py','topics/v4_attention.py','topics/v4_attention_arithmetic.py','topics/v4_sparse_kernel.py','topics/transforms.py','topics/experts.py','topics/expert_arithmetic.py','topics/expert_dispatch.py','topics/v4_expert_format.py','topics/hyper_connections.py','topics/v4_fp8_linear.py']
files=[x for x in sorted(P.rglob('*')) if x.is_file() and '__pycache__' not in x.parts and x.name!='bindings.json']+[PROJECT/'src/infra_calc'/f for f in deps]
(P/'bindings.json').write_text(json.dumps([dict(file=str(x.relative_to(PROJECT)),sha256=hashlib.sha256(x.read_bytes()).hexdigest()) for x in files],indent=2)+'\n')
print([(x['id'],x['summary']['matrix_flops']) for x in summary])
