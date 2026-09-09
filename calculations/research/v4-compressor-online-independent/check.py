import hashlib,json,math,sys
from pathlib import Path
import torch
HERE=Path(__file__).resolve().parent
CALC=HERE.parents[1];P=HERE.parent/'v4-compressor-online/public'
sys.path.insert(0,str(CALC/'src'))
from infra_calc import topics
topics.__path__.insert(0,str(P/'src/infra_calc/topics'))
from infra_calc.topics import v4_compressor_online as m
checks=[];worst=0.
def check(n,c):
 assert c,n
 checks.append(n)
def close(n,a,b):
 global worst
 a=torch.as_tensor(a,dtype=torch.float64);b=b.detach();worst=max(worst,(a-b).abs().max().item())
 check(n,torch.allclose(a,b,atol=2e-9,rtol=2e-9))
for case,(ratio,S,N)in enumerate([(4,1,1),(4,3,10),(4,8,9),(128,127,3),(128,255,3)]):
 torch.manual_seed(410+case);D=4;H=3;W=D*(2 if ratio==4 else 1);slots=ratio*(2 if ratio==4 else 1)
 values=[torch.randn(*shape,dtype=torch.float64,requires_grad=True)for shape in [(slots,W),(slots,W),(N,H),(W,H),(W,H),(ratio,W),(D,)]]
 ik,isc,x,wk,wg,ape,gamma=values
 mask=torch.zeros(slots,W,dtype=torch.bool);mask[::3,::2]=True
 score=isc.masked_fill(mask,-torch.inf);kv=ik
 emits=(S+N)//ratio-S//ratio
 ang=[[.1,-.3]for _ in range(emits)];up=torch.randn(emits,D,dtype=torch.float64)
 fk=torch.randn(slots,W,dtype=torch.float64);fs=torch.randn(slots,W,dtype=torch.float64)
 args=[ik.detach().tolist(),score.detach().tolist(),x.detach().tolist(),S,ratio,wk.detach().tolist(),wg.detach().tolist(),ape.detach().tolist(),gamma.detach().tolist(),ang,up.tolist(),fk.tolist(),fs.tolist()]
 got=m.reference(*args)
 out=[]
 for step in range(N):
  pos=S+step;i=(ratio if ratio==4 else 0)+pos%ratio
  # Functional one-hot replacement gives zero derivative to old overwritten slot.
  selector=torch.nn.functional.one_hot(torch.tensor(i),slots).bool()[:,None]
  kv=torch.where(selector,(wk@x[step])[None,:],kv)
  score=torch.where(selector,(wg@x[step]+ape[pos%ratio])[None,:],score)
  if (pos+1)%ratio==0:
   vals=torch.cat([kv[:ratio,:D],kv[ratio:,D:]],0)if ratio==4 else kv
   scores=torch.cat([score[:ratio,:D],score[ratio:,D:]],0)if ratio==4 else score
   pooled=(scores.softmax(0)*vals).sum(0)
   norm=pooled*(pooled.square().mean()+1e-6).rsqrt()*gamma
   freq=torch.polar(torch.ones(2,dtype=torch.float64),torch.tensor(ang[len(out)],dtype=torch.float64))
   out.append(torch.view_as_real(torch.view_as_complex(norm.reshape(2,2))*freq).flatten())
   if ratio==4:
    gather=torch.arange(ratio,slots).repeat(2);kv=kv[gather];score=score[gather]
 loss=(kv*fk).sum()+(torch.where(torch.isfinite(score),score,torch.zeros_like(score))*fs).sum()
 if out:loss=loss+(torch.stack(out)*up).sum()
 loss.backward()
 for key,tensor in zip(['dinitial_kv','dinitial_score','dx','dwkv','dwgate','dape','dgamma'],values):
  close(str(case)+key,got[key],tensor.grad if tensor.grad is not None else torch.zeros_like(tensor))
 check(str(case)+' mask gradient zero',all(got['dinitial_score'][i][j]==0 for i in range(slots)for j in range(W)if mask[i,j]))
 close(str(case)+' finalKV',got['final_kv'],kv)

