"""Validate native records; no historical C70 data or voice inference."""
import argparse,hashlib,json
from pathlib import Path
BASE=Path(__file__).absolute().parent

def analyze():
    lock=json.loads((BASE/'source-lock.json').read_text())
    for r in lock['files']:
        x=(BASE/'source'/r['path']).read_bytes()
        assert len(x)==r['bytes'] and hashlib.sha256(x).hexdigest()==r['sha256']
    rows=[];latencies=[];reference=None;last_end=0
    for i,pool in enumerate([True,False,False,True]):
        d=BASE/'runs'/f'{i}-pool-{str(pool).lower()}'
        x=json.loads((d/'raw.json').read_text());e=json.loads((d/'execution.json').read_text())
        assert e['exit_code']==0 and last_end<=e['start_unix_s']<=e['end_unix_s'];last_end=e['end_unix_s']
        assert x['schema_version']==1 and x['source']['goos']=='darwin' and x['source']['goarch']=='arm64'
        p=dict(x['path']);assert p.pop('quic_pool')==pool
        if reference is None:reference=p
        assert p==reference
        assert (p['rtt_ms'],p['rate_mbits'],p['queue_bytes'],p['object_bytes'],p['seed'],p['loss_percent'])==(40,100,500000,355000,1207,0)
        assert [(r['stack'],r['flows']) for r in x['trials']]==[('baseline',1),('baseline',4),('queqiao',1),('queqiao',4)]
        assert [r['stack'] for r in x['latency']]==['baseline','queqiao']
        for r in x['trials']:
            assert r['complete'] and r['seconds']>0 and r['mbits_per_sec']>0
            # Native seconds and goodput were rounded independently to .001.
            duration=p['object_bytes']*r['flows']*8/(r['mbits_per_sec']*1e6)
            assert abs(duration-r['seconds'])<.0006
            rows.append(dict(round=i,pool=pool,**r))
        for r in x['latency']:
            assert r['complete'] and r['cold_ms']>0 and r['warm_ms']>0
            latencies.append(dict(round=i,pool=pool,**r))
    return dict(revision=lock['revision'],path_except_pool=reference,bulk_cells=rows,latency_cells=latencies,
        successful_bulk_cells=len(rows),successful_latency_pairs=len(latencies),
        first_playable_ms=None,audio_stall_count=None,cancel_latency_ms=None,voice_quality=None,
        boundary='Native loopback sockets plus userspace path emulation; complete means received expected byte count, not content hash or audio quality.')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,default=BASE/'analysis.json');a=p.parse_args()
    a.out.write_text(json.dumps(analyze(),ensure_ascii=False,indent=2)+'\n')
