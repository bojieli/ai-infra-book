import os,pathlib,time,json,hashlib,dataclasses,subprocess,threading,signal,traceback,sys,importlib.metadata
ROOT=pathlib.Path(__file__).resolve().parents[1]
MODE=sys.argv[1]; OUT=ROOT/'raw'/MODE; OUT.mkdir(parents=True,exist_ok=True)
for k in ['HF_HOME','XDG_CACHE_HOME','TRITON_CACHE_DIR','VLLM_CACHE_ROOT','CUDA_CACHE_PATH','FLASHINFER_WORKSPACE_BASE']:
 os.environ[k]=str(ROOT/'cache'/k)
os.environ.update(VLLM_ENABLE_V1_MULTIPROCESSING='0',VLLM_USE_FLASHINFER_SAMPLER='0',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',TOKENIZERS_PARALLELISM='false')
f=(OUT/'events.jsonl').open('a',buffering=1)
def emit(kind,**kw):f.write(json.dumps({'kind':kind,'t':time.perf_counter(),**kw},default=lambda x:dataclasses.asdict(x) if dataclasses.is_dataclass(x) else vars(x) if hasattr(x,'__dict__') else str(x))+'\n')
def mem():
 return subprocess.check_output(['nvidia-smi','--query-compute-apps=pid,used_memory','--format=csv,noheader,nounits'],text=True)
def watchdog():
 while not done.wait(.5):
  try:
   s=mem(); emit('gpu_memory',processes=s)
   for line in s.splitlines():
    pid,m=line.split(',')
    if int(pid)==os.getpid() and int(m)>24576:
     emit('memory_limit_exceeded',MiB=int(m)); os.kill(os.getpid(),signal.SIGTERM)
  except Exception as e:emit('monitor_error',error=str(e))
done=threading.Event()
try:
 free=int(subprocess.check_output(['nvidia-smi','--query-gpu=memory.free','--format=csv,noheader,nounits'],text=True).strip())
 emit('preflight',free_MiB=free,pid=os.getpid(),processes=mem())
 if free<27648:raise RuntimeError('GPU不足27GiB：保存配置并等待主agent，不启动模型')
 import torch
 torch.cuda.set_per_process_memory_fraction(22*1024**3/torch.cuda.get_device_properties(0).total_memory)
 import vllm
 from vllm import SamplingParams
 from vllm.engine.arg_utils import EngineArgs
 from vllm.v1.engine.llm_engine import LLMEngine
 from vllm.v1.metrics.loggers import StatLoggerBase
 from transformers import AutoTokenizer
 class Recorder(StatLoggerBase):
  def __init__(self,vllm_config,engine_index=0):emit('resolved_config',config=str(vllm_config))
  def log_engine_initialized(self):emit('engine_initialized')
  def record(self,scheduler_stats,iteration_stats,mm_cache_stats=None,engine_idx=0):
   emit('stats',scheduler=dataclasses.asdict(scheduler_stats) if scheduler_stats else None,iteration=vars(iteration_stats) if iteration_stats else None)
 target='/home/ubuntu/.cache/huggingface/hub/models--Qwen--Qwen3-8B/snapshots/b968826d9c46dd6066d109eabc6255188de91218'
 tokenizer=AutoTokenizer.from_pretrained(target,local_files_only=True)
 inputs=ROOT/'inputs.json'
 if not inputs.exists():
  tasks=[]
  for length in ['short','long']:
   filler='\n'.join(f'Record {i:03d}: color=gray; status=closed.' for i in range(160)) if length=='long' else 'Record 000: color=gray; status=closed.'
   for typ,q,answer in [('math','Compute 37 * 19 + 16. Reply with only the integer.','719'),('lookup','Find the value of key ALPHA in the document. Reply with only that value.','5837')]:
    doc=filler+'\nALPHA=5837\n'
    messages=[{'role':'user','content':doc+'\n'+q}]
    ids=tokenizer.apply_chat_template(messages,add_generation_prompt=True,enable_thinking=False,return_dict=False)
    assert len(ids)+128<=4096
    tasks.append(dict(id=length+'_'+typ,length=length,task=typ,answer=answer,messages=messages,input_ids=ids))
  inputs.write_text(json.dumps({'chat_template':tokenizer.chat_template,'enable_thinking':False,'tasks':tasks},ensure_ascii=False,indent=2))
 tasks=json.loads(inputs.read_text())['tasks']
 args=dict(model=target,tokenizer=target,dtype='bfloat16',seed=42,tensor_parallel_size=1,enforce_eager=True,enable_prefix_caching=False,async_scheduling=False,max_model_len=4096,max_num_batched_tokens=512,max_num_seqs=2,kv_cache_memory_bytes=1342177280,gpu_memory_utilization=.23,attention_config={'backend':'FLASH_ATTN'},disable_log_stats=False)
 if MODE!='ar':args['speculative_config']={'method':'dflash','model':str(ROOT/'weights'/'Qwen3-8B-DFlash-b16'),'num_speculative_tokens':int(MODE.split('-')[1])}
 emit('configuration',args=args,versions={x:importlib.metadata.version(x) for x in ['vllm','torch','transformers','flashinfer-python']},input_sha256=hashlib.sha256(inputs.read_bytes()).hexdigest())
 threading.Thread(target=watchdog,daemon=True).start()
 load=time.perf_counter(); engine=LLMEngine.from_engine_args(EngineArgs(**args),stat_loggers=[Recorder]); emit('load_complete',wall_s=time.perf_counter()-load)
 for phase,rounds in [('warmup',1),('measured',2)]:
  for rep in range(rounds):
   for concurrency in [1,2]:
    for start in range(0,len(tasks),concurrency):
     group=tasks[start:start+concurrency]; state={}; batch_start=time.perf_counter()
     for task in group:
      rid=f'{phase}-{rep}-c{concurrency}-{task["id"]}'; submitted=time.perf_counter(); state[rid]={'submitted':submitted,'first':None,'task':task}
      engine.add_request(rid,{'prompt_token_ids':task['input_ids']},SamplingParams(temperature=0,seed=42,max_tokens=128))
      emit('submit',request_id=rid,phase=phase,rep=rep,concurrency=concurrency,task_id=task['id'],submitted=submitted)
     while engine.has_unfinished_requests():
      t=time.perf_counter(); outputs=engine.step(); end=time.perf_counter()
      emit('step',wall_s=end-t,phase=phase,rep=rep,concurrency=concurrency)
      for o in outputs:
       s=state[o.request_id]; co=o.outputs[0]
       if co.token_ids and s['first'] is None:s['first']=end
       emit('tokens',request_id=o.request_id,token_ids=list(co.token_ids),finished=o.finished)
       if o.finished:
        emit('result',request_id=o.request_id,phase=phase,rep=rep,concurrency=concurrency,task_id=s['task']['id'],expected=s['task']['answer'],text=co.text,token_ids=list(co.token_ids),finish_reason=co.finish_reason,stop_reason=co.stop_reason,ttft_s=s['first']-s['submitted'] if s['first'] else None,wall_s=end-s['submitted'],quality_pass=co.text.strip()==s['task']['answer'])
     emit('batch_complete',phase=phase,rep=rep,concurrency=concurrency,wall_s=time.perf_counter()-batch_start,torch_peak_allocated=torch.cuda.max_memory_allocated(),torch_peak_reserved=torch.cuda.max_memory_reserved())
 emit('success')
 del engine
 if torch.distributed.is_initialized():torch.distributed.destroy_process_group()
 done.set();emit('cleanup',status='engine_deleted_process_exit_releases_cuda')
except BaseException:
 emit('failure',traceback=traceback.format_exc());raise
finally:
 done.set();f.close()
