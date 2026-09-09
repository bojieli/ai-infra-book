"""Offline PyTorch CPU AdamW reference; no DeepSpeed, GPU or NumPy required."""
import ctypes,hashlib,json
from pathlib import Path
import torch

p=Path(__file__).parent
torch.set_num_threads(4)
fixture=torch.load(p/'results/fixture.pt',map_location='cpu',weights_only=True)
parameter=torch.nn.Parameter(fixture['initial'].clone())
optimizer=torch.optim.AdamW([parameter],lr=.001,weight_decay=.01,foreach=False)
expected=json.loads((p/'tensor-evidence/checks.json').read_text())
checks=[]
for step in range(1,4):
    states=torch.load(p/f'tensor-evidence/step-{step}.pt',map_location='cpu',weights_only=True)
    for k,t in states.items():
        assert t.is_contiguous()
        h=hashlib.sha256()
        for lo in range(0,t.numel()*t.element_size(),4*1024**2):
            h.update(ctypes.string_at(t.data_ptr()+lo,min(4*1024**2,t.numel()*t.element_size()-lo)))
        assert h.hexdigest()==expected[step-1]['sha'][k]
    parameter.grad=states['gradient']
    optimizer.step()
    for key,reference in [('parameter',parameter),('moment1',optimizer.state[parameter]['exp_avg']),('moment2',optimizer.state[parameter]['exp_avg_sq'])]:
        torch.testing.assert_close(states[key],reference,atol=2e-6,rtol=1e-4)
        checks.append(dict(step=step,tensor=key,max_abs=(states[key]-reference).abs().max().item(),elements=reference.numel()))
    del states
(p/'tensor-evidence/offline-verification.json').write_text(json.dumps(dict(torch=torch.__version__,checks=checks,passed=True),indent=2))
print('All 9 full tensors match independent CPU AdamW; stored tensors match original-run SHA.')
