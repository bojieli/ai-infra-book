"""Bounded actual training jobs; no synthetic traffic, queue or forced period."""
import argparse
import hashlib
import json
import multiprocessing as mp
import os
from pathlib import Path
import platform
import random
import socket
import subprocess
import time
from train_phase import worker

ROOT=Path(__file__).resolve().parent


def port():
    with socket.socket() as s:s.bind(('127.0.0.1',0));return s.getsockname()[1]


def main(args):
    args.out=args.out.absolute();args.out.mkdir(parents=True,exist_ok=False)
    ctx=mp.get_context('spawn')
    spec=json.loads((ROOT/'protocol.json').read_text())
    if args.smoke:spec.update(steps=5,warmup=2,repetitions=1)
    (args.out/'protocol.json').write_text(json.dumps(spec,indent=2)+'\n')
    src={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in ROOT.glob('*.py')}
    (args.out/'environment.json').write_text(json.dumps(dict(platform=platform.platform(),
        machine=platform.machine(),sources=src,data_sha256=hashlib.sha256((ROOT/'data/input.txt').read_bytes()).hexdigest()),indent=2)+'\n')
    order=[]
    for rep in range(spec['repetitions']):
        conditions=['solo-a','solo-b','aligned','offset-50ms']
        random.Random(708+rep).shuffle(conditions)
        order.extend((rep,c) for c in conditions)
    (args.out/'order.json').write_text(json.dumps(order,indent=2)+'\n')
    all_results=[]
    for rep,condition in order:
        run=args.out/f'r{rep}-{condition}';run.mkdir()
        jobs=[0] if condition=='solo-a' else [1] if condition=='solo-b' else [0,1]
        run_spec=dict(spec,offset_ns=50_000_000 if condition=='offset-50ms' else 0)
        count=2*len(jobs);ready=ctx.Array('i',count);done=ctx.Array('i',count)
        release=ctx.Value('q',0);save_event=ctx.Event();processes=[];samples=[]
        start=time.monotonic();reason=None
        try:
            index=0;ports=[]
            for job in jobs:
                p=port()
                while p in ports:p=port()
                ports.append(p)
                for rank in range(2):
                    proc=ctx.Process(target=worker,args=(index,job,rank,p,str(run/f'job{job}-rank{rank}'),
                         run_spec,ready,done,release,save_event));proc.start();processes.append(proc);index+=1
            while any(p.is_alive() for p in processes):
                if any(p.exitcode not in (None,0) for p in processes):raise RuntimeError('worker failed')
                if all(ready) and release.value==0:release.value=time.monotonic_ns()+200_000_000
                if all(done):save_event.set()
                live=[str(p.pid) for p in processes if p.is_alive()]
                if live:
                    text=subprocess.run(['ps','-o','rss=','-p',','.join(live)],capture_output=True,text=True).stdout
                    rss=sum(int(v)*1024 for v in text.split())
                    samples.append(dict(elapsed_s=time.monotonic()-start,pids=live,rss_sum_bytes=rss))
                    if rss>20*1024**3:raise RuntimeError('own RSS limit')
                if time.monotonic()-start>600:raise TimeoutError('600 s run deadline')
                time.sleep(.2)
            for p in processes:p.join();assert p.exitcode==0
        except BaseException as e:
            reason=repr(e);raise
        finally:
            for p in processes:
                if p.is_alive():p.terminate();p.join(10)
                if p.is_alive():p.kill();p.join(5)
            result=dict(rep=rep,condition=condition,jobs=jobs,release_ns=release.value,
                        offset_ns=run_spec['offset_ns'],exit_codes=[p.exitcode for p in processes],
                        reason=reason,wall_s=time.monotonic()-start)
            (run/'supervisor.json').write_text(json.dumps(result,indent=2)+'\n')
            (run/'resources.json').write_text(json.dumps(samples,indent=2)+'\n')
        all_results.append(result);print(json.dumps(result),flush=True)
    (args.out/'completion.json').write_text(json.dumps(all_results,indent=2)+'\n')


if __name__=='__main__':
    os.environ.update(OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1')
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--smoke',action='store_true')
    main(p.parse_args())
