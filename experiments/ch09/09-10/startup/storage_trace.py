"""Observe original HiCacheFile get/set without changing their results."""
import json,os,time
from pathlib import Path
from sglang.srt.mem_cache.hicache_storage import HiCacheFile

def install():
    if getattr(HiCacheFile,'_book_traced',False):return
    HiCacheFile._book_traced=True
    for method in ['get','set']:
        original=getattr(HiCacheFile,method)
        def wrapper(self,key,*args,_original=original,_method=method,**kwargs):
            begin=time.monotonic();result=_original(self,key,*args,**kwargs);end=time.monotonic()
            path=Path(self.file_path)/(self._get_suffixed_key(key)+'.bin')
            record=dict(method=_method,key=key,start_s=begin,end_s=end,success=(result is not None if _method=='get' else bool(result)),file=str(path),bytes=path.stat().st_size if path.exists() else 0,pid=os.getpid())
            dest=os.environ.get('BOOK_HICACHE_TRACE')
            if dest:
                fd=os.open(dest,os.O_CREAT|os.O_APPEND|os.O_WRONLY,0o600)
                try:os.write(fd,(json.dumps(record)+'\n').encode())
                finally:os.close(fd)
            return result
        setattr(HiCacheFile,method,wrapper)
