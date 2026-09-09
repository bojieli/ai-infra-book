import hashlib,json
from pathlib import Path
root=Path(__file__).parent
summaries=[];alloutputs={};environments={}
for name in ['small','large','cancel']:
 r=root/'results'/name
 env=json.loads((r/'environment.json').read_text());environments[name]=env
 for file,digest in env['hashes'].items():assert hashlib.sha256((root/file).read_bytes()).hexdigest()==digest
 assert hashlib.sha256((r/'inputs.json').read_bytes()).hexdigest()==env['input_sha256']
 blocks=[json.loads(x) for x in (r/'blocks.jsonl').read_text().splitlines()]
 requests=[json.loads(x) for x in (r/'requests.jsonl').read_text().splitlines()]
 assert len(requests)==4
 initial=blocks[0];reserved=initial['total_blocks']-initial['free_blocks'];assert reserved==1
 preemptions=[];previous={};total_scheduled=0;timeline=[]
 for s in blocks:
  owned={};counts={}
  for q in s['requests']:
   assert len(q['blocks'])==1
   ids=[b['id'] for b in q['blocks'][0]]
   assert len(ids)==len(set(ids))
   for b in q['blocks'][0]:
    assert b['refs']==1 and b['id'] not in owned
    owned[b['id']]=q['id']
   counts[q['id']]=len(ids)
   if q['status']=='PREEMPTED' and previous.get(q['id'])!='PREEMPTED':
    assert q['computed']==0 and not ids
    preemptions.append(dict(time_s=s['time_s'],id=q['id'],preserved_output_tokens=q['output_tokens']))
  previous={q['id']:q['status'] for q in s['requests']}
  assert s['free_blocks']+len(owned)+reserved==s['total_blocks']
  if s['event']=='schedule':total_scheduled+=sum(s['scheduled_tokens'].values())
  timeline.append(dict(time_s=s['time_s'],event=s['event'],allocated_blocks=len(owned),free_blocks=s['free_blocks'],request_blocks=counts))
 assert blocks[-1]['free_blocks']==initial['free_blocks'] and blocks[-1]['requests']==[]
 actions=[json.loads(x) for x in (r/'actions.jsonl').read_text().splitlines()]
 abort_events=[s for s in blocks if s['event']=='finish_after' and s['finish_ids']]
 if name=='cancel':
  assert len(actions)==1 and len(abort_events)>=1
  assert len({rid for s in abort_events for rid in s['finish_ids']})==1
  for s in abort_events:
   for rid in s['finish_ids']:assert rid not in [q['id'] for q in s['requests']]
 else:assert not actions and not abort_events
 for q in requests:
  if name=='cancel' and q['id']=='r3':assert q['cancelled'] and 128<=len(q['output_ids'])<512
  else:assert len(q['output_ids'])==512 and q['finish_reason']=='length'
 alloutputs[name]={q['id']:q['output_ids'] for q in requests}
 summaries.append(dict(name=name,total_blocks=initial['total_blocks'],block_size=initial['block_size'],reserved_blocks=reserved,
   max_allocated_blocks=max(t['allocated_blocks'] for t in timeline),snapshots=len(blocks),
   preemptions=preemptions,scheduled_token_positions=total_scheduled,
   elapsed_s=max(q['end_s'] for q in requests)-min(q['start_s'] for q in requests),
   output_tokens={q['id']:len(q['output_ids']) for q in requests},actions=actions,
   abort_transitions=[s for s in blocks if s['event'] in ['finish_before','finish_after'] and s['finish_ids']],
   all_request_blocks_released=True,timeline=timeline))
expected=dict(environments['small']['config']);expected['kv_cache_memory_bytes']=2*1024**3
assert environments['large']['config']==expected
assert environments['cancel']['config']==environments['small']['config']
assert len(set(e['input_sha256'] for e in environments.values()))==1
assert summaries[0]['preemptions'] and not summaries[1]['preemptions'] and not summaries[2]['preemptions']
comparison=dict(small_large_outputs_match=alloutputs['small']==alloutputs['large'],
 cancel_survivor_outputs_match=all(alloutputs['cancel'][f'r{i}']==alloutputs['large'][f'r{i}'] for i in range(3)),
 recomputed_positions_observed=summaries[0]['scheduled_token_positions']-summaries[1]['scheduled_token_positions'])
(root/'results/summary.json').write_text(json.dumps(dict(configurations=summaries,comparison=comparison),indent=2)+'\n')
for x in summaries:print(json.dumps({k:v for k,v in x.items() if k not in ['timeline','abort_transitions']}))
print(json.dumps(comparison))
