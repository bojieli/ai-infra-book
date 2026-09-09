"""Verify actual requests, storage calls and archived file content offline."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent

def main():
    rows=[];all_outputs=[];raws={};traces={}
    for phase in ['producer','consumer']:
        path=ROOT/'results'/f'{phase}-v6';d=json.loads((path/'raw.json').read_text());raws[phase]=d
        for name,sha in d['source_hashes'].items():assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==sha,name
        assert len(d['requests'])==3
        t=[json.loads(x) for x in (path/'storage.jsonl').read_text().splitlines()];traces[phase]=t
        assert all(x['success'] for x in t)
        for r in d['requests']:
            o=r['response'];m=o['meta_info'];assert m['prompt_tokens']==1024 and m['completion_tokens']==16 and m['num_retractions']==0
            assert len(o['output_ids'])==16;all_outputs.append(o['output_ids'])
            rows.append(dict(phase=phase,index=r['index'],elapsed_s=r['end_s']-r['start_s'],cached_tokens=m['cached_tokens'],details=m['cached_tokens_details']))
    assert all(o==all_outputs[0] for o in all_outputs)
    assert raws['producer']['config']==raws['consumer']['config']
    assert rows[0]['cached_tokens']==0
    assert rows[3]['details']==dict(device=0,host=0,storage=1008,storage_backend='HiCacheFile')
    assert all(rows[i]['details']['device']==1008 for i in [1,2,4,5])
    files={f['path']:f for f in raws['producer']['storage_files']}
    assert files=={f['path']:f for f in raws['consumer']['storage_files']}
    assert len(files)==65
    for name,f in files.items():
        b=(ROOT/'storage-v3'/name).read_bytes();assert len(b)==f['bytes'];assert hashlib.sha256(b).hexdigest()==f['sha256']
    gets=[x for x in traces['consumer'] if x['method']=='get']
    sets=[x for x in traces['producer'] if x['method']=='set']
    assert len(gets)==64 and len(sets)==65 and len({x['key'] for x in gets})==64
    assert not any(x['method']=='get' for x in traces['producer'])
    assert {x['pid'] for x in traces['producer']}.isdisjoint({x['pid'] for x in traces['consumer']})
    for x in gets:
        assert Path(x['file']).name in files
        assert x['bytes']==files[Path(x['file']).name]['bytes']
        assert raws['consumer']['requests'][0]['start_s']<=x['start_s']<=x['end_s']<=raws['consumer']['requests'][0]['end_s']
    report=dict(status='passed',requests=rows,output_ids=all_outputs[0],file_count=len(files),stored_bytes=sum(f['bytes'] for f in files.values()),read_calls=len(gets),read_file_bytes=sum(x['bytes'] for x in gets),get_wall_interval_s=max(x['end_s'] for x in gets)-min(x['start_s'] for x in gets),limitations=['one sequential restart pair; no speedup estimate','file bytes are not physical disk IO; page cache uncontrolled','no fsync/crash consistency or remote PD claim'])
    (ROOT/'summary.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,ensure_ascii=False))
if __name__=='__main__':main()
