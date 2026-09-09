import hashlib,json,os,platform,random,subprocess,time,traceback
from pathlib import Path
import torch
R=Path(__file__).resolve().parent;D=R/'results';D.mkdir(exist_ok=False)
def save(p,x):p.write_text(json.dumps(x,indent=2)+'\n')
def sha(t):return hashlib.sha256(t.contiguous().view(torch.int16).numpy().tobytes()).hexdigest()
def gpu():return subprocess.check_output(['nvidia-smi','--query-compute-apps=pid,process_name,used_memory','--format=csv'],text=True)
torch.set_num_threads(8)
free=int(subprocess.check_output(['nvidia-smi','--query-gpu=memory.free','--format=csv,noheader,nounits'],text=True).strip());assert free>=4096
(D/'gpu-before.txt').write_text(gpu())
rows=[((torch.arange(4096)%128-64).float()/32+i/16).to(torch.bfloat16) for i in range(8)]
sources=[r.expand(8192,-1).clone() for r in rows]
refs=[(r.double()*torch.rsqrt(r.double().square().mean()+1e-6)).to(torch.bfloat16) for r in rows]
torch.save(dict(input_rows=rows,reference_rows=refs,shape=[8192,4096]),D/'fixture.pt')
refsha=[sha(r.expand(8192,-1)) for r in refs]
save(D/'environment.json',dict(torch=torch.__version__,cuda=torch.version.cuda,device=torch.cuda.get_device_name(),platform=platform.platform(),cpu_threads=8,source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),source_input_sha256=[sha(s) for s in sources],reference_sha256=refsha))
records=[]
def execute(policy,trial,kind):
 setup=time.perf_counter();nh=1 if policy=='serial' else 2;nd=2 if policy=='double' else 1
 hosts=[torch.empty_like(sources[0],pin_memory=True) for _ in range(nh)];assert all(h.is_pinned() for h in hosts)
 devices=[torch.empty_like(sources[0],device='cuda') for _ in range(nd)]
 scratch=[torch.empty((8192,4096),device='cuda',dtype=torch.float32) for _ in range(nd)]
 squared=[torch.empty_like(t) for t in scratch];stats=[torch.empty((8192,1),device='cuda') for _ in range(nd)]
 outputs=[torch.empty_like(devices[0]) for _ in range(8)]
 copy=torch.cuda.Stream();consume=torch.cuda.Stream();torch.cuda.synchronize();setup_s=time.perf_counter()-setup
 torch.cuda.reset_peak_memory_stats();allocated=torch.cuda.memory_allocated();anchor=torch.cuda.Event(enable_timing=True);anchor.record();copy.wait_event(anchor);consume.wait_event(anchor)
 events=[];host_last=[None]*nh;device_last=[None]*nd;begin=time.perf_counter_ns()
 for i in range(8):
  hi=i%nh;di=i%nd;wait_start=time.perf_counter_ns()
  if host_last[hi] is not None:host_last[hi].synchronize()
  prepare_start=time.perf_counter_ns()
  with torch.profiler.record_function(f'cpu_prepare_{i}'):hosts[hi].copy_(sources[i])
  prepared=time.perf_counter_ns();hs=torch.cuda.Event(enable_timing=True);he=torch.cuda.Event(enable_timing=True);cs=torch.cuda.Event(enable_timing=True);ce=torch.cuda.Event(enable_timing=True)
  with torch.cuda.stream(copy):
   if device_last[di] is not None:copy.wait_event(device_last[di])
   hs.record();devices[di].copy_(hosts[hi],non_blocking=True);he.record()
  with torch.cuda.stream(consume):
   consume.wait_event(he);cs.record()
   with torch.profiler.record_function(f'rmsnorm_consume_{i}'):
    scratch[di].copy_(devices[di]);torch.square(scratch[di],out=squared[di]);torch.mean(squared[di],dim=1,keepdim=True,out=stats[di]);stats[di].add_(1e-6).rsqrt_();scratch[di].mul_(stats[di]);outputs[i].copy_(scratch[di])
   ce.record()
  host_last[hi]=he;device_last[di]=ce
  if policy=='serial':ce.synchronize()
  events.append((dict(block=i,host_slot=hi,device_slot=di,wait_start_ns=wait_start,prepare_start_ns=prepare_start,prepared_ns=prepared),hs,he,cs,ce))
 torch.cuda.synchronize();end=time.perf_counter_ns();peak=torch.cuda.max_memory_allocated();reserved=torch.cuda.memory_reserved()
 stages=[]
 for row,hs,he,cs,ce in events:
  row.update(h2d_start_ms=anchor.elapsed_time(hs),h2d_end_ms=anchor.elapsed_time(he),consume_start_ms=anchor.elapsed_time(cs),consume_end_ms=anchor.elapsed_time(ce));stages.append(row)
 quality=[]
 for i,out in enumerate(outputs):
  cpu=out.cpu();err=float((cpu.float()-refs[i].float()).abs().max());quality.append(dict(block=i,max_abs=err,exact=bool(torch.equal(cpu,refs[i].expand_as(cpu))),sha256=sha(cpu),reference_sha256=refsha[i],passed=err<=1/128))
 row=dict(policy=policy,trial=trial,kind=kind,setup_s=setup_s,begin_ns=begin,end_ns=end,wall_ms=(end-begin)/1e6,host_slots=nh,device_slots=nd,pageable_input_bytes=sum(s.numel()*s.element_size() for s in sources),pinned_live_bytes=nh*64*2**20,device_input_bytes=nd*64*2**20,scratch_bytes=nd*(256*2**20+8192*4),retained_output_bytes=512*2**20,allocated_before=allocated,peak_allocated=peak,reserved_after=reserved,stages=stages,quality=quality)
 records.append(row);save(D/'raw.json',records);assert all(q['passed'] for q in quality),row
 print(json.dumps(dict(policy=policy,trial=trial,kind=kind,wall_ms=row['wall_ms'],all_exact=all(q['exact'] for q in quality))),flush=True)
try:
 for policy in ['serial','one_device','double']:execute(policy,-1,'warmup')
 order=[(p,t) for t in range(7) for p in ['serial','one_device','double']];random.Random(10010).shuffle(order);save(D/'order.json',order)
 for policy,trial in order:execute(policy,trial,'formal')
 for policy in ['serial','one_device','double']:
  with torch.profiler.profile(activities=[torch.profiler.ProfilerActivity.CPU,torch.profiler.ProfilerActivity.CUDA]) as prof:execute(policy,-2,'profile')
  prof.export_chrome_trace(str(D/f'{policy}-trace.json'))
 save(D/'completion.json',dict(status='complete',groups=len(records),blocks=sum(len(r['quality']) for r in records)))
except BaseException:
 (D/'failure.txt').write_text(traceback.format_exc());raise
finally:
 (D/'gpu-after.txt').write_text(gpu())
