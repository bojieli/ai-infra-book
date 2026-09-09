"""Independent coverage, installed-path and paired-output audit."""
import hashlib
import json
from pathlib import Path
import statistics
ROOT=Path(__file__).resolve().parent
path=ROOT/'results/paired-eager-v1';raw=json.loads((path/'raw.json').read_text())
assert raw['status']=='passed'
for f,h in raw['source_hashes'].items():assert hashlib.sha256((ROOT/f).read_bytes()).hexdigest()==h,f
assert raw['config']['enforce_eager'] and not raw['config']['enable_prefix_caching']
assert len(raw['installed'][0]['layer_names'])==36
for audit in raw['audits']:
    records=audit['records'][0];assert len(records)==72
    assert len({r['layer'] for r in records})==36
    assert sum(r['shape']==[7239,24576] for r in records)==36
    assert sum(r['shape']==[1,24576] for r in records)==36
    assert all(r['mode']==audit['mode'] and r['dtype']=='torch.bfloat16' for r in records)
for switch in raw['switches']:
    s=switch[0];assert not s['audit'] and s['layers']==36
    assert all(m['module']==('candidate' if s['mode']=='schedule' else 'vllm.model_executor.layers.activation') for m in s['methods'])
requests=[r for r in raw['requests'] if r['phase']=='measure'];assert len(requests)==22
log=[json.loads(line) for line in (path/'requests.jsonl').read_text().splitlines()];assert log==requests
rows=[]
for mode in ['native','schedule']:
    group=[r for r in requests if r['mode']==mode];assert sorted(r['trial'] for r in group)==list(range(11))
    for r in group:
        assert r['prompt_tokens']==7239 and r['output_tokens']==32
        counts=[e['token_count'] for e in r['events']];assert counts==list(range(1,33))
    rows.append(dict(mode=mode,median_ttft_ms=statistics.median(r['ttft_s'] for r in group)*1000,
        median_latency_ms=statistics.median(r['latency_s'] for r in group)*1000,
        median_request_output_tokens_per_s=statistics.median(32/r['latency_s'] for r in group),
        distinct_outputs=len({tuple(r['output_ids']) for r in group}),
        median_client_mean_itl_ms=statistics.median((r['events'][-1]['elapsed_s']-r['events'][0]['elapsed_s'])/31*1000 for r in group)))
pairs=[]
for trial in range(11):
    group={r['mode']:r for r in requests if r['trial']==trial};n,s=group['native'],group['schedule']
    pairs.append(dict(trial=trial,ttft_saving_ms=(n['ttft_s']-s['ttft_s'])*1000,
        latency_saving_ms=(n['latency_s']-s['latency_s'])*1000,output_equal=n['output_ids']==s['output_ids']))
summary=dict(status='passed',rows=rows,pairs=pairs,
    matched_output_pairs=sum(p['output_equal'] for p in pairs),
    positive_ttft_pairs=sum(p['ttft_saving_ms']>0 for p in pairs),
    positive_latency_pairs=sum(p['latency_saving_ms']>0 for p in pairs),
    paired_median_ttft_saving_ms=statistics.median(p['ttft_saving_ms'] for p in pairs),
    paired_median_latency_saving_ms=statistics.median(p['latency_saving_ms'] for p in pairs),
    raw_sha256=hashlib.sha256((path/'raw.json').read_bytes()).hexdigest(),
    scope='One fixed prompt, forced 32-token output, one eager engine, concurrency 1, APC disabled. Client output events need not be individual GPU decode timestamps. No general quality or saturated throughput claim.')
(ROOT/'results/summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