for ratio in [4,128]:
 for B,S,N in [(1,1,1),(2,ratio-1,3),(3,ratio,ratio+3)]:
  r=m.calculate(B,S,N,ratio);D=r['dimensions']['head_dim'];W=r['dimensions']['projection_width'];K=r['dimensions']['state_slots'];R=B*N;E=B*((S+N)//ratio-S//ratio)
  check(f'{ratio,B,S,N} emits',sum(e['emit']for e in r['timeline'])==E//B)
  check(f'{ratio,B,S,N} pool forward',r['scalar']['forward_pool_softmax_flops']==E*D*(K+(K-1)+K+K+(K-1)))
  check(f'{ratio,B,S,N} pool backward',r['scalar']['backward_pool_softmax_flops']==E*D*(K+K+(K-1)+2*K+K))
  multiplicities=[sum((S+i)%ratio==p for i in range(N))*B for p in range(ratio)]
  check(f'{ratio,B,S,N} APE',r['scalar']['backward_ape_reduce_flops']==W*sum(max(c-1,0)for c in multiplicities))
  check(f'{ratio,B,S,N} state copies',r['state_operations']['forward_copy_previous_kv_and_score_write_bytes']==(8*ratio*W*E if ratio==4 else 0))
  check(f'{ratio,B,S,N} saved',r['saved_forward_boundary']['total_bytes']==4*(R*r['dimensions']['hidden']+2*E*K*D+E*D+E))
  check(f'{ratio,B,S,N} replay',r==m.calculate(**r['scenario']))
  # Version identities independently emulate ownership, including both channels after copy.
  versions=['initial:'+str(i)for i in range(K)]
  for i,event in enumerate(r['timeline']):
   slot=(ratio if ratio==4 else 0)+(S+i)%ratio
   check(f'{ratio,B,S,N} overwritten {i}',event['overwritten_version']==versions[slot])
   versions[slot]='token:'+str(i)
   if event['emit']:
    expected=versions[:ratio]+versions[ratio:] if ratio==4 else versions[:]
    check(f'{ratio,B,S,N} pool ids {i}',[x['version']for x in event['pool_dependencies']]==expected)
    check(f'{ratio,B,S,N} rope {i}',event['rope_position']==S+i+1-ratio)
    if ratio==4:versions[:ratio]=versions[ratio:]
  check(f'{ratio,B,S,N} finalversions',versions==r['final_state_versions'])
for scene in json.loads((P/'book.append.json').read_text()):
 r=m.calculate(**{k:v for k,v in scene.items()if k!='id'});f=P/'results'/(scene['id']+'.json')
 check(scene['id']+' output',r==json.loads(f.read_text()))
 check(scene['id']+' md',m.markdown(r)==f.with_suffix('.md').read_text())
binding=json.loads((P/'bindings.json').read_text())
for e in binding.get('artifacts',[])+binding.get('dependencies',[]):
 check('binding '+e['file'],hashlib.sha256((CALC.parent/e['file']).read_bytes()).hexdigest()==e['sha256'])
lock=json.loads((P/'sources.lock.subset.json').read_text())['sources']
shared=json.loads((CALC/'configs/sources.lock.json').read_text())['sources']
for e in lock:
 raw=(CALC/e['file']).read_bytes()
 check('source '+e['file'],e in shared and len(raw)==e['bytes'] and hashlib.sha256(raw).hexdigest()==e['sha256'])
(HERE/'results.json').write_text(json.dumps(dict(check_count=len(checks),max_abs_error=worst,checks=checks,module_sha256=hashlib.sha256(Path(m.__file__).read_bytes()).hexdigest()),indent=2)+'\n')
print(len(checks),'passed max error',worst)
