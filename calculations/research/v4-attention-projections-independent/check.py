import hashlib
import json
import math
from pathlib import Path
import sys
import torch

HERE=Path(__file__).resolve().parent
CALC=HERE.parents[1]
PUBLIC=HERE.parent/'v4-attention-projections/public'
sys.path.insert(0,str(CALC/'src'))
from infra_calc import topics
topics.__path__.insert(0,str(PUBLIC/'src/infra_calc/topics'))
from infra_calc.topics import v4_attention_projections as m
checks=[];worst=0.
def check(name,condition):
    assert condition,name
    checks.append(name)
def close(name,got,expected):
    global worst
    a=torch.as_tensor(got,dtype=torch.float64);b=expected.detach()
    worst=max(worst,(a-b).abs().max().item())
    check(name,torch.allclose(a,b,rtol=2e-10,atol=2e-10))
for case,(B,H,D,groups) in enumerate([(2,2,6,1),(3,2,6,2),(2,4,6,2)]):
    torch.manual_seed(296+case)
    hidden,rank,orank=5,4,3
    shapes={'wq_a':(rank,hidden),'wq_b':(H*D,rank),'wkv':(D,hidden),'wo_a':(groups,orank,H*D//groups),'wo_b':(hidden,groups*orank)}
    w={k:(torch.randn(*s,dtype=torch.float64)/3).requires_grad_()for k,s in shapes.items()}
    x=torch.randn(B,hidden,dtype=torch.float64,requires_grad=True)
    qg=torch.randn(rank,dtype=torch.float64,requires_grad=True)
    kg=torch.randn(D,dtype=torch.float64,requires_grad=True)
    up=torch.randn(B,hidden,dtype=torch.float64)
    angles=[.31,-.27];eps=.004
    norm=lambda a:a*(a.square().mean(-1,keepdim=True)+eps).rsqrt()
    def rot(a,inverse=False):
        freq=torch.polar(torch.ones(2,dtype=torch.float64),torch.tensor(angles,dtype=torch.float64))
        if inverse:freq=freq.conj()
        pairs=torch.view_as_complex(a[...,-4:].contiguous().reshape(*a.shape[:-1],2,2))
        return torch.cat([a[...,:-4],torch.view_as_real(pairs*freq).flatten(-2)],-1)
    qr=norm(x@w['wq_a'].T)*qg
    q=rot(norm((qr@w['wq_b'].T).reshape(B,H,D)))
    kv=rot(norm(x@w['wkv'].T)*kg)
    # Single-key tied attention plus denominator-only sink, not a diagonal callback.
    p=torch.sigmoid((q*kv[:,None,:]).sum(-1)/math.sqrt(D)-.2)
    o=p[:,:,None]*kv[:,None,:]
    grouped=rot(o,True).reshape(B,groups,-1)
    mid=torch.einsum('bgi,gri->bgr',grouped,w['wo_a'])
    out=mid.flatten(1)@w['wo_b'].T
    (out*up).sum().backward()
    def core(q,kv):
        probs=[1/(1+math.exp(-sum(a*b for a,b in zip(row,kv))/math.sqrt(D)+.2))for row in q]
        return [[p*v for v in kv]for p in probs]
    def vjp(q,kv,g):
        probs=[1/(1+math.exp(-sum(a*b for a,b in zip(row,kv))/math.sqrt(D)+.2))for row in q]
        score=[sum(a*b for a,b in zip(row,kv))*p*(1-p)/math.sqrt(D)for row,p in zip(g,probs)]
        return [[s*v for v in kv]for s in score],[sum(probs[h]*g[h][d]+score[h]*q[h][d]for h in range(H))for d in range(D)]
    got=[m.reference(x[b].detach().tolist(),{k:v.detach().tolist()for k,v in w.items()},qg.detach().tolist(),kg.detach().tolist(),H,groups,angles,core,vjp,up[b].tolist(),eps)for b in range(B)]
    close('output '+str(case),[r['output']for r in got],out)
    close('input '+str(case),[r['dx']for r in got],x.grad)
    for key,tensor in [('dq_gamma',qg),('dkv_gamma',kg)]:
        close(key+' shared rows '+str(case),sum(torch.tensor(r[key],dtype=torch.float64)for r in got),tensor.grad)
    for key,tensor in w.items():
        close(key+' shared rows '+str(case),sum(torch.tensor(r['dweights'][key],dtype=torch.float64)for r in got),tensor.grad)

for B,T in [(1,1),(2,3),(1,129)]:
    r=m.calculate(B,T);d=r['dimensions'];R=B*T;H=d['heads'];D=d['head_dim'];Q=d['q_rank'];G=d['groups'];O=d['o_rank'];hidden=d['hidden'];RD=d['rope_dim']
    dimensions={'wq_a':(1,Q,hidden),'wq_b':(1,H*D,Q),'wkv':(1,D,hidden),'wo_a':(G,O,H*D//G),'wo_b':(1,hidden,G*O)}
    for row in r['matrices']:
        group,n,k=dimensions[row['name']]
        check(row['name']+' shape '+str(R),row['weight_shape']==[group,n,k])
        check(row['name']+' 3 matmuls '+str(R),all(row[name]==R*group*2*n*k for name in ['forward_flops','backward_dx_flops','backward_dw_flops']))
    for name,width,rows,weighted in [('weighted_q_rank',Q,R,True),('weighted_kv',D,R,True),('unweighted_q_heads',D,R*H,False)]:
        forward=width+(width-1)+1+1+width+(width if weighted else 0)
        backward=width+(width-1)+1+3*width+(2*width if weighted else 0)
        check(name+' forward '+str(R),r['norms'][name]['forward_scalar_flops']==rows*forward)
        check(name+' backward '+str(R),r['norms'][name]['backward_scalar_flops']==rows*backward+(width*(rows-1) if weighted else 0))
    check('rope pairs '+str(R),r['rope']['forward_scalar_flops']==R*(H+1+H)*(RD//2)*6==r['rope']['backward_scalar_flops'])
    expected=4*R*(hidden+Q+1+Q+H*D+H+D+1+H*D+G*O)
    check('unique saved '+str(R),r['saved_forward_boundary']['total_bytes']==expected)
    check('frequency no batch copies '+str(R),r['saved_forward_boundary']['fixed_frequency_constants_fp32_bytes']==4*T*RD)
    check('core excluded '+str(R),r['coverage']['core_work_included'] is False)

if (PUBLIC/'book.append.json').exists():
    for scene in json.loads((PUBLIC/'book.append.json').read_text()):
        r=m.calculate(**{k:v for k,v in scene.items()if k!='id'})
        f=PUBLIC/'results'/(scene['id']+'.json')
        check('replay '+scene['id'],r==m.calculate(**r['scenario'])==json.loads(f.read_text()))
        check('markdown '+scene['id'],m.markdown(r)==f.with_suffix('.md').read_text())
if (PUBLIC/'bindings.json').exists():
    binding=json.loads((PUBLIC/'bindings.json').read_text())
    for e in binding.get('artifacts',[])+binding.get('dependencies',[]):
        check('binding '+e['file'],hashlib.sha256((CALC.parent/e['file']).read_bytes()).hexdigest()==e['sha256'])
subset=json.loads((PUBLIC/'sources.lock.subset.json').read_text())['sources']
shared=json.loads((CALC/'configs/sources.lock.json').read_text())['sources']
check('54 official source records',len(subset)==54)
for entry in subset:
    raw=(CALC/entry['file']).read_bytes()
    check('source '+entry['file'],entry in shared and len(raw)==entry['bytes'] and hashlib.sha256(raw).hexdigest()==entry['sha256'])
(HERE/'results.json').write_text(json.dumps(dict(check_count=len(checks),checks=checks,max_abs_error=worst,module_sha256=hashlib.sha256(Path(m.__file__).read_bytes()).hexdigest()),indent=2)+'\n')
print(len(checks),'passed max error',worst)
