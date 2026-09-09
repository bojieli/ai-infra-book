import argparse,ctypes,hashlib,json,os,time
from pathlib import Path
import torch
from torch.utils.data import DataLoader,Dataset,Sampler
from torch.nn import functional as F
from model import Model
B=Path(__file__).resolve().parent

def write(p,x):p.write_text(json.dumps(x,indent=2)+'\n')
def event(p,x):
 with p.open('a') as f:f.write(json.dumps(dict(time=time.monotonic(),**x))+'\n')
def sha(t):
 t=t.detach().contiguous();return hashlib.sha256((ctypes.c_char*(t.numel()*t.element_size())).from_address(t.data_ptr())).hexdigest()
def ident(x):return x

def init_worker(_):torch.set_num_threads(1)
class Records(Dataset):
 def __init__(self,path,out):
  self.path=path;self.out=out;self.offsets=[0]
  while self.offsets[-1]<Path(path).stat().st_size:self.offsets.append(self.offsets[-1]+257+2*((len(self.offsets)-1)%7))
 def __len__(self):return len(self.offsets)-2
 def __getitem__(self,i):
  start,end=self.offsets[i:i+2]
  with open(self.path,'rb') as f:f.seek(start);data=f.read(end-start)
  assert len(data)==end-start
  event(Path(self.out)/f'worker-{os.getpid()}.jsonl',dict(kind='read_complete',pid=os.getpid(),record=i,start=start,end=end,bytes=len(data)))
  return dict(record=i,start=start,data=data)
class Ordered(Sampler):
 def __init__(self,start,count,out):self.start=start;self.count=count;self.out=out;self.dispatched=[]
 def __iter__(self):
  for i in range(self.start,self.count):
   self.dispatched.append(i);event(self.out/'dispatch.jsonl',dict(kind='dispatch',record=i));yield i
 def __len__(self):return self.count-self.start

def durable(p,x):
 q=p.with_suffix('.tmp')
 with q.open('wb') as f:torch.save(x,f);f.flush();os.fsync(f.fileno())
 os.replace(q,p);fd=os.open(p.parent,os.O_RDONLY);os.fsync(fd);os.close(fd)

def main(a):
 out=Path(a.output);out.mkdir(parents=True,exist_ok=False)
 torch.set_num_threads(2);torch.set_num_interop_threads(1);torch.use_deterministic_algorithms(True);torch.manual_seed(a.seed)
 model=Model(64);opt=torch.optim.AdamW(model.parameters(),lr=.001,betas=(.9,.95),eps=1e-8,weight_decay=.01)
 generator=torch.Generator().manual_seed(10106)
 cursor=step=0;buf=b'';positions=[];cp=None
 if a.checkpoint:
  cp=torch.load(a.checkpoint,map_location='cpu',weights_only=True);model.load_state_dict(cp['model']);opt.load_state_dict(cp['optimizer']);torch.set_rng_state(cp['rng']);generator.set_state(cp['loader_rng']);cursor=cp['cursor'];step=cp['step'];buf=cp['buffer'];positions=cp['positions']
  if a.control=='omit_buffer':buf=b'';positions=[]
  if a.control=='dispatch_cursor':cursor=cp['dispatch_cursor']
 data=Records(str(B/'data/input.txt'),str(out));sampler=Ordered(cursor,len(data),out)
 loader=DataLoader(data,batch_size=None,num_workers=2,prefetch_factor=2,multiprocessing_context='spawn',sampler=sampler,collate_fn=ident,worker_init_fn=init_worker,generator=generator)
 iterator=iter(loader)
 # Workers perform deterministic reads. Undo only the extra iterator seed draw on recovery.
 if cp is not None:generator.set_state(cp['loader_rng'])
 write(out/'identity.json',dict(pid=os.getpid(),pgid=os.getpgrp(),seed=a.seed,control=a.control,resume_from=a.checkpoint,start_step=step,torch=torch.__version__,threads=torch.get_num_threads(),time=time.monotonic(),record_cursor=cursor,parameters=sum(p.numel() for p in model.parameters())))
 def state():return dict(model=model.state_dict(),optimizer=opt.state_dict(),rng=torch.get_rng_state(),loader_rng=generator.get_state(),cursor=cursor,buffer=buf,positions=positions,step=step,dispatch_cursor=max(sampler.dispatched)+1,seed=a.seed)
 while step<a.steps:
  while len(buf)<129:
   row=next(iterator);assert row['record']==cursor;cursor+=1;buf+=row['data'];positions.extend(range(row['start'],row['start']+len(row['data'])));event(out/'consume.jsonl',dict(kind='record_consumed',record=row['record'],cursor=cursor))
  raw=buf[:129];ids=positions[:129];buf=buf[128:];positions=positions[128:]
  x=torch.tensor(list(raw[:128]),dtype=torch.long).reshape(1,128);y=torch.tensor(list(raw[1:]),dtype=torch.long).reshape(1,128)
  start=time.monotonic();opt.zero_grad(set_to_none=True);logits=model(x);loss=F.cross_entropy(logits.reshape(-1,256),y.reshape(-1));loss.backward();grad=torch.nn.utils.clip_grad_norm_(model.parameters(),1.,error_if_nonfinite=True);opt.step();step+=1
  event(out/'steps.jsonl',dict(kind='update',step=step,start=start,end=time.monotonic(),loss=loss.item(),gradient=grad.item(),positions=ids,input_bytes=list(raw),input_sha256=hashlib.sha256(raw).hexdigest(),buffer_bytes=len(buf),cursor=cursor))
  if step==a.stop:
   pending=[i for i in sampler.dispatched if i>=cursor];deadline=time.monotonic()+10
   while True:
    completed=[];workers=[]
    for p in out.glob('worker-*.jsonl'):
     for line in p.read_text().splitlines():
      try:r=json.loads(line)
      except json.JSONDecodeError:continue
      if r['record']>=cursor:completed.append(r['record']);workers.append(r['pid'])
    if completed:break
    assert time.monotonic()<deadline,'No completed unconsumed prefetch';time.sleep(.01)
   assert len(buf)>1 and pending and completed,(step,len(buf),pending,completed)
   before=time.monotonic();durable(out/'checkpoint.pt',state());done=time.monotonic()
   write(out/'ready.json',dict(step=step,pid=os.getpid(),pgid=os.getpgrp(),buffer_bytes=len(buf),cursor=cursor,pending=pending,completed_unconsumed=sorted(set(completed)),worker_pids=sorted(set(workers)),checkpoint_bytes=(out/'checkpoint.pt').stat().st_size,save_start=before,save_complete=done,time=time.monotonic()))
   while True:time.sleep(.1)
 durable(out/'final.pt',state());write(out/'completion.json',dict(done=True,step=step,pid=os.getpid(),time=time.monotonic()))
 del iterator,loader
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',required=True);p.add_argument('--seed',type=int,required=True);p.add_argument('--steps',type=int,default=64);p.add_argument('--stop',type=int,default=-1);p.add_argument('--checkpoint');p.add_argument('--control',default='correct',choices=['correct','omit_buffer','dispatch_cursor']);main(p.parse_args())
