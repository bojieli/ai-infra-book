"""Validate downloaded author histories; never generates or digitizes observations."""
import json,pathlib
B=pathlib.Path(__file__).resolve().parent
runs={e['node']['name']:e['node'] for e in json.loads((B/'wandb/runs.json').read_text())['data']['project']['runs']['edges']}
selected={};summary=[]
def flat(obj,p=''):
 if isinstance(obj,dict):
  out={}
  for k,v in obj.items():out.update(flat(v,p+'.'+k if p else k))
  return out
 return {p:obj}
for p in sorted((B/'wandb/histories').glob('*.json')):
 if '.query.' in p.name or '.source.' in p.name:continue
 response=json.loads(p.read_text());assert not response.get('errors');r=response['data']['project']['run'];h=[json.loads(x) for x in r['history']]
 assert [x['_step'] for x in h]==list(range(101)),r['name'];assert r['state']=='finished';assert not r['files']['pageInfo']['hasNextPage']
 config=json.loads(runs[r['name']]['config']);selected[r['name']]=config
 names=['train/token_mult_prob_error','train/js_divergence_error','train/reward','train/loss','timing/train/generation','timing/train/policy_and_reference_logprobs','timing/train/policy_training','timing/train/total_step_time']
 coverage={k:sum(type(x.get(k)) in (int,float) for x in h) for k in names}
 summary.append(dict(run=r['name'],state=r['state'],rows=len(h),steps=[0,100],metric_coverage=coverage,file_names=[e['node']['name'] for e in r['files']['edges']],raw_route_trace_present=any('r3_trace' in e['node']['name'] or 'routed_experts' in e['node']['name'] for e in r['files']['edges'])))
pairs=[]
for v in [1,2,6,7]:
 on=next(n for n in selected if n.startswith(f'gate3-v{v}-r3on'));off=next(n for n in selected if n.startswith(f'gate3-v{v}-r3off'));a=flat(selected[on]);b=flat(selected[off]);diff=[dict(key=k,on=a.get(k),off=b.get(k)) for k in sorted(a.keys()|b.keys()) if a.get(k)!=b.get(k)];pairs.append(dict(label=f'gate3-v{v}',on=on,off=off,config_differences=diff))
(B/'history-inventory.json').write_text(json.dumps(dict(scope='Author-logged history JSON rows returned by W&B history(samples=1000); each selected run has all integer steps 0..100, no missing steps; not original per-token route tensors',total_rows=sum(x['rows'] for x in summary),runs=summary,pairs=pairs),indent=2)+'\n')
print('rows',sum(x['rows'] for x in summary))
for pair in pairs:print(pair['label'],[(d['key'],d['on'],d['off']) for d in pair['config_differences']])
print('coverage',summary[0]['metric_coverage'])
