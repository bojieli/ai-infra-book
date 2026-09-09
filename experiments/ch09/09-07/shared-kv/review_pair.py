"""Independent raw-data checks and capacity comparison; no inference rerun."""
import hashlib
import json
from pathlib import Path
import statistics
import subprocess
import tempfile

ROOT=Path(__file__).resolve().parent
checks=0
def check(value):
    global checks
    assert value
    checks+=1

def metric(path,name):
    rows=[l for l in path.read_text().splitlines() if l.startswith(name+' ')]
    check(len(rows)<=1)
    # OTel exports some counters only after the first event. Preserve absence.
    return float(rows[0].split()[1]) if rows else None

comparison=[]
for name,pool in [('formal-002',4),('capacity008-001',8)]:
    root=ROOT/'runs'/name
    with tempfile.TemporaryDirectory() as tmp:
        out=Path(tmp)/'analysis.json'
        subprocess.run(['python3','-B',str(ROOT/'analyze_pair.py'),str(root),'--out',str(out)],check=True)
        check(out.read_bytes()==(root/'analysis.json').read_bytes())
    for f,digest in json.loads((root/'executed-hashes.json').read_text()).items():
        check(hashlib.sha256((root/'executed-source'/f).read_bytes()).hexdigest()==digest)
    data=json.loads((root/'analysis.json').read_text());rows=data['rows']
    raw=[json.loads(x) for x in (root/'requests.jsonl').read_text().splitlines()]
    prepared=json.loads((root/'prepared.json').read_text());cases={x['id']:x for x in prepared['cases']}
    for r in raw:
        check(r['text'].strip()==cases[r['case_id']]['expected'] and r['finish_reason']=='stop')
        check(r['start_s']<=r['events'][0][0]<=r['events'][-1][0]<=r['end_s'])
    for row in rows:
        check(row['token_ids_equal_reference'])
        if row['path']=='baseline':
            check(row['scheduled_tokens']==row['input_tokens']+row['output_tokens']-1)
        if row['path'] in ['producer','miss']:
            check(row['lookup_matched_tokens']==[0])
        if row['path']=='resident':
            check(row['operations']['retrieve']['submissions']==0)
            check(row['scheduled_tokens']<=16+row['output_tokens']-1)
        if row['operations']['retrieve']['submissions']:
            check(row['operations']['retrieve']['all_reported_completions_successful'])
    guard=json.loads((ROOT/'runs'/(name+'-guard')/'supervisor.json').read_text())
    check(guard['exit_code']==0 and guard['reason'] is None and not guard['leftovers'])
    resources=[json.loads(l) for l in (ROOT/'runs'/(name+'-guard')/'resources.jsonl').read_text().splitlines()]
    candidates=[x for x in rows if x['path']=='retrieve']
    trajectory=[]
    for r in raw:
        if r['path']=='baseline':continue
        path=root/'daemon-metrics'/(r['id']+'.txt')
        trajectory.append(dict(id=r['id'],path=r['path'],
            evicted_chunks=metric(path,'lmcache_mp_l1_evicted_chunks_total'),
            l1_memory_usage_bytes=metric(path,'lmcache_mp_l1_memory_usage_bytes')))
    observed=[x['evicted_chunks'] for x in trajectory if x['evicted_chunks'] is not None]
    check(all(a<=b for a,b in zip(observed,observed[1:])))
    comparison.append(dict(run=name,pool_gib=pool,records=len(raw),quality_pass=data['quality_pass'],
        full_prefix_hits=sum(max(r['lookup_matched_tokens'])==r['input_tokens']//256*256 for r in candidates),
        zero_prefix_hits=sum(max(r['lookup_matched_tokens'])==0 for r in candidates),
        candidates=[dict(case_id=r['case_id'],aligned_prefix_tokens=r['input_tokens']//256*256,
                         matched_tokens=max(r['lookup_matched_tokens']),ttft_s=r['observed_ttft_s']) for r in candidates],
        final_evicted_chunks=trajectory[-1]['evicted_chunks'],metrics_trajectory=trajectory,
        fetch_ttft_median_ms={str(size):statistics.median(r['observed_ttft_s'] for r in candidates if (r['input_tokens']<4096)==(size==2048))*1000 for size in [2048,8192]},
        sampled_own_gpu_mib_peak=max(r['gpu_mib'] for r in resources),
        sampled_rss_sum_bytes_peak=max(r['rss_bytes'] for r in resources),
        sampled_system_available_bytes_min=min(r['mem_available_bytes'] for r in resources)))
check((ROOT/'runs/formal-002/prepared.json').read_bytes()==(ROOT/'runs/capacity008-001/prepared.json').read_bytes())
a=[r for r in map(json.loads,(ROOT/'runs/formal-002/requests.jsonl').read_text().splitlines()) if r['path']=='baseline']
b=[r for r in map(json.loads,(ROOT/'runs/capacity008-001/requests.jsonl').read_text().splitlines()) if r['path']=='baseline']
check(a==b)
out=dict(checks=checks,comparison=comparison,reused_baseline_records=24,
         distinct_formal_records=120,scope='24 shared reference records + 48 actual requests per CPU-pool configuration; phases not simultaneous')
(ROOT/'capacity-comparison.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({'checks':checks,'full_prefix_hits':[x['full_prefix_hits'] for x in comparison]}))
