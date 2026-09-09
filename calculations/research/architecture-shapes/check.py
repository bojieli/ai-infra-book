from pathlib import Path
import hashlib,importlib.util,json,sys
HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[1]
sys.path.insert(0,str(PROJECT/'src'))
p=HERE/'public/src/infra_calc/architecture_shape_plot.py'
s=importlib.util.spec_from_file_location('shape_plot',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
d=m.calculate();assert d==json.loads((HERE/'figures/data.json').read_text())
original=json.loads((PROJECT/'results/architecture-decode.json').read_text())
moe=json.loads((PROJECT/'configs/models/qwen3-235b-a22b/config.json').read_text())
checks=1
for r in d['panels']:
 if r['family']=='Dense':
  c=next(x['config'] for x in original['variants'] if x['name']==r['name'])
 else:c={**moe,'num_experts':r['experts'],'moe_intermediate_size':r['intermediate']}
 h=c['hidden_size'];layers=c['num_hidden_layers'];head=c['head_dim'];q=c['num_attention_heads']*head;kv=c['num_key_value_heads']*head;v=c['vocab_size']
 attention=2*h*q+2*h*kv;norm=2*h+2*head
 if r['family']=='Dense':
  f=c['intermediate_size'];ffn=3*h*f;total=2*v*h+h+layers*(attention+norm+ffn)
  assert r['ffn_parameters_all_layers']==layers*ffn
  assert r['weights_per_ffn']==[[f,h],[f,h],[h,f]]
 else:
  f=r['intermediate'];e=r['experts'];ffn=3*e*h*f;router=h*e;total=2*v*h+h+layers*(attention+norm+ffn+router)
  assert r['expert_parameters_all_layers']==layers*ffn
  assert r['router_parameters_all_layers']==layers*router
  assert r['active_expert_parameters_all_layers']==3*layers*r['top_k']*h*f
  assert r['weights_per_expert']==[[f,h],[f,h],[h,f]]
  assert r['first_recorded_expert_set']==r['first_recorded_route']['experts']
  checks+=3
 assert total==r['total_parameters'],(r['name'],total,r['total_parameters'])
 assert r['layers']==layers and r['hidden']==h
 assert r['released_baseline']==(r['name']=='baseline')
 checks+=5
assert sum(r['released_baseline'] for r in d['panels'])==2
checks+=1
files=[p,HERE/'check.py',*sorted((HERE/'figures').glob('*'))]
report={'passed':checks,'checks':checks,'input_bindings':d['inputs'],'bindings':[{'file':str(f.relative_to(HERE)),'sha256':hashlib.sha256(f.read_bytes()).hexdigest()} for f in files]}
(HERE/'verification.json').write_text(json.dumps(report,indent=2)+'\n');print(checks)
