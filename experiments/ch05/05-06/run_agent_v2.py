"""Actual Qwen model/tool loop; candidates never receive heldout observations."""
import argparse
import ast
import asyncio
import hashlib
import json
import os
from pathlib import Path
import statistics
import subprocess
import sys
import time
from agent_guard import validate_code, ATTRS

ROOT=Path(__file__).resolve().parent
def dump(path,value):path.write_text(json.dumps(value,indent=2)+'\n')
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

async def main(a):
    if a.output.exists():raise RuntimeError('Fresh output directory required')
    a.output.mkdir(parents=True)
    protocol=json.loads((ROOT/'protocol.json').read_text())
    config=json.loads((ROOT/'engine-config.json').read_text())
    config.pop('worker_extension_cls')
    config.update(gpu_memory_utilization=.30,kv_cache_memory_bytes=6*1024**3,max_num_seqs=1,seed=506)
    os.environ['VLLM_USE_FLASHINFER_SAMPLER']='0'
    from transformers import AutoTokenizer
    from vllm import AsyncEngineArgs,AsyncLLMEngine,SamplingParams
    tokenizer=AutoTokenizer.from_pretrained(config['model'],local_files_only=True)
    budget=protocol['maximum_gpu_event_window_seconds_per_strategy']
    environment=dict(config=config,thinking=False,temperature=0,max_tokens=1400,
        budget_policy='Conservative: charge inference wall time plus evaluator GPU event window; startup and subprocess import time separately reported. Same 60 s ceiling, at most 6 candidates. Timings with model resident but no concurrent generation.',
        protocol_sha256=sha(ROOT/'protocol.json'),source_hashes={f:sha(ROOT/f) for f in ['run_agent_v2.py','evaluate_agent.py','agent_guard.py','schedule.py']})
    dump(a.output/'environment.json',environment)
    start=time.perf_counter()
    engine=AsyncLLMEngine.from_engine_args(AsyncEngineArgs(**config))
    environment['engine_startup_s']=time.perf_counter()-start
    dump(a.output/'environment.json',environment)
    system='''Optimize a BF16 SwiGLU GPU kernel on RTX PRO 6000 Blackwell SM120, 188 SM, 128 MiB L2.
Each turn submit exactly one JSON tool call, no markdown:
{"tool":"evaluate","code":"complete Python module defining run(x)","reason":"brief hypothesis"}
You must CHANGE the starting kernel and make a different concrete optimization each turn. Do not resubmit identical source. Explain which operation or launch geometry you changed. Duplicate Python ASTs are rejected without benchmarking. You must author the full candidate kernel code. Imports: import torch, import triton, import triton.language as tl.
Only imports and functions at top level. No file, network, process access, introspection, reference or validator access.
Input contiguous BF16 [T,24576]. Return fresh BF16 [T,12288] equal to silu(first half)*second half. No input mutation.
Training T=1 and T=7239, actual layer-0 Qwen3-8B inputs. Fixed vLLM native reference, atol=rtol=0.0078125, no failing elements.
Minimize sum of CUDA Graph median microseconds over both shapes. Five warmups, 11 trials, 10 calls per graph.
You receive correctness and timing after each submission. You cannot change this evaluator, tolerance or score.
There are at most six candidates within 60 seconds charged inference wall time plus evaluation event windows.
The original model trace has 36 prefill SwiGLU calls totaling 11204.399 us and 36 decode calls totaling 78.080 us.
Initial measured native graph times: 2.7008 us (T=1), 351.824 us (T=7239). Compiler expression: 0.8928, 348.832 us.
Sequential shared GPU timings are noisy. Choose reasonable code changes, shape specialization allowed.
'''
    system+='Allowed attribute names: '+', '.join(sorted(ATTRS))
    messages=[dict(role='system',content=system),dict(role='user',content='Starting kernel source:\n'+(ROOT/'schedule.py').read_text()+'\nSubmit your first candidate.')]
    charged=0.;rows=[];origin=time.perf_counter();seen={ast.dump(ast.parse((ROOT/'schedule.py').read_text()))}
    try:
        for turn in range(protocol['maximum_candidates_per_strategy']):
            remaining=budget-charged
            if remaining<=0:break
            tokens=tokenizer.apply_chat_template(messages,tokenize=True,return_dict=False,add_generation_prompt=True,enable_thinking=False)
            request=f'kernel-agent-{turn}';latest=None;events=[]
            async def generate():
                nonlocal latest
                async for output in engine.generate({'prompt_token_ids':tokens},SamplingParams(temperature=0,max_tokens=1400),request):
                    latest=output;events.append(dict(wall_s=time.perf_counter()-origin,tokens=len(output.outputs[0].token_ids)))
            start=time.perf_counter();timeout=False
            try:await asyncio.wait_for(generate(),timeout=remaining)
            except asyncio.TimeoutError:
                timeout=True;await engine.abort(request)
            model_s=time.perf_counter()-start;charged+=model_s
            text=latest.outputs[0].text if latest else ''
            row=dict(turn=turn,messages=messages,prompt_token_ids=tokens,output_text=text,
                output_token_ids=list(latest.outputs[0].token_ids) if latest else [],
                finish_reason=latest.outputs[0].finish_reason if latest else None,
                generation_s=model_s,generation_timeout=timeout,events=events)
            dump(a.output/f'round-{turn}.json',row)
            reply={};evaluation_start=time.perf_counter()
            try:
                if timeout or charged>=budget:raise RuntimeError('Inference exhausted conservative budget; candidate not evaluated')
                action=json.loads(text);row['action']=action
                if action.get('tool')!='evaluate':raise ValueError('Expected evaluate tool')
                code=action['code'];candidate=a.output/f'candidate-{turn}.py';candidate.write_text(code)
                validate_code(code)
                fingerprint=ast.dump(ast.parse(code))
                if fingerprint in seen:raise ValueError('Repeated unchanged kernel. Modify the actual code before resubmitting.')
                seen.add(fingerprint)
                result_path=a.output/f'evaluation-{turn}.json'
                with (a.output/f'evaluation-{turn}.log').open('w') as log:
                    result=subprocess.run([sys.executable,str(ROOT/'evaluate_agent.py'),'--kind','agent','--candidate',str(candidate.resolve()),'--output',str(result_path.resolve())],stdout=log,stderr=subprocess.STDOUT,timeout=protocol['candidate_process_timeout_seconds'])
                if not result_path.exists():raise RuntimeError('Evaluator failed before JSON output; inspect retained log')
                reply=json.loads(result_path.read_text());charged+=reply['gpu_event_window_s']
                if reply['status']=='passed':
                    reply['score_us']=sum(statistics.median(r['samples_us']) for r in reply['rows'])
                    row['candidate_sha256']=sha(candidate)
            except Exception as exc:reply=dict(status='failed',error=repr(exc))
            row.update(tool_result=reply,evaluation_subprocess_wall_s=time.perf_counter()-evaluation_start,charged_s=charged)
            dump(a.output/f'round-{turn}.json',row);rows.append(row)
            print(turn,reply.get('status'),reply.get('score_us'),charged,flush=True)
            feedback={k:v for k,v in reply.items() if k in ['status','error','score_us','rows','gpu_event_window_s']}
            messages=messages+[dict(role='assistant',content=text),dict(role='user',content='Tool result: '+json.dumps(feedback)+'\nRemaining conservative budget seconds: '+str(max(0,budget-charged))+'. Submit a revised candidate.')]
            if timeout:break
        passed=[r for r in rows if r['tool_result'].get('status')=='passed' and r['charged_s']<=budget]
        winner=min(passed,key=lambda r:(r['tool_result']['score_us'],r['turn'])) if passed else None
        dump(a.output/'summary.json',dict(status='selected' if winner else 'no_valid_candidate',
            selected_turn=winner['turn'] if winner else None,selected_sha256=winner.get('candidate_sha256') if winner else None,
            score_us=winner['tool_result']['score_us'] if winner else None,
            charged_s=charged,budget_s=budget,budget_overrun_s=max(0,charged-budget),
            elapsed_s=time.perf_counter()-origin,round_count=len(rows),
            inference_s=sum(r['generation_s'] for r in rows),
            evaluator_gpu_event_s=sum(r['tool_result'].get('gpu_event_window_s',0) for r in rows),
            protocol_sha256=sha(ROOT/'protocol.json')))
    finally:engine.shutdown()

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True)
    asyncio.run(main(parser.parse_args()))
