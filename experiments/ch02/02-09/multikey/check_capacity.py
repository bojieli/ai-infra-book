"""Resolve candidate args and inspect resource gate; never creates an Engine."""
import json,time,hashlib,os
from pathlib import Path
os.environ['CUDA_HOME']='/home/ubuntu/ai-infra-book-experiments/tools/flashinfer-cuda130/nvidia/cu13'
os.environ['PATH']=os.environ['CUDA_HOME']+'/bin:'+os.environ['PATH']
from sglang.srt.server_args import ServerArgs
ROOT=Path(__file__).absolute().parent
cases=json.loads((ROOT/'prepared/cases.json').read_text());model='/home/ubuntu/.cache/huggingface/hub/models--deepseek-ai--DeepSeek-V4-Flash-0731/snapshots/'+cases['model_revision']
cfg=dict(model_path=model,dtype='bfloat16',cpu_offload_gb=110,context_length=cases['proposed_context'],max_total_tokens=cases['proposed_context'],max_running_requests=1,chunked_prefill_size=256,mem_fraction_static=.9,swa_full_tokens_ratio=1.0,disable_cuda_graph=True,disable_radix_cache=True,log_level='info',port=18329,random_seed=20260909)
a=ServerArgs(**cfg);assert a.context_length==5120 and a.max_total_tokens==5120
mem=Path('/proc/meminfo').read_text();available=int(next(l.split()[1] for l in mem.splitlines() if l.startswith('MemAvailable:')))*1024
result=dict(status='arguments_resolved_no_engine',requests_executed=0,CUDA_HOME=os.environ['CUDA_HOME'],driver_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),cases_sha256=hashlib.sha256((ROOT/'prepared/cases.json').read_bytes()).hexdigest(),requested=cfg,resolved=vars(a),available_bytes=available,required_start_available_bytes=140*1024**3,host_memory_start_gate_passed=available>=140*1024**3,scope='Prior full-model guard retained; argument resolution does not prove actual pool or model execution',checked_at_unix=time.time())
(ROOT/'capacity-check.json').write_text(json.dumps(result,indent=2,default=str)+'\n');print(json.dumps({k:result[k] for k in ['status','available_bytes','required_start_available_bytes','host_memory_start_gate_passed']}))
