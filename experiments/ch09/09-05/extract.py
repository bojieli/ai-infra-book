"""Parse fixed deployment records; never execute their shell commands."""
import hashlib,json,re,shlex
from pathlib import Path
ROOT=Path(__file__).resolve().parent
sources=json.loads((ROOT/'sources.json').read_text());texts={}
for s in sources:
 p=ROOT/'source-snapshots'/Path(s['file']).name;assert hashlib.sha256(p.read_bytes()).hexdigest()==s['sha256'];texts[s['id']]=p.read_text()
def command(text,needle):
 blocks=re.findall(r'```(?:bash|shell)?\n(.*?)```',text,re.S);matches=[b for b in blocks if needle in b];assert len(matches)==1
 block=matches[0];tokens=shlex.split(block[block.index(needle):].replace('\\\n',' '));flags={};i=0
 while i<len(tokens):
  if tokens[i].startswith('--'):
   flag=tokens[i];value=True
   if i+1<len(tokens) and not tokens[i+1].startswith('--'):i+=1;value=tokens[i]
   assert flag not in flags;flags[flag]=value
  i+=1
 return dict(raw=block,flags=flags,executed=False)
v4=command(texts['kt-v4'],'python -m sglang.launch_server');k2=command(texts['kt-kimi2'],'python ktransformers/server/main.py')
docker={m.group(1):m.group(2) for m in re.finditer(r'^\| `([A-Z_]+)` \| `([^`]+)` \|',texts['kt-v4'],re.M)}
assert docker['CHUNKED_PREFILL_SIZE']=='4096' and v4['flags']['--chunked-prefill-size']=='2048'
assert docker['KT_GPU_PREFILL_TOKEN_THRESHOLD']=='2048' and v4['flags']['--kt-gpu-prefill-token-threshold']=='4096'
assert docker['MEM_FRACTION']=='0.90' and v4['flags']['--mem-fraction-static']=='0.85'
assert v4['flags']['--context-length']=='16384' and v4['flags']['--max-running-requests']=='2'
assert v4['flags']['--kt-method']=='MXFP4' and v4['flags']['--kt-num-gpu-experts']=='10'
assert k2['flags']['--cache_lens']=='32768' and k2['flags']['--max_batch_size']=='4'
assert 'DeepSeek-V4-Flash-0731' in texts['kt-v4'] and '26.5 → 32.74' in texts['kt-v4'] and '8× RTX 5090' in texts['kt-v4']
assert 'roughly 10 TPS' in texts['kt-kimi2'] and 'about 14 TPS' in texts['kt-kimi2']
report=dict(status='fixed_records_extracted',revision='31985f40bcc40da08107efdb1f81bf88cb38c6b2',v4_native=v4,v4_docker_defaults=docker,kimi2_command=k2,published_observations=[dict(id='v4-single',model='DeepSeek-V4-Flash-0731',gpu='1x RTX 5090 32GB',cpu_model=None,system_ram='>=200GB requirement',weights_storage='~340GB requirement',decode='20+ tok/s',startup='about 4-5 minutes (weight load + CUDA Graph capture)',measured_concurrency=None,context_in_command=16384,max_running_in_command=2,actual_request_lengths=None,quality=None,wall_power=None,evidence='tutorial report; raw measurements not attached'),dict(id='v4-mtp',gpu='8x RTX 5090',decode_before=26.5,decode_after=32.74,unit='tok/s',reported_accept_rate=.90,reported_chain_depth=1,reported_request_concurrency=1,complete_eight_gpu_command_supplied=False,quality=None,evidence='separate tutorial report, not single-GPU result'),dict(id='kimi2-single',model='Kimi-K2 Q4_K_M (tutorial also mentions 0905)',gpu='one consumer GPU, model unspecified',cpu='single socket, model unspecified',system_ram='about 600GB',gpu_memory='about 14GB for 384 experts',decode='roughly 10 TPS',actual_context=None,actual_concurrency=None,quality=None,wall_power=None,evidence='tutorial report'),dict(id='kimi2-dual',model='Kimi-K2 Q4_K_M',cpu='dual socket, model unspecified',numa='enabled',decode='about 14 TPS',other_conditions_matched=None,quality=None,evidence='tutorial report; no controlled NUMA ablation demonstrated')],gaps=['context/concurrency measurements with same request set','full-GPU comparator at matched quality','expert reads, CPU work and actual PCIe transfers','system power, DRAM/SSD/host costs and ownership conditions','raw output, acceptance accounting and quality data','fixed executable engine revision, model weight hashes and image digest'],version_notes=['DSV4-specific Docker tag has no digest in tutorial','source install uses unpinned clone/submodules; doc commit is not full environment lock','tutorial requires transformers==4.57.1; flashinfer>=0.6.9 matched python/cubin; tilelang tested 0.1.8; tvm-ffi<0.1.12','Kimi command default download is original Instruct GGUF, not specifically 0905','Kimi K2 evidence does not represent Kimi K3'])
(ROOT/'records.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(dict(status=report['status'],v4_native_flags=len(v4['flags']),kimi2_flags=len(k2['flags']),published_records=len(report['published_observations'])),ensure_ascii=False))
if __name__=='__main__':pass
