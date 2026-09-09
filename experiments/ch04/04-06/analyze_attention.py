import hashlib,json,statistics
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parent

def analyze():
    reports={d:json.loads((ROOT/f'results/attention-{d}/results.json').read_text()) for d in ['mps','cuda']}
    arrays={d:np.load(ROOT/f'results/attention-{d}/tensors.npz') for d in reports}
    summary=[]
    expected=['prefill-128','prefill-257','prefill-512','prefill-2048','decode-2048']
    for d,report in reports.items():
        assert report['environment']['source_sha256']==hashlib.sha256((ROOT/'attention.py').read_bytes()).hexdigest()
        assert report['environment']['fallback_env'] in ['unset','0']
        assert [r['case'] for r in report['rows']]==expected
        for r in report['rows']:
            case=r['case'];z=arrays[d];q,k,v=[z[f'{case}_{name}'].astype(np.float64) for name in ('q','k','v')]
            for name in ['q','k','v']:
                t=z[f'{case}_{name}']
                assert hashlib.sha256(t.tobytes()).hexdigest()==r['input_sha256'][name]
                np.testing.assert_array_equal(t,arrays['mps'][f'{case}_{name}'])
            scores=q@k.swapaxes(-1,-2)/np.sqrt(128)
            if case.startswith('prefill'):
                scores=np.where(np.triu(np.ones((r['n'],r['n']),dtype=bool),1),-np.inf,scores)
                assert r['causal_future_value_check']=='passed'
            weights=np.exp(scores-np.max(scores,axis=-1,keepdims=True));weights/=weights.sum(-1,keepdims=True)
            reference=weights@v
            np.testing.assert_allclose(reference,z[f'{case}_reference'],atol=1e-12,rtol=1e-12)
            for path,result in r['paths'].items():
                actual=z[f'{case}_{path}'].astype(np.float64)
                np.testing.assert_allclose(actual,reference,atol=.002,rtol=.01)
                error=float(np.max(np.abs(actual-reference)))
                assert abs(error-result['max_abs_error'])<1e-12
                times=result['samples_wall_us'];assert len(times)==11 and all(np.isfinite(t) and t>0 for t in times)
                summary.append(dict(device=d,case=case,path=path,median_wall_us=statistics.median(times),max_abs_error=error))
        # Decode uses exactly the final prefill query and all prior KV, so its reference must agree.
        np.testing.assert_allclose(arrays[d]['decode-2048_reference'],arrays[d]['prefill-2048_reference'][:,:,-1:,:],atol=1e-12,rtol=1e-12)
    return summary
if __name__=='__main__':
    (ROOT/'results/attention-summary.json').write_text(json.dumps(analyze(),indent=2)+'\n')
    print('PASS: identical inputs, independent NumPy FP64 references, all 20 outputs and 220 batches')
