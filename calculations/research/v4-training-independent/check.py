"""Independent batched, coupled-inner VJP and primitive accounting review."""
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import sys
import torch

HERE = Path(__file__).resolve().parent
CALC = HERE.parents[1]
sys.path.insert(0, str(CALC / 'src'))

def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

primitive_path = HERE.parent / 'v4-training-reference/src/infra_calc/topics/v4_training_primitives.py'
hc_path = HERE.parent / 'v4-hc-training-completion/src/v4_hc_training.py'
p = load('review_primitive', primitive_path)
m = load('review_hc', hc_path)
checks = []
max_error = 0.

def check(name, value):
    assert value, name
    checks.append(name)

def close(name, actual, expected):
    global max_error
    a = torch.as_tensor(actual, dtype=torch.float64)
    b = torch.as_tensor(expected, dtype=torch.float64).detach()
    max_error = max(max_error, (a-b).abs().max().item())
    check(name, torch.allclose(a, b, rtol=2e-9, atol=2e-9))

# A dense nonlinear inner function ensures dy cannot accidentally be dz times a diagonal.
for case, (c, h, iters, batch, eps) in enumerate([(2,3,1,2,.02),(2,4,2,3,.1),(4,3,20,2,1e-6),(4,2,20,3,.03)]):
    torch.manual_seed(962+case)
    v = c*(c+2)
    x = torch.randn(batch,c,h,dtype=torch.float64,requires_grad=True)
    w = (torch.randn(v,c*h,dtype=torch.float64)/4).requires_grad_()
    base = (torch.randn(v,dtype=torch.float64)/3).requires_grad_()
    scale = torch.tensor([.6,-.4,1.1],dtype=torch.float64,requires_grad=True)
    inner_w = torch.randn(h,h,dtype=torch.float64)/3
    upstream = torch.randn(batch,c,h,dtype=torch.float64)
    flat = x.flatten(1)
    mixes = (flat @ w.T)*(flat.square().mean(-1,keepdim=True)+.005).rsqrt()
    pre = torch.sigmoid(mixes[:,:c]*scale[0]+base[:c])+eps
    post = 2*torch.sigmoid(mixes[:,c:2*c]*scale[1]+base[c:2*c])
    comb = (mixes[:,2*c:]*scale[2]+base[2*c:]).reshape(batch,c,c).softmax(-1)+eps
    comb = comb/(comb.sum(-2,keepdim=True)+eps)
    for _ in range(iters-1):
        comb = comb/(comb.sum(-1,keepdim=True)+eps)
        comb = comb/(comb.sum(-2,keepdim=True)+eps)
    y = torch.einsum('bi,bih->bh',pre,x)
    z = torch.tanh(y @ inner_w.T)
    out = torch.einsum('bj,bh->bjh',post,z)+torch.einsum('bij,bih->bjh',comb,x)
    (out*upstream).sum().backward()
    weights = inner_w.tolist()
    def inner(y):
        return [math.tanh(sum(a*b for a,b in zip(row,y))) for row in weights]
    def inner_vjp(y,g):
        values = inner(y)
        return [sum(g[j]*(1-values[j]**2)*weights[j][k] for j in range(h)) for k in range(h)]
    got = [m.vjp(x[b].detach().tolist(),w.detach().tolist(),scale.detach().tolist(),base.detach().tolist(),inner,inner_vjp,upstream[b].tolist(),iters,eps,.005) for b in range(batch)]
    close(f'joint dx {case}',[r['dx'] for r in got],x.grad)
    close(f'joint output {case}',[r['output'] for r in got],out)
    for key, ref in [('dweight',w.grad),('dbase',base.grad),('dscale',scale.grad)]:
        close(f'batch shared {key} {case}',sum(torch.tensor(r[key],dtype=torch.float64) for r in got),ref)
    check(f'eps not exact stochastic {case}',not torch.allclose(comb.sum(-2),torch.ones(batch,c,dtype=torch.float64),rtol=0,atol=eps/10))

