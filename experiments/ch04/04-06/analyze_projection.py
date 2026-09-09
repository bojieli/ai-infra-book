import hashlib,json,statistics
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parent

def analyze():
    predictions=json.loads((ROOT/'results/prediction-compatibility.json').read_text())['records']
    rows=[];inputs={};activation_hashes={}
    for device in ['mps','cuda']:
        d=json.loads((ROOT/f'results/projection-{device}/results.json').read_text());z=np.load(ROOT/f'results/projection-{device}/tensors.npz')
        e=d['environment'];assert e['source_sha256']==hashlib.sha256((ROOT/'projection.py').read_bytes()).hexdigest()
        assert len(set(e['weight_addresses']))==e['weight_buffers']==16 and e['weight_buffer_bytes']==33554432
        weight=z['weight'];assert hashlib.sha256(weight.tobytes()).hexdigest()==e['weight_sha256']
        inputs[device]=e['weight_sha256']
        assert [r['m'] for r in d['rows']]==[1,256]
        for r in d['rows']:
            m=r['m'];a=z[f'a_{m}'];assert a.shape==(m,4096) and weight.shape==(4096,4096)
            assert hashlib.sha256(a.tobytes()).hexdigest()==r['input_sha256']
            if m in activation_hashes:assert activation_hashes[m]==r['input_sha256']
            activation_hashes[m]=r['input_sha256']
            ref=a.astype(np.float64)@weight.astype(np.float64)
            np.testing.assert_array_equal(ref,z[f'ref_{m}'])
            for i in [0,15]:np.testing.assert_allclose(z[f'output_{m}_{i}'],ref,atol=.01,rtol=.01)
            assert r['all_16_weight_buffers_checked']
            model_device='m2-max-38gpu-96gb' if device=='mps' else 'rtx-pro6000-blackwell-ws'
            pred=next(x for x in predictions if x['scenario']['device']==model_device and x['scenario']['batch']==m)
            assert pred['shapes']['A']==[m,4096] and pred['shapes']['W_math']==[4096,4096]
            for mode,p in r['paths'].items():
                assert len(p['wall_us'])==11 and all(np.isfinite(v) and v>0 for v in p['wall_us'])
                assert len(p['cuda_event_us'])==(11 if device=='cuda' else 0)
                rows.append(dict(device=device,m=m,mode=mode,wall_median_us=statistics.median(p['wall_us']),
                                 event_median_us=statistics.median(p['cuda_event_us']) if device=='cuda' else None,
                                 reference_max_abs_error=float(np.max(np.abs(z[f'output_{m}_15']-ref))),
                                 predicted_memory_service_us=pred['summary']['memory_service_seconds']*1e6,
                                 predicted_roofline_us=pred['summary']['roofline_lower_bound_seconds']*1e6 if pred['summary']['roofline_lower_bound_seconds'] else None,
                                 comparison='shape/dtype matched; cache state not measured; wall includes host overhead. MPS accumulator precision not independently verified. No efficiency ratio.'))
    assert inputs['mps']==inputs['cuda']
    return rows
if __name__=='__main__':
    result=analyze();(ROOT/'results/projection-summary.json').write_text(json.dumps(result,indent=2)+'\n')
    for r in result:print(r['device'],r['m'],r['mode'],round(r['wall_median_us'],3),r['reference_max_abs_error'])
