import argparse,hashlib,importlib.metadata,json,os,time,urllib.request,urllib.error
from pathlib import Path
B=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--job',required=True);p.add_argument('--output',required=True);p.add_argument('--url',required=True);p.add_argument('--attempt',type=int,required=True);a=p.parse_args();job=json.loads(Path(a.job).read_text());out=Path(a.output);out.mkdir(exist_ok=False)
def log(name,x):
 with (out/name).open('a') as f:f.write(json.dumps(dict(time=time.monotonic(),**x))+'\n')
def send(route,data=None):
 raw=None if data is None else json.dumps(data).encode();req=urllib.request.Request(a.url+route,data=raw,headers={'Content-Type':'application/json'})
 try:
  with urllib.request.urlopen(req,timeout=120) as r:return json.load(r)
 except urllib.error.HTTPError as e:
  if e.code==409:return {'conflict':True}
  raise
import mlx.core as mx
from mlx_lm import load
from mlx_lm.models.cache import make_prompt_cache
mx.set_default_device(mx.gpu);meta=json.loads((B/'model-identity.json').read_text());t=time.monotonic();model,tok=load(meta['snapshot'],lazy=False);mx.eval(model.parameters());mx.synchronize();loaded=time.monotonic()
prompt=tok.apply_chat_template([{'role':'user','content':job['task']['prompt']}],tokenize=True,add_generation_prompt=True,enable_thinking=False,return_dict=False);assert isinstance(prompt,list) and all(type(x)==int for x in prompt)
identity=hashlib.sha256(json.dumps(prompt,separators=(',',':')).encode()).hexdigest();ready=send('/state',{'prompt_sha':identity,'prompt_ids':prompt,'model_revision':meta['revision']});prefix=ready['tokens'] if a.attempt==1 and job['strategy']=='preserve' else []
(out/'environment.json').write_text(json.dumps(dict(pid=os.getpid(),pgid=os.getpgrp(),attempt=a.attempt,versions={n:importlib.metadata.version(n) for n in ['mlx','mlx-lm','transformers','numpy']},load_start=t,load_end=loaded,load_s=loaded-t,prompt_ids=prompt,prompt_sha=identity,preserved_prefix=prefix,model=meta['revision'],device=mx.device_info()),indent=2)+'\n')
cache=make_prompt_cache(model)
def forward(ids,kind):
 start=time.monotonic();z=model(mx.array([ids]),cache=cache);mx.eval(z,[c.state for c in cache]);mx.synchronize();end=time.monotonic();active=mx.get_active_memory();assert active<=16*1024**3
 log('calls.jsonl',dict(kind=kind,input_tokens=len(ids),start=start,end=end,offsets=[c.offset for c in cache],active_bytes=active,peak_bytes=mx.get_peak_memory()));return z
for offset in range(0,len(prompt),256):logits=forward(prompt[offset:offset+256],'prompt_prefill')
for offset in range(0,len(prefix),64):logits=forward(prefix[offset:offset+64],'prefix_rebuild')
seq=len(prefix);reason='length';eos=set(tok.eos_token_ids)
while seq<job['max_tokens']:
 t=time.monotonic();chosen=mx.argmax(logits[0,-1,:]);mx.eval(chosen);mx.synchronize();token=int(chosen.item());generated=time.monotonic();is_eos=token in eos
 log('generated.jsonl',dict(seq=seq,token=token,eos=is_eos,sample_start=t,generated=generated,active_bytes=mx.get_active_memory(),peak_bytes=mx.get_peak_memory()))
 response=send('/token',dict(seq=seq,token=token,eos=is_eos,attempt=a.attempt,pid=os.getpid(),generated=generated));log('acks.jsonl',dict(seq=seq,response=response))
 if response.get('conflict'):reason='conflict';break
 seq+=1
 if is_eos:reason='stop';break
 if seq<job['max_tokens']:logits=forward([token],'decode')
finish=send('/finish',dict(reason=reason,attempt=a.attempt,pid=os.getpid()));(out/'completion.json').write_text(json.dumps(dict(reason=reason,attempt=a.attempt,finish=finish,time=time.monotonic(),pid=os.getpid()))+'\n')
