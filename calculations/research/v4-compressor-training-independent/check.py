"""Independent batched tensor oracle and accounting reconstruction."""
from pathlib import Path
import sys,json,hashlib,unittest
import torch
ROOT=Path(__file__).resolve().parents[3]
BASE=ROOT/'calculations/research/v4-compressor-training/public'
sys.path.insert(0,str(ROOT/'calculations/src'))
import infra_calc.topics
infra_calc.topics.__path__.insert(0,str(BASE/'src/infra_calc/topics'))
from infra_calc.topics import v4_compressor_training as m
checks=0; errors=[]
def check(ok,label):
 global checks
 checks+=1
 if not ok: raise AssertionError(label)
def close(a,b,label):
 err=(torch.as_tensor(a,dtype=torch.float64)-b.detach()).abs().max().item()
 errors.append(err);check(err<1e-10,label)
torch.manual_seed(829)
for B,C,R,H,D in [(2,3,128,3,4),(3,2,2,4,6),(2,1,128,2,4)]:
 T=C*R
 shapes=[(B,T,H),(D,H),(D,H),(R,D),(D,)]
 vals=[(torch.randn(shape,dtype=torch.float64)*.25).requires_grad_() for shape in shapes]
 x,wk,wg,ape,gamma=vals
 angles=torch.randn(C,2,dtype=torch.float64)*.4
 up=torch.randn(B,C,D,dtype=torch.float64)
 kv=(x@wk.T).reshape(B,C,R,D)
 score=(x@wg.T).reshape(B,C,R,D)+ape
 prob=score.softmax(dim=2)
 pool=(prob*kv).sum(dim=2)
 norm=pool*torch.rsqrt(pool.square().mean(dim=-1,keepdim=True)+1e-6)*gamma
 z=torch.view_as_complex(norm[...,-4:].contiguous().reshape(B,C,2,2))
 z=z*torch.polar(torch.ones_like(angles),angles)
 y=torch.cat((norm[...,:-4],torch.view_as_real(z).flatten(-2)),dim=-1)
 (y*up).sum().backward()
 refs=[m.reference(x[b].tolist(),wk.tolist(),wg.tolist(),ape.tolist(),gamma.tolist(),angles.tolist(),up[b].tolist(),ratio=R) for b in range(B)]
 close([a['output'] for a in refs],y,'batched forward')
 close([a['dx'] for a in refs],x.grad,'batched input gradient')
 for key,v in [('dwkv',wk),('dwgate',wg),('dape',ape),('dgamma',gamma)]:
  close(sum(torch.tensor(a[key],dtype=torch.float64) for a in refs),v.grad,'shared '+key)
for B,T in [(1,128),(2,256),(3,384),(1,1024)]:
 d=m.calculate(batch=B,tokens=T);g=d['dimensions'];H=g['hidden'];D=g['head_dim'];RD=g['rope_dim'];C=B*T//128;N=B*T
 # Independently enumerate block-feature work, retaining n-1 reductions.
 f=b=0
 for block in range(C):
  for feature in range(D):
   f+=128+128+127+128+128+127
   b+=128+128+128+127+128+128
 check(f==d['scalar']['forward_ape_softmax_pool_flops'],'forward scalar')
 check(b==d['scalar']['backward_pool_softmax_flops'],'backward scalar')
 check(d['scalar']['backward_ape_reduce_flops']==128*D*(C-1),'APE across batch blocks')
 check(d['totals']['forward_matrix_flops']==sum(2*N*H*D for _ in range(2)),'two projections')
 check(d['totals']['backward_matrix_flops']==sum(2*N*H*D for _ in range(4)),'four adjoints')
 check(d['saved_forward_boundary']['total_bytes']==4*(N*H+2*N*D+C*D+C),'saved unique')
 check(d['execution']['rope_positions']==list(range(0,T,128)),'block start positions')
 check(d['coverage']['cast_surrogate_gradient'] is None,'no invented STE')
for t in [1,127,129,255,257]:
 try:m.calculate(tokens=t)
 except ValueError:check(True,'reject tail')
 else:check(False,'reject tail')
lock=json.loads((ROOT/'calculations/configs/sources.lock.json').read_text())['sources']
for row in json.loads((BASE/'sources.lock.subset.json').read_text())['sources']:
 check(row in lock,'source membership')
 data=(ROOT/'calculations'/row['file']).read_bytes()
 check(len(data)==row['bytes'] and hashlib.sha256(data).hexdigest()==row['sha256'],'source content')
for scene in json.loads((BASE/'book.append.json').read_text()):
 out=m.calculate(**{k:v for k,v in scene.items() if k!='id'})
 check(out==json.loads((BASE/'results'/(scene['id']+'.json')).read_text()),'frozen JSON replay')
 check(m.markdown(out)==(BASE/'results'/(scene['id']+'.md')).read_text(),'frozen MD replay')
result=unittest.TextTestRunner(verbosity=1).run(unittest.defaultTestLoader.discover(str(BASE/'tests')))
check(result.wasSuccessful() and not result.skipped,'author tests all execute')
summary={'checks':checks,'max_gradient_or_forward_error':max(errors),'author_tests':result.testsRun,'skipped':len(result.skipped),'module_sha256':hashlib.sha256(Path(m.__file__).read_bytes()).hexdigest(),'scope':'unrounded ratio128 complete blocks only'}
(Path(__file__).parent/'results.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps(summary,indent=2))
