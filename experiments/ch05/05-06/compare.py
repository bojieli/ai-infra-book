"""Post-selection interleaved validation; does not search or change protocol."""
import argparse
import hashlib
import json
from pathlib import Path
import random
import subprocess
import time
import torch
import triton
from evaluate_v2 import native, expression
import schedule

ROOT=Path(__file__).resolve().parent
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def gpu():return subprocess.check_output(['nvidia-smi','--query-compute-apps=pid,process_name,used_memory','--format=csv'],text=True)
def main(a):
    if a.output.exists():raise RuntimeError('Use fresh output directory')
    a.output.mkdir(parents=True)
    protocol=json.loads((ROOT/'protocol.json').read_text())
    selection=json.loads((ROOT/'results/schedule-summary.json').read_text())['selected_schedule']
    out=dict(protocol_sha256=sha(ROOT/'protocol.json'),selection_sha256=sha(ROOT/'results/schedule-summary.json'),
        source_hashes={f:sha(ROOT/f) for f in ['compare.py','evaluate_v2.py','schedule.py']},
        torch=torch.__version__,triton=triton.__version__,gpu_before=gpu(),seed=506,
        scope='Post-selection validation, no new search. Interleaved eager/graph event samples with resident services. Pmon 1-second sampling cannot prove an exclusive GPU window.',
        correctness=[],samples=[],profiles=[],status='running')
    process_log=(a.output/'gpu-activity.log').open('w')
    monitor=subprocess.Popen(['nvidia-smi','pmon','-s','um','-d','1'],stdout=process_log,stderr=subprocess.STDOUT)
    origin=time.perf_counter();rng=random.Random(506)
    try:
        funcs={'native':native,'compiled':torch.compile(expression,fullgraph=True),
            'schedule':lambda x:schedule.run(x,selection['block'],selection['warps'])}
        for index in [1,0]:
            data=torch.load(ROOT/f'results/capture/tensors/layer0-call{index}.pt',weights_only=True)
            x=data['input'].cuda();ref=data['reference'].cuda();t=x.shape[0]
            assert torch.equal(native(x),ref)
            graphs={};outputs={}
            for name,fn in funcs.items():
                start=time.perf_counter();y=fn(x);torch.cuda.synchronize()
                preparation=time.perf_counter()-start
                assert y.shape==ref.shape and y.dtype==ref.dtype
                assert y.untyped_storage().data_ptr()!=x.untyped_storage().data_ptr()
                torch.testing.assert_close(y,ref,atol=protocol['atol'],rtol=protocol['rtol'])
                assert torch.equal(x.cpu(),data['input'])
                for _ in range(protocol['warmups']):fn(x)
                graph=torch.cuda.CUDAGraph()
                with torch.cuda.graph(graph):
                    for _ in range(protocol['graph_repeats']):y=fn(x)
                for _ in range(3):graph.replay()
                torch.cuda.synchronize()
                torch.testing.assert_close(y,ref,atol=protocol['atol'],rtol=protocol['rtol'])
                graphs[name]=graph;outputs[name]=y
                out['correctness'].append(dict(t=t,name=name,prepare_s=preparation,
                    different_elements=int((y!=ref).sum()),max_abs_error=float((y.float()-ref.float()).abs().max())))
            # Every trial has all three implementations and both submission modes.
            for trial in range(protocol['trials']):
                order=[(name,mode) for name in funcs for mode in ['eager','graph']];rng.shuffle(order)
                for rank,(name,mode) in enumerate(order):
                    begin,end=torch.cuda.Event(enable_timing=True),torch.cuda.Event(enable_timing=True)
                    torch.cuda.synchronize();wall=time.perf_counter();begin.record()
                    if mode=='graph':graphs[name].replay()
                    else:
                        for _ in range(protocol['graph_repeats']):y=funcs[name](x)
                    end.record();end.synchronize()
                    out['samples'].append(dict(t=t,trial=trial,order=rank,name=name,mode=mode,
                        event_us=begin.elapsed_time(end)*1000/protocol['graph_repeats'],
                        wall_us=(time.perf_counter()-wall)*1e6/protocol['graph_repeats']))
            for name,fn in funcs.items():
                with torch.profiler.profile(activities=[torch.profiler.ProfilerActivity.CPU,torch.profiler.ProfilerActivity.CUDA]) as prof:
                    y=fn(x);torch.cuda.synchronize()
                trace=a.output/f'trace-{t}-{name}.json';prof.export_chrome_trace(str(trace))
                trace_data=json.loads(trace.read_text())
                kernels=[e for e in trace_data['traceEvents'] if e.get('cat')=='kernel']
                out['profiles'].append(dict(t=t,name=name,trace=trace.name,
                    kernels=[dict(name=e['name'],duration_us=e['dur'],stream=e.get('args',{}).get('stream')) for e in kernels]))
                torch.testing.assert_close(y,ref,atol=protocol['atol'],rtol=protocol['rtol'])
                torch.testing.assert_close(outputs[name],ref,atol=protocol['atol'],rtol=protocol['rtol'])
            assert torch.equal(x.cpu(),data['input'])
            del graphs,outputs,x,ref,data,y
            torch.cuda.empty_cache()
        out['status']='passed'
    finally:
        monitor.terminate();monitor.wait(timeout=10);process_log.close()
        out['elapsed_s']=time.perf_counter()-origin;out['gpu_after']=gpu()
        (a.output/'raw.json').write_text(json.dumps(out,indent=2)+'\n')
    print(out['status'],len(out['samples']),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);main(p.parse_args())
