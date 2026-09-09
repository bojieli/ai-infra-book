"""Read raw records independently and verify every plotted field and binding."""
from pathlib import Path
import json,hashlib
P=Path(__file__).resolve().parents[2]
H=Path(__file__).resolve().parent
D=P/'research/chat-agent-figure/figure'
data=json.loads((D/'data.json').read_text());checks=[]
def check(name,condition):
    assert condition,name
    checks.append(name)
raw=[json.loads(x) for x in (P/'sources/agent-traces/thinking-on/rounds.jsonl').read_text().splitlines()]
check('four aligned agent rows',len(raw)==len(data['agent'])==4)
for x,y in zip(raw,data['agent']):
    for out,source in [('model_start','model_start_s'),('model_end','model_end_s'),('tool_start','tool_start_s'),('tool_end','tool_end_s'),('cached_tokens','cached_tokens')]:
        check(str(x['turn'])+out,x[source]==y[out])
    ids=x['output_token_ids'];matches=[i+1 for i,v in enumerate(ids) if v==x['reasoning_end_token_id']]
    boundary=matches[0] if matches else None
    check('boundary'+str(x['turn']),boundary==y['reasoning_boundary_count'])
    events=[e['t_s'] for e in x['output_events'] if boundary is not None and e['token_count']>=boundary]
    check('event'+str(x['turn']),(events[0] if events else None)==y['reasoning_boundary_observed_seconds'])
    check('kv'+str(x['turn']),y['hypothetical_retained_kv_bytes']==(len(x['prompt_token_ids'])+len(ids)-1)*147456)
chat=json.loads((P/'sources/trace-resource-bridge/sources/chat/prompts.json').read_text())
check('four aligned chat rows',len(chat)==len(data['chat'])==4)
for x,y in zip(chat,data['chat']):
    check('chat'+str(x['id']),y==dict(request=x['id'],input_tokens=len(x['input_ids']),output_tokens=len(x['response']['output_ids']),cached_tokens=x['response']['meta_info']['cached_tokens']))
manifest=json.loads((D/'manifest.json').read_text())
expected={str((D/name).relative_to(P)) for name in ('figure.png','figure.svg','figure.pdf','data.json')}
check('all four distinct artifacts',{r['file'] for r in manifest['artifacts']}==expected and len(manifest['artifacts'])==4)
check('distinct inputs',len({r['file'] for r in manifest['inputs']})==len(manifest['inputs']))
check('chat inputs bound',any('sources/chat/prompts.json' in r['file'] for r in manifest['inputs']))
check('agent inputs bound',any('thinking-on/rounds.jsonl' in r['file'] for r in manifest['inputs']))
for row in manifest['inputs']+manifest['artifacts']:
    check('hash:'+row['file'],hashlib.sha256((P/row['file']).read_bytes()).hexdigest()==row['sha256'])
(H/'verification.json').write_text(json.dumps(dict(checks=len(checks),names=checks),indent=2)+'\n')
print(len(checks),'checks passed')
