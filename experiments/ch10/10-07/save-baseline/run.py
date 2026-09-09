"""Matched no-save / synchronous / asynchronous actual CPU training windows."""
import argparse,hashlib,json,os,random,resource,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parent

def child(out,mode,trial):
    import torch
    import torch.distributed.checkpoint as dcp
    torch.set_num_threads(1);torch.manual_seed(1007)
    model=torch.nn.Sequential(torch.nn.Linear(1024,1024),torch.nn.Tanh(),torch.nn.Dropout(.1))
    optim=torch.optim.AdamW(model.parameters(),lr=.001);gen=torch.Generator().manual_seed(107)
    def step():
        x=torch.randn(16,1024,generator=gen);target=torch.randn(16,1024,generator=gen)
        optim.zero_grad(set_to_none=True);loss=(model(x)-target).square().mean();loss.backward();optim.step();return loss.item()
    def state(cursor):
        s={f'model.{k}':v for k,v in model.state_dict().items()}
        for i,p in enumerate(model.parameters()):
            for k,v in optim.state[p].items():s[f'optim.{i}.{k}']=v
        s.update(rng=torch.get_rng_state(),data_rng=gen.get_state(),cursor=torch.tensor(cursor));return s
    def hashes(s):return {k:hashlib.sha256(v.numpy().tobytes()).hexdigest() for k,v in s.items()}
    out.mkdir(parents=True);events=[]
    def event(name):events.append(dict(event=name,t_s=time.monotonic()))
    class Writer(dcp.FileSystemWriter):
        def stage(self,s):
            event('stage_start');r=super().stage(s);event('stage_end');return r
        def write_data(self,*a,**kw):
            event('write_start');r=super().write_data(*a,**kw);r.wait();event('write_end');return r
        def finish(self,*a,**kw):
            event('commit_start');r=super().finish(*a,**kw);event('commit_end');return r
    for _ in range(3):step()
    snapshot=state(3);expected=hashes(snapshot)
    writer=Writer(out/'checkpoint',sync_files=True) if mode!='none' else None
    rss_before=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    event('window_start');future=None
    if mode=='sync':
        event('save_call');dcp.save(snapshot,storage_writer=writer,no_dist=True);event('save_return')
    if mode=='async':
        event('save_call');future=dcp.async_save(snapshot,storage_writer=writer,no_dist=True);event('save_return')
    event('training_start');losses=[]
    for i in range(20):
        t=time.monotonic();loss=step();losses.append(dict(step=i+4,loss=loss,start_s=t,end_s=time.monotonic()))
    event('training_end')
    if future is not None:future.result();event('future_observed_complete')
    event('window_end');rss_after=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    final=hashes(state(23));restored=None
    if mode!='none':
        dst={k:torch.zeros_like(v) for k,v in state(23).items()};dcp.load(dst,checkpoint_id=out/'checkpoint',no_dist=True)
        restored=hashes(dst);assert restored==expected
    result=dict(status='passed',mode=mode,trial=trial,events=events,steps=losses,expected_snapshot=expected,restored_snapshot=restored,final_state=final,torch=torch.__version__,threads=1,device='cpu',ru_maxrss_before_kib=rss_before,ru_maxrss_after_kib=rss_after,checkpoint_files=[dict(path=str(p.relative_to(out)),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in sorted((out/'checkpoint').rglob('*')) if p.is_file()],source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    (out/'raw.json').write_text(json.dumps(result,indent=2)+'\n')

def main(a):
    if a.child:return child(a.output,a.mode,a.trial)
    if a.output.exists():raise RuntimeError('Fresh output required')
    a.output.mkdir(parents=True);order=[];rng=random.Random(1007)
    for trial in range(5):
        modes=['none','sync','async'];rng.shuffle(modes)
        for mode in modes:
            dest=a.output/f'trial-{trial}-{mode}'
            with (a.output/f'trial-{trial}-{mode}.log').open('w') as log:
                subprocess.run([sys.executable,str(Path(__file__).resolve()),'--child','--mode',mode,'--trial',str(trial),'--output',str(dest)],stdout=log,stderr=subprocess.STDOUT,check=True)
            order.append(dict(trial=trial,mode=mode,path=dest.name));print(trial,mode,'complete',flush=True)
    (a.output/'order.json').write_text(json.dumps(order,indent=2)+'\n')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--child',action='store_true');p.add_argument('--mode',choices=['none','sync','async']);p.add_argument('--trial',type=int);main(p.parse_args())
