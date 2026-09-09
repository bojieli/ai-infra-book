"""Independent route/ownership/bytes and real-message reduction replay."""
from pathlib import Path
import sys,json,hashlib,copy,gzip
from collections import Counter,defaultdict
HERE=Path(__file__).resolve().parent;CALC=HERE.parents[1];CAND=CALC/'research/qwen235-execution/public'
sys.path.insert(0,str(CALC/'src'))
from infra_calc import topics
topics.__path__.insert(0,str(CAND/'src/infra_calc/topics'))
from infra_calc.topics import qwen235_execution as m,qwen235_placement
from infra_calc.sources import model_config
c=model_config('qwen3-235b-a22b');H=c['hidden_size'];F=c['moe_intermediate_size'];E=c['num_experts'];K=c['num_experts_per_tok'];L=c['num_hidden_layers']
checks=[]
def ck(label,condition):
 checks.append({'check':label,'passed':bool(condition)})
 assert condition,label
for tp,ep,pp in [(2,4,1),(1,4,2),(4,2,1),(8,1,1),(2,2,2)]:
 for policy in ['balanced','hot']:
  args=dict(tp=tp,ep=ep,pp=pp,requests=2,tokens=3,route_policy=policy)
  r=m.calculate(**args);R=6;tag=f'{tp}/{ep}/{pp}/{policy}'
  ck(tag+' true total matrix',r['summary']['expert_matrix_flops']==6*L*R*K*H*F)
  ck(tag+' explicit logical route bytes',r['metadata']['route_table_logical_bytes']==L*R*(24+8*K))
  ck(tag+' no fabricated dispatch',r['summary']['dispatch_wire_bytes']==0 and all('dispatch' not in x['phase'] for x in r['messages']))
  expected_wire=0
  layers=defaultdict(list)
  for route in r['route_table']:layers[route['layer']].append(route)
  for layer,table in layers.items():
   hist=Counter(e for x in table for e in x['experts']);active=[set() for _ in range(ep)]
   for row in table:
    for expert in row['experts']:active[expert//(E//ep)].add(row['request_id']*3+row['position'])
   S=sum(map(len,active));A0=len(active[0]);expected_rows=tp*S-A0+(tp*ep-1)*R
   msgs=[x for x in r['messages'] if x['layer']==layer and x['phase'] not in ('pp_transfer','pp_replicate')]
   ck(tag+f' L{layer} closed wire rows',sum(len(x['token_ids']) for x in msgs)==expected_rows)
   expected_wire+=expected_rows*(H*2+16)
   stage=next(rank['pipeline_stage'] for rank in r['ranks'] if rank['layer_range'][0]<=layer<rank['layer_range'][1])
   for rank in r['ranks']:
    entries=[x for x in rank['experts'] if x['layer']==layer]
    for entry in entries:
     ck(tag+f' L{layer} rank{rank["rank"]} e{entry["expert"]}',entry['rows']==hist[entry['expert']] and entry['matrix_flops']==6*hist[entry['expert']]*H*(F//tp))
   # A 2-coordinate projection proxy retains the actual route weights and exact message token identities.
   values={stage*tp*ep+o*tp+t:[[0.,0.] for _ in range(R)] for o in range(ep) for t in range(tp)}
   direct=[[0.,0.] for _ in range(R)]
   for row in table:
    token=row['request_id']*3+row['position']
    for expert,weight in zip(row['experts'],row['weights']):
     for t in range(tp):
      owner=expert//(E//ep);rank=stage*tp*ep+owner*tp+t
      v=[weight*(expert+1)*(t+1),weight*(token+1)*(t+2)]
      for j in range(2):values[rank][token][j]+=v[j];direct[token][j]+=v[j]
   for phase in ['tp_reduce','ep_reduce','ep_broadcast','tp_broadcast']:
    for msg in [x for x in msgs if x['phase']==phase]:
     src,dst=msg['source'],msg['target'];ck(tag+f' L{layer} endpoint',src in values and dst in values and src!=dst)
     for token in msg['token_ids']:
      if phase.endswith('reduce'):values[dst][token]=[a+b for a,b in zip(values[dst][token],values[src][token])]
      else:values[dst][token]=values[src][token][:]
   ck(tag+f' L{layer} actual messages reconstruct all cohort replicas',all(v==direct for v in values.values()))
  ppmsgs=[x for x in r['messages'] if x['phase']=='pp_transfer'];fan=[x for x in r['messages'] if x['phase']=='pp_replicate']
  ck(tag+' PP count',len(ppmsgs)==pp-1 and len(fan)==(pp-1)*(tp*ep-1))
  expected_wire+=(pp-1)*tp*ep*R*(H*2+16)
  ck(tag+' full closed wire total',r['summary']['total_wire_bytes']==expected_wire)
  ck(tag+' source destination conservation',sum(x['sent_wire_bytes'] for x in r['ranks'])==sum(x['received_wire_bytes'] for x in r['ranks'])==expected_wire)
  placed=qwen235_placement.calculate(tp=tp,ep=ep,pp=pp)
  for actual,original in zip(r['ranks'],placed['ranks']):
   fmt=original['formats'][0];ck(tag+' placement '+str(actual['rank']),actual['conditional_resident_bytes']==fmt['weight_bytes']+2*fmt['kv_bytes_per_request']+2*2**30)
  boundary=max(x['conditional_resident_bytes'] for x in r['ranks'])
  for delta in [-1,0,1]:ck(tag+f' capacity {delta}',m.calculate(**args,capacity_bytes=boundary+delta)['summary']['all_necessary_capacity_fits']==(delta>=0))
# Explicit legal routing with all contributions on a non-root EP, including zero route weights.
a=m.calculate(tokens=1);table=copy.deepcopy(a['route_table'])
for row in table:row['experts']=list(range(64,72));row['weights']=[1.]+[0.]*7
r=m.calculate(tokens=1,routes=table)
ck('EP0 zero local contribution still receives complete reduce',all(x['source']==4 and x['target']==0 for x in r['messages'] if x['phase']=='ep_reduce'))
ck('Zero weights still execute selected expert matrices',r['summary']['expert_matrix_flops']==6*L*K*H*F)
for scene in json.loads((CAND/'book.append.json').read_text()):
 r=m.calculate(**{k:v for k,v in scene.items() if k!='id'});ck(scene['id']+' frozen replay',r==json.loads((CAND/'results'/(scene['id']+'.json')).read_text()))
raw=Path(m.__file__).read_bytes();(HERE/'candidate.snapshot.py').write_bytes(raw)
output=dict(candidate_sha256=hashlib.sha256(raw).hexdigest(),checks=len(checks),passed=sum(x['passed'] for x in checks),failed=[x for x in checks if not x['passed']]);(HERE/'verification.json').write_text(json.dumps(output,indent=2)+'\n');(HERE/'checks.json.gz').write_bytes(gzip.compress((json.dumps(checks,indent=2)+'\n').encode(),mtime=0));print(json.dumps(output,indent=2))
