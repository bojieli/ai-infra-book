import argparse,hashlib,json,math,platform,random,time
from pathlib import Path
R=Path(__file__).resolve().parent

def main(out,smoke):
 import torch
 out.mkdir(exist_ok=False);torch.manual_seed(402);torch.backends.cuda.matmul.allow_tf32=False
 env=dict(torch=torch.__version__,device=torch.cuda.get_device_name(),capability=torch.cuda.get_device_capability(),platform=platform.platform(),source_sha256=hashlib.sha256((R/'run.py').read_bytes()).hexdigest(),smoke=smoke)
 (out/'environment.json').write_text(json.dumps(env,indent=2))
 k,n=2048,768;w=torch.randn(k,n,device='cuda',dtype=torch.float32)/math.sqrt(k);sw=w.abs().amax(0).clamp_min(1e-12)/127;qw=(w/sw).round().clamp(-127,127).to(torch.int8).contiguous();torch.cuda.synchronize()
 def quant(x):
  sx=x.abs().amax(1,keepdim=True).clamp_min(1e-12)/127;q=(x/sx).round().clamp(-127,127).to(torch.int8)
  pad=max(32,((q.shape[0]+7)//8)*8)-q.shape[0]
  if pad:q=torch.nn.functional.pad(q,(0,0,0,pad))
  return q,sx
 def direct(x):
  q,sx=quant(x);z=torch._int_mm(q,qw)[:x.shape[0]];return z.float()*sx*sw
 def dequant(x):
  q,sx=quant(x);a=(q[:x.shape[0]].float()*sx).to(torch.bfloat16);b=(qw.float()*sw).to(torch.bfloat16);return (a@b).float()
 def timing(fn,repeats):
  torch.cuda.synchronize()
  start=torch.cuda.Event(enable_timing=True);end=torch.cuda.Event(enable_timing=True);wall=time.perf_counter();start.record()
  for _ in range(repeats):y=fn()
  end.record();end.synchronize();return dict(device_ms=start.elapsed_time(end)/repeats,wall_ms=(time.perf_counter()-wall)*1000/repeats)
 rows=[]
 for m in ([1,8] if smoke else [1,8,64,512]):
  x=torch.randn(m,k,device='cuda');q,sx=quant(x);reference=x@w;integer_ref=(q.double()@qw.double()).to(torch.int32);native=torch._int_mm(q,qw)
  torch.save(dict(x=x.cpu(),w=w.cpu(),qw=qw.cpu(),sw=sw.cpu(),reference=reference.cpu()),out/f'fixture-m{m}.pt')
  integer_check=dict(exact=torch.equal(native,integer_ref),max_abs_difference=int((native.to(torch.int64)-integer_ref.to(torch.int64)).abs().max()))
  (out/f'integer-check-m{m}.json').write_text(json.dumps(integer_check))
  assert integer_check['exact'],integer_check
  checks={}
  for name,fn in [('int8_direct',direct),('int8_dequant_bf16',dequant)]:
   y=fn(x);error=float(torch.linalg.vector_norm(y-reference)/torch.linalg.vector_norm(reference))
   checks[name]=dict(relative_l2_to_original_fp32=error,max_abs_error=float((y-reference).abs().max()),output_sha256=hashlib.sha256(y.cpu().contiguous().numpy().tobytes()).hexdigest(),passed=error<=.02)
   (out/f'quality-m{m}.json').write_text(json.dumps(checks,indent=2))
   torch.save(y.cpu(),out/f'output-m{m}-{name}.pt')
   assert error<=.02,(name,m,error)
  torch.cuda.synchronize()
  decoded_a=(q[:m].float()*sx).to(torch.bfloat16);decoded_w=(qw.float()*sw).to(torch.bfloat16)
  funcs={'int8_direct_e2e':lambda:direct(x),'int8_dequant_bf16_e2e':lambda:dequant(x),'activation_quant_pad':lambda:quant(x),'weight_dequant_bf16':lambda:(qw.float()*sw).to(torch.bfloat16),'int8_matmul_only':lambda:torch._int_mm(q,qw),'bf16_matmul_only':lambda:decoded_a@decoded_w}
  for fn in funcs.values():
   for _ in range(3):fn()
  order=[(trial,name) for trial in range(1 if smoke else 9) for name in funcs];random.Random(402+m).shuffle(order)
  samples=[]
  for trial,name in order:samples.append(dict(trial=trial,stage=name,**timing(funcs[name],1 if smoke else 20)))
  if not smoke:
   with torch.profiler.profile(activities=[torch.profiler.ProfilerActivity.CPU,torch.profiler.ProfilerActivity.CUDA],record_shapes=True) as prof:
    for name,fn in [('int8_direct_e2e',direct),('int8_dequant_bf16_e2e',dequant)]:
     with torch.profiler.record_function(name):fn(x);torch.cuda.synchronize()
   prof.export_chrome_trace(str(out/f'trace-m{m}.json'))
  rows.append(dict(m=m,k=k,n=n,padded_m=q.shape[0],checks=checks,integer_exact=True,storage_bytes=dict(quantized_weight=qw.numel()*qw.element_size(),weight_scale=sw.numel()*sw.element_size(),decoded_weight=decoded_w.numel()*decoded_w.element_size(),activation_scale=sx.numel()*sx.element_size(),quantized_padded_activation=q.numel()*q.element_size(),int32_padded_output=q.shape[0]*n*4),samples=samples))
  (out/'raw.json').write_text(json.dumps(rows,indent=2));print('completed',m,checks,flush=True)
 (out/'completion.json').write_text(json.dumps(dict(done=True,shapes=len(rows)))+'\n')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--smoke',action='store_true');a=p.parse_args();existed=a.output.exists()
 try:main(a.output,a.smoke)
 except Exception as e:
  if not existed and a.output.exists():(a.output/'failure.json').write_text(json.dumps(dict(error_type=type(e).__name__,error=str(e)))+'\n')
  raise
