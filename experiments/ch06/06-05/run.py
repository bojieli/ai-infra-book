"""Real CPU Gloo all-reduce and CPU matrix work, separately and concurrently."""
import argparse,ctypes,datetime,hashlib,json,os,platform,random,socket,subprocess,time
from pathlib import Path
import torch
import torch.distributed as dist
import torch.multiprocessing as mp

SIZES=[4096,4194304,67108864];MODES=['comm','compute','shared']
def digest(x):
 x=x.detach().contiguous();raw=(ctypes.c_char*(x.numel()*x.element_size())).from_address(x.data_ptr())
 return hashlib.sha256(raw).hexdigest()
def worker(rank,port,root,plan):
 torch.set_num_threads(2);torch.set_num_interop_threads(2)
 dist.init_process_group('gloo',init_method=f'tcp://127.0.0.1:{port}',rank=rank,world_size=4,timeout=datetime.timedelta(seconds=60))
 b=Path(root);torch.manual_seed(605+rank)
 a=torch.randint(-4,5,(16,4096),dtype=torch.int8).float()/16
 w=torch.randint(-4,5,(4096,4096),dtype=torch.int8).float()/16
 ref=a.double()@w.double();h=dict(a=digest(a),w=digest(w),reference=digest(ref))
 buffers={n:torch.empty(n//4,dtype=torch.float32) for n in {r['bytes'] for r in plan}}
 result=torch.empty_like(ref,dtype=torch.float32)
 saved=False
 with (b/f'rank{rank}.jsonl').open('x') as f:
  for index,cfg in enumerate(plan):
   x=buffers[cfg['bytes']];value=rank+1+cfg['trial']%11;x.fill_(value);expected=10+4*(cfg['trial']%11)
   dist.barrier();start=time.perf_counter_ns();cpu0=time.process_time_ns();marks={};work=None;future=None
   if cfg['mode']!='compute':
    marks['comm_submit_ns']=time.perf_counter_ns();work=dist.all_reduce(x,op=dist.ReduceOp.SUM,async_op=True);marks['comm_submit_return_ns']=time.perf_counter_ns()
    def callback(fut):marks['comm_callback_ns']=time.perf_counter_ns();return None
    future=work.get_future().then(callback)
   if cfg['mode']!='comm':
    marks['compute_start_ns']=time.perf_counter_ns();torch.mm(a,w,out=result);marks['compute_end_ns']=time.perf_counter_ns()
   if future is not None:future.wait();work.wait()
   end=time.perf_counter_ns();cpu1=time.process_time_ns()
   comm_ok=bool(torch.all(x==expected)) if cfg['mode']!='compute' else None
   compute_ok=bool(torch.all(result.double()==ref)) if cfg['mode']!='comm' else None
   row=dict(index=index,rank=rank,pid=os.getpid(),**cfg,start_ns=start,end_ns=end,process_cpu_ns=cpu1-cpu0,marks=marks,comm_correct=comm_ok,compute_correct=compute_ok,expected_comm=expected,comm_min=float(x.min()) if comm_ok is not None else None,comm_max=float(x.max()) if comm_ok is not None else None,output_sha256=digest(result) if compute_ok is not None else None)
   f.write(json.dumps(row)+'\n');f.flush()
   assert comm_ok is not False and compute_ok is not False,row
   if cfg['mode']!='comm' and not saved:
    torch.save(dict(a=a,actual=result.clone(),reference=ref,seed=605+rank),b/f'rank{rank}-tensors.pt');saved=True
 input_unchanged=h['a']==digest(a) and h['w']==digest(w)
 (b/f'rank{rank}-identity.json').write_text(json.dumps(dict(rank=rank,pid=os.getpid(),seed=605+rank,hashes=h,input_unchanged=input_unchanged,threads=torch.get_num_threads(),interop_threads=torch.get_num_interop_threads()),indent=2)+'\n');assert input_unchanged
 dist.destroy_process_group()

def main():
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--smoke',action='store_true');a=p.parse_args();a.output.mkdir(parents=True,exist_ok=False)
 if a.smoke:plan=[dict(bytes=4096,mode=m,trial=0,warmup=True) for m in MODES]
 else:
  plan=[dict(bytes=n,mode=m,trial=0,warmup=True) for n in SIZES for m in MODES];rnd=random.Random(605)
  for trial in range(5):
   sizes=SIZES.copy();rnd.shuffle(sizes)
   for n in sizes:
    modes=MODES.copy();rnd.shuffle(modes)
    plan.extend(dict(bytes=n,mode=m,trial=trial,warmup=False) for m in modes)
 env=dict(time=time.time(),platform=platform.platform(),python=platform.python_version(),torch=torch.__version__,backend='gloo',world_size=4,threads_per_rank=2,shape=[16,4096,4096],plan=plan,smoke=a.smoke,protocol_sha256=hashlib.sha256(Path(__file__).with_name('PROTOCOL.md').read_bytes()).hexdigest(),source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),clock=time.get_clock_info('perf_counter').__dict__,hardware=subprocess.check_output(['sysctl','-n','machdep.cpu.brand_string','hw.memsize'],text=True).strip())
 (a.output/'environment.json').write_text(json.dumps(env,indent=2)+'\n')
 with socket.socket() as sock:sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
 mp.spawn(worker,args=(port,str(a.output),plan),nprocs=4,join=True)
 (a.output/'completion.json').write_text(json.dumps(dict(completed=True,ranks=4,groups=len(plan),time=time.time()))+'\n')
if __name__=='__main__':main()
