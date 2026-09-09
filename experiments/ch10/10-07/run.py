"""Actual DCP async completion and process-failure boundary experiment.

python run.py --output results
The fault writer blocks immediately before committing checkpoint metadata.
This gate is an explicit failure-injection device, not a bandwidth model.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import threading
import time


def child(root,fault):
    import torch
    import torch.distributed.checkpoint as dcp
    torch.set_num_threads(1)
    torch.manual_seed(1007)
    model=torch.nn.Sequential(torch.nn.Linear(1024,1024),torch.nn.Tanh(),torch.nn.Dropout(.1))
    optim=torch.optim.AdamW(model.parameters(),lr=.001)
    gen=torch.Generator().manual_seed(107)
    root.mkdir(parents=True,exist_ok=True)
    events=(root/'events.jsonl').open('w',buffering=1)
    lock=threading.Lock()
    def event(kind,**fields):
        with lock:events.write(json.dumps(dict(event=kind,monotonic_s=time.monotonic(),**fields))+'\n')
    def step():
        x=torch.randn(16,1024,generator=gen);target=torch.randn(16,1024,generator=gen)
        optim.zero_grad(set_to_none=True)
        loss=(model(x)-target).square().mean();loss.backward();optim.step()
        return loss.item()
    def snapshot(cursor):
        # Live tensor references are passed to DCP; staging must isolate them
        # before subsequent in-place optimizer updates.
        s={f'model.{k}':v for k,v in model.state_dict().items()}
        for i,p in enumerate(model.parameters()):
            for key,v in optim.state[p].items():s[f'optim.{i}.{key}']=v
        s.update(rng=torch.get_rng_state(),data_rng=gen.get_state(),cursor=torch.tensor(cursor))
        return s
    def hashes(s):return {k:hashlib.sha256(v.numpy().tobytes()).hexdigest() for k,v in s.items()}
    class Writer(dcp.FileSystemWriter):
        def __init__(self,label):
            super().__init__(root/label,sync_files=True)
            self.label=label
        def stage(self,s):
            event('stage_start',checkpoint=self.label)
            result=super().stage(s)
            event('stage_complete',checkpoint=self.label)
            return result
        def write_data(self,plan,planner):
            event('write_start',checkpoint=self.label)
            result=super().write_data(plan,planner)
            result.wait()
            event('data_write_complete',checkpoint=self.label)
            return result
        def finish(self,metadata,results):
            event('metadata_commit_enter',checkpoint=self.label)
            if fault and self.label=='checkpoint-2':
                (root/'fault-gate-ready').write_text('data files written; metadata not committed\n')
                threading.Event().wait()  # Parent terminates only this child.
            super().finish(metadata,results)
            event('metadata_commit_complete',checkpoint=self.label)
    for _ in range(3):step()
    expected={}
    for number,cursor in [(1,3),(2,23)]:
        label=f'checkpoint-{number}'
        s=snapshot(cursor)
        expected[label]=hashes(s)
        (root/'expected.json').write_text(json.dumps(expected,indent=2)+'\n')
        writer=Writer(label)
        event('api_call',checkpoint=label)
        future=dcp.async_save(s,storage_writer=writer,no_dist=True)
        event('api_return',checkpoint=label,future_done=future.done())
        started=time.perf_counter()
        losses=[step() for _ in range(20)]
        event('training_complete',checkpoint=label,steps=20,seconds=time.perf_counter()-started,last_loss=losses[-1])
        if fault and number==2:
            (root/'training-ready').write_text('twenty post-snapshot steps completed\n')
        future.result()
        event('future_complete',checkpoint=label)
    # Reload into zero destinations after training has advanced beyond snapshots.
    recovered={}
    for label in expected:
        target={k:torch.zeros_like(v) for k,v in snapshot(43).items()}
        started=time.perf_counter();dcp.load(target,checkpoint_id=root/label,no_dist=True)
        assert hashes(target)==expected[label]
        recovered[label]=dict(cursor=int(target['cursor']),load_s=time.perf_counter()-started,hashes=hashes(target))
    (root/'recovered.json').write_text(json.dumps(recovered,indent=2)+'\n')
    (root/'environment.json').write_text(json.dumps(dict(torch=torch.__version__,device='cpu',threads=1,
        source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        failure_gate='before metadata commit after data write' if fault else None),indent=2)+'\n')
    events.close()


def run(args):
    root=args.output.resolve()
    if root.exists():raise RuntimeError('Use a new output directory to retain previous evidence.')
    root.mkdir(parents=True)
    outcomes={}
    for case in ['normal','fault']:
        dest=root/case;dest.mkdir()
        with (dest/'process.log').open('w') as log:
            cmd=[sys.executable,str(Path(__file__).resolve()),'--output',str(dest),'--child']
            if case=='fault':cmd.append('--fault')
            process=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT)
            if case=='fault':
                deadline=time.monotonic()+120
                while not ((dest/'fault-gate-ready').exists() and (dest/'training-ready').exists()):
                    if process.poll() is not None:raise RuntimeError(f'Child exited early: {process.returncode}')
                    if time.monotonic()>deadline:
                        process.terminate();process.wait(timeout=10);raise TimeoutError('Fault gate not reached')
                    time.sleep(.02)
                killed=time.monotonic();process.kill()
            code=process.wait(timeout=120)
        assert code==(-signal.SIGKILL if case=='fault' else 0),code
        outcomes[case]=dict(returncode=code)
        if case=='fault':outcomes[case]['sigkill_monotonic_s']=killed
    import torch
    import torch.distributed.checkpoint as dcp
    fault=root/'fault'
    # Templates from complete checkpoint metadata, without touching partial metadata.
    meta=dcp.FileSystemReader(fault/'checkpoint-1').read_metadata()
    def empty():return {k:torch.zeros(v.size,dtype=v.properties.dtype) for k,v in meta.state_dict_metadata.items()}
    target=empty();dcp.load(target,checkpoint_id=fault/'checkpoint-1',no_dist=True)
    hashes={k:hashlib.sha256(v.numpy().tobytes()).hexdigest() for k,v in target.items()}
    assert hashes==json.loads((fault/'expected.json').read_text())['checkpoint-1']
    failure=None
    try:dcp.load(empty(),checkpoint_id=fault/'checkpoint-2',no_dist=True)
    except BaseException as exc:
        if isinstance(exc,(KeyboardInterrupt,SystemExit)):raise
        failure=dict(type=type(exc).__name__,message=str(exc))
    assert failure is not None
    assert not (fault/'checkpoint-2/.metadata').exists()
    outcomes['fault'].update(recovered_cursor=int(target['cursor']),recovered_hashes=hashes,
                            incomplete_load_error=failure,
                            incomplete_data_files=[p.name for p in (fault/'checkpoint-2').glob('*.distcp')])
    outcomes['source_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    (root/'outcomes.json').write_text(json.dumps(outcomes,indent=2)+'\n')
    print(json.dumps(dict(normal_completed=True,fault_exit=outcomes['fault']['returncode'],
                          recovered_cursor=int(target['cursor']),incomplete_rejected=True)))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True)
    p.add_argument('--child',action='store_true');p.add_argument('--fault',action='store_true')
    args=p.parse_args()
    child(args.output,args.fault) if args.child else run(args)
