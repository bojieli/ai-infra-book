"""Run a bounded, real model/tool repair loop and preserve every round.

python run.py --model /local/Qwen3-8B/snapshot --output results
No production requests, external APIs, or adjacent experiment files are used.
"""
import argparse
import asyncio
import ast
from dataclasses import asdict
import hashlib
import json
import os
from pathlib import Path
import resource
import subprocess
import sys
import time

INITIAL='''def merge_intervals(intervals):
    intervals.sort()
    result = []
    for start, end in intervals:
        if result and start < result[-1][1]:
            result[-1][1] = end
        else:
            result.append([start, end])
    return result
'''
SPEC='''Implement merge_intervals(intervals). Input: list of [start,end] integer pairs, start <= end.
Return new sorted pairs merging overlaps AND touching endpoints. Nested intervals must not shorten a merged end.
Do not mutate the input, including its nested lists. Empty input returns [].
'''
CHECKER='''import copy, json, runpy
f = runpy.run_path('intervals.py')['merge_intervals']
cases = [([], []), ([[3,5],[1,2]], [[1,2],[3,5]]),
         ([[1,10],[2,3]], [[1,10]]), ([[1,2],[2,4]], [[1,4]]),
         ([[5,7],[1,3],[2,6]], [[1,7]]), ([[-4,-1],[-2,0],[3,3]], [[-4,0],[3,3]])]
results=[]
for original, expected in cases:
    data=copy.deepcopy(original)
    try:
        actual=f(data)
        results.append(dict(input=original, expected=expected,actual=actual,
                            unchanged=data==original,passed=actual==expected and data==original))
    except Exception as e: results.append(dict(input=original,passed=False,error=repr(e)))
print(json.dumps(dict(passed=all(r['passed'] for r in results),cases=results)))
'''


def validate_code(code):
    tree=ast.parse(code)
    forbidden=(ast.Import,ast.ImportFrom,ast.Global,ast.Nonlocal,ast.ClassDef,ast.With,ast.AsyncWith)
    calls={'sorted','len','min','max','range','list','tuple','enumerate','zip','merge_intervals'}
    attrs={'append','extend','sort','copy'}
    for node in ast.walk(tree):
        if isinstance(node,forbidden):raise ValueError('Only a self-contained function is allowed')
        if isinstance(node,ast.Name) and node.id.startswith('__'):raise ValueError('Dunder names prohibited')
        if isinstance(node,ast.Attribute) and node.attr not in attrs:raise ValueError('Unsupported attribute')
        if isinstance(node,ast.Call) and not ((isinstance(node.func,ast.Name) and node.func.id in calls) or
                    (isinstance(node.func,ast.Attribute) and node.func.attr in attrs)):
            raise ValueError('Unsupported call')


def limits():
    resource.setrlimit(resource.RLIMIT_CPU,(2,2))
    resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,512*1024**2))


def execute(action,work):
    tool=action.get('tool')
    if tool=='read_file':
        name=action.get('path')
        if name not in ['intervals.py','test_intervals.py','SPEC.txt']:raise ValueError('Unknown fixture file')
        return {'content':(work/name).read_text()}
    if tool=='write_file':
        if action.get('path')!='intervals.py':raise ValueError('Only intervals.py is editable')
        code=action['content'];validate_code(code);(work/'intervals.py').write_text(code)
        return {'written_bytes':len(code.encode()),'sha256':hashlib.sha256(code.encode()).hexdigest()}
    if tool=='run_tests':
        result=subprocess.run([sys.executable,'-B','test_intervals.py'],cwd=work,capture_output=True,
                              text=True,timeout=4,preexec_fn=limits)
        return {'returncode':result.returncode,'stdout':result.stdout,'stderr':result.stderr}
    if tool=='finish':return {'answer':action.get('answer','')}
    raise ValueError('Unknown tool')


