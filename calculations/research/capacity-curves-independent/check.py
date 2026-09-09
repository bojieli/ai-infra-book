"""Independent staircase evaluation from integer feasible cohorts."""
from pathlib import Path
import hashlib
import importlib.util
import json
import random
import sys

HERE=Path(__file__).resolve().parent;P=HERE.parents[1];C=HERE.parent/'capacity-curves'
sys.path.insert(0,str(P/'src'))
spec=importlib.util.spec_from_file_location('plot_candidate',C/'public/src/infra_calc/capacity_plot.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
data=json.loads((C/'figures/data.json').read_text());checks=[]
def check(name,ok):
    assert ok,name
    checks.append(name)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
for row in json.loads((C/'verification.json').read_text())['bindings']:
    check('artifact:'+row['file'],sha(C/row['file'])==row['sha256'])
for row in data['inputs']:check('input:'+row['file'],sha(P/row['file'])==row['sha256'])
check('complete data replay',m.calculate()==data)
for panel in data['panels']:
    snapshots=[json.loads(m.source_path(panel['model'],n).read_text()) for n in (24,48,80)]
    base=snapshots[0];ws=base['scenario']['workspace_bytes']
    for bits in (16,8,4):
        curve=next(x for x in panel['curves'] if x['bits']==bits)
        rows=[next(x for x in rank['formats'] if x['bits']==bits) for rank in base['ranks']]
        def count(c):return max(0,min((c-x['weight_bytes']-ws)//x['kv_bytes_per_request'] for x in rows))
        def line(n):return max(x['weight_bytes']+ws+n*x['kv_bytes_per_request'] for x in rows)
        def plotted(c):return next(x['maximum_requests'] for x in reversed(curve['points']) if x['capacity_bytes']<=c)
        check(panel['model']+str(bits)+':zero threshold',curve['weights_workspace_minimum_bytes']==line(0))
        check(panel['model']+str(bits)+':one threshold',curve['first_request_minimum_bytes']==line(1))
        # Every threshold in visible range, including final/first plotted jump.
        for n in range(1,count(80*10**9)+2):
            c=line(n)
            check(f'{panel["model"]}:{bits}:{n}:exact boundary',count(c)==n and count(c-1)==n-1 and count(c+1)==n)
            for probe in (c-1,c,c+1):
                if 24*10**9<=probe<=80*10**9:
                    check(f'{panel["model"]}:{bits}:{n}:{probe}:stairs',plotted(probe)==count(probe))
        for cap,snap in zip((24,48,80),snapshots):
            saved=next(x for x in snap.get('summary',snap.get('cohort')) if x['bits']==bits)
            expected=saved.get('maximum_global_requests',saved.get('maximum_requests'))
            check(f'{panel["model"]}:{bits}:{cap}:public',plotted(cap*10**9)==count(cap*10**9)==expected)
# Different rank slopes and intercepts, ties and three successive limiters.
ranks=[{'formats':[dict(bits=16,weight_bytes=w,kv_bytes_per_request=k)]} for w,k in [(200,1),(100,8),(0,12)]]
limiters=[]
for n in range(0,41):
    values=[200+n,100+8*n,12*n]
    check('changing limiter:'+str(n),m.threshold(ranks,16,17,n)==max(values)+17)
    limiters.append(values.index(max(values)))
check('all three rank limiters exercised',set(limiters)=={0,1,2})
check('correct layout labels',[x['topology'] for x in data['panels']]==['TP8','TP8','TP8','TP2 / EP4'])
check('zero notfit disclosure','Zero requests includes weights-not-fitting' in data['scope'])
(HERE/'results.json').write_text(json.dumps({'checks':len(checks),'passed':len(checks),'source_count':len(data['inputs']),'curves':12,'limiter_sequence':limiters,'module_sha':sha(C/'public/src/infra_calc/capacity_plot.py'),'data_sha':sha(C/'figures/data.json'),'png_sha':sha(C/'figures/figure.png')},indent=2)+'\n')
print(len(checks),'checks passed')
