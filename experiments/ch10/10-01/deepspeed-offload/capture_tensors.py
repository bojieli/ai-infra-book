"""Unscored evidence replay; each state must match completed experiment SHA."""
import hashlib,json
from pathlib import Path
import torch
from deepspeed.ops.adam import DeepSpeedCPUAdam

p=Path(__file__).parent;r=p/'results';out=p/'tensor-evidence';out.mkdir(exist_ok=False)
torch.set_num_threads(4);torch.backends.cuda.matmul.allow_tf32=False
fixture=torch.load(r/'fixture.pt',map_location='cpu',weights_only=True)
rows=[json.loads(x) for x in (r/'records.jsonl').read_text().splitlines()]
master=torch.nn.Parameter(fixture['initial'].clone())
weight=torch.nn.Parameter(master.detach().to('cuda',dtype=torch.bfloat16))
opt=DeepSpeedCPUAdam([master],lr=.001,weight_decay=.01,adamw_mode=True)
def sha(t):return hashlib.sha256(t.detach().cpu().contiguous().view(torch.uint8).numpy().tobytes()).hexdigest()
checks=[]
for step,(xx,yy) in enumerate(fixture['inputs'],1):
    weight.grad=None
    loss=(torch.nn.functional.linear(xx.cuda(),weight)*yy.cuda()).float().sum()
    loss.backward();torch.cuda.synchronize()
    master.grad=weight.grad.float().cpu()
    opt.step()
    with torch.no_grad():weight.copy_(master.detach().bfloat16())
    states=dict(parameter=master.detach().clone(),gradient=master.grad.clone(),
                moment1=opt.state[master]['exp_avg'].clone(),moment2=opt.state[master]['exp_avg_sq'].clone())
    expected=next(x for x in rows if x['step']==step)
    hashes={k:sha(v) for k,v in states.items()}
    assert all(v==expected[k+'_sha'] for k,v in hashes.items()),(step,hashes)
    torch.save(states,out/f'step-{step}.pt')
    checks.append(dict(step=step,sha=hashes,all_match_formal=True))
    (out/'checks.json').write_text(json.dumps(checks,indent=2))
    del states,loss
print(json.dumps({'completed':True,'steps':3,'timings':'not_scored','checks':checks}))
