"""Execute the pinned scheduler's actual CPU float32 method, without diffusers imports."""
import ast
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
import torch

root=Path(__file__).resolve().parent
source=root/'huggingface--diffusers/src/diffusers/schedulers/scheduling_minimax_h3.py'
raw=source.read_bytes();tree=ast.parse(raw)
cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='MiniMaxH3Scheduler')
method=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='set_timesteps')
method.decorator_list=[]
module=ast.Module(body=[ast.ImportFrom(module='__future__',names=[ast.alias(name='annotations')],level=0),method],type_ignores=[])
namespace={'torch':torch};exec(compile(ast.fix_missing_locations(module),str(source),'exec'),namespace)
rows={}
for evaluations in range(1,129):
    result={}
    for name,shift in [('video',12.0),('audio',3.0)]:
        obj=SimpleNamespace(_shift=shift)
        namespace['set_timesteps'](obj,num_inference_steps=evaluations+1)
        result[name]=obj.timesteps.tolist()
        assert len(result[name])==evaluations
    rows[str(evaluations)]=result
out=dict(torch_version=torch.__version__,source_sha256=hashlib.sha256(raw).hexdigest(),
         convention='key is forward evaluations; scheduler grid points = key + 1',schedules=rows)
(root/'h3-schedules-fp32.json').write_text(json.dumps(out,indent=2)+'\n')
print('captured 128 paired actual CPU float32 schedules')
