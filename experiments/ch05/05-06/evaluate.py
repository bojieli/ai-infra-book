import argparse,hashlib,importlib.util,json,subprocess,time
from pathlib import Path
import torch,triton
import vllm._custom_ops as ops
ROOT=Path(__file__).resolve().parent

def native(x):
 out=torch.empty((x.shape[0],x.shape[1]//2),device=x.device,dtype=x.dtype);ops.silu_and_mul(out,x);return out
def expression(x):
 d=x.shape[1]//2;return (torch.nn.functional.silu(x[:,:d].float())*x[:,d:].float()).bfloat16()
def main(a):
 if a.output.exists():raise RuntimeError('Use fresh output file')
 a.output.parent.mkdir(parents=True,exist_ok=True)
 protocol=json.loads((ROOT/'protocol.json').read_text());result=dict(kind=a.kind,block=a.block,warps=a.warps,rows=[],status='running',protocol_sha256=hashlib.sha256((ROOT/'protocol.json').read_bytes()).hexdigest(),torch=torch.__version__,triton=triton.__version__)
 if a.kind=='native':fn=native
 elif a.kind=='compiled':fn=torch.compile(expression,fullgraph=True)
 else:
  import schedule
  fn=lambda x:schedule.run(x,a.block,a.warps)
 result['gpu_before']=subprocess.check_output(['nvidia-smi','--query-compute-apps=pid,process_name,used_memory','--format=csv'],text=True)
 wall=time.perf_counter();event_start=torch.cuda.Event(enable_timing=True);event_end=torch.cuda.Event(enable_timing=True);event_start.record()
 try:
  for index in [1,0]:
   data=torch.load(ROOT/f'results/capture/tensors/layer0-call{index}.pt',weights_only=True);x=data['input'].cuda();expected=data['reference'].cuda();t=x.shape[0]
   baseline=native(x);assert torch.equal(baseline,expected),'Current native reference differs from captured model'
   start=time.perf_counter();actual=fn(x);torch.cuda.synchronize();prepare=time.perf_counter()-start
   assert actual.shape==expected.shape and actual.dtype==expected.dtype
   torch.testing.assert_close(actual,expected,atol=protocol['atol'],rtol=protocol['rtol'])
   # Validate absence of input mutation against the original CPU bytes.
   assert torch.equal(x.cpu(),data['input'])
   row=dict(t=t,max_abs_error=float((actual.float()-expected.float()).abs().max()),different_elements=int((actual!=expected).sum()),prepare_s=prepare,samples_us=[])
   for _ in range(protocol['warmups']):fn(x)
   graph=torch.cuda.CUDAGraph()
   with torch.cuda.graph(graph):
    for _ in range(protocol['graph_repeats']):out=fn(x)
   for _ in range(3):graph.replay()
   torch.cuda.synchronize();torch.testing.assert_close(out,expected,atol=protocol['atol'],rtol=protocol['rtol'])
   for _ in range(protocol['trials']):
    start_event,end_event=torch.cuda.Event(enable_timing=True),torch.cuda.Event(enable_timing=True)
    start_event.record();graph.replay();end_event.record();end_event.synchronize()
    row['samples_us'].append(start_event.elapsed_time(end_event)*1000/protocol['graph_repeats'])
   result['rows'].append(row)
  result['status']='passed'
 except Exception as e:
  result['status']='failed';result['error']=repr(e)
 finally:
  event_end.record();event_end.synchronize();result['gpu_event_window_s']=event_start.elapsed_time(event_end)/1000
  result['wall_s']=time.perf_counter()-wall;result['gpu_after']=subprocess.check_output(['nvidia-smi','--query-compute-apps=pid,process_name,used_memory','--format=csv'],text=True)
  result['source_hashes']={f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in ['evaluate.py','schedule.py','protocol.json']}
  a.output.write_text(json.dumps(result,indent=2)+'\n')
 print(a.kind,a.block,a.warps,result['status'],flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--kind',choices=['native','compiled','schedule'],required=True);p.add_argument('--block',type=int,default=256);p.add_argument('--warps',type=int,default=4);p.add_argument('--output',type=Path,required=True);main(p.parse_args())
