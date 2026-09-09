class CaptureWorker:
 def install_capture(self,output):
  import torch,hashlib
  from pathlib import Path
  from vllm.model_executor.layers.activation import SiluAndMul
  out=Path(output);out.mkdir(parents=True,exist_ok=False);self.capture_records=[]
  layers=[(name,mod) for name,mod in self.model_runner.model.named_modules() if isinstance(mod,SiluAndMul)]
  assert len(layers)==36
  for index,(name,mod) in enumerate(layers):
   original=mod._forward_method
   def make(orig,idx,label):
    def wrapped(x):
     y=orig(x)
     item=dict(layer=idx,name=label,input_shape=list(x.shape),input_stride=list(x.stride()),input_dtype=str(x.dtype),output_shape=list(y.shape),output_dtype=str(y.dtype))
     if idx==0:
      cpu_x=x.detach().cpu();cpu_y=y.detach().cpu();file=out/f'layer0-call{len([r for r in self.capture_records if r["layer"]==0])}.pt'
      torch.save(dict(input=cpu_x,reference=cpu_y),file)
      item.update(file=str(file),file_sha256=hashlib.sha256(file.read_bytes()).hexdigest(),input_sha256=hashlib.sha256(cpu_x.view(torch.uint8).numpy().tobytes()).hexdigest())
     self.capture_records.append(item);return y
    return wrapped
   mod._forward_method=make(original,index,name)
  return dict(layers=len(layers))
 def capture_snapshot(self):return self.capture_records
