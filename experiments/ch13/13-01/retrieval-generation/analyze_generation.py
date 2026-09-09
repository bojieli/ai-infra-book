"""Validate real request/KV event joins and report observed pipeline intervals."""
import argparse
from collections import defaultdict
import json
from pathlib import Path
import statistics

p=argparse.ArgumentParser();p.add_argument('--run',type=Path,required=True)
p.add_argument('--prepared',type=Path,required=True);a=p.parse_args()
supervisor=json.loads((a.run/'supervisor.json').read_text())
assert supervisor['exit_code']==0 and supervisor['reason'] is None and not supervisor['leftovers']
d=a.run/'data';prepared=json.loads(a.prepared.read_text())
refs={r['id']:r for r in prepared['requests']}
rows=json.loads((d/'records.json').read_text())
assert len(rows)==len(refs)==288 and len({r['id'] for r in rows})==288
assert rows==[json.loads(l) for l in (d/'requests.jsonl').read_text().splitlines()]
assert json.loads((d/'completion.json').read_text())['count']==288
assert json.loads((d/'retriever-exit.json').read_text())['exit_code']==0
blocks=[json.loads(l) for l in (d/'blocks.jsonl').read_text().splitlines()]
snap=json.loads((d/'kv-snapshots.json').read_text())
assert len(snap['before'])==len(snap['after'])==1
before=snap['before'][0];after=snap['after'][0]
assert before['kv_tensors']==after['kv_tensors']
assert before['unique_kv_storage_bytes']==after['unique_kv_storage_bytes']
assert all(t['dtype']=='torch.bfloat16' for t in before['kv_tensors'])
total_blocks=blocks[0]['total_blocks'];block_size=blocks[0]['block_size']
assert all(b['total_blocks']==total_blocks and b['block_size']==block_size for b in blocks)
storage=before['unique_kv_storage_bytes'];assert storage%total_blocks==0
bytes_per_pool_block=storage//total_blocks
events=defaultdict(list);scheduled=defaultdict(int);internal={}
for b in blocks:
    for r in b['requests']:
        rid=r['id']
        if rid not in internal:
            matches=[x for x in refs if rid.startswith(x+'-') or rid==x]
            assert len(matches)==1;internal[rid]=matches[0]
        events[internal[rid]].append((b,r))
    for rid,n in b.get('scheduled_tokens',{}).items():
        assert rid in internal;scheduled[internal[rid]]+=n
assert len(internal)==288 and len(set(internal.values()))==288
reports=[]
for row in rows:
    rid=row['id'];ref=refs[rid];retr=row['retrieval'];start=row['start_s'];end=row['end_s']
    assert retr['prompt_token_ids']==ref['prompt_token_ids']
    assert retr['retrieved_doc_ids']==ref['retrieved_doc_ids']
    assert start<=retr['start_monotonic']<=retr['end_monotonic']<=row['generation_start_s']<=end
    assert not row['metrics']['is_corrupted']
    assert len(row['output_ids'])==row['metrics']['num_generation_tokens']
    assert scheduled[rid]==ref['input_tokens']+len(row['output_ids'])-1
    relevant=events[rid];assert relevant
    for event,request in relevant:
        assert start<=event['time_s']<=end
        assert len(request['blocks'])==1
        ids=[b['id'] for b in request['blocks'][0]]
        assert len(ids)==len(set(ids)) and all(b['refs']==1 for b in request['blocks'][0])
    peak=max(len(r['blocks'][0]) for _,r in relevant)
    first=next(t for t,n in row['events'] if n>0)
    m=row['metrics'];assert start<=m['queued_ts']<=m['scheduled_ts']<=m['first_token_ts']<=m['last_token_ts']<=end
    reports.append(dict(id=rid,config_id=row['config_id'],split=row['split'],input_tokens=ref['input_tokens'],
        output_tokens=len(row['output_ids']),end_to_end_s=end-start,
        cpu_retrieval_envelope_s=row['generation_start_s']-start,generation_envelope_s=end-row['generation_start_s'],
        first_delivery_s=first-start,engine_scheduled_to_first_token_s=m['first_token_ts']-m['scheduled_ts'],
        pure_prefill_kernel_s=None,actual_scheduled_tokens=scheduled[rid],peak_request_pool_blocks=peak,
        assigned_kv_storage_bytes=peak*bytes_per_pool_block))
groups=[]
for cfg in prepared['configs']:
    # Config identifiers are supplied by the frozen request plan.
    cid=cfg.get('id',cfg.get('config_id'))
    if cid is None:cid=prepared['configs'].index(cfg)
    for split in ['calibration','evaluation']:
        group=[r for r in reports if r['config_id']==cid and r['split']==split];assert group
        groups.append(dict(config_id=cid,split=split,count=len(group),
            median_e2e_s=statistics.median(r['end_to_end_s'] for r in group),
            median_input_tokens=statistics.median(r['input_tokens'] for r in group),
            max_assigned_kv_storage_bytes=max(r['assigned_kv_storage_bytes'] for r in group)))
result=dict(records=reports,groups=groups,pool_blocks=total_blocks,block_size=block_size,
            reserved_pool_storage_bytes=storage,bytes_per_pool_block=bytes_per_pool_block,
            scope='Real sequential CPU-to-GPU pipeline; assigned block backing bytes are not measured KV traffic or global peak memory; observer overhead included')
(d/'pipeline-analysis.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(dict(requests=len(reports),pool_blocks=total_blocks,reserved_bytes=storage,groups=len(groups))))
