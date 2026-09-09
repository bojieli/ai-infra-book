import json,pathlib
p=pathlib.Path(__file__).resolve().parents[1]
read=lambda f:[json.loads(x) for x in f.read_text().splitlines()]
e=read(p/'raw/smoke-dflash-7/events.jsonl')
ref=read(p.parent/'raw/dflash-7/events.jsonl')
a=[x for x in e if x['kind']=='result' and x['phase']=='observed']; b=[x for x in ref if x['kind']=='result' and x['phase']=='measured' and x['task_id']=='short_lookup']
assert len(a)==1 and b
assert all(a[0]['token_ids']==x['token_ids'] and a[0]['text']==x['text'] and a[0]['finish_reason']==x['finish_reason'] for x in b)
assert any(x['kind']=='success' for x in e)
t=json.loads((p/'raw/smoke-dflash-7/trace.json').read_text())
from collections import Counter
c=Counter(x.get('cat','') for x in t['traceEvents'])
assert c['kernel']>0,c
result={'pass':True,'token_ids':a[0]['token_ids'],'text':a[0]['text'],'reference_matches':len(b),'trace_categories':dict(c)}
(p/'smoke-check.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
