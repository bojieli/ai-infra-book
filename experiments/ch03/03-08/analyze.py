"""Offline verification of complete real training artifacts; no fitting or training reruns."""
import ctypes,hashlib,json,math
from pathlib import Path
import torch
from torch.nn import functional as F
from model import Model
B=Path(__file__).resolve().parent;torch.set_num_threads(4);torch.set_num_interop_threads(1);torch.use_deterministic_algorithms(True)
def shat(t):
 t=t.detach().contiguous();return hashlib.sha256((ctypes.c_char*(t.numel()*t.element_size())).from_address(t.data_ptr())).hexdigest()
def shas(state):
 h=hashlib.sha256()
 for n,v in state.items():h.update(n.encode());h.update(shat(v).encode())
 return h.hexdigest()
data=(B/'data/input.txt').read_bytes();tokens=torch.tensor(list(data),dtype=torch.long);checks=[];formal=[];summary=[]
def check(name,value):
 checks.append(dict(check=name,passed=bool(value)))
 if not value:raise AssertionError(name)
for dataset in ['smoke','formal']:
 root=B/dataset;done=json.loads((root/'completion.json').read_text());env=json.loads((root/'environment.json').read_text());sup=json.loads((B/(dataset+'-supervisor.json')).read_text());check(dataset+' normal exit',sup['exit_code']==0 and sup['reason'] is None and done['complete']);check(dataset+' source',hashlib.sha256(data).hexdigest()==env['source']['sha256']);check(dataset+' resource',sup['peak_rss_bytes']<=8*1024**3)
 expected=[(64,308)] if dataset=='smoke' else [(w,s) for w in [64,128,256] for s in [308,309]];check(dataset+' run coverage',sorted(map(tuple,env['order']))==sorted(expected));v=env['valstart'];nt=env['val_targets'];maxstep=2 if dataset=='smoke' else 512
 for width,seed in expected:
  work=root/f'w{width}-seed{seed}';identity=json.loads((work/'identity.json').read_text());end=json.loads((work/'completion.json').read_text());steps=[json.loads(l) for l in (work/'steps.jsonl').read_text().splitlines()];rows=[json.loads(l) for l in (work/'evaluations.jsonl').read_text().splitlines()];model=Model(width).eval();n=sum(p.numel() for p in model.parameters());check(str(work)+' parameters',n==identity['parameters']);check(str(work)+' steps',len(steps)==maxstep and [r['step'] for r in steps]==list(range(1,maxstep+1)));check(str(work)+' checkpoint coverage',[r['step'] for r in rows]==([0,2] if dataset=='smoke' else [0,32,128,512]));check(str(work)+' no split overlap',maxstep*1024<v and v+nt<len(data))
  for r in steps:check(f'{dataset}/{width}/{seed}/step{r["step"]}',r['D']==r['step']*1024 and all(math.isfinite(r[k]) for k in ['loss','gradient_norm_before_clip','wall_s','cpu_s']) and r['gradient_norm_before_clip']>0 and r['wall_s']>0)
  for r in rows:
   item=torch.load(work/r['checkpoint'],map_location='cpu',weights_only=True);model.load_state_dict(item['model'],strict=True);check(f'{work}/{r["step"]} identity',shas(item['model'])==r['model_sha256'] and item['width']==width and item['seed']==seed and item['step']==r['step'] and r['N']==n and r['D']==r['step']*1024);check(f'{work}/{r["step"]} prefix',hashlib.sha256(data[:r['D']+1]).hexdigest()==r['train_prefix_sha256'])
   losses=[]
   with torch.inference_mode():
    for i in range(0,nt,1024):
     count=min(1024,nt-i);xs=tokens[v+i:v+i+count].reshape(-1,128);ys=tokens[v+i+1:v+i+count+1].reshape(-1,128);z=model(xs);losses.append(F.cross_entropy(z.reshape(-1,256),ys.reshape(-1),reduction='none'))
     if i==0:check(f'{work}/{r["step"]} full saved logits',torch.equal(z[0],item['first_logits']) and torch.equal(ys[0],item['first_labels']))
   loss=torch.cat(losses);delta=(loss-item['losses']).abs().max().item();check(f'{work}/{r["step"]} all heldout targets',delta<=1e-6 and loss.numel()==nt and abs(loss.double().mean().item()-r['val_mean_nll'])<=1e-6)
   z=item['first_logits'].double();label=item['first_labels'];ref=torch.logsumexp(z,dim=-1)-z[torch.arange(128),label];err=(ref-item['losses'][:128].double()).abs().max().item();check(f'{work}/{r["step"]} independent FP64 CE',err<=2e-6)
   if dataset=='formal':formal.append(dict(**r,reload_max_abs_error=delta,fp64_ce_max_abs_error=err))
  opt=torch.load(work/'optimizer-final.pt',map_location='cpu',weights_only=True)['optimizer'];states=list(opt['state'].values());check(str(work)+' optimizer',len(states)==len(list(model.parameters())) and all(int(s['step'].item())==maxstep and torch.isfinite(s['exp_avg']).all().item() and torch.isfinite(s['exp_avg_sq']).all().item() for s in states));check(str(work)+' parameters changed',rows[0]['model_sha256']!=rows[-1]['model_sha256'] and end['initial_sha256']==rows[0]['model_sha256'] and end['final_sha256']==rows[-1]['model_sha256']);check(str(work)+' training interval sum',abs(sum(s['wall_s'] for s in steps)-end['train_wall_s'])<1e-8 and abs(sum(s['cpu_s'] for s in steps)-end['train_cpu_s'])<1e-8)
  if dataset=='formal':summary.append(dict(width=width,seed=seed,N=n,steps=maxstep,D=maxstep*1024,initial_loss=rows[0]['val_mean_nll'],final_loss=rows[-1]['val_mean_nll'],train_wall_s=end['train_wall_s'],train_cpu_s=end['train_cpu_s']))
result=dict(status='verified_local_small_model_training',formal_runs=6,formal_optimizer_steps=3072,formal_target_bytes=3145728,formal_checkpoints=24,checks=len(checks),passed=sum(r['passed'] for r in checks),summary=summary,scope='local byte-level training only; no fitted scaling exponent, lifetime cost or large-model extrapolation')
for name,obj in [('analysis.json',result),('checks.json',checks),('evaluations.json',formal)]: (B/name).write_text(json.dumps(obj,indent=2)+'\n')
print(json.dumps(result,indent=2))
