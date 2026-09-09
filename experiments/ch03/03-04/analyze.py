"""Summarize observed model/tool rounds, without simulating KV residency."""
import hashlib
import json
from pathlib import Path

root=Path(__file__).parent/'results'
rows=[json.loads(x) for x in (root/'rounds.jsonl').read_text().splitlines()]
env=json.loads((root/'environment.json').read_text())
assert env['source_sha256']==hashlib.sha256((root.parent/'run.py').read_bytes()).hexdigest()
summary=[]
for i,r in enumerate(rows):
    assert r['turn']==i
    assert r['model_start_s']<=r['model_end_s']<=r['tool_start_s']<=r['tool_end_s']
    if i:
        assert r['model_start_s']>=rows[i-1]['tool_end_s']
        previous=rows[i-1]
        expected=previous['messages']+[
            dict(role='assistant',content=previous['output_text']),
            dict(role='user',content='Tool result: '+json.dumps(previous['tool_result']))]
        assert r['messages']==expected
    n=len(r['prompt_token_ids']);cached=r['cached_tokens']
    assert isinstance(cached,int) and 0<=cached<=n
    ev=r['output_events'];assert ev[-1]['token_count']==len(r['output_token_ids'])
    assert all(a['token_count']<=b['token_count'] and a['t_s']<=b['t_s'] for a,b in zip(ev,ev[1:]))
    summary.append(dict(turn=i,tool=r['action']['tool'],prompt_tokens=n,cached_tokens=cached,
        uncached_prompt_tokens=n-cached,output_tokens=len(r['output_token_ids']),
        model_s=r['model_end_s']-r['model_start_s'],tool_s=r['tool_end_s']-r['tool_start_s'],
        tool_parent_cpu_s=r['tool_parent_cpu_s']))
final=json.loads((root/'final.json').read_text())
baseline=json.loads(json.loads((root/'baseline.json').read_text())['stdout'])
validation=json.loads(final['validation']['stdout'])
assert not baseline['passed']
assert final['agent_finished']==(rows[-1]['action']['tool']=='finish')
if not final['agent_finished']:assert len(rows)==12
result=dict(rounds=summary,total_model_s=sum(r['model_s'] for r in summary),
            total_tool_s=sum(r['tool_s'] for r in summary),
            sum_prompt_tokens=sum(r['prompt_tokens'] for r in summary),
            sum_cached_tokens=sum(r['cached_tokens'] for r in summary),
            sum_output_tokens=sum(r['output_tokens'] for r in summary),
            agent_finished=final['agent_finished'],visible_tests_passed=validation['passed'],
            termination='agent_finish' if final['agent_finished'] else 'round_budget_exhausted',
            thinking='disabled; no separately measured reasoning output',
            limitation='Serial controlled task. No physical KV lifetime or GPU-active-time inference from wall duration.')
(root/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k!='rounds'},indent=2))
