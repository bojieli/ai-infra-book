"""Recompute medians and rate boundaries directly from the archived raw samples."""
from pathlib import Path
from fractions import Fraction
import json,hashlib
p=Path(__file__).resolve().parent;root=p.parents[2]
r=json.loads((p/'result.json').read_text());checks=0
raw={d:json.loads((root/f'experiments/ch04/04-06/results/projection-{d}/results.json').read_text(),parse_float=str) for d in ('mps','cuda')}

def equal(a,b):
    global checks
    assert a==b,(a,b)
    checks+=1

for case in r.values():
    for row in case['rows']:
        times={}
        for device in raw:
            source=next(x for x in raw[device]['rows'] if x['m']==row['m'])
            values=[Fraction(v) for v in source['paths'][row['mode']]['wall_us']]
            # Rank-based median identification, independent of sorted()[5].
            median=next(v for v in values if sum(x<=v for x in values)>=6 and sum(x>=v for x in values)>=6)
            times[device]=median/1000000
            equal(Fraction(**row['times_seconds_exact'][device]),times[device])
        threshold=times['mps']/times['cuda']
        equal(Fraction(**row['rtx_over_mac_rate_tie_ratio']),threshold)
        equal(row['matrix_flops'],2*row['m']*4096*4096)
        for parameter,field,divisor,winner in [('hourly_cost_units','cost_per_call_proxy',3600,'lower_declared_cost'),('whole_system_watts','joules_per_call_proxy',1,'lower_declared_energy')]:
            declared=case['scenario'][parameter]
            if declared is None:
                equal(row[field],None);equal(row[winner],None)
            else:
                values={d:times[d]*Fraction(declared[d])/divisor for d in times}
                for d,value in values.items():equal(Fraction(**row[field][d]),value)
                equal(row[winner],[d for d,v in values.items() if v==min(values.values())])
        equal(row['measured_task_energy_joules'],None)
        equal(row['observed_cost_per_call'],None)
report={'status':'passed','independent_checks':checks,'cases':len(r),'sha256':{name:hashlib.sha256((p/name).read_bytes()).hexdigest() for name in ['calculate.py','inputs.lock.json','result.json']}}
(p/'verification.json').write_text(json.dumps(report,indent=2)+'\n');print(report)
