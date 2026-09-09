"""Independent integer-tick scheduler and cohort cost audit."""
import importlib.util,json
from pathlib import Path
from fractions import Fraction as F
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('cohort_candidate',HERE/'calculate.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

def tick(requests,replicas,durations,work,fault,recovery):
 results=[];attempts=[];used=False
 for replica in range(replicas):
  queue=list(range(replica,requests,replicas));active=None;time=0;blocked_until=0;attempt_number=0
  while queue or active:
   # First settle stage completion; full request commit wins failure ties.
   just_completed=False
   if active and time==active['stage_end']:
    name,flops=work[active['stage']]
    active['completed_stages'].append(dict(name=name,matrix_flops=flops));just_completed=True
    active['stage']+=1
    if active['stage']==len(durations):
     attempts.append(dict(request=active['request'],replica=replica,attempt=attempt_number,
       start_ms=active['start'],end_ms=time,aborted=False,completed_stages=active['completed_stages'],
       partial_stage=None,completed_stage_matrix_flops=sum(s['matrix_flops'] for s in active['completed_stages'])))
     results.append(dict(request=active['request'],replica=replica,arrival_ms=0,completion_ms=time,latency_ms=time,attempts=attempt_number+1))
     active=None;attempt_number=0
   if replica==0 and fault is not None and time==fault and (active or queue):
    used=True;blocked_until=time+recovery
    if active:
     partial=None if just_completed else dict(name=work[active['stage']][0],elapsed_ms=time-active['stage_start'],matrix_flops=None)
     attempts.append(dict(request=active['request'],replica=replica,attempt=attempt_number,
       start_ms=active['start'],end_ms=time,aborted=True,completed_stages=active['completed_stages'],partial_stage=partial,
       completed_stage_matrix_flops=sum(s['matrix_flops'] for s in active['completed_stages'])))
     queue.insert(0,active['request']);active=None;attempt_number+=1
   if time>=blocked_until:
    if active and just_completed:
     active['stage_start']=time;active['stage_end']=time+durations[active['stage']]
    if active is None and queue:
     active=dict(request=queue.pop(0),start=time,stage=0,stage_start=time,stage_end=time+durations[0],completed_stages=[])
   time+=1
   assert time<100000
 return dict(requests=sorted(results,key=lambda r:r['request']),attempts=attempts,
  horizon_ms=max(r['completion_ms'] for r in results),fault_used=used,
  abandoned_completed_stage_matrix_flops=sum(r['completed_stage_matrix_flops'] for r in attempts if r['aborted']),
  abandoned_partial_stage_work_unknown=any(r['partial_stage'] is not None for r in attempts))

# Tiny known stage work makes exact boundaries transparent. Failures cover0,
# stage ends, full-request ends, the queued request, and after all work.
trace_cases=[]
for durations in ([3],[3,2],[3,2,1]):
 work=[(f's{i}',(i+1)*101) for i in range(len(durations))]
 for requests in (1,3,7):
  for replicas in (1,2,4):
   for fault in [None,*range(0,20)]:
    for recovery in (0,1,5):
     expected=tick(requests,replicas,durations,work,fault,recovery)
     actual=m.schedule(requests,replicas,durations,work,fault,recovery)
     assert actual==expected,(durations,requests,replicas,fault,recovery,actual,expected)
     trace_cases.append((durations,requests,replicas,fault,recovery))
scene_count=0;infeasible_count=0;eligibility=[]
for model in ('qwen3-8b','qwen3-32b'):
 for requests in (1,4,8):
  for deadline in (80,250,600):
   for tag,fault,recovery,fee in [('healthy',None,0,'0'),('short',50,20,'0'),('long',50,200,'1')]:
    r=m.calculate(model=model,requests=requests,deadline_ms=deadline,fault_at_ms=fault,recovery_ms=recovery,recovery_fee=fee)
    required=(3*requests+3)//4
    assert r['selection']['required_valid_requests']==required
    eligible=[];work=[(s['name'],s['matrix_flops']) for s in r['stages']]
    assert [n for n,f in work]==['prefill']+[f'decode{i}' for i in range(7)]
    assert all(type(f)==int and f>0 for n,f in work)
    for c in r['candidates']:
     assert c['total_cards']==8 and c['tp']*c['replicas']==8
     assert len(c['placement_cards'])==8
     # TP<=KV-head count here; each physical replica owns precisely one full
     # final-history KV set, with no head duplication at these TP choices.
     unit=147456 if model=='qwen3-8b' else 262144
     assert sum(p['kv_bytes'] for p in c['placement_cards'])==c['replicas']*unit*(256+8-1)
     assert c['capacity_fits']==all(p['resident_bytes']<=24000000000 for p in c['placement_cards'])
     assert all(p['resident_bytes']==p['weight_bytes']+p['kv_bytes']+p['workspace_bytes'] for p in c['placement_cards'])
     if not c['capacity_fits']:
      assert c['schedule'] is None and c['cost'] is None and c['valid_requests'] is None and not c['slo_eligible']
      infeasible_count+=1;continue
     expected=tick(requests,c['replicas'],c['declared_stage_durations_ms'],work,fault,recovery)
     assert c['schedule']==expected
     valid=sum(x['completion_ms']<=deadline for x in expected['requests'])
     total=F(8*expected['horizon_ms'],1000)+(F(fee) if expected['fault_used'] else 0)
     assert c['valid_requests']==valid
     assert c['slo_eligible']==(valid>=required)
     assert F(c['cost']['full_declared_cost_exact'])==total
     assert F(c['cost']['subtotals_exact']['steady_service'])==F(8*expected['horizon_ms'],1000)
     assert F(c['cost']['subtotals_exact']['recovery_and_replay'])==(F(fee) if expected['fault_used'] else 0)
     assert c['cost']['observed_or_measured'] is False
     if valid:assert F(c['cost']['cost_per_slo_valid_request_exact'])==total/valid
     else:assert c['cost']['cost_per_slo_valid_request_exact'] is None
     if valid>=required:eligible.append((c['id'],total/valid))
    best=min((v for _,v in eligible),default=None)
    assert r['selection']['eligible']==[k for k,v in eligible]
    assert r['selection']['winners']==[k for k,v in eligible if v==best]
    assert r['selection']['minimum_cost_per_valid_request_exact']==(None if best is None else str(best))
    eligibility.append(dict(model=model,requests=requests,deadline=deadline,fault=tag,selection=r['selection']))
    scene_count+=1
assert scene_count==54 and infeasible_count>0
invalid=[{'requests':0},{'requests':True},{'outputs':0},{'deadline_ms':0},{'recovery_ms':-1},
         {'fault_at_ms':-1},{'recovery_fee':'-1'},{'minimum_valid_fraction':'0'},
         {'minimum_valid_fraction':'5/4'},{'model':'bad'}]
for args in invalid:
 try:m.calculate(**args)
 except ValueError:pass
 else:raise AssertionError(args)
(HERE/'check-result.json').write_text(json.dumps(dict(status='passed',tick_scenarios=len(trace_cases),
 official_composite_scenes=scene_count,infeasible_candidate_exclusions=infeasible_count,
 invalid_inputs=len(invalid),selections=eligibility),indent=2)+'\n')
print(f'PASS: {len(trace_cases)} independent tick cases;54 composite scenes;{infeasible_count} capacity exclusions;10 invalid inputs.')