# Count reductions as k-1 additions independently of helper implementation.
for batch,tokens in [(1,1),(1,7),(2,3),(3,19)]:
    a=p.calculate(batch,tokens);b=m.calculate(batch,tokens)
    R=batch*tokens;L=43;c=4;E=256;k=6;V=c*(c+2);Q=2*L;norms=1+2*19
    fwd_affine=2*V
    fwd_pre_post=c+c
    fwd_softmax=c*(c+(c-1)+c+c)
    fwd_norm=norms*c*((c-1)+1+c)
    check(f'split forward {R}',a['sinkhorn_split']['forward_scalar_flops']==Q*R*(fwd_affine+fwd_pre_post+fwd_softmax+fwd_norm))
    vjp_norm=norms*c*(c+(c-1)+c+c)
    vjp_softmax=c*(c+(c-1)+c+c)
    vjp_sigmoid=3*c+4*c
    vjp_mixes=V
    scale_grad=R*V+(R*c-1)+(R*c-1)+(R*c*c-1)
    base_grad=V*(R-1)
    check(f'split backward {R}',a['sinkhorn_split']['backward_scalar_flops']==Q*(R*(vjp_norm+vjp_softmax+vjp_sigmoid+vjp_mixes)+scale_grad+base_grad))
    router_forward=L*R*((k-1)+k+k)+(L-3)*R*E
    router_backward=L*R*(k+k+(k-1)+k+k+3*E)
    check(f'router forward {R}',a['router']['forward_scalar_flops']==router_forward)
    check(f'router backward {R}',a['router']['backward_scalar_flops']==router_backward)
    d=b['dimensions'];n=d['flat'];H=d['hidden']
    forward_rms=n+(n-1)+1+1
    post_scalar=n+n
    check(f'outer forward {R}',b['outer_forward_scalar_flops']==Q*R*(forward_rms+V+post_scalar))
    backward_mix=V+V+(V-1)
    backward_rms=3+1+n
    backward_pre=n
    joins=3*n
    check(f'outer backward {R}',b['outer_backward_scalar_flops']==Q*R*(backward_mix+backward_rms+backward_pre+joins))
    check(f'inner counted zero {R}',b['totals']['backward_scalar_flops']==b['outer_backward_scalar_flops']+a['sinkhorn_split']['backward_scalar_flops'])
    # Unique saved scalar identities, not sum of distinct names for one tensor.
    split_elements=2*c+c*c+norms*(c*c+c)
    expected=4*R*(n+1+V+V+c+c+H+split_elements)
    saved=b['saved_forward_boundary']
    check(f'saved per sublayer {R}',saved['per_sublayer_bytes']==expected)
    check(f'saved all independent layers {R}',saved['all_sublayers_no_recompute_saved_subset_bytes']==Q*expected)
    check(f'39 normalizations {R}',a['sinkhorn_split']['normalizations_per_occurrence']==39)

# Hash fixed IDs must retain selected score gradient, including denominator cross terms.
for ids in [[0,3],[1,2]]:
    z=torch.tensor([.2,-.5,.9,1.2],dtype=torch.float64,requires_grad=True)
    s=z.softplus() if hasattr(z,'softplus') else torch.nn.functional.softplus(z)
    s=s.sqrt();weights=1.5*s[ids]/s[ids].sum()
    (weights*torch.tensor([.8,-.3],dtype=torch.float64)).sum().backward()
    out,grad=p.router_vjp(z.detach().tolist(),ids,[.8,-.3])
    close('hash scores '+str(ids),grad,z.grad)
    check('inactive logits '+str(ids),all(grad[i]==0 for i in range(4) if i not in ids))

# Frozen artifacts and official dependency bytes must agree, then replay JSON.
for directory,module in [('v4-training-reference',p),('v4-hc-training-completion',m)]:
    folder=HERE.parent/directory
    binding=json.loads((folder/'bindings.json').read_text())
    for entry in binding.get('artifacts',[])+binding.get('dependencies',[]):
        path=CALC.parent/entry['file']
        check('binding '+entry['file'],hashlib.sha256(path.read_bytes()).hexdigest()==entry['sha256'])
    for artifact in (folder/'results').glob('*.json'):
        expected=json.loads(artifact.read_text())
        check('replay '+str(artifact.relative_to(HERE.parent)),module.calculate(**expected['scenario'])==expected)

result=dict(check_count=len(checks),checks=checks,max_abs_error=max_error,files=[dict(file=str(path.relative_to(CALC)),sha256=hashlib.sha256(path.read_bytes()).hexdigest()) for path in [primitive_path,hc_path,CALC/'sources/deepseek-v4-flash/inference/model.py',CALC/'sources/deepseek-v4-flash/inference/kernel.py']])
(HERE/'results.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
