import json,os,time
from pathlib import Path
from storage_trace import install
install()
ROOT=Path(__file__).resolve().parent

def event(name,**kw):
 with (ROOT/'results/lifecycle.jsonl').open('a') as f:f.write(json.dumps(dict(event=name,time_s=time.monotonic(),pid=os.getpid(),**kw))+'\n')
def main():
 os.environ['BOOK_HICACHE_TRACE']=str(ROOT/'results/storage.jsonl');os.environ['SGLANG_HICACHE_FILE_BACKEND_STORAGE_DIR']=str(ROOT/'storage')
 import sglang as sgl
 event('initializing');engine=sgl.Engine(**json.loads((ROOT/'config.json').read_text()));event('ready')
 try:
  event('request_start')
  out=engine.generate(input_ids=json.loads((ROOT/'inputs.json').read_text()),sampling_params=dict(temperature=0,max_new_tokens=16,ignore_eos=True))
  event('request_return',response=out)
 except Exception as e:event('request_exception',type=type(e).__name__,message=str(e));raise
 finally:
  event('shutdown_start');engine.shutdown();event('shutdown_end')
if __name__=='__main__':main()
