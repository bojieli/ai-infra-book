"""Process-local observational wrappers; originals called once, unchanged arguments/return.
All value reads occur under obs.readback and intentionally synchronize CUDA.
"""
import inspect,functools,hashlib,json,contextlib
import torch
ACTIVE=False
STEP=0
RUNNER=None
SCHEDULE={}
EMIT=None
@contextlib.contextmanager
def scope(name):
 with torch.profiler.record_function(name):
  torch.cuda.nvtx.range_push(name)
  try: yield
  finally: torch.cuda.nvtx.range_pop()
def val(x):
 if isinstance(x,torch.Tensor):return x.detach().cpu().tolist()
 return x

def install(emit,out):
 global EMIT
 EMIT=emit
 from vllm.v1.worker.gpu_model_runner import GPUModelRunner as R
 from vllm.v1.spec_decode.llm_base_proposer import SpecDecodeBaseProposer as P
 from vllm.v1.spec_decode.dflash import DFlashProposer as D
 from vllm.v1.sample.rejection_sampler import RejectionSampler as S
 import vllm.v1.sample.rejection_sampler as sm
 specs=[(R,'execute_model'),(R,'_model_forward'),(R,'_sample'),(R,'_bookkeeping_sync'),(P,'propose'),(P,'prepare_inputs_padded'),(P,'prepare_inputs'),(D,'set_inputs_first_pass'),(S,'forward'),(sm,'rejection_sample')]
 source=[]
 for owner,name in specs:
  orig=getattr(owner,name); src=inspect.getsource(orig)
  label=owner.__name__+'.'+name
  source.append(dict(boundary=label,file=inspect.getsourcefile(orig),sha256=hashlib.sha256(src.encode()).hexdigest(),source=src))
  def make(orig,name,label):
   sig=inspect.signature(orig)
   @functools.wraps(orig)
   def wrapped(*a,**kw):
    global RUNNER,STEP,SCHEDULE
    if not ACTIVE:return orig(*a,**kw)
    b=sig.bind(*a,**kw).arguments
    if name=='execute_model':
     RUNNER=a[0];STEP+=1;s=b['scheduler_output'];SCHEDULE=dict(s.num_scheduled_tokens)
     emit('schedule',step=STEP,scheduled=SCHEDULE,drafts=s.scheduled_spec_decode_tokens)
    ids=list(RUNNER.input_batch.req_ids) if RUNNER is not None else []
    data={'boundary':label,'step':STEP,'request_ids':ids}
    with scope('obs.readback.before/'+label):
     if name=='_model_forward':
      ids=list(a[0].input_batch.req_ids);data['request_ids']=ids
      data.update(input_shape=list(b['input_ids'].shape),positions=val(b['positions']),scheduled=SCHEDULE)
     if name=='forward':
      m=b['metadata'];data.update(logits_shape=list(b['logits'].shape),metadata={k:val(v) for k,v in vars(m).items()})
     if name=='rejection_sample':
      data.update(draft_ids=val(b['draft_token_ids']),num_draft_tokens=b['num_draft_tokens'],target_argmax=val(b['target_logits'].argmax(dim=-1)) if 'target_logits' in b else None)
     if name in ['prepare_inputs_padded','set_inputs_first_pass','propose']:
      cad=b.get('common_attn_metadata',b.get('cad'))
      if cad is not None:data.update(seq_lens_before=val(cad.seq_lens),query_start=val(cad.query_start_loc))
      for key in ['num_rejected_tokens_gpu','valid_sampled_tokens_count','next_token_ids']:
       if key in b:data[key]=val(b[key])
    with scope('stage/'+label+'/step='+str(STEP)):
     result=orig(*a,**kw)
    with scope('obs.readback.after/'+label):
     if name=='propose':data['draft_ids']=val(result)
     if name=='forward':data['sampled_token_ids']=val(result.sampled_token_ids)
     if name=='rejection_sample':data['sampled_token_ids']=val(result)
     if name=='prepare_inputs_padded':data.update(seq_lens_after=val(result[0].seq_lens),token_indices=val(result[1]),num_rejected=val(result[2]))
     if name=='set_inputs_first_pass':data.update(query_rows=result[0],seq_lens_after=val(result[2].seq_lens),token_indices=val(result[1]))
    emit('boundary',**data)
    return result
   return wrapped
  setattr(owner,name,make(orig,name,label))
 (out/'original-functions.json').write_text(json.dumps(source,indent=2))
