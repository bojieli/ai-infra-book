"""Compare observed controlled runs; includes failures and output truncation."""
import hashlib
import json
from pathlib import Path

root=Path(__file__).parent
summary=[]
configs=[]
first_messages=[]
for folder,source in [('results','run.py'),('reasoning-results','run_reasoning.py')]:
    p=root/folder
    env=json.loads((p/'environment.json').read_text());configs.append(env['config'])
    assert env['source_sha256']==hashlib.sha256((root/source).read_bytes()).hexdigest()
    rows=[json.loads(s) for s in (p/'rounds.jsonl').read_text().splitlines()]
    first_messages.append(rows[0]['messages'])
    reasoning=0;after=0;delimiter=0;truncated=0
    for i,r in enumerate(rows):
        assert r['turn']==i
        assert r['model_start_s']<=r['model_end_s']<=r['tool_start_s']<=r['tool_end_s']
        if i:
            prev=rows[i-1]
            assert r['messages']==prev['messages']+[
                dict(role='assistant',content=prev['output_text']),
                dict(role='user',content='Tool result: '+json.dumps(prev['tool_result']))]
        ids=r['output_token_ids'];end=r.get('reasoning_end_token_id')
        if end is not None:
            if end in ids:
                pos=ids.index(end);reasoning+=pos;delimiter+=1;after+=len(ids)-pos-1
            else:
                reasoning+=len(ids)
        else:after+=len(ids)
        truncated+=r['finish_reason']=='length'
    final=json.loads((p/'final.json').read_text())
    quality=json.loads((p/'independent-checks-v2.json').read_text())
    summary.append(dict(thinking=env['thinking'],rounds=len(rows),
        total_model_s=sum(r['model_end_s']-r['model_start_s'] for r in rows),
        total_tool_s=sum(r['tool_end_s']-r['tool_start_s'] for r in rows),
        input_tokens=sum(len(r['prompt_token_ids']) for r in rows),
        cached_tokens=sum(r['cached_tokens'] for r in rows),
        generated_tokens=sum(len(r['output_token_ids']) for r in rows),
        reasoning_tokens=reasoning,reasoning_end_delimiters=delimiter,
        post_reasoning_tokens=after,truncated_rounds=truncated,
        agent_finished=final['agent_finished'],
        visible_passed=json.loads(final['validation']['stdout'])['passed'],
        independent_passed=quality['passed'],independent_cases=quality['cases'],
        value_and_input_passed=quality['value_and_input_passed'],
        additional_alias_failures=quality['additional_alias_failures']))
    assert reasoning+delimiter+after==summary[-1]['generated_tokens']
assert configs[0]==configs[1]
assert first_messages[0]==first_messages[1]
result=dict(runs=summary,controls='Same model, engine configuration, task messages, tool definitions, greedy sampling, 1200-token per-round and 12-round limits; thinking and associated output parsing differ.',
    caveat='One task, one run per mode; cache contents and round sequence follow model decisions. Not an estimate of general success probability or isolated kernel speed.')
(root/'reasoning-comparison.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
