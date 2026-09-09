"""One worker at a time; release proof required before any CUDA process."""
import argparse,hashlib,itertools,json,os,random,shutil,signal,subprocess,time,traceback
from pathlib import Path
R=Path(__file__).resolve().parent
ENV=Path('/home/ubuntu/ai-infra-book-experiments/tools/sglang0513-venv')
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,x): p.write_text(json.dumps(x,indent=2)+'\n')
def proc(pid):
    try:
        raw=Path(f'/proc/{pid}/stat').read_text();f=raw.rsplit(') ',1)[1].split()
        return dict(pid=pid,ppid=int(f[1]),starttime=f[19],state=f[0],cmdline=Path(f'/proc/{pid}/cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace'))
    except (FileNotFoundError,ProcessLookupError): return None

def gpu():
    raw=subprocess.check_output(['nvidia-smi','--query-compute-apps=pid,used_memory','--format=csv,noheader,nounits'],text=True)
    rows={}
    for line in raw.splitlines():
        f=line.split(',')
        if len(f)==2 and all(x.strip().isdigit() for x in f):rows[int(f[0])]=int(f[1])
    return rows

def release_check(path,pids):
    assert path.is_file(),'Missing main-agent release JSON'
    data=json.loads(path.read_text());assert data.get('released') is True,'Release not affirmative';assert pids,'No explicit 8-5 PID list'
    # Require each supplied PID appear as a numeric value anywhere in the release document.
    def values(x):
        if isinstance(x,dict): return list(map(str,x.keys())) + sum((values(v) for v in x.values()),[])
        if isinstance(x,list): return sum((values(v) for v in x),[])
        return [str(x)]
    vals=values(data)
    assert all(str(pid) in vals for pid in pids),'PID not in release document'
    evidence=[dict(pid=pid,proc=proc(pid)) for pid in pids]
    assert all(x['proc'] is None for x in evidence),'8-5 /proc PID still exists'
    listed=gpu();assert not set(pids)&set(listed),'8-5 PID still holds GPU memory'
    return dict(release_document=data,release_sha256=sha(path),checked_monotonic_ns=time.monotonic_ns(),pids=evidence,gpu=listed)

def collect(owned):
    states={int(p.name):proc(int(p.name)) for p in Path('/proc').glob('[0-9]*')};states={p:s for p,s in states.items() if s}
    changed=True
    while changed:
        changed=False
        for pid,s in states.items():
            parent=states.get(s['ppid']);known=owned.get(s['ppid'])
            if pid not in owned and known and parent and known['starttime']==parent['starttime']:
                owned[pid]=s;changed=True
    return states

def cleanup(owned):
    actions=[]
    for sig in (signal.SIGTERM,signal.SIGKILL):
        for pid,old in owned.items():
            now=proc(pid)
            if now and now['starttime']==old['starttime'] and now['state']!='Z':
                os.kill(pid,sig);actions.append(dict(pid=pid,signal=int(sig),proof=now,monotonic_ns=time.monotonic_ns()))
        if sig==signal.SIGTERM:time.sleep(2)
    return actions

