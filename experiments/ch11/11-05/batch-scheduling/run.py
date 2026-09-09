import argparse,asyncio,hashlib,json,platform,random,sys,time
from pathlib import Path
R=Path(__file__).resolve().parent
CODE='value=b"validation-work-v1"\nfor _ in range(iterations): value=hashlib.sha256(value).digest()\n'
TASKS=[dict(id=f'B{i}',batch='B',arrival_s=0,iterations=3000000 if i==2 else 600000,sequence=i) for i in range(3)]+[dict(id=f'A{i}',batch='A',arrival_s=.03,iterations=600000,sequence=3+i) for i in range(3)]
def work(iterations):
 c0=time.monotonic();compiled=compile(CODE,'<validation>','exec');c1=time.monotonic();cpu=time.process_time();start=time.monotonic();scope=dict(iterations=iterations,hashlib=hashlib);exec(compiled,scope);end=time.monotonic()
 return dict(compile_start_s=c0,compile_end_s=c1,work_start_s=start,work_end_s=end,cpu_s=time.process_time()-cpu,digest=scope['value'].hex(),iterations=iterations)
async def main():
 out=R/'results';assert not out.exists();out.mkdir();references={str(n):work(n) for n in [600000,3000000]};(out/'references.json').write_text(json.dumps(references,indent=2)+'\n')
 rng=random.Random(1105);order=[]
 for trial in range(3):
  policies=['fixed_quota','fifo','batch_A_first'];rng.shuffle(policies);order.extend(dict(trial=trial,policy=p) for p in policies)
 (out/'order.json').write_text(json.dumps(order,indent=2)+'\n');children=[]
 try:
  for case in order:
   start=time.monotonic();pending=[dict(t) for t in TASKS];running={};rows=[]
   async def launch(job,dispatch):
    p=await asyncio.create_subprocess_exec(sys.executable,str(R/'run.py'),'--child',str(job['iterations']),stdout=asyncio.subprocess.PIPE,stderr=asyncio.subprocess.PIPE);children.append(p)
    line=await p.stdout.readline();feedback=time.monotonic();result=json.loads(line);await p.wait();released=time.monotonic();stderr=(await p.stderr.read()).decode();assert p.returncode==0 and not stderr
    assert result['digest']==references[str(job['iterations'])]['digest']
    return dict(**job,dispatch_s=dispatch,feedback_s=feedback,release_s=released,result=result,pid=p.pid,exit_code=p.returncode)
   while pending or running:
    now=time.monotonic();eligible=[j for j in pending if start+j['arrival_s']<=now]
    if case['policy']=='fixed_quota':eligible=[j for j in eligible if j['batch'] not in {v['batch'] for v in running.values()}]
    while eligible and len(running)<2:
     job=min(eligible,key=lambda j:(j['batch']!='A',j['sequence']) if case['policy']=='batch_A_first' else (j['arrival_s'],j['sequence']))
     pending.remove(job);task=asyncio.create_task(launch(job,time.monotonic()));running[task]=job
     eligible=[j for j in pending if start+j['arrival_s']<=time.monotonic()]
     if case['policy']=='fixed_quota':eligible=[j for j in eligible if j['batch'] not in {v['batch'] for v in running.values()}]
    if running:
     future=[start+j['arrival_s']-time.monotonic() for j in pending if start+j['arrival_s']>time.monotonic()]
     timeout=min(future) if future else None
     done,_=await asyncio.wait(running,timeout=timeout,return_when=asyncio.FIRST_COMPLETED)
     for task in done:rows.append(await task);del running[task]
    elif pending:await asyncio.sleep(max(0,min(start+j['arrival_s'] for j in pending)-time.monotonic()))
   record=dict(**case,start_s=start,end_s=time.monotonic(),tasks=rows)
   with (out/'raw.jsonl').open('a') as f:f.write(json.dumps(record)+'\n')
   print('completed',case,flush=True)
 finally:
  for p in children:
   if p.returncode is None:p.kill();await p.wait()
  (out/'execution.json').write_text(json.dumps(dict(source_sha256=hashlib.sha256((R/'run.py').read_bytes()).hexdigest(),platform=platform.platform(),python=sys.version,children=[dict(pid=p.pid,exit_code=p.returncode) for p in children],task_spec=TASKS),indent=2)+'\n')
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--child',type=int);args=parser.parse_args()
 if args.child:print(json.dumps(work(args.child)),flush=True)
 else:asyncio.run(main())
