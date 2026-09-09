"""Analyze sealed real Agent records without rerunning model or calculations."""
import ast,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
evidence=ROOT/'evidence'
def read(f):return json.loads((evidence/f).read_text())
summary=read('summary.json');environment=read('environment.json')
rows=[];previous=None
for i in range(6):
    r=read(f'round-{i}.json')
    assert r['turn']==i and len(r['messages'])==2+2*i
    if previous:
        assert r['messages'][:-2]==previous['messages']
        assert r['messages'][-2]['content']==previous['output_text']
        assert r['messages'][-1]['content'].startswith('Tool result:')
    assert json.loads(r['output_text'])==r['action']
    assert hashlib.sha256(r['action']['code'].encode()).hexdigest()==r['candidate_sha256']
    assert r['tool_result']['status']=='passed'
    assert ast.dump(ast.parse(r['action']['code']))==ast.dump(ast.parse((evidence/'schedule.py').read_text()))
    rows.append(dict(turn=i+1,prompt_tokens=len(r['prompt_token_ids']),output_tokens=len(r['output_token_ids']),
        code_utf8_bytes=len(r['action']['code'].encode()),model_generation_wall_s=r['generation_s'],
        tool_subprocess_wall_s=r['evaluation_subprocess_wall_s'],
        tool_gpu_event_window_s=r['tool_result']['gpu_event_window_s'],
        candidate_sha256=r['candidate_sha256']))
    previous=r
for f,h in environment['source_hashes'].items():assert hashlib.sha256((evidence/f).read_bytes()).hexdigest()==h
generation=sum(r['model_generation_wall_s'] for r in rows)
tools=sum(r['tool_subprocess_wall_s'] for r in rows)
assert abs(generation-summary['inference_s'])<1e-6
assert abs(sum(r['tool_gpu_event_window_s'] for r in rows)-summary['evaluator_gpu_event_s'])<1e-6
result=dict(status='passed',rows=rows,loop_wall_s=summary['elapsed_s'],generation_wall_s=generation,
    tool_wall_s=tools,other_loop_wall_s=summary['elapsed_s']-generation-tools,
    startup_wall_s=environment['engine_startup_s'],
    resources=[
        dict(location='RTX host CPU/RAM',activity='Build chat messages and token IDs; parse model JSON; validate candidate AST; launch evaluator and collect result.',evidence='run_agent.py; messages/prompt_token_ids/action fields'),
        dict(location='RTX GPU / device memory',activity='Qwen model inference, then evaluator tensor copies and kernels. Model remains resident during evaluation; generation and evaluation are sequential.',evidence='engine config and run_agent.py awaited generation; evaluate_agent.py cuda() and CUDA Graph'),
        dict(location='RTX host filesystem',activity='Read model cache and captured tensor files; write candidates, evaluator logs/results, and complete round records.',evidence='engine config model path; run_agent.py candidate write/subprocess; evaluate_agent.py torch.load'),
        dict(location='Local Mac',activity='Receives archived artifacts for offline analysis; outside recorded Agent loop timing.',evidence='This standalone evidence copy; do not infer transfer cost from loop events')],
    boundaries=[
        dict(source='CPU controller',destination='GPU inference worker',payload='Prompt token IDs; model outputs return to controller',wait='Controller awaits generation completion before invoking evaluator',certainty='API/source and actual token records; transport bytes and latency not measured'),
        dict(source='CPU controller',destination='Host files and evaluator subprocess',payload='Candidate source file, evaluator command/path, result JSON and log',wait='Synchronous subprocess completion before next prompt',certainty='Source and actual round records; UTF-8 source bytes are file payload, not filesystem traffic'),
        dict(source='Host files / CPU tensors',destination='GPU evaluator',payload='Captured BF16 activation/reference tensors loaded by torch.load, then cuda()',wait='GPU synchronization and input comparison before feedback',certainty='Executed evaluator passed; no per-copy byte/time counters in this record'),
        dict(source='GPU evaluator',destination='CPU controller',payload='Correctness, timings and score',wait='Feedback must arrive before the next model turn',certainty='Actual tool_result is present in next messages')],
    conclusion='Six serial model/tool rounds produced unchanged code. Successful validation is not optimization success. GPU event windows are nested in tool wall time and must not be added a second time.')
(ROOT/'results').mkdir(exist_ok=True)
(ROOT/'results/analysis.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k not in ['resources','boundaries','rows']},indent=2))