def wait_release(owned,out):
    rows=[];deadline=time.monotonic()+60
    while True:
        listed=gpu();live=[p for p,s in owned.items() if (n:=proc(p)) and n['starttime']==s['starttime'] and n['state']!='Z']
        left=sorted(set(owned)&set(listed));rows.append(dict(monotonic_ns=time.monotonic_ns(),live=live,gpu_pids=left))
        dump(out/'release-wait.json',rows)
        if not live and not left:break
        if time.monotonic()>deadline:raise RuntimeError('Own processes or memory did not release')
        time.sleep(1)
    dump(out/'process-final.json',{str(p):proc(p) for p in owned})

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--release',type=Path,required=True);ap.add_argument('--released-pids',type=int,nargs='+',required=True);ap.add_argument('--output',type=Path,default=R/'results');ap.add_argument('--cache',type=Path,default=Path('/home/ubuntu/ai-infra-book-experiments/ch09/09-08/storage-v3'));a=ap.parse_args()
    proof=release_check(a.release,a.released_pids)
    a.output.mkdir(exist_ok=False);dump(a.output/'gpu-release-proof.json',proof)
    manifest=json.loads((R/'cache-manifest.json').read_text())
    for f in manifest:assert (a.cache/f['path']).stat().st_size==f['bytes'] and sha(a.cache/f['path'])==f['sha256']
    source=json.loads((R/'source-manifest.json').read_text())
    for f,h in source['sha256'].items():assert sha(Path(source['installed_root'])/f)==h
    rng=random.Random(9102);order=[]
    for trial in range(2):
        conditions=[1,8];rng.shuffle(conditions);order.extend(dict(trial=trial,count=n) for n in conditions)
    files=['run.py','worker.py','observer.py','source-manifest.json','config.json','inputs.json','reference.json','cache-manifest.json','PROTOCOL.md']
    dump(a.output/'plan.json',dict(order=order,source_sha256={f:sha(R/f) for f in files},cache_source=str(a.cache),controller_pid=os.getpid(),controller_proc=proc(os.getpid()),budget_MiB=24576))
    cuda=str(ENV/'lib/python3.10/site-packages/nvidia/cu13');env=dict(os.environ,CUDA_HOME=cuda,PATH=cuda+'/bin:'+os.environ['PATH'],TVM_FFI_CACHE_DIR='/home/ubuntu/ai-infra-book-experiments/ch09/09-08/jit-cache-cu13-v2',PYTHONUNBUFFERED='1',PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='4',MKL_NUM_THREADS='4',OPENBLAS_NUM_THREADS='4',NUMEXPR_NUM_THREADS='4')
    records=[]
    try:
        for c in order:
            release_check(a.release,a.released_pids)
            out=a.output/f"{c['trial']}-native-{c['count']}";out.mkdir()
            free=int(subprocess.check_output(['nvidia-smi','--query-gpu=memory.free','--format=csv,noheader,nounits'],text=True).strip());dump(out/'gpu-before.json',dict(free_MiB=free,processes=gpu()))
            assert free>=24576,'Less than 24GiB headroom; no existing service will be stopped'
            storage=out/'storage';storage.mkdir();begin=time.monotonic_ns()
            for f in manifest:
                shutil.copy2(a.cache/f['path'],storage/f['path']);assert sha(storage/f['path'])==f['sha256']
            dump(out/'cache-preparation.json',dict(files_verified=len(manifest),manifest_sha256=sha(R/'cache-manifest.json'),begin_ns=begin,end_ns=time.monotonic_ns()))
            runenv=dict(env,BOOK_BRANCH_TRACE=str((out/'events').resolve()),SGLANG_HICACHE_FILE_BACKEND_STORAGE_DIR=str(storage.resolve()))
            cmd=[str(ENV/'bin/python'),str(R/'worker.py'),'--count',str(c['count']),'--output',str(out.resolve())]
            owned={};resources=[];error=None
            with (out/'worker.log').open('x') as log:
                p=subprocess.Popen(cmd,env=runenv,stdout=log,stderr=subprocess.STDOUT)
                owned[p.pid]=proc(p.pid);assert owned[p.pid]
                dump(out/'launch.json',dict(command=cmd,pid=p.pid,proc=owned[p.pid],monotonic_ns=time.monotonic_ns()))
                deadline=time.monotonic()+600
                try:
                    while p.poll() is None:
                        collect(owned);dump(out/'owned-processes.json',{'processes':owned,'method':'Observed /proc PPID chain with parent starttime verification'})
                        memory=gpu();used=sum(memory.get(pid,0) for pid in owned)
                        resources.append(dict(monotonic_ns=time.monotonic_ns(),own_MiB=used,gpu=memory));dump(out/'resource-samples.json',resources)
                        if used>24576:raise RuntimeError('Own GPU allocation exceeds 24GiB budget')
                        if time.monotonic()>deadline:raise TimeoutError('Worker exceeded 600 seconds')
                        time.sleep(.5)
                except BaseException as e:error=repr(e)
                finally:
                    collect(owned);dump(out/'owned-processes.json',{'processes':owned,'method':'Observed /proc PPID chain with parent starttime verification'})
                    dump(out/'cleanup.json',cleanup(owned));p.wait(timeout=15)
            record=dict(**c,pid=p.pid,exit_code=p.returncode,error=error);records.append(record);dump(out/'coordinator.json',record);dump(a.output/'coordinator.json',records)
            wait_release(owned,out)
            dump(out/'gpu-after.json',gpu())
            assert p.returncode==0 and error is None,record
            assert list(out.glob('events.*.jsonl')),'No observer events'
            print(json.dumps(record),flush=True)
        dump(a.output/'execution.json',dict(status='completed',groups=len(records),controller_exit_code=0))
    except BaseException:
        dump(a.output/'failure.json',dict(traceback=traceback.format_exc(),records=records,monotonic_ns=time.monotonic_ns(),controller_exit_code=1));raise
    finally:
        dump(a.output/'source-after.json',{f:sha(Path(source['installed_root'])/f) for f in source['sha256']})
if __name__=='__main__':main()
