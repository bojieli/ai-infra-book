"""CPU-only export of actual saved tensors for an independent stdlib audit."""
import json,os,pathlib,sys,time
import torch
from transformers import AutoTokenizer
r=pathlib.Path(os.environ['VERLRL_ROOT']);p=pathlib.Path(os.environ['VERLRL_PRIVATE']);tok=AutoTokenizer.from_pretrained(p/'model',local_files_only=True)
for mode in ['main','control']:
 d=r/os.environ.get('VERLRL_MAIN_RUN' if mode=='main' else 'VERLRL_CONTROL_RUN',mode);ex=json.loads((d/'exit.json').read_text());assert ex['returncode']==0 and not ex['remaining_pids']
 output={'run':mode,'tensor_files':{},'decoded_batches':{}}
 for path in sorted((d/'observations').glob('*.pt')):
  values=torch.load(path,map_location='cpu',weights_only=True)
  output['tensor_files'][path.name]={k:{'dtype':str(t.dtype),'shape':list(t.shape),'values':t.tolist()} for k,t in values.items()}
  if 'batch-' in path.name:
   metadata=json.loads(path.with_suffix('.json').read_text());nt=metadata['non_tensor_batch'];rows=[]
   for i,resp in enumerate(values['responses']):
    prompt=tok.decode(values['prompts'][i],skip_special_tokens=True)
    text=tok.decode(resp,skip_special_tokens=True);truth=str(nt['reward_model'][i]['ground_truth'])
    mask=values.get('response_mask',values['attention_mask'][:,-values['responses'].shape[1]:])[i]
    rows.append(dict(index=i,prompt=prompt,response=text,ground_truth=truth,arithmetic_correct=text.strip()==truth,uid=nt.get('uid',[None]*len(values['responses']))[i],actual_response_token_ids=resp[mask.bool()].tolist()))
   output['decoded_batches'][path.name]=rows
 (d/'tensor-export.json').write_text(json.dumps(output,indent=2,allow_nan=False)+'\n')
print(json.dumps({'runs':['main','control'],'cpu_only':True,'completed_time_ns':time.time_ns(),'torch':torch.__version__}))
