import argparse,ctypes,hashlib,json,math,os,platform,random,resource,time
from pathlib import Path
import torch
from torch.nn import functional as F
from model import Model
B=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--output',required=True);p.add_argument('--smoke',action='store_true');a=p.parse_args();out=Path(a.output);out.mkdir(parents=True,exist_ok=False)
torch.set_num_threads(4);torch.set_num_interop_threads(1);torch.use_deterministic_algorithms(True)
def dump(p,x):p.write_text(json.dumps(x,indent=2)+'\n')
def tensor_sha(t):
 t=t.detach().contiguous();return hashlib.sha256((ctypes.c_char*(t.numel()*t.element_size())).from_address(t.data_ptr())).hexdigest()
def model_sha(m):
 h=hashlib.sha256()
 for n,v in m.state_dict().items():h.update(n.encode());h.update(tensor_sha(v).encode())
 return h.hexdigest()
data=(B/'data/input.txt').read_bytes();source=json.loads((B/'data/source.json').read_text());assert hashlib.sha256(data).hexdigest()==source['sha256'];tokens=torch.tensor(list(data),dtype=torch.long);valstart=int(.9*len(data));valn=256 if a.smoke else 8192;assert 524289<valstart and valstart+valn<len(data)
order=[(64,308)] if a.smoke else [(w,s) for w in [64,128,256] for s in [308,309]];random.Random(308).shuffle(order)
dump(out/'environment.json',dict(torch=torch.__version__,platform=platform.platform(),machine=platform.machine(),threads=torch.get_num_threads(),interop_threads=torch.get_num_interop_threads(),device='cpu',source=source,valstart=valstart,val_targets=valn,order=order,source_sha256={n:hashlib.sha256((B/n).read_bytes()).hexdigest() for n in ['run.py','model.py','PROTOCOL.md']},env={k:os.environ.get(k) for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','VECLIB_MAXIMUM_THREADS']}))
for width,seed in order:
 work=out/f'w{width}-seed{seed}';work.mkdir();torch.manual_seed(seed);model=Model(width);opt=torch.optim.AdamW(model.parameters(),lr=.001,betas=(.9,.95),eps=1e-8,weight_decay=.01);n=sum(p.numel() for p in model.parameters());init=model_sha(model);x=tokens[:128].reshape(1,128);y=x.clone();y[:,64:]=(y[:,64:]+17)%256
 with torch.no_grad():assert torch.equal(model(x)[:,:64],model(y)[:,:64])
 dump(work/'identity.json',dict(width=width,seed=seed,parameters=n,initial_sha256=init,causal_prefix_exact=True))
 def evaluate(step,train_wall,train_cpu):
  model.eval();start=time.monotonic();losses=[];first_logits=None
  with torch.inference_mode():
   for i in range(0,valn,1024):
    count=min(1024,valn-i);xs=tokens[valstart+i:valstart+i+count].reshape(-1,128);ys=tokens[valstart+i+1:valstart+i+count+1].reshape(-1,128);logits=model(xs);losses.append(F.cross_entropy(logits.reshape(-1,256),ys.reshape(-1),reduction='none'))
    if first_logits is None:first_logits=logits[0].clone();first_labels=ys[0].clone()
  loss=torch.cat(losses);state={k:v.detach().clone() for k,v in model.state_dict().items()};h=model_sha(model);file=f'checkpoint-{step:04}.pt';torch.save(dict(width=width,seed=seed,step=step,model=state,losses=loss,first_logits=first_logits,first_labels=first_labels),work/file)
  row=dict(step=step,D=step*1024,N=n,width=width,seed=seed,val_mean_nll=loss.double().mean().item(),val_targets=loss.numel(),model_sha256=h,checkpoint=file,train_wall_s=train_wall,train_cpu_s=train_cpu,eval_and_save_wall_s=time.monotonic()-start,train_prefix_sha256=hashlib.sha256(data[:step*1024+1]).hexdigest())
  with (work/'evaluations.jsonl').open('a') as f:f.write(json.dumps(row)+'\n')
  print(json.dumps(dict(run=work.name,**row)),flush=True);model.train()
 wall=cpu=0.;evaluate(0,wall,cpu);steps=2 if a.smoke else 512;milestones={2} if a.smoke else {32,128,512}
 with (work/'steps.jsonl').open('w',buffering=1) as log:
  for step in range(1,steps+1):
   i=(step-1)*1024;xs=tokens[i:i+1024].reshape(8,128);ys=tokens[i+1:i+1025].reshape(8,128);t=time.monotonic();c=time.process_time();opt.zero_grad(set_to_none=True);z=model(xs);loss=F.cross_entropy(z.reshape(-1,256),ys.reshape(-1));loss.backward();grad=torch.nn.utils.clip_grad_norm_(model.parameters(),1.0,error_if_nonfinite=True);opt.step();elapsed=time.monotonic()-t;cp=time.process_time()-c;wall+=elapsed;cpu+=cp
   assert math.isfinite(loss.item()) and math.isfinite(grad.item())
   log.write(json.dumps(dict(step=step,D=step*1024,loss=loss.item(),gradient_norm_before_clip=grad.item(),wall_s=elapsed,cpu_s=cp))+'\n')
   if step in milestones:evaluate(step,wall,cpu)
 final=model_sha(model);assert final!=init
 torch.save(dict(optimizer=opt.state_dict(),rng=torch.get_rng_state()),work/'optimizer-final.pt')
 dump(work/'completion.json',dict(steps=steps,parameters_changed=True,initial_sha256=init,final_sha256=final,all_optimizer_state_steps=sorted(set(int(s['step'].item()) for s in opt.state.values())),train_wall_s=wall,train_cpu_s=cpu))
 del opt,model
(out/'completion.json').write_text(json.dumps(dict(runs=len(order),smoke=a.smoke,complete=True))+'\n')
