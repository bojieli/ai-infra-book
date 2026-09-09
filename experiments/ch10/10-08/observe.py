"""Read-only tensor observation; core training/sync functions are not replaced."""
import hashlib,json,os,pathlib,time
import torch
ROOT=pathlib.Path(os.environ['VERLRL_OBSERVE']);ROOT.mkdir(parents=True,exist_ok=True)
def event(kind,**data):
 with (ROOT/f'events-{os.getpid()}.jsonl').open('a') as f:f.write(json.dumps(dict(kind=kind,pid=os.getpid(),time_ns=time.time_ns(),**data),default=str)+'\n')
def digest(t,dtype=None):
 h=hashlib.sha256();flat=t.detach().reshape(-1)
 for part in flat.split(262144):
  z=part.to(dtype=dtype or t.dtype,device='cpu').contiguous();h.update(z.view(torch.uint8).numpy().tobytes())
 return h.hexdigest()
def optimizer(engine,phase):
 start=time.monotonic();step=getattr(engine,'_verlrl_observation_step',0)
 if phase=='before':step+=1;engine._verlrl_observation_step=step
 for name,p in engine.module.named_parameters():
  if 'embed_tokens.weight' not in name:continue
  flat=p.detach().reshape(-1);payload={'param_first4096':flat[:4096].cpu().clone()};g=p.grad
  if g is not None:
   gf=g.detach().reshape(-1);idx=[]
   for offset in range(0,gf.numel(),262144):
    nz=gf[offset:offset+262144].nonzero().reshape(-1)[:64].cpu()+offset;idx.extend(nz.tolist())
    if len(idx)>=64:break
   ids=torch.tensor(idx[:64],device=flat.device,dtype=torch.long);payload.update(indices=ids.cpu(),param_at_indices=flat[ids].cpu().clone(),gradient_at_indices=gf[ids].cpu().clone())
  for key,val in engine.optimizer.state.get(p,{}).items():
   if torch.is_tensor(val):
    vf=val.detach().reshape(-1);payload['optimizer_'+key]=vf[:4096].cpu().clone()
    if g is not None and vf.numel()==flat.numel():payload['optimizer_'+key+'_at_indices']=vf[ids].cpu().clone()
  file=f'optimizer-{os.getpid()}-{step}-{phase}.pt';torch.save(payload,ROOT/file)
  event('optimizer_observation',phase=phase,step=step,name=name,shape=list(p.shape),dtype=str(p.dtype),sha256=digest(p),bf16_sha256=digest(p,torch.bfloat16),gradient_sha256=digest(g) if g is not None else None,tensors=file,observation_s=time.monotonic()-start)
def receiver(model,updates):
 if not any('embed_tokens.weight' in n for n,_ in updates):return
 start=time.monotonic()
 for n,p in model.named_parameters():
  if 'embed_tokens.weight' in n:event('receiver_loaded_embedding',name=n,shape=list(p.shape),dtype=str(p.dtype),bf16_sha256=digest(p,torch.bfloat16),observation_s=time.monotonic()-start)
def sender(weights,step):
 for n,t in weights:
  if 'embed_tokens.weight' in n:
   start=time.monotonic();h=digest(t,torch.bfloat16)
   event('sender_embedding',step=step,name=n,shape=list(t.shape),bf16_sha256=h,observation_s=time.monotonic()-start)
  yield n,t
def batch(data,step,stage='advantage'):
 start=time.monotonic();file=f'{stage}-batch-{step}.pt'
 torch.save({k:v.detach().cpu() for k,v in data.batch.items()},ROOT/file)
 def encode(x):
  if hasattr(x,'tolist'):return x.tolist()
  return str(x)
 metadata_file=f'{stage}-batch-{step}.json'
 (ROOT/metadata_file).write_text(json.dumps(dict(meta_info=data.meta_info,non_tensor_batch=data.non_tensor_batch),default=encode,indent=2)+'\n')
 event(stage+'_batch',step=step,tensors=file,keys=list(data.batch.keys()),metadata_file=metadata_file,observation_s=time.monotonic()-start)

def metrics(values,step):
 scalar={k:(v.item() if hasattr(v,'item') else v) for k,v in values.items()}
 event('trainer_metrics',step=step,metrics=scalar)
