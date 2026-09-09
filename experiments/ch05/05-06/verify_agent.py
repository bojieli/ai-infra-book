"""Offline audit of actual prompts/actions, duplicate code and recorded costs."""
import ast
import hashlib
import json
from pathlib import Path
import statistics
ROOT=Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def verify():
    rows=[];initial=ast.dump(ast.parse((ROOT/'schedule.py').read_text()))
    for version in [1,2]:
        path=ROOT/f'results/agent-search-v{version}';summary=read(path/'summary.json');env=read(path/'environment.json')
        assert summary['protocol_sha256']==env['protocol_sha256']==sha(ROOT/'protocol.json')
        for f,h in env['source_hashes'].items():assert sha(ROOT/f)==h,(version,f)
        rounds=[read(f) for f in sorted(path.glob('round-*.json'))]
        assert len(rounds)==summary['round_count']==6
        generation=0.;events=0.;previous=[];asts=[]
        for i,r in enumerate(rounds):
            assert r['turn']==i and len(r['messages'])==2+2*i
            assert all(isinstance(t,int) for t in r['prompt_token_ids']+r['output_token_ids'])
            if i:
                assert r['messages'][:-2]==previous
                assert r['messages'][-2]['content']==rounds[i-1]['output_text']
                assert 'Tool result:' in r['messages'][-1]['content']
            previous=r['messages'];action=json.loads(r['output_text']);assert action==r['action']
            assert (path/f'candidate-{i}.py').read_text()==action['code']
            tree=ast.dump(ast.parse(action['code']));asts.append(tree);assert tree==initial
            generation+=r['generation_s'];reply=r['tool_result']
            if version==1:
                ev=read(path/f'evaluation-{i}.json')
                assert ev['status']=='passed' and ev['candidate_sha256']==sha(path/f'candidate-{i}.py')
                score=sum(statistics.median(x['samples_us']) for x in ev['rows'])
                assert abs(score-reply['score_us'])<1e-9
                assert [x['t'] for x in ev['rows']]==[1,7239]
                events+=ev['gpu_event_window_s']
            else:assert reply['status']=='failed' and 'Repeated unchanged kernel' in reply['error']
            assert abs(r['charged_s']-generation-events)<1e-6
        assert abs(summary['charged_s']-generation-events)<1e-6
        if version==1:
            winner=min(rounds,key=lambda r:(r['tool_result']['score_us'],r['turn']))
            assert summary['selected_turn']==winner['turn']
            assert summary['selected_sha256']==sha(path/f"candidate-{winner['turn']}.py")
        else:assert summary['status']=='no_valid_candidate'
        rows.append(dict(version=version,rounds=len(rounds),distinct_asts=len(set(asts)),
            changed_asts=sum(t!=initial for t in set(asts)),inference_s=generation,evaluator_gpu_event_s=events,
            charged_s=summary['charged_s'],elapsed_s=summary['elapsed_s'],engine_startup_s=env['engine_startup_s']))
    heldout=read(ROOT/'results/agent-heldout-v1.json')
    assert heldout['selection_sha256']==sha(ROOT/'results/agent-search-v1/summary.json')
    assert heldout['source_sha256']==sha(ROOT/'heldout_agent.py')
    assert len(heldout['rows'])==5 and all(r['status']=='passed' for r in heldout['rows'])
    report=dict(status='passed',runs=rows,interpretation='Both runs generated the starting AST unchanged. V1 repeats were timed, V2 duplicates rejected; no new optimized kernel.')
    (ROOT/'results/agent-audit.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
if __name__=='__main__':verify()
