"""Independent per-tick resource simulation and slot/shape conservation checks."""
import json,hashlib
from pathlib import Path
p=Path(__file__).resolve().parent;r=json.loads((p/'result.json').read_text());checks=0

def equal(a,b):
    global checks
    assert a==b,(a,b)
    checks+=1

for name,case in r.items():
    c=case['scenario'];n=c['length'];g=c['group_rows'];groups=n//g;slots=c['slots'];hop=2 if c['path']=='staged' else 1
    ceil=lambda a,b:(a+b-1)//b
    tasks=[]
    for i in range(groups):
        prefix=f'g{i}';matrix=ceil(2*g*n*128,c['matrix_flops_per_tick'])
        vector=ceil(3*g*n-g,c['scalar_ops_per_tick'])+ceil(g*(n-1),c['comparison_ops_per_tick'])+ceil(g*n,c['exp_ops_per_tick'])+ceil(g*n,c['div_ops_per_tick'])
        deps=([f'g{i-slots}.pv'] if i>=slots else [])+([f'g{i-1}.qk'] if i else [])
        for suffix,duration,dependencies,resource in [('qk',matrix,deps,'matrix'),('scores',ceil(hop*4*g*n,c['link_bytes_per_tick']),[prefix+'.qk'],'handoff'),('softmax',vector,[prefix+'.scores'],'vector'),('probabilities',ceil(hop*2*g*n,c['link_bytes_per_tick']),[prefix+'.softmax'],'handoff'),('pv',matrix,[prefix+'.probabilities'],'matrix')]:
            tasks.append((prefix+'.'+suffix,duration,dependencies,resource))
    pending=tasks[:];active={};done={};starts={};tick=0
    while len(done)<len(tasks):
        for resource,(tid,end) in list(active.items()):
            if end==tick:done[tid]=end;del active[resource]
        for task in pending[:]:
            tid,duration,deps,resource=task
            if all(dep in done for dep in deps) and resource not in active:
                starts[tid]=tick;active[resource]=(tid,tick+duration);pending.remove(task)
        tick+=1
    equal(max(done.values()),case['summary']['finish_tick'])
    for event in case['timeline']:
        equal(event['start_tick'],starts[event['id']]);equal(event['end_tick'],done[event['id']])
    for i,owner in enumerate(case['slot_ownership']):
        equal(owner['start_tick'],starts[f'g{i}.qk']);equal(owner['release_tick'],done[f'g{i}.pv'])
        if i>=slots:equal(starts[f'g{i}.qk']>=done[f'g{i-slots}.pv'],True)
    equal(case['summary']['total_matrix_flops'],4*n*n*128)
    equal(case['summary']['crossing_payload_bytes'],6*n*n)
    equal(case['summary']['served_handoff_bytes'],hop*6*n*n)
    equal(sum(w['masked_score_elements'] for w in case['work']),n*(n-1)//2)
    equal(case['summary']['reserved_handoff_bytes'],slots*6*g*n)
report={'status':'passed','independent_checks':checks,'scenarios':len(r),'sha256':{name:hashlib.sha256((p/name).read_bytes()).hexdigest() for name in ['calculate.py','result.json']}}
(p/'verification.json').write_text(json.dumps(report,indent=2)+'\n');print(report)
