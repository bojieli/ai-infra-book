"""Shared immutable candidate and read-only OS evidence; importing starts no model."""
import hashlib,json,os,subprocess,time
from pathlib import Path
BASE=Path(__file__).resolve().parent
TOOLS=Path('/home/ubuntu/ai-infra-book-experiments/tools')
PYTHON=TOOLS/'sglang0513-venv/bin/python'
MODEL=Path('/home/ubuntu/.cache/huggingface/hub/models--deepseek-ai--DeepSeek-V4-Flash-0731/snapshots/7872f01b1d1fe23eabc4c98b48bffcef5a386062')
CONFIG=dict(model_path=str(MODEL),dtype='bfloat16',cpu_offload_gb=110,context_length=5120,max_total_tokens=5120,max_running_requests=1,chunked_prefill_size=256,mem_fraction_static=.9,swa_full_tokens_ratio=1.0,disable_cuda_graph=True,disable_radix_cache=True,log_level='info',port=18329,random_seed=20260909)
SAMPLING=dict(temperature=0,top_p=1,top_k=1,max_new_tokens=128,ignore_eos=False)
LIMITS=dict(start_available_gib=140,start_gpu_free_mib=80*1024,max_rss_gib=175,max_gpu_mib=78*1024,min_available_gib=24,min_gpu_free_mib=4*1024,init_timeout_s=1800,request_timeout_s=600,total_timeout_s=7200,poll_s=1)
def save(path,obj):
 path=Path(path);tmp=path.with_suffix(path.suffix+'.tmp');tmp.write_text(json.dumps(obj,ensure_ascii=False,indent=2,default=str)+'\n');tmp.replace(path)
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def command(args):return subprocess.check_output(args,text=True,timeout=15).strip()
def processes():
 rows=[]
 for d in Path('/proc').iterdir():
  if not d.name.isdigit():continue
  try:
   status={k:v.strip() for k,v in (l.split(':',1) for l in (d/'status').read_text().splitlines() if ':' in l)}
   stat=(d/'stat').read_text().rsplit(')',1)[1].split()
   rows.append(dict(pid=int(d.name),ppid=int(stat[1]),sid=int(stat[3]),birth=int(stat[19]),name=status.get('Name'),rss_kib=int(status.get('VmRSS','0 kB').split()[0]),anon_kib=int(status.get('RssAnon','0 kB').split()[0]),is_verl=any(marker in (d/'cmdline').read_bytes() for marker in [b'/tools/verl-private/',b'/experiments/ch10/10-08/'])))
  except (FileNotFoundError,ProcessLookupError,PermissionError):pass
 return rows

def snapshot():
 mem=Path('/proc/meminfo').read_text()
 gpu=command(['nvidia-smi','--query-gpu=index,uuid,name,memory.total,memory.used,memory.free,utilization.gpu','--format=csv,noheader,nounits'])
 apps=command(['nvidia-smi','--query-compute-apps=pid,process_name,used_memory','--format=csv,noheader,nounits'])
 gpu_rows=[x.split(',') for x in gpu.splitlines()];assert len(gpu_rows)==1,'Single GPU host required'
 return dict(time=time.time(),monotonic=time.monotonic(),meminfo=mem,available_bytes=int(next(l.split()[1] for l in mem.splitlines() if l.startswith('MemAvailable:')))*1024,gpu_raw=gpu,gpu_free_mib=int(gpu_rows[0][5]),gpu_apps_raw=apps,processes=processes(),scope='read_only_shared_host_snapshot')
