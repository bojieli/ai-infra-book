import hashlib,json,math,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parent

def analyze():
    summary=[]
    for device in ('mac','rtx'):
        rows=json.loads((ROOT/f'results/{device}/results.json').read_text())
        assert len(rows)==6
        assert [r['m'] for r in rows if r['kind']=='matmul']==[1,32,256]
        assert [r['payload_bytes'] for r in rows if r['kind']=='copy']==[16*1024**2,64*1024**2,256*1024**2]
        for r in rows:
            assert len(r['samples'])==11
            assert all(math.isfinite(s[k]) and s[k]>0 for s in r['samples'] for k in ('gpu_s','wall_s'))
            if r['kind']=='matmul':
                assert r['k']==r['n']==512 and r['max_abs_error_fp64']==0
                assert r['reference_elements']==r['m']*r['n']
                label=f"M={r['m']}"
            else:
                assert r['all_bytes_match'] is True
                label=f"{r['payload_bytes']//1024**2} MiB"
            t=statistics.median(s['gpu_s'] for s in r['samples'])
            item=dict(device=device,kind=r['kind'],label=label,gpu_median_us=t*1e6,
                      wall_median_us=statistics.median(s['wall_s'] for s in r['samples'])*1e6)
            if r['kind']=='copy':item['payload_GB_s']=r['payload_bytes']/t/1e9
            summary.append(item)
    env=json.loads((ROOT/'results/rtx/environment.json').read_text())
    assert env['source_sha256']==hashlib.sha256((ROOT/'rtx.py').read_bytes()).hexdigest()
    return summary
if __name__=='__main__':
    (ROOT/'results/summary.json').write_text(json.dumps(analyze(),indent=2)+'\n')
    print('Validated 12 configurations, 132 timing samples and recorded correctness checks')
