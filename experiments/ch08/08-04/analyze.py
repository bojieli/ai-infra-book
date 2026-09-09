import hashlib
import json
from pathlib import Path
import statistics
root=Path(__file__).parent
names=['cache6','gap6','pressure1','pressure6','nocache6']
inputs=json.loads((root/'inputs/agent-prompts.json').read_text())['requests']
summary=[];outputs=[];environments={};pressure_inputs={}
for name in names:
    p=root/'results'/name
    env=json.loads((p/'environment.json').read_text())
    assert env['source_sha256']==hashlib.sha256((root/'run.py').read_bytes()).hexdigest()
    assert env['input_sha256']==hashlib.sha256((root/'inputs/agent-prompts.json').read_bytes()).hexdigest()
    rows=[json.loads(x) for x in (p/'requests.jsonl').read_text().splitlines()]
    agent=[r for r in rows if r['kind']=='agent'];pressure=[r for r in rows if r['kind']=='pressure']
    environments[name]=env
    pressure_inputs[name]=[(r['id'],r['prompt_sha256']) for r in pressure]
    assert len(agent)==len(inputs)==12
    assert len(pressure)==11*env['pressure_requests']
    for r,inp in zip(agent,inputs):
        assert r['prompt_sha256']==hashlib.sha256(json.dumps(inp['prompt_token_ids']).encode()).hexdigest()
        assert r['prompt_tokens']==len(inp['prompt_token_ids'])
        assert 0<=r['cached_tokens']<=r['prompt_tokens']
        assert len(r['output_ids'])==1
    if name=='nocache6':assert sum(r['cached_tokens'] for r in agent)==0
    outputs.append([r['output_ids'] for r in agent])
    summary.append(dict(name=name,input_tokens=sum(r['prompt_tokens'] for r in agent),
        cached_tokens=sum(r['cached_tokens'] for r in agent),
        agent_total_s=sum(r['end_s']-r['start_s'] for r in agent),
        median_ttft_ms=statistics.median(r['delivery_ttft_s'] for r in agent)*1000,
        pressure_total_s=sum(r['end_s']-r['start_s'] for r in pressure),
        replay_elapsed_s=rows[-1]['end_s']-rows[0]['start_s'],
        cached_by_round=[r['cached_tokens'] for r in agent],
        ttft_ms_by_round=[r['delivery_ttft_s']*1000 for r in agent]))
assert all(v==outputs[0] for v in outputs)
assert pressure_inputs['pressure1']==pressure_inputs['pressure6']
for name in names:
    expected=dict(environments['cache6']['config'])
    if name=='pressure1':expected['kv_cache_memory_bytes']=1024**3
    if name=='nocache6':expected['enable_prefix_caching']=False
    assert environments[name]['config']==expected
    assert environments[name]['gap_s']==(.2 if name=='gap6' else 0)
    assert environments[name]['pressure_requests']==(3 if name.startswith('pressure') else 0)
(root/'results/summary.json').write_text(json.dumps(dict(configurations=summary,
    output_tokens_match=True,scope='Agent-request time excludes intervening pressure work and explicit gaps; total replay includes both. One output token per frozen prompt.'),indent=2)+'\n')
for r in summary:print(json.dumps({k:v for k,v in r.items() if not k.endswith('by_round')}))