async def main(args):
    os.environ['VLLM_USE_FLASHINFER_SAMPLER']='0'
    from transformers import AutoTokenizer
    import torch,vllm
    from vllm import AsyncEngineArgs,AsyncLLMEngine,SamplingParams
    root=args.output
    if root.exists():raise RuntimeError('Use a new output directory')
    work=root/'workspace';work.mkdir(parents=True)
    for name,content in [('intervals.py',INITIAL),('test_intervals.py',CHECKER),('SPEC.txt',SPEC)]:
        (work/name).write_text(content)
    tokenizer=AutoTokenizer.from_pretrained(args.model,local_files_only=True)
    config=dict(model=args.model,dtype='bfloat16',max_model_len=8192,max_num_seqs=1,
                max_num_batched_tokens=512,enable_chunked_prefill=True,enable_prefix_caching=True,
                enforce_eager=True,gpu_memory_utilization=.30,kv_cache_memory_bytes=6*1024**3,seed=304,async_scheduling=False)
    (root/'environment.json').write_text(json.dumps(dict(config=config,torch=torch.__version__,vllm=vllm.__version__,
        source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        thinking=False,fixture_origin='authored controlled repair task; model chooses actual tool actions',
        VLLM_USE_FLASHINFER_SAMPLER='0'),indent=2)+'\n')
    engine=AsyncLLMEngine.from_engine_args(AsyncEngineArgs(**config))
    system='''You are a code repair agent in a small workspace. Fix intervals.py according to SPEC.txt.
Inspect files before editing, then run tests. Finish only after tests pass.
Respond with exactly one JSON object each turn, no markdown. Tools:
{"tool":"read_file","path":"intervals.py"} (also SPEC.txt or test_intervals.py)
{"tool":"write_file","path":"intervals.py","content":"complete Python file"}
{"tool":"run_tests"}
{"tool":"finish","answer":"short summary"}
Use no imports or external libraries in the repaired file. Tools run on the CPU; model inference runs on GPU.
'''
    messages=[dict(role='system',content=system),dict(role='user',content=SPEC+'\nInspect the implementation, fix it, and validate it.')]
    baseline=execute({'tool':'run_tests'},work)
    (root/'baseline.json').write_text(json.dumps(baseline,indent=2)+'\n')
    origin=time.monotonic();completed=False
    try:
        with (root/'rounds.jsonl').open('w',buffering=1) as log:
            for turn in range(12):
                tokens=tokenizer.apply_chat_template(messages,tokenize=True,return_dict=False,add_generation_prompt=True,enable_thinking=False)
                assert isinstance(tokens,list) and all(isinstance(t,int) for t in tokens)
                start=time.monotonic();events=[];final=None
                async for out in engine.generate({'prompt_token_ids':tokens},
                        SamplingParams(temperature=0,max_tokens=1200),f'agent-{turn}'):
                    events.append(dict(t_s=time.monotonic()-origin,token_count=len(out.outputs[0].token_ids)))
                    final=out
                end=time.monotonic();text=final.outputs[0].text
                tool_start=time.monotonic();cpu_start=time.process_time()
                try:
                    action=json.loads(text);reply=execute(action,work)
                except Exception as exc:
                    action={'tool':'invalid'};reply={'error':type(exc).__name__+': '+str(exc)}
                tool_end=time.monotonic()
                row=dict(turn=turn,messages=messages,prompt_token_ids=tokens,output_token_ids=list(final.outputs[0].token_ids),
                    output_text=text,finish_reason=final.outputs[0].finish_reason,cached_tokens=final.num_cached_tokens,
                    engine_metrics=asdict(final.metrics) if final.metrics else None,
                    model_start_s=start-origin,model_end_s=end-origin,output_events=events,
                    tool_start_s=tool_start-origin,tool_end_s=tool_end-origin,tool_parent_cpu_s=time.process_time()-cpu_start,
                    action=action,tool_result=reply,
                    file_sha256=hashlib.sha256((work/'intervals.py').read_bytes()).hexdigest())
                log.write(json.dumps(row)+'\n')
                messages=messages+[dict(role='assistant',content=text),dict(role='user',content='Tool result: '+json.dumps(reply))]
                if action.get('tool')=='finish':completed=True;break
        final_check=execute({'tool':'run_tests'},work)
        (root/'final.json').write_text(json.dumps(dict(agent_finished=completed,validation=final_check,
            elapsed_s=time.monotonic()-origin,final_code=(work/'intervals.py').read_text()),indent=2)+'\n')
    finally:engine.shutdown()
    print(json.dumps(dict(finished=completed,rounds=turn+1,output=str(root))))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--model',required=True);p.add_argument('--output',type=Path,required=True)
    asyncio.run(main(p.parse_args()))
