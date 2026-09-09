import hashlib,json,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parent
raw=json.loads((ROOT/'results/run-v1/raw.json').read_text());assert raw['status']=='passed'
for f,h in raw['source_hashes'].items():assert hashlib.sha256((ROOT/f).read_bytes()).hexdigest()==h
assert len(raw['records'])==11
blocks={h:[] for h in range(0,8192,512)};other=[];outputs=[];ratios=[]
for r in raw['records']:
    assert len(r['steps'])==1
    active=[s for s in r['steps'][0] if s['total_scheduled_tokens']]
    assert len(active)==16
    histories=[];request_ids=set()
    for s in active:
        assert s['total_scheduled_tokens']==512
        assert len(s['per_request_scheduled_tokens'])==1
        rid=next(iter(s['per_request_scheduled_tokens']));request_ids.add(rid)
        assert rid.startswith(f"trial-{r['trial']}-") and s['per_request_scheduled_tokens'][rid]==512
        h=s['prior_scheduled_tokens'][rid];histories.append(h)
        assert s['event_ms']>0;blocks[h].append(s['event_ms'])
    assert len(request_ids)==1
    assert histories==list(range(0,8192,512))
    other.extend(s for s in r['steps'][0] if not s['total_scheduled_tokens'])
    assert r['output']['cached_tokens'] in (0,None) and len(r['output']['output_ids'])==1
    outputs.append(r['output']['output_ids']);ratios.append(active[-1]['event_ms']/active[0]['event_ms'])
assert all(o==outputs[0] for o in outputs)
summary=dict(status='passed',requests=11,prefill_blocks=176,empty_execute_calls=len(other),output_ids=outputs[0],
    blocks=[dict(history_tokens=h,new_tokens=512,samples_ms=x,median_ms=statistics.median(x),min_ms=min(x),max_ms=max(x)) for h,x in blocks.items()],
    paired_last_first_ratios=ratios,paired_ratio_median=statistics.median(ratios),
    scope='Same512 new tokens; actual sequential8192-token prefill. CUDA events around execute_model include host gaps and full model operations. Position, contents and last-chunk processing are not separately controlled; not attention-only or DRAM ratio. No concurrent requests.')
(ROOT/'results/summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
