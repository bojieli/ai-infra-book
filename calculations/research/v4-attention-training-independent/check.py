import hashlib
import json
import math
from pathlib import Path
import sys
import torch

HERE=Path(__file__).resolve().parent
CALC=HERE.parents[1]
PUBLIC=HERE.parent/'v4-attention-training/public'
sys.path.insert(0,str(CALC/'src'))
from infra_calc import topics
topics.__path__.insert(0,str(PUBLIC/'src/infra_calc/topics'))
from infra_calc.topics import v4_attention_training as m
checks=[];worst=0.
def check(name,condition):
    assert condition,name
    checks.append(name)
def close(name,got,expected):
    global worst
    a=torch.as_tensor(got,dtype=torch.float64);b=expected.detach()
    worst=max(worst,(a-b).abs().max().item())
    check(name,torch.allclose(a,b,rtol=1e-11,atol=1e-11))
for case,(B,T,H,D,K,ids) in enumerate([
 (3,2,2,3,4,[[0,-1,0,1],[3,0,-1,3]]),
 (2,3,3,5,5,[[2,2,-1,2],[0,4,3,-1],[1,2,3,4]]),
 (2,1,1,1,1,[[0,0,0]]),
 (3,2,2,4,3,[[1,-1,-1,-1],[2,0,2,0]])]):
    torch.manual_seed(174+case)
    q=torch.randn(B,T,H,D,dtype=torch.float64,requires_grad=True)
    kv=torch.randn(B,K,D,dtype=torch.float64,requires_grad=True)
    sink=torch.randn(H,dtype=torch.float64,requires_grad=True)
    g=torch.randn(B,T,H,D,dtype=torch.float64)
    # A single padded batched gather preserves duplicate slots, masking only -1.
    index=torch.tensor(ids); mask=index!=-1
    gathered=kv[:,index.clamp_min(0)]
    logits=torch.einsum('bthd,btjd->bthj',q,gathered)/math.sqrt(D)
    logits=logits.masked_fill(~mask[None,:,None,:],-torch.inf)
    probability=torch.cat([logits,sink[None,None,:,None].expand(B,T,H,1)],-1).softmax(-1)
    out=torch.einsum('bthj,btjd->bthd',probability[...,:-1],gathered)
    (out*g).sum().backward()
    actual=[m.reference(q[b].detach().tolist(),kv[b].detach().tolist(),sink.detach().tolist(),ids,g[b].tolist())for b in range(B)]
    close('output '+str(case),[r['output'] for r in actual],out)
    close('Q VJP '+str(case),[r['dq'] for r in actual],q.grad)
    close('tied KV VJP '+str(case),[r['dkv'] for r in actual],kv.grad)
    close('shared sink batch sum '+str(case),sum(torch.tensor(r['dsink'],dtype=torch.float64)for r in actual),sink.grad)
    ledger=m.calculate(B,T,K,H,D,ids)
    per_forward=[];per_backward=[]
    for row in ids:
        v=sum(i!=-1 for i in row)
        per_forward.append(v+(v+1)+v+(v+1))
        per_backward.append((v+v-1)+2*v+1+v)
    A=B*H*sum(sum(i!=-1 for i in row)for row in ids)
    check('forward scalar '+str(case),ledger['totals']['forward_scalar_flops']==B*H*sum(per_forward))
    check('backward scalar '+str(case),ledger['totals']['backward_scalar_flops']==B*H*sum(per_backward)+A*D+A*D+H*(B*T-1))
    check('six contractions '+str(case),len(ledger['matrices'])==6 and all(r['flops']==2*A*D for r in ledger['matrices']))
    check('shared KV single identity '+str(case),ledger['saved_forward_boundary']['buffers']['kv_fp32_shared_key_value']==4*B*K*D)
    check('scatter bytes '+str(case),ledger['reference_data_ops']['dkv_scatter_write_bytes']==4*A*D and ledger['reference_data_ops']['dkv_zero_initialization_bytes']==4*B*K*D)
    check('no source quantization equivalence '+str(case),ledger['coverage']['quantized_kernel_value_equivalence'] is False and ledger['dtype_contract']['cast_surrogate_gradient'] is None)

for scene in json.loads((PUBLIC/'book.append.json').read_text()):
    r=m.calculate(**{k:v for k,v in scene.items()if k!='id'})
    check(scene['id']+' replay',r==m.calculate(**r['scenario']))
    file=PUBLIC/'results'/(scene['id']+'.json')
    check(scene['id']+' frozen',r==json.loads(file.read_text()))
    check(scene['id']+' MD',m.markdown(r)==file.with_suffix('.md').read_text())
# Independent closed prefix/window length sum checks (128 window, not square T²).
for T in [1,127,128,129,257]:
    r=m.calculate(tokens=T)
    slots=T*(T+1)//2 if T<=128 else 128*129//2+(T-128)*128
    check('window edges '+str(T),r['schedule']['valid_head_slots']==r['scenario']['heads']*slots)
lock=json.loads((PUBLIC/'sources.lock.subset.json').read_text())['sources']
shared=json.loads((CALC/'configs/sources.lock.json').read_text())['sources']
for row in lock:
    raw=(CALC/row['file']).read_bytes()
    check('source '+row['file'],row in shared and len(raw)==row['bytes'] and hashlib.sha256(raw).hexdigest()==row['sha256'])
binding=json.loads((PUBLIC/'bindings.json').read_text())
for entry in binding.get('artifacts',[])+binding.get('dependencies',[]):
    check('binding '+entry['file'],hashlib.sha256((CALC.parent/entry['file']).read_bytes()).hexdigest()==entry['sha256'])
(HERE/'results.json').write_text(json.dumps(dict(check_count=len(checks),checks=checks,max_abs_gradient_error=worst,module_sha256=hashlib.sha256(Path(m.__file__).read_bytes()).hexdigest()),indent=2)+'\n')
print(len(checks),'checks passed; max error',worst)
