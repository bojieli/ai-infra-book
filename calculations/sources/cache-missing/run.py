import argparse,hashlib,json,os,time
from pathlib import Path
from storage_trace import install
install()
ROOT=Path(__file__).resolve().parent

def main(a):
    if a.output.exists():raise RuntimeError('Fresh output required')
    a.output.mkdir(parents=True);os.environ['BOOK_HICACHE_TRACE']=str((a.output/'storage.jsonl').resolve());os.environ['SGLANG_HICACHE_FILE_BACKEND_STORAGE_DIR']=str(a.storage.resolve())
    import sglang as sgl
    config=json.loads((ROOT/'config.json').read_text());ids=json.loads((ROOT/'inputs.json').read_text())
    begin=time.monotonic();engine=sgl.Engine(**config);ready=time.monotonic();records=[]
    try:
        for i in range(3):
            start=time.monotonic();response=engine.generate(input_ids=ids,sampling_params=dict(temperature=0,max_new_tokens=16,ignore_eos=True))
            records.append(dict(index=i,start_s=start,end_s=time.monotonic(),response=response));print('request',i,'completed',flush=True)
        # Observe actual files until all expected prefix pages exist; max wait is not a measured persistence guarantee.
        deadline=time.monotonic()+15
        while len(list(a.storage.glob('*.bin')))<len(ids)//16-1 and time.monotonic()<deadline:time.sleep(.05)
        info=engine.get_server_info()
    finally:engine.shutdown()
    files=[dict(path=p.name,bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in sorted(a.storage.glob('*.bin'))]
    result=dict(status='passed',phase=a.phase,config=config,ready_s=ready-begin,requests=records,server_info=info,storage_files=files,source_hashes={f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in ['run.py','storage_trace.py','config.json','inputs.json']})
    (a.output/'raw.json').write_text(json.dumps(result,indent=2,default=str)+'\n')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--storage',type=Path,required=True);p.add_argument('--phase',required=True);main(p.parse_args())
