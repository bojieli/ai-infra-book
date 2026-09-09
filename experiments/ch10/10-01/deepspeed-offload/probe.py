import json
import torch
import deepspeed
from deepspeed.ops.adam import DeepSpeedCPUAdam

torch.set_num_threads(4)
p = torch.nn.Parameter(torch.linspace(-1, 1, 1024))
reference = torch.nn.Parameter(p.detach().clone())
optimizer = DeepSpeedCPUAdam([p], lr=.001, weight_decay=.01, adamw_mode=True)
baseline = torch.optim.AdamW([reference], lr=.001, weight_decay=.01, foreach=False)
checks = []
for step in range(3):
    gradient = torch.linspace(-.25, .25, 1024) + step * .01
    p.grad = gradient.clone()
    reference.grad = gradient.clone()
    optimizer.step()
    baseline.step()
    checks.append({'step':step+1, 'max_abs':(p-reference).abs().max().item()})
    torch.testing.assert_close(p, reference, atol=2e-6, rtol=1e-4)
    for name in ['exp_avg', 'exp_avg_sq']:
        torch.testing.assert_close(optimizer.state[p][name], baseline.state[reference][name], atol=2e-6, rtol=1e-4)
print(json.dumps({'torch':torch.__version__, 'deepspeed':deepspeed.__version__, 'checks':checks, 'passed':True}))
