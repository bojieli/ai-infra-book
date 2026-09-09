"""Exercise the installed file backend on isolated copies of a real KV page."""
import hashlib,inspect,json,os,time
from pathlib import Path
import torch,sglang
from sglang.srt.mem_cache.hicache_storage import HiCacheFile,HiCacheStorageConfig
ROOT=Path(__file__).resolve().parent
sha=lambda b:hashlib.sha256(b).hexdigest()
def main():
 out=ROOT/'results';assert not out.exists();out.mkdir()
 os.environ.pop('SGLANG_HICACHE_FILE_BACKEND_STORAGE_DIR',None)
 source=(ROOT/'page.bin').read_bytes();assert len(source)==2359296
 cfg=dict(tp_rank=0,tp_size=1,pp_rank=0,pp_size=1,attn_cp_rank=0,attn_cp_size=1,is_mla_model=False,enable_storage_metrics=False,is_page_first_layout=False,model_name='fixed-qwen-snapshot')
 records=[]
 for case in ['intact','missing','truncated','bitflip','trailing_bytes','model_identity_changed','set_existing_corrupt']:
  path=out/case;backend=HiCacheFile(HiCacheStorageConfig(**cfg),file_path=str(path));key='real-page-fixture'
  filename=path/(backend._get_suffixed_key(key)+'.bin')
  data=source
  if case=='truncated':data=source[:-2]
  if case in ['bitflip','set_existing_corrupt']:
   data=bytes([source[0]^1])+source[1:]
  if case=='trailing_bytes':data=source+b'EXTRA'
  if case!='missing':filename.write_bytes(data)
  before=filename.read_bytes() if filename.exists() else None
  if case=='model_identity_changed':backend=HiCacheFile(HiCacheStorageConfig(**{**cfg,'model_name':'different-qwen-snapshot'}),file_path=str(path))
  target=torch.zeros(len(source)//2,dtype=torch.bfloat16);start=time.monotonic()
  record=dict(case=case,before_bytes=len(before) if before is not None else None,before_sha256=sha(before) if before is not None else None,exists=backend.exists(key))
  if case=='set_existing_corrupt':
   value=torch.frombuffer(bytearray(source),dtype=torch.bfloat16).clone();record['set_result']=backend.set(key,value=value)
  try:
   result=backend.get(key,target);record.update(returned_tensor=result is not None,exception=None)
  except Exception as e:record.update(returned_tensor=False,exception=dict(type=type(e).__name__,message=str(e)))
  target_bytes=target.view(torch.uint8).numpy().tobytes();record.update(elapsed_s=time.monotonic()-start,target_sha256=sha(target_bytes),target_equals_reference=target_bytes==source,target_changed_from_zero=any(target_bytes))
  after=filename.read_bytes() if filename.exists() else None;record.update(after_sha256=sha(after) if after is not None else None,after_equals_reference=after==source)
  records.append(record)
 expected={r['case']:r for r in records}
 assert expected['intact']['target_equals_reference']
 assert not expected['missing']['returned_tensor'] and expected['missing']['exception'] is None
 assert expected['truncated']['exception']['type']=='OSError'
 assert expected['bitflip']['returned_tensor'] and not expected['bitflip']['target_equals_reference']
 assert expected['trailing_bytes']['returned_tensor'] and expected['trailing_bytes']['target_equals_reference']
 assert not expected['model_identity_changed']['returned_tensor']
 assert expected['set_existing_corrupt']['set_result'] and not expected['set_existing_corrupt']['after_equals_reference']
 source_file=Path(inspect.getfile(HiCacheFile));(out/'hicache_storage.py.snapshot').write_bytes(source_file.read_bytes())
 raw=dict(status='observations_verified',torch=torch.__version__,sglang=sglang.__version__,config=cfg,fixture_sha256=sha(source),run_sha256=sha(Path(__file__).read_bytes()),backend_sha256=sha(source_file.read_bytes()),cases=records)
 (out/'raw.json').write_text(json.dumps(raw,indent=2)+'\n');print(json.dumps(raw))
if __name__=='__main__':main()
