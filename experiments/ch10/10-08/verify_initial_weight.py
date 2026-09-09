"""CPU-only independent hash of the frozen public model tensor; no training."""
import hashlib,json,os,pathlib,time
from safetensors import safe_open
import torch
start=time.monotonic();root=pathlib.Path(os.environ['VERLRL_ROOT']);model=pathlib.Path(os.environ['VERLRL_PRIVATE'])/'model/model.safetensors'
with safe_open(str(model),framework='pt',device='cpu') as f:
 tensor=f.get_tensor('model.embed_tokens.weight');h=hashlib.sha256()
 for part in tensor.reshape(-1).split(262144):h.update(part.to(torch.bfloat16).contiguous().view(torch.uint8).numpy().tobytes())
 result=dict(model_revision='7ae557604adf67be50417f59c2c2f167def9a775',parameter='model.embed_tokens.weight',shape=list(tensor.shape),source_dtype=str(tensor.dtype),hash_dtype='torch.bfloat16',bf16_sha256=h.hexdigest(),cpu_only=True,elapsed_s=time.monotonic()-start)
(root/'initial-weight-independent.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
