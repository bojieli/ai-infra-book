"""Verify actual assignment buffers against full native routing arrays."""
import collections,gzip,hashlib,json,sys
from pathlib import Path
import numpy as np
B=Path(__file__).absolute().parent;O=Path(sys.argv[1]) if len(sys.argv)>1 else B/'results';O.mkdir(parents=True,exist_ok=True)
out=B/'runs/observe-001/output'
def read(p):return json.loads(p.read_text())
def rows(p):return [json.loads(l) for l in p.read_text().splitlines()]
sup=read(out.parent/'supervisor.json');assert sup['exit_code']==0 and sup['reason'] is None and not sup['leftovers']
assert hashlib.sha256((B/'run.py').read_bytes()).hexdigest()==read(out/'environment.json')['driver_sha256']
old=rows(B/'reference/requests.jsonl');new=rows(out/'requests.jsonl');assert len(old)==len(new)==4
routes={}
for a,b in zip(old,new):
    assert a['id']==b['id'] and a['prompt_ids']==b['prompt_ids'] and a['output_ids']==b['output_ids'] and a['text']==b['text']
    assert a['finish_reason']==b['finish_reason']=='stop'
    x=np.load(B/'reference'/a['route_file'],allow_pickle=False);y=np.load(out/b['route_file'],allow_pickle=False)
    assert np.array_equal(x,y);routes[b['id']]=y
observations=list(out.glob('*-assignments.jsonl.gz'));assert len(observations)==1
calls=collections.Counter();offsets={k:[0]*48 for k in routes};summaries={};record_count=0;active_verified=0
for p in observations:
    with gzip.open(p,'rt') as f:
        for line in f:
            r=json.loads(line);case=r['case_id'];layer=calls[case]%48;calls[case]+=1
            n=r['num_tokens'];start=offsets[case][layer];end=start+n;ids=routes[case][start:end,layer,:]
            assert ids.shape==(n,8) and r['topk_shape']==[n,8]
            assert hashlib.sha256(ids.tobytes()).hexdigest()==r['topk_uint8_sha256']
            assert hashlib.sha256((B/'observer.py').read_bytes()).hexdigest()==r['observer_sha256']
            flat=ids.reshape(-1);assert np.bincount(flat,minlength=128).tolist()==r['counts']
            padded=r['num_tokens_post_padded'];bm=r['config']['BLOCK_SIZE_M'];blocks=np.array(r['expert_block_ids'])
            assert padded%bm==0 and len(blocks)==padded//bm
            if r['sorted_token_ids'] is None:
                path='naive';assert blocks.tolist()==flat.tolist();assert padded==len(flat)*bm
            else:
                path='aligned';values=np.array(r['sorted_token_ids']);assert len(values)==padded<=r['sorted_buffer_allocated_elements']
                assert bool(np.all(values>=0));valid=values<len(flat)
                assert np.array_equal(np.sort(values[valid]),np.arange(len(flat)))
                assert np.array_equal(flat[values[valid]],np.repeat(blocks,bm)[valid])
                active_verified+=int(valid.sum())
            key=f'{path}-tokens{n}-block{bm}'
            s=summaries.setdefault(key,dict(path=path,input_tokens=n,block_size_m=bm,records=0,
                  returned_padded_min=padded,returned_padded_max=padded,returned_padded_sum=0,
                  logical_assignments_sum=0,allocated_sorted_min=None,allocated_sorted_max=None))
            s['records']+=1;s['returned_padded_sum']+=padded;s['logical_assignments_sum']+=len(flat)
            s['returned_padded_min']=min(s['returned_padded_min'],padded);s['returned_padded_max']=max(s['returned_padded_max'],padded)
            if r['sorted_buffer_allocated_elements'] is not None:
                alloc=r['sorted_buffer_allocated_elements']
                s['allocated_sorted_min']=alloc if s['allocated_sorted_min'] is None else min(s['allocated_sorted_min'],alloc)
                s['allocated_sorted_max']=alloc if s['allocated_sorted_max'] is None else max(s['allocated_sorted_max'],alloc)
            offsets[case][layer]=end;record_count+=1
assert all(v==[7280]*48 for v in offsets.values());assert all(n==49*48 for n in calls.values())
assert record_count==9408
j=dict(records=record_count,records_per_case=dict(calls),groups=list(summaries.values()),
       aligned_real_assignments_verified_once=active_verified,quality_output_pairs_exact=4,native_route_arrays_exact=4,
       scope='Read actual returned tensors; padded count and allocated buffer length are not executed FLOP or network measurements.',
       layer_mapping='Sequential 48-layer call order, checked against each native per-layer route slice SHA; observer did not emit a layer ID.',
       resources=dict(wall_s=sup['wall_s']),observer_changes='Calls original, synchronously copies results for recording, returns original tuple unchanged.')
(O/'analysis.json').write_text(json.dumps(j,indent=2)+'\n');print(json.dumps(j))
