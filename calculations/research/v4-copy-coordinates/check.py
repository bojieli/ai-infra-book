"""Independent row-interval coverage and source-coordinate checks."""
from pathlib import Path
from collections import Counter
import json,hashlib
p=Path(__file__).resolve().parent;r=json.loads((p/'result.json').read_text());checks=0

def equal(a,b):
    global checks
    assert a==b,(a,b)
    checks+=1

for call in r['calls']:
    m,n,k=call['M'],call['N'],call['K'];kb=k//128
    coverage={'A':Counter(),'B':Counter()};payload={'A':0,'B':0}
    scale_a=Counter();scale_b=Counter();out=Counter()
    for event in call['input_copy_coordinates']:
        by,bx=event['block'];ki=event['k_iteration']
        for name,start,count in [('A',by*32,32),('B',bx*128,128)]:
            view=event[name]
            equal(view['origin'],[start,ki*128]);equal(view['offset_bytes'],start*k+ki*128)
            equal(view['row_stride_bytes'],k);equal(view['row_bytes'],128);equal(view['rows'],count)
            for row in range(start,start+count):
                coverage[name][(row,ki*128)]+=1;payload[name]+=128
                equal((row*k+ki*128)//k,row)
                equal((row*k+ki*128)%k+128<=k,True)
        equal(event['scale_B']['offset_bytes'],bx*kb+ki);scale_b[(bx,ki)]+=1
        equal(event['scale_A']['first_offset_bytes'],by*32*kb+ki)
        for row in range(by*32,(by+1)*32):scale_a[(row,ki)]+=1
    for name,rows,repetitions in [('A',m,n//128),('B',n,m//32)]:
        equal(len(coverage[name]),rows*kb)
        equal(set(coverage[name].values()),{repetitions})
        equal(payload[name],rows*k*repetitions)
        equal(call['summary'][name+'_copy_payload_bytes'],payload[name])
        for row in range(rows):equal([col for col in range(0,k,128) if (row,col) in coverage[name]],list(range(0,k,128)))
    equal(set(scale_a.values()),{n//128});equal(set(scale_b.values()),{m//32})
    equal(sum(scale_a.values()),call['summary']['scale_A_read_bytes'])
    equal(sum(scale_b.values()),call['summary']['scale_B_read_bytes'])
    for view in call['output_copy_coordinates']:
        by,bx=view['block'];equal(view['offset_bytes'],2*(by*32*n+bx*128))
        for row in range(by*32,(by+1)*32):out[(row,bx*128)]+=1
    equal(len(out),m*(n//128));equal(set(out.values()),{1})
    equal(call['summary']['output_global_write_bytes'],2*m*n)
    for key in ['lowered_load_store_instructions','integer_address_instructions','TMA_descriptor_count','measured_hbm_bytes']:equal(call['summary'][key],None)
report={'status':'passed','independent_checks':checks,'calls':len(r['calls']),'sha256':{name:hashlib.sha256((p/name).read_bytes()).hexdigest() for name in ['calculate.py','result.json']}}
(p/'verification.json').write_text(json.dumps(report,indent=2)+'\n');print(report)
