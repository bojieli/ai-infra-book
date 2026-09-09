"""Execute pinned original ServeGen on an explicitly selected public chunk."""
import ast,hashlib,json,os,sys
from dataclasses import asdict
from pathlib import Path
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'vendor'))
import numpy as np
import scipy
from scipy.stats import spearmanr
from servegen import Category,ClientPool
from servegen.construct import generate_workload,_sample_iats

def scalar(x):
    if isinstance(x,np.generic):return x.item()
    raise TypeError(type(x).__name__)
def correlation(a,b):
    return float(spearmanr(a,b).statistic) if len(set(a))>1 and len(set(b))>1 else None
def main():
    out=ROOT/'results'
    if out.exists():raise RuntimeError('Fresh results directory required')
    sources=json.loads((ROOT/'sources.json').read_text())
    for f in sources['files']:assert hashlib.sha256((ROOT/f['path']).read_bytes()).hexdigest()==f['sha256']
    # Verify all loader-evaluated strings are numeric literal dictionaries first.
    dataset=json.loads((ROOT/'vendor/data/language/m-small/chunk-0-dataset.json').read_text())
    for fields in dataset.values():
        for value in fields.values():
            d=ast.literal_eval(value);assert isinstance(d,dict)
            assert all(isinstance(k,(int,float)) and isinstance(v,(int,float)) and np.isfinite(k) and np.isfinite(v) for k,v in d.items())
    os.chdir(ROOT/'vendor')
    pool=ClientPool(Category.LANGUAGE,'m-small')
    assert list(pool.clients)==[0]
    client=pool.clients[0]
    starts=[ts for ts,r in client.trace.items() if r and r['rate']>0]
    out.mkdir();reports=[]
    for start in starts:
        view=pool.span(start,start+120);window=view.get()[0]
        assert window.dataset is not None
        for seed in [302,303,304]:
            requests=generate_workload(view,{0:4.0},duration=120,seed=seed)
            rows=[asdict(r) for r in requests]
            assert rows and [r['request_id'] for r in rows]==list(range(len(rows)))
            assert all(0<=r['timestamp']<120 for r in rows)
            assert all(a['timestamp']<=b['timestamp'] for a,b in zip(rows,rows[1:]))
            iats=_sample_iats(window,4.0,np.random.RandomState(seed));a=[r['data']['input_tokens'] for r in rows];b=[r['data']['output_tokens'] for r in rows]
            shuffled=np.random.RandomState(seed+1000).permutation(b).tolist()
            file=f'window-{start}-seed-{seed}.json';(out/file).write_text(json.dumps(rows,default=scalar)+'\n')
            reports.append(dict(source_window_start=start,seed=seed,arrival_pattern=window.arrival_pat,
                generated_requests=len(rows),target_requests=480,realized_generated_rate=len(rows)/120,
                first_s=rows[0]['timestamp'],last_s=rows[-1]['timestamp'],
                sampled_iats_count=len(iats),sampled_iats_sum=float(np.sum(iats)),unfiltered_final_timestamp=float(np.cumsum(iats)[-1]),
                input_min=int(min(a)),input_max=int(max(a)),output_min=int(min(b)),output_max=int(max(b)),
                input_output_spearman=correlation(a,b),shuffled_output_spearman=correlation(a,shuffled),
                fields=list(rows[0]['data']),request_fields=list(rows[0]),file=file,
                sha256=hashlib.sha256((out/file).read_bytes()).hexdigest()))
    result=dict(status='passed',numpy=np.__version__,scipy=scipy.__version__,revision=sources['revision'],client_ids=[0],
        source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),cases=reports,
        scope='Five active windows from public m-small chunk0, first120s of each, target4rps, three seeds. Original generator and loader unmodified. Marginal PDFs are public; generated joint pairing is not observed production pairing. Request lacks client/conversation IDs and prefix hashes.')
    (out/'summary.json').write_text(json.dumps(result,indent=2,default=scalar)+'\n')
    for r in reports:print(r['source_window_start'],r['seed'],r['generated_requests'],r['input_output_spearman'],r['shuffled_output_spearman'])
if __name__=='__main__':main()
