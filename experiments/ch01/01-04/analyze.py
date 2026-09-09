import hashlib,json,statistics
from collections import defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parent;E=ROOT/'evidence'
def read(name):return json.loads((E/name).read_text())
env=read('environment.json');inputs=read('inputs.json')['requests']
assert env['source_sha256']==hashlib.sha256((E/'run.py').read_bytes()).hexdigest()
assert env['input_sha256']==hashlib.sha256((E/'inputs.json').read_bytes()).hexdigest()
requests=defaultdict(list);stats=defaultdict(list)
for line in (E/'requests.jsonl').read_text().splitlines():
    r=json.loads(line);requests[r['run_id']].append(r)
for line in (E/'engine-stats.jsonl').read_text().splitlines():
    r=json.loads(line);stats[r['run_id']].append(r)
batches=[]
for line in (E/'batches.jsonl').read_text().splitlines():
    b=json.loads(line)
    if b['trial']=='warm':continue
    rows=requests[b['run_id']];assert len(rows)==b['batch'];tpots=[];ttfts=[]
    for r in rows:
        index=int(r['id'].rsplit('-r',1)[1]);ids=inputs[b['kind']][index]
        assert r['input_sha256']==hashlib.sha256(json.dumps(ids).encode()).hexdigest()
        assert len(ids)==r['input_tokens']==(2048 if b['kind']=='short' else 8192)
        assert r['cached_tokens']==(0 if b['kind']=='short' else 6144)
        assert len(r['output_ids'])==256 and r['events'][-1][1]==256
        assert all(a[0]<=c[0] and a[1]<=c[1] for a,c in zip(r['events'],r['events'][1:]))
        first=next(e[0] for e in r['events'] if e[1]>0)
        tpots.append((r['events'][-1][0]-first)/255*1000);ttfts.append((first-r['start_s'])*1000)
    observations=stats[b['run_id']]
    batches.append(dict(kind=b['kind'],batch=b['batch'],trial=b['trial'],
        throughput=256*b['batch']/(b['end_s']-b['start_s']),tpot_ms=statistics.median(tpots),ttft_ms=statistics.median(ttfts),
        max_running=max(s['scheduler']['num_running_reqs'] for s in observations),
        preemptions=sum((s['iteration'] or {}).get('num_preempted_reqs',0) for s in observations)))
assert len(batches)==24
groups=[]
for kind in ['short','prefix']:
    for b in [1,4,16,64]:
        rows=[r for r in batches if r['kind']==kind and r['batch']==b];assert len(rows)==3
        assert max(r['max_running'] for r in rows)==b
        groups.append(dict(kind=kind,batch=b,**{k:statistics.median(r[k] for r in rows) for k in ['throughput','tpot_ms','ttft_ms']},preemptions=sum(r['preemptions'] for r in rows)))
counts=[]
for b in [1,64]:
    r=read(f'qwen3-8b-decode-b{b}-s8192.json');assert r['scenario']['history']==8192 and r['scenario']['batch']==b
    counts.append(dict(batch=b,weight_read_once_per_operator_bytes=r['summary']['weight_read_once_per_operator_bytes'],
        kv_attention_unique_payload_bytes=r['summary']['kv_attention_unique_payload_bytes']))
result=dict(status='passed',groups=groups,batches=batches,existing_logical_counts=counts,
    prediction='Retrospective simplified hypothesis: if only once-per-operator weight reads govern a full batch decode step, increasing batch should leave step time almost unchanged. This is not an independently preregistered RTX timing forecast.',
    missing_terms=['KV payload increases with active sequences and history','attention and other GPU work','host submission and scheduler/observer costs','prefill and cache reuse affect full-request throughput'],
    compatibility='Qwen3-8B BF16 revision matches; logical history8192 describes one step, whereas raw8192-token requests generate256 tokens and history grows. No logical byte count is a DRAM counter. The window scenario has teaching interface parameters and predicted_decode_seconds=null; it is not used as RTX timing prediction.',
    decision='Do not choose batch64 from weight reuse alone. Keep measured RTX engine as tested candidate; compare same-path batch1/4/16/64 under latency requirements. Other devices cannot be ranked from this single-device record.',
    minimum_followup='For a causal length comparison, retain the same model/backend/batch and disable APC in both2048/8192 groups; collect per-step GPU timing with lightweight or disabled scheduler observation, alongside the same client TPOT. No new SLO or device superiority is claimed.')
(ROOT/'results').mkdir(exist_ok=True);(ROOT/'results/analysis.json').write_text(json.dumps(result,indent=2)+'\n')
for r in groups:print(r)
