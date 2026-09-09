"""Actual full-model execution. Only launch.py may call this after root scheduling."""
import argparse,json,os,time,traceback
from pathlib import Path
from common import *
# Spawned scheduler imports this module as __mp_main__; install there too.
if os.environ.get('V4_FULL_RUN_TOKEN'):
 from offload_alias import install
 install()
def main():
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args();out=a.out
 assert os.environ.get('V4_FULL_RUN_TOKEN')
 while not (out/'start-gate.json').is_file():time.sleep(.05)
 frozen=json.loads((out/'cases.json').read_text());config=json.loads((out/'candidate.json').read_text())
 assert config==CONFIG and 'json_model_override_args' not in config
 assert json.loads((MODEL/'config.json').read_text())['num_hidden_layers']==43
 for n,h in json.loads((out/'small-model-hashes.json').read_text()).items():assert sha(MODEL/n)==h
 def phase(name,**kw):save(out/'phase.json',dict(phase=name,monotonic=time.monotonic(),time=time.time(),**kw))
 import torch,sglang
 torch.set_num_threads(4);torch.set_num_interop_threads(4)
 save(out/'environment.json',dict(torch=torch.__version__,sglang=sglang.__version__,python=os.sys.version,torch_path=torch.__file__,affinity=sorted(os.sched_getaffinity(0)),environment={k:v for k,v in os.environ.items() if (k.startswith(('SGLANG_','CUDA_','TVM_','TILELANG_','TRITON_','TORCH','HF_','TRANSFORMERS_')) or k in ['CPATH','TMPDIR','XDG_CACHE_HOME','OMP_NUM_THREADS','V4_FULL_RUN_TOKEN']) and (k=='V4_FULL_RUN_TOKEN' or not any(part in k.upper() for part in ['TOKEN','SECRET','PASSWORD','API_KEY']))}))
 engine=None;rows=[]
 try:
  phase('initializing');start=time.monotonic();save(out/'initialization-start.json',dict(time=time.time(),monotonic=start))
  engine=sglang.Engine(**config)
  ready_time=time.monotonic();info=engine.get_server_info()
  save(out/'ready.json',dict(time=time.time(),initialization_s=ready_time-start,server_info=info,scope='actual_43_layer_engine_constructor_returned',effective_sglang_environment={k:v for k,v in os.environ.items() if k.startswith('SGLANG_')}))
  for case in frozen['cases']:
   phase('request',case_id=case['id']);sent=time.monotonic()
   row=dict(case_id=case['id'],status='in_flight',input_ids=case['input_ids'],sampling_params=frozen['sampling'],sent_time=time.time(),sent_monotonic=sent)
   rows.append(row);save(out/'requests.json',rows)
   response=engine.generate(input_ids=case['input_ids'],sampling_params=frozen['sampling'])
   row.update(status='returned',end_time=time.time(),request_wall_s=time.monotonic()-sent,response=response)
   save(out/'requests.json',rows)
   # Preserve engine output verbatim before validating or scoring.
   if not isinstance(response,dict) or 'output_ids' not in response or 'text' not in response or not isinstance(response.get('meta_info'),dict) or 'finish_reason' not in response['meta_info']:
    row['schema_error']='Engine response missing required raw IDs/text/finish';save(out/'requests.json',rows)
  phase('shutdown');save(out/'completion.json',dict(status='all_frozen_requests_returned',count=len(rows),time=time.time(),strict_numerical_clearance=False))
 except BaseException as exc:
  save(out/'failure.json',dict(type=type(exc).__name__,message=str(exc),traceback=traceback.format_exc(),time=time.time()));raise
 finally:
  phase('shutdown')
  if engine is not None:engine.shutdown()
  save(out/'finally.json',dict(time=time.time(),engine_created=engine is not None))
if __name__=='__main__':main()
