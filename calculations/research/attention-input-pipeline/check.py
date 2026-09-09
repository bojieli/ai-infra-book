"""Independent tick-by-tick simulator, without importing the scheduling code."""
import json
from pathlib import Path
import hashlib
p=Path(__file__).resolve().parent
r=json.loads((p/'result.json').read_text())
checks=0

def equal(a,b):
    global checks
    assert a==b,(a,b)
    checks+=1

def simulate(count,slots,load,compute,latency,register,sync):
    owners={};events=[];issued=done=0;port_free=0;computing=None
    tick=0
    while done<count:
        if computing is not None and computing[1]==tick:
            owners.pop(computing[0]%slots);done+=1;computing=None
        if computing is None and done<issued and events[done]['ready']<=tick:
            computing=(done,tick+compute)
            events[done]['compute_start']=tick;events[done]['compute_end']=tick+compute
        if issued<count and tick>=port_free and issued%slots not in owners and (not sync or done==issued):
            owners[issued%slots]=issued
            events.append({'issue_start':tick,'ready':tick+load+latency+register})
            issued+=1;port_free=tick+load
        tick+=1
    return events

for name,case in r.items():
    c=case['scenario'];m,n,k=(c[key] for key in ('tile_m','tile_n','tile_k'))
    count=128//k;size=2*k*(m+n);flops=2*m*n*k
    ceil=lambda x,y:(x+y-1)//y
    equal(case['chunk_input_bytes'],size);equal(case['total_flops'],2*m*n*128)
    for row in case['rows']:
        sync=row['mode'].startswith('synchronous')
        load=ceil(size,c['input_bytes_per_tick']);comp=ceil(flops,c['matrix_flops_per_tick'])
        reg=ceil(2*size,c['register_bytes_per_tick']) if sync else 0
        trace=simulate(count,row['input_slots'],load,comp,c['latency_ticks'],reg,sync)
        for actual,expected in zip(row['timing']['chunks'],trace):
            for key in ('issue_start','compute_start','compute_end'):equal(actual[key],expected[key])
            equal(actual['data_ready'],expected['ready'])
        equal(row['timing']['finish_tick'],trace[-1]['compute_end'])
        equal(row['timing']['total_compute_busy_ticks']+row['timing']['total_compute_idle_ticks'],trace[-1]['compute_end'])
        equal(row['smem_reserved_bytes'],row['input_slots']*size)
        equal(row['register_interface_bytes'],2*size*count if sync else 0)
        equal(row['external_input_payload_bytes'],size*count)
        fits=row['input_slots']*size<=c['capacity_bytes']
        equal(row['capacity_qualified_finish_tick'],trace[-1]['compute_end'] if fits else None)
    rows=[x for x in case['rows'] if x['mode'].startswith('asynchronous')]
    ref=simulate(count,count,load,comp,c['latency_ticks'],0,False)[-1]['compute_end']
    equal(case['no_slot_backpressure_finish_tick'],ref)
    equal(case['smallest_enumerated_slots_matching_unlimited'],next((x['input_slots'] for x in rows if x['timing']['finish_tick']==ref),None))
report={'status':'passed','independent_checks':checks,'scenarios':len(r),'sha256':{name:hashlib.sha256((p/name).read_bytes()).hexdigest() for name in ('calculate.py','result.json')}}
(p/'verification.json').write_text(json.dumps(report,indent=2)+'\n');print(report)
