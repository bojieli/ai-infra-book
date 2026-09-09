import dataclasses,hashlib,importlib.metadata,json,platform,random,resource,shutil,subprocess,time
from pathlib import Path
import mlx.core as mx
from mlx_lm import load,stream_generate
from mlx_lm.models.cache import make_prompt_cache
from mlx_lm.sample_utils import make_sampler
P=Path(__file__).resolve().parent;R=P/'results';R.mkdir(exist_ok=False)
meta=json.loads((P/'model-local.json').read_text());modelpath=Path(meta['snapshot'])
clock=time.perf_counter_ns
mx.set_default_device(mx.gpu)
mx.set_cache_limit(1024**3)
mx.set_memory_limit(24*1024**3)
def memory():
 return dict(active=mx.get_active_memory(),peak=mx.get_peak_memory(),cache=mx.get_cache_memory(),process_peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
def describe(cache):
 return [dict(layer=i,type=type(c).__name__,offset=c.offset,nbytes=c.nbytes,state=[dict(shape=list(z.shape),dtype=str(z.dtype),nbytes=z.nbytes) for z in c.state]) for i,c in enumerate(cache)]
start=clock();model,tokenizer=load(str(modelpath),lazy=False);mx.eval(model.parameters());mx.synchronize();loaded=clock()
(R/'environment.json').write_text(json.dumps(dict(platform=platform.platform(),allocator_limits=dict(cache_bytes=1024**3,memory_bytes=24*1024**3,active_guard_bytes=20*1024**3),device=mx.device_info(),versions={n:importlib.metadata.version(n) for n in ['mlx','mlx-lm','transformers','numpy']},python=platform.python_version(),model=meta,load_start_ns=start,load_end_ns=loaded,load_s=(loaded-start)/1e9,loaded_memory=memory(),run_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()),indent=2)+'\n')
(R/'vm-before.txt').write_text(subprocess.check_output(['vm_stat'],text=True))
shutil.copyfile(modelpath/'config.json',R/'model-config.json')
tasks=[dict(id='lookup-a',fact='The project ORION has access code 7319.',question='What is the access code of project ORION? Answer only its digits.',answer='7319'),dict(id='lookup-b',fact='The label for archive KESTREL is violet.',question='What is the label for archive KESTREL? Answer only the lowercase word.',answer='violet'),dict(id='integer-a',fact='',question='Compute 37 + 48. Answer only the integer.',answer='85'),dict(id='integer-b',fact='',question='Compute 9 * 7 - 5. Answer only the integer.',answer='58')]
def tokens(task,long=False):
 marker='CONTENT_MARKER_807'
 template=tokenizer.apply_chat_template([dict(role='user',content=marker)],tokenize=False,add_generation_prompt=True,enable_thinking=False)
 a,b=template.split(marker)
 enc=lambda text:tokenizer.encode(text,add_special_tokens=False)
 if not long:return enc(a+task['fact']+'\n'+task['question']+b)
 prefix=enc(a+task['fact']+'\nReference notes follow.\n');suffix=enc('\nEnd of notes.\n'+task['question']+b)
 fill=enc('This note contains no project codes or arithmetic answers.\n')
 n=32768-len(prefix)-len(suffix)
 return prefix+(fill*((n+len(fill)-1)//len(fill)))[:n]+suffix
allprompts={t['id']:{kind:tokens(t,kind=='long') for kind in ['short','long']} for t in tasks}
(R/'tasks.json').write_text(json.dumps(dict(tasks=tasks,prompts=allprompts,decoded_long={t['id']:tokenizer.decode(allprompts[t['id']]['long']) for t in tasks}),indent=2)+'\n')
def generate(task,prompt,cache):
 begin=clock();events=[];text=''
 for response in stream_generate(model,tokenizer,prompt=prompt,prompt_cache=cache,max_tokens=64,sampler=make_sampler(temp=0),prefill_step_size=512):
  mx.synchronize();now=clock();text+=response.text
  event={f.name:getattr(response,f.name) for f in dataclasses.fields(response) if f.name!='logprobs'};event['t_ns']=now;events.append(event)
 mx.synchronize();end=clock()
 return dict(task=task['id'],input_ids=prompt,begin_ns=begin,end_ns=end,ttft_s=(events[0]['t_ns']-begin)/1e9,elapsed_s=(end-begin)/1e9,text=text,passed=text.strip()==task['answer'],events=events,finish_reason=events[-1]['finish_reason'],memory=memory(),cache=describe(cache))
# Same two tasks in both conditions, matched across two repetitions.
tasks=[tasks[0],tasks[3]]
plan=[(trial,slots) for trial in range(2) for slots in [1,2]];random.Random(80732).shuffle(plan)
(R/'plan.json').write_text(json.dumps(plan)+'\n')
for trial,slots in plan:
 mx.clear_cache();mx.reset_peak_memory();case=R/f'{trial}-{slots}slots';case.mkdir();chunks=[];rows=[];snapshots=[];begin=clock()
 batches=[[t] for t in tasks] if slots==1 else [tasks]
 for batch in batches:
  caches=[];batch_begin=clock()
  for task in batch:
   c=make_prompt_cache(model);ids=allprompts[task['id']]['long'];assert len(ids)==32768
   for offset in range(0,32767,512):
    if mx.get_active_memory()>20*1024**3:raise RuntimeError('Configured active-memory guard exceeded')
    part=ids[offset:min(offset+512,32767)];a=clock();logits=model(mx.array([part]),cache=c);mx.eval(logits,[x.state for x in c]);mx.synchronize();b=clock();record=dict(task=task['id'],offset=offset,count=len(part),start_ns=a,end_ns=b,memory=memory());chunks.append(record)
    with (case/'chunks.jsonl').open('a') as f:f.write(json.dumps(record)+'\n')
   caches.append(c)
  ready=clock();snapshots.append(dict(tasks=[t['id'] for t in batch],begin_ns=batch_begin,ready_ns=ready,memory=memory(),caches=[describe(c) for c in caches],vm_stat=subprocess.check_output(['vm_stat'],text=True)))
  (case/'ready.json').write_text(json.dumps(snapshots,indent=2)+'\n')
  for task,c in zip(batch,caches):rows.append(generate(task,allprompts[task['id']]['long'][-1:],c))
  (case/'outputs.json').write_text(json.dumps(rows,indent=2)+'\n')
  del caches,c,logits;mx.clear_cache()
 (case/'after.json').write_text(json.dumps(dict(begin_ns=begin,end_ns=clock(),memory=memory()))+'\n')
 print(json.dumps(dict(trial=trial,slots=slots,passed=sum(r['passed'] for r in rows))),flush=True)
(R/'vm-after.txt').write_text(subprocess.check_output(['vm_stat'],text=True))
(R/'completion.json').write_text(json.dumps(dict(completed=True,long=8))+'\n')
