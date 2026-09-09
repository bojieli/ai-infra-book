"""Native four-layer runtime compatibility probe; NOT full-model quality."""
import os,json,time,traceback
from pathlib import Path
B=Path(__file__).resolve().parent

def main():
 import torch,sglang
 torch.set_num_threads(4);torch.set_num_interop_threads(4)
 def save(n,v):(B/'results'/n).write_text(json.dumps(v,indent=2,default=str)+'\n')
 model='/home/ubuntu/.cache/huggingface/hub/models--deepseek-ai--DeepSeek-V4-Flash-0731/snapshots/7872f01b1d1fe23eabc4c98b48bffcef5a386062'
 config=dict(model_path=model,dtype='bfloat16',json_model_override_args=json.dumps(dict(num_hidden_layers=4,compress_ratios=[0,0,4,128])),cpu_offload_gb=8,context_length=1024,max_total_tokens=2048,max_running_requests=1,chunked_prefill_size=256,mem_fraction_static=.9,swa_full_tokens_ratio=1.0,log_level="info",disable_cuda_graph=True,disable_radix_cache=True,port=18205)
 save('config.json',config);save('environment.json',dict(torch=torch.__version__,torch_path=torch.__file__,sglang=sglang.__version__,affinity=sorted(os.sched_getaffinity(0)),scope='truncated native four-layer loading/forward only, not original V4 quality'))
 engine=None;start=time.time()
 try:
  engine=sglang.Engine(**config)
  save('ready.json',dict(time=time.time(),elapsed=time.time()-start,server_info=engine.get_server_info()))
  # Valid repeated ordinary vocabulary IDs; synthetic input, no retrieval score.
  rows=[]
  for length in (256,512):
   ids=([1000,1001,1002,1003]*128)[:length]
   sent=time.time()
   response=engine.generate(input_ids=ids,sampling_params=dict(temperature=0,max_new_tokens=4,ignore_eos=True))
   rows.append(dict(input_ids=ids,sent=sent,end=time.time(),response=response))
   save('requests.json',rows)
  save('completion.json',dict(status='native_truncated_forward_returned',requests=len(rows),time=time.time()))
 except BaseException as exc:
  save('failure.json',dict(type=type(exc).__name__,message=str(exc),traceback=traceback.format_exc(),time=time.time()))
  raise
 finally:
  if engine is not None:engine.shutdown()
  save('finally.json',dict(time=time.time(),engine_created=engine is not None))
if __name__=='__main__':main()
