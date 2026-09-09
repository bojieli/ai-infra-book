import ast
import hashlib
import json
from pathlib import Path
import torch
import torch.nn.functional as F

HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[1]
source=PROJECT/'sources/flash-linear-attention/fla/ops/kda/gate.py'
node=next(n for n in ast.parse(source.read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='naive_kda_lowerbound_gate')
namespace={'torch':torch,'F':F}
exec(compile(ast.Module(body=[node],type_ignores=[]),str(source),'exec'),namespace)
fn=namespace[node.name]
g=torch.zeros(1,1,96,128)
bias=torch.zeros(96*128)
checks=[]
for length in (96,128):
 try:
  result=fn(g,torch.zeros(length),bias)
  checks.append(dict(a_log_length=length,supported=True,output_shape=list(result.shape)))
 except RuntimeError as exc:
  checks.append(dict(a_log_length=length,supported=False,error=str(exc)))
assert checks[0]['supported'] and not checks[1]['supported']
# Illustrates ordinary parameter shape loading, not a whole HuggingFace checkpoint load.
module=torch.nn.Module()
module.register_parameter('A_log',torch.nn.Parameter(torch.empty(96)))
try:
 module.load_state_dict({'A_log':torch.zeros(128)},strict=False)
 raise AssertionError('shape mismatch unexpectedly accepted')
except RuntimeError as exc:
 loader_error=str(exc)
result=dict(torch_version=torch.__version__,source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),official_reference_function=node.name,synthetic_zero_values=True,gate_probes=checks,ordinary_parameter_loader_strict_false_error=loader_error,scope='CPU shape-contract probe only; no official payload values, K3 loader or GPU fused kernel execution tested')
(HERE/'reference-probe.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
