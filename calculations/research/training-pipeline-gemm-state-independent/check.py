"""Independent closed-form tensor storage and interval/VJP checks; no shared writes."""
from pathlib import Path
import hashlib,json,sys,math
HERE=Path(__file__).resolve().parent;CALC=HERE.parents[1]
sys.path.insert(0,str(CALC/'src'))
from infra_calc import topics
CAND=CALC/'research/training-pipeline-gemm-state/public'
topics.__path__.insert(0,str(CAND/'src/infra_calc/topics'))
from infra_calc.topics import training_pipeline_gemm_state as m,training_pipeline_schedule as base
checks=[]
def ck(name,cond):
 checks.append({'name':name,'passed':bool(cond)})
 assert cond,name
for policy in ['gpipe','1f1b']:
 for nonlinear in ['save_nonlinear','recompute_silu']:
  for strategy in ['save_inputs','recompute_products']:
   r=m.calculate(microbatches=3,microbatch_size=2,tokens=3,policy=policy,activation_policy=nonlinear,gemm_policy=strategy)
   tag='/'.join([policy,nonlinear,strategy]);R=6
   perlayer=4*R*(4*4096+2*1024+12288) if strategy=='save_inputs' else 4*R*(2*4096+2*1024)
   expected=[9*perlayer]*4
   if strategy=='save_inputs':expected[3]+=4*R*4096
   ck(tag+' closed form stage bytes',r['reservation']['added_persistent_bytes_per_microbatch_stage']==expected)
   extra=0 if strategy=='save_inputs' else R*(36*(2*4096+12288)+4096)
   ck(tag+' scalar',r['work']['extra_per_microbatch_scalar_flops']==extra)
   ck(tag+' no duplicate specials',r['work']['extra_special_calls']==0 and r['work']['extra_matrix_flops']==0)
   objects={x['id']:x for x in r['tensor_objects']};old={x['id']:x for x in r['reused_nonlinear_saved_objects']}
   ck(tag+' distinct IDs',not(objects.keys()&old.keys()) and len(objects)==253)
   ck(tag+' 325 matrices',len(r['matrix_vjp_requirements'])==325)
   for layer in range(36):
    req={x['matrix']:x['saved_operand_ids'] for x in r['matrix_vjp_requirements'] if x['layer']==layer}
    ck(tag+f' L{layer} input sharing',req['q_proj']==req['k_proj']==req['v_proj'] and req['gate_proj']==req['up_proj'])
    ck(tag+f' L{layer} unique GQA',objects[req['qk'][1]]['elements']==R*1024 and objects[req['pv'][1]]['elements']==R*1024)
    ck(tag+f' L{layer} existing P',old[req['pv'][0]]['name']=='attention_probabilities')
   b=base.calculate(microbatches=3,microbatch_size=2,tokens=3,policy=policy,activation_policy=nonlinear)
   ck(tag+' source arithmetic unchanged',r['work']['original_pipeline_work']==b['work'])
   ck(tag+' same explicit time contract',r['schedule']['events']==b['events'])
   # Independently add actual identity envelopes to baseline; candidate aggregates them instead.
   intervals=b['activation_intervals']+r['reservation']['individual_tensor_envelopes']
   for event in b['events']:
    if event['kind']=='B' and strategy=='recompute_products':
     intervals.append(dict(stage=event['stage'],start=event['start'],end=event['end'],bytes=4*R*12288))
   for stage in range(4):
    own=[x for x in intervals if x['stage']==stage]
    times=sorted({x[k] for x in own for k in ['start','end']})
    peak=max(sum(x['bytes'] for x in own if x['start']<=a<x['end']) for a in times)
    ck(tag+f' stage{stage} independent identity union peak',peak==r['reservation']['combined_peak_declared_bytes'][stage])
   if nonlinear=='recompute_silu':
    pair=[i for i in r['reservation']['combined_intervals'] if i.get('kind')=='recompute_workspace_reservation']
    ck(tag+' one existing SiLU pair per stage B',len(pair)==12 and all(i['bytes']==8*R*12288 for i in pair))
# A small linear VJP finite-difference check validates why actual weighted/product inputs matter.
z=[.5,-.2,.8];gamma=[1.2,.7,-.4];up=[1.1,.4,-.2];gate=[.3,-.7,.9];dy=[.2,-.6];W=[[.1,-.4,.8],[.5,.2,-.1]]
for name,x in [('weighted',[a*b for a,b in zip(z,gamma)]),('swiglu',[g/(1+math.exp(-g))*u for g,u in zip(gate,up)])]:
 def loss(weights):return sum(d*sum(w*v for w,v in zip(row,x)) for d,row in zip(dy,weights))
 for i in range(2):
  for j in range(3):
   eps=1e-6;wp=[v[:] for v in W];wm=[v[:] for v in W];wp[i][j]+=eps;wm[i][j]-=eps
   ck(name+f' dW{i,j}',abs((loss(wp)-loss(wm))/(2*eps)-dy[i]*x[j])<1e-10)
for scene in json.loads((CAND/'book.append.json').read_text()):
 result=m.calculate(**{k:v for k,v in scene.items() if k!='id'})
 ck(scene['id']+' replay',result==json.loads((CAND/'results'/(scene['id']+'.json')).read_text()))
raw=Path(m.__file__).read_bytes();(HERE/'candidate.snapshot.py').write_bytes(raw)
output={'candidate_sha256':hashlib.sha256(raw).hexdigest(),'checks':len(checks),'passed':sum(x['passed'] for x in checks),'failed':[x for x in checks if not x['passed']]}
(HERE/'verification.json').write_text(json.dumps(output,indent=2)+'\n');(HERE/'checks.json').write_text(json.dumps(checks,indent=2)+'\n');print(json.dumps(output,indent=2))
