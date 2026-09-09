import argparse,gzip,hashlib,json,math,time
from pathlib import Path
import torch,tilelang
from attention_generated import redfuser_flash_attention
ROOT=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args()
if a.output.exists():raise RuntimeError('Use fresh output directory')
a.output.mkdir(parents=True);kernel=redfuser_flash_attention()
if hasattr(kernel,'get_kernel_source'):(a.output/'generated.cu').write_text(kernel.get_kernel_source())
rows=[]
for case in ['two_blocks','swapped_blocks']:
 shape=(128,16,512,64);q=torch.zeros(shape,device='cuda',dtype=torch.float16);q[:,:,:,0]=8
 k=torch.zeros_like(q);k[:,:,:,0]=-100;v=torch.zeros_like(q)
 idx=[0,1,64] if case=='two_blocks' else [64,65,0]
 for i,s,val in zip(idx,[0,math.log(2),math.log(4)],[1,3,-2]):k[:,:,i,0]=s;v[:,:,i,:]=val
 scores=k[0,0,:,0].cpu().double();values=v[0,0,:,0].cpu().double()
 expected=float((scores.softmax(0)*values).sum())
 out=kernel(q,k,v);torch.cuda.synchronize()
 assert torch.isfinite(out).all()
 torch.testing.assert_close(out.float(),torch.full(shape,expected,device='cuda'),atol=.001,rtol=.01)
 with torch.profiler.profile(activities=[torch.profiler.ProfilerActivity.CPU,torch.profiler.ProfilerActivity.CUDA]) as prof:kernel(q,k,v);torch.cuda.synchronize()
 prof.export_chrome_trace(str(a.output/f'{case}-trace.json'))
 cpu=out.cpu()
 with gzip.open(a.output/f'{case}.pt.gz','wb') as f:torch.save(dict(output=cpu,scores=scores,values=values),f)
 rows.append(dict(case=case,expected_fp64=expected,output_min=float(out.min()),output_max=float(out.max()),max_abs_error=float((out.float()-expected).abs().max()),output_sha256=hashlib.sha256(cpu.view(torch.uint8).numpy().tobytes()).hexdigest()))
 print(rows[-1],flush=True)
(a.output/'results.json').write_text(json.dumps(dict(rows=rows,source_hashes={f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in ['attention_run.py','attention_generated.py']},torch=torch.__version__,tilelang=tilelang.__version__,scope='Unmodified generated attention at [128,16,512,64], structured repeated inputs spanning two K blocks; FP64 reference uses actual FP16 input scores. Not masked/causal attention or generator pass reproduction.'),indent=2)+'\n')
