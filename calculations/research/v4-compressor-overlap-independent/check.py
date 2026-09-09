"""Independent tensor overlap graph including state-output losses."""
from pathlib import Path
import sys,json,hashlib,unittest
import torch
ROOT=Path(__file__).resolve().parents[3];BASE=ROOT/'calculations/research/v4-compressor-overlap/public'
sys.path.insert(0,str(ROOT/'calculations/src'))
import infra_calc.topics
infra_calc.topics.__path__.insert(0,str(BASE/'src/infra_calc/topics'))
from infra_calc.topics import v4_compressor_overlap as m
checks=0;errors=[]
def check(ok,label):
 global checks
 checks+=1
 if not ok:raise AssertionError(label)
def close(a,b,label):
 err=(torch.as_tensor(a,dtype=torch.float64)-b.detach()).abs().max().item();errors.append(err);check(err<1e-10,label)
torch.manual_seed(203)
for B,T in [(2,1),(3,3),(2,4),(2,7),(3,8),(2,11),(2,13)]:
 H,D=3,4;C=T//4;tail=T%4
 vals=[(torch.randn(s,dtype=torch.float64)*.2).requires_grad_() for s in [(B,T,H),(2*D,H),(2*D,H),(4,2*D),(D,)]]
 x,wk,wg,ape,gamma=vals
 k=x@wk.T;s=x@wg.T+ape[torch.arange(T)%4]
 ang=torch.randn(C,2,dtype=torch.float64)*.3;up=torch.randn(B,C,D,dtype=torch.float64)
 uk=torch.randn(B,8,2*D,dtype=torch.float64);us=torch.randn(B,8,2*D,dtype=torch.float64)
 outputs=[];loss=x.sum()*0+gamma.sum()*0
 for c in range(C):
  current_k=k[:,4*c:4*c+4,D:];current_s=s[:,4*c:4*c+4,D:]
  if c:
   prev_k=k[:,4*c-4:4*c,:D];prev_s=s[:,4*c-4:4*c,:D]
  else:
   prev_k=torch.zeros_like(current_k);prev_s=torch.full_like(current_s,-torch.inf)
  pool=(torch.cat((prev_k,current_k),1)*torch.cat((prev_s,current_s),1).softmax(1)).sum(1)
  norm=pool*torch.rsqrt(pool.square().mean(-1,keepdim=True)+1e-6)*gamma
  z=torch.view_as_complex(norm.reshape(B,2,2).contiguous())*torch.polar(torch.ones_like(ang[c]),ang[c])
  out=torch.view_as_real(z).flatten(-2);outputs.append(out);loss=loss+(out*up[:,c]).sum()
 writes=([(i,4*(C-1)+i) for i in range(4)] if C else [])+[(4+i,4*C+i) for i in range(tail)]
 for slot,t in writes:loss=loss+(k[:,t]*uk[:,slot]).sum()+(s[:,t]*us[:,slot]).sum()
 loss.backward()
 refs=[m.reference(x[b].tolist(),wk.tolist(),wg.tolist(),ape.tolist(),gamma.tolist(),ang.tolist(),up[b].tolist(),uk[b].tolist(),us[b].tolist()) for b in range(B)]
 if C:close([a['output'] for a in refs],torch.stack(outputs,1),'outputs')
 close([a['dx'] for a in refs],x.grad,'dx')
 for name,v in [('dwkv',wk),('dwgate',wg),('dape',ape),('dgamma',gamma)]:close(sum(torch.tensor(a[name],dtype=torch.float64) for a in refs),v.grad if v.grad is not None else torch.zeros_like(v),'shared '+name)
 for slot,t in writes:
  close([a['state_kv'][slot] for a in refs],k[:,t],'state K')
  close([a['state_score'][slot] for a in refs],s[:,t],'state score')
for B in [1,2,3]:
 for T in [1,3,4,5,8,9,16,17]:
  out=m.calculate(batch=B,tokens=T);d=out['dimensions'];H=d['hidden'];D=d['head_dim'];C=T//4
  hits=[0]*4
  for b in range(B):
   for t in range(T):hits[t%4]+=1
  check(out['scalar']['backward_ape_reduce_flops']==2*D*sum(max(n-1,0) for n in hits),'APE occurrence reduce')
  valid=sum(4 if c==0 else 8 for c in range(C))
  check(out['scalar']['backward_compressed_gradient_scatter_add_flops']==2*B*valid*D,'valid scatter')
  check(out['scalar']['backward_returned_state_scatter_add_flops']==4*B*((4 if C else 0)+T%4)*D,'state scatter')
  check(out['totals']['forward_matrix_flops']==2*(2*B*T*H*(2*D)),'matrix')
  check(out['coverage']['arbitrary_restored_state_vjp'] is False,'scope')
  check(out['declared_source_difference']['source_extra_forward_ape_additions_for_last_complete_state']==(B*4*2*D if C else 0),'source duplicated APE')
lock=json.loads((ROOT/'calculations/configs/sources.lock.json').read_text())['sources']
for row in json.loads((BASE/'sources.lock.subset.json').read_text())['sources']:
 check(row in lock,'source membership');data=(ROOT/'calculations'/row['file']).read_bytes();check(len(data)==row['bytes'] and hashlib.sha256(data).hexdigest()==row['sha256'],'source hash')
for rows in json.loads((BASE/'bindings.json').read_text()).values():
 if isinstance(rows,list):
  for row in rows:
   if isinstance(row,dict) and 'file' in row and 'sha256' in row:check(hashlib.sha256((ROOT/row['file']).read_bytes()).hexdigest()==row['sha256'],'binding')
for scene in json.loads((BASE/'book.append.json').read_text()):
 out=m.calculate(**{k:v for k,v in scene.items() if k!='id'});check(out==json.loads((BASE/'results'/(scene['id']+'.json')).read_text()),'JSON');check(m.markdown(out)==(BASE/'results'/(scene['id']+'.md')).read_text(),'MD')
r=unittest.TextTestRunner().run(unittest.defaultTestLoader.discover(str(BASE/'tests')));check(r.wasSuccessful() and not r.skipped,'author tests')
summary={'checks':checks,'max_error':max(errors),'author_tests':r.testsRun,'skipped':len(r.skipped),'module_sha256':hashlib.sha256(Path(m.__file__).read_bytes()).hexdigest()}
(Path(__file__).parent/'results.json').write_text(json.dumps(summary,indent=2)+'\n');print(summary)
