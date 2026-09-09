import argparse,hashlib,json,time
from pathlib import Path
import torch,tilelang
from generated import redfuser_ptpc_quant_gemm
ROOT=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args()
if a.output.exists():raise RuntimeError('Use fresh output directory')
a.output.mkdir(parents=True)
start=time.perf_counter();kernel=redfuser_ptpc_quant_gemm();compile_s=time.perf_counter()-start
if hasattr(kernel,'get_kernel_source'):(a.output/'generated.cu').write_text(kernel.get_kernel_source())
rows=[]
for case in ['original_order','swapped_blocks','zero_input']:
 x=torch.zeros((4096,4096),device='cuda',dtype=torch.float16)
 w=torch.zeros((4096,4096),device='cuda',dtype=torch.float8_e4m3fn)
 if case=='original_order':x[:,0]=1;x[:,128]=10;w[:,0]=1
 elif case=='swapped_blocks':x[:,0]=10;x[:,128]=1;w[:,128]=1
 else:w[:,0]=1
 scales=torch.ones(4096,device='cuda',dtype=torch.float32)
 start=time.perf_counter();out=kernel(x,w,scales);torch.cuda.synchronize();wall=time.perf_counter()-start
 # Native global-scale cast, using the selected nonzero weight column; no synthetic rounding implementation.
 scale=x.float().abs().amax(-1)/448
 index=128 if case=='swapped_blocks' else 0
 ref=((x[:,index].float()/scale.clamp_min(1e-30)).to(torch.float8_e4m3fn).float()*scale).half()
 with torch.profiler.profile(activities=[torch.profiler.ProfilerActivity.CPU,torch.profiler.ProfilerActivity.CUDA]) as prof:
  again=kernel(x,w,scales);torch.cuda.synchronize()
 prof.export_chrome_trace(str(a.output/f'{case}-trace.json'))
 torch.testing.assert_close(again,out,equal_nan=True)
 cpu=out.cpu();torch.save(dict(output=cpu,global_scale_reference=ref.cpu()),a.output/f'{case}.pt')
 finite=torch.isfinite(out);rows.append(dict(case=case,first_call_wall_s=wall,finite_elements=int(finite.sum()),total_elements=out.numel(),
  output_min=float(out[finite].min()) if finite.any() else None,output_max=float(out[finite].max()) if finite.any() else None,
  global_scale_reference_min=float(ref.min()),global_scale_reference_max=float(ref.max()),different_from_global=int((out!=ref[:,None]).sum()),
  output_sha256=hashlib.sha256(cpu.view(torch.uint8).numpy().tobytes()).hexdigest()))
 print(rows[-1],flush=True)
(a.output/'results.json').write_text(json.dumps(dict(rows=rows,torch=torch.__version__,tilelang=tilelang.__version__,gpu=torch.cuda.get_device_name(),compile_s=compile_s,source_hashes={f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in ['run.py','generated.py']},scope='Unmodified frozen author generated kernel at its original 4096x4096 shape; structured sparse fixtures, actual TileLang CUDA execution. Not RedFuser generator pass or paper performance reproduction.'),indent=2)+'\n')
