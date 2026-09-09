"""Actual timeout/worker-release experiment, not a queue simulation."""
import argparse,asyncio,hashlib,json,os,platform,sys,threading,time
from pathlib import Path
ROOT=Path(__file__).resolve().parent
ITERATIONS=600000

def work():
    start=time.monotonic();cpu=time.thread_time();value=b'validation-work-v1'
    for _ in range(ITERATIONS):value=hashlib.sha256(value).digest()
    return dict(start_s=start,end_s=time.monotonic(),cpu_s=time.thread_time()-cpu,iterations=ITERATIONS,digest=value.hex())

async def main(a):
    if a.child:
        print(json.dumps(dict(event='ready',t_s=time.monotonic())),flush=True)
        print(json.dumps(dict(event='complete',**work())),flush=True);return
    if a.output.exists():raise RuntimeError('Fresh output required')
    a.output.mkdir(parents=True);reference=await asyncio.to_thread(work);records=[]
    for trial in range(3):
        started=threading.Event();box={}
        def thread_worker():
            box['start_s']=time.monotonic();started.set();box['result']=work();return box['result']
        task=asyncio.create_task(asyncio.to_thread(thread_worker))
        while not started.is_set():await asyncio.sleep(.001)
        wait_start=time.monotonic();timed_out=False
        try:await asyncio.wait_for(asyncio.shield(task),timeout=.01)
        except asyncio.TimeoutError:timed_out=True
        feedback=time.monotonic();still_running=not task.done();result=await task;joined=time.monotonic()
        assert result['digest']==reference['digest']
        records.append(dict(trial=trial,mode='thread-wait-timeout',wait_start_s=wait_start,feedback_s=feedback,timed_out=timed_out,worker_running_at_feedback=still_running,release_observed_s=joined,result=result))
        process=await asyncio.create_subprocess_exec(sys.executable,str(Path(__file__).resolve()),'--child',stdout=asyncio.subprocess.PIPE,stderr=asyncio.subprocess.PIPE)
        ready=json.loads(await process.stdout.readline());assert ready['event']=='ready'
        wait_start=time.monotonic();timed_out=False
        try:await asyncio.wait_for(process.wait(),timeout=.01)
        except asyncio.TimeoutError:timed_out=True
        feedback=time.monotonic();alive=process.returncode is None
        if alive:process.terminate()
        await process.wait();released=time.monotonic();out=await process.stdout.read();err=await process.stderr.read()
        records.append(dict(trial=trial,mode='process-terminate-and-reap',pid=process.pid,ready=ready,wait_start_s=wait_start,feedback_s=feedback,timed_out=timed_out,worker_running_at_feedback=alive,release_observed_s=released,returncode=process.returncode,stdout_tail=out.decode(),stderr=err.decode()))
        # Recheck the identical deterministic work with a wider limit.
        t=time.monotonic();check=await asyncio.wait_for(asyncio.to_thread(work),timeout=10)
        assert check['digest']==reference['digest']
        records.append(dict(trial=trial,mode='wide-limit-recheck',wait_start_s=t,feedback_s=time.monotonic(),result=check,correct=True))
    result=dict(status='passed',records=records,reference=reference,python=sys.version,platform=platform.platform(),source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),scope='Fixed deterministic SHA256 validation work; 10ms wait limit starts after worker readiness. No real model/candidate quality or GPU allocation. Thread shield explicitly retains worker, process path terminates only own child and waits for exit. 10s recheck limit.')
    (a.output/'raw.json').write_text(json.dumps(result,indent=2)+'\n');print('completed',len(records),'records')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--child',action='store_true');p.add_argument('--output',type=Path);asyncio.run(main(p.parse_args()))
