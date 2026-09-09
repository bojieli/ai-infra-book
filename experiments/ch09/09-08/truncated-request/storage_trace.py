import json,os,time
from pathlib import Path
from sglang.srt.mem_cache.hicache_storage import HiCacheFile

def emit(record):
 dest=os.environ.get('BOOK_HICACHE_TRACE')
 if dest:
  fd=os.open(dest,os.O_CREAT|os.O_APPEND|os.O_WRONLY,0o600)
  try:os.write(fd,(json.dumps(record)+'\n').encode())
  finally:os.close(fd)
def install():
 if getattr(HiCacheFile,'_book_traced',False):return
 HiCacheFile._book_traced=True
 for method in ['get','set']:
  original=getattr(HiCacheFile,method)
  def wrapper(self,key,*args,_original=original,_method=method,**kwargs):
   base=dict(method=_method,key=key,pid=os.getpid(),start_s=time.monotonic());emit({**base,'event':'begin'})
   try:result=_original(self,key,*args,**kwargs)
   except Exception as e:
    emit({**base,'event':'exception','end_s':time.monotonic(),'type':type(e).__name__,'message':str(e)});raise
   emit({**base,'event':'return','end_s':time.monotonic(),'success':result is not None if _method=='get' else bool(result)})
   return result
  setattr(HiCacheFile,method,wrapper)
