"""Read current OS resource evidence; no allocation, inference or other-job control."""
from pathlib import Path
import argparse,json,subprocess,time,hashlib
p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
def command(args):return subprocess.check_output(args,text=True)
mem=Path('/proc/meminfo').read_text();gpu=command(['nvidia-smi','--query-gpu=name,memory.total,memory.used,memory.free','--format=csv,noheader']);apps=command(['nvidia-smi','--query-compute-apps=pid,process_name,used_memory','--format=csv,noheader'])
rows=[]
for d in Path('/proc').iterdir():
 if not d.name.isdigit():continue
 try:
  s={k:v.strip() for k,v in (l.split(':',1) for l in (d/'status').read_text().splitlines() if ':' in l)}
  rss=int(s.get('VmRSS','0 kB').split()[0]);anon=int(s.get('RssAnon','0 kB').split()[0])
  if rss>512*1024:rows.append(dict(pid=int(d.name),name=s.get('Name'),rss_kib=rss,anon_kib=anon))
 except (FileNotFoundError,PermissionError,ProcessLookupError):pass
for name,text in [('meminfo.txt',mem),('gpu.txt',gpu),('gpu-processes.txt',apps)]: (a.out/name).write_text(text)
result=dict(time=time.time(),status='read_only_snapshot_not_a_full_model_capacity_proof',candidate_cpu_offload_gib=110,candidate_source='../runtime-preflight/resolved-config.json',available_kib=int(next(l.split()[1] for l in mem.splitlines() if l.startswith('MemAvailable:'))),processes_by_anon=sorted(rows,key=lambda x:x['anon_kib'],reverse=True),probe_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),actions_on_existing_processes=[])
(a.out/'observation.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
