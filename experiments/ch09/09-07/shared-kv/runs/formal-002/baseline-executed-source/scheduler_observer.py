"""Observe native vLLM scheduler; delegate scheduling and state changes unchanged."""
import json,os,time
from vllm.v1.core.sched.scheduler import Scheduler

class ObservedScheduler(Scheduler):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.trace=open(os.environ['KV_OBSERVER_LOG'],'w',buffering=1)
        self.snapshot('init')
    def snapshot(self,event,**extra):
        pool=self.kv_cache_manager.block_pool
        requests=[]
        for rid,r in self.requests.items():
            blocks=self.kv_cache_manager.get_blocks(rid).blocks
            requests.append(dict(id=rid,status=r.status.name,computed=r.num_computed_tokens,
                tokens=r.num_tokens,output_tokens=len(r.output_token_ids),
                blocks=[[dict(id=b.block_id,refs=b.ref_cnt) for b in group] for group in blocks]))
        self.trace.write(json.dumps(dict(time_s=time.monotonic(),event=event,
            total_blocks=pool.num_gpu_blocks,free_blocks=pool.get_num_free_blocks(),
            block_size=self.block_size,requests=requests,**extra))+'\n')
    def schedule(self):
        out=super().schedule()
        self.snapshot('schedule',scheduled_tokens=out.num_scheduled_tokens)
        return out
    def update_from_output(self,*args,**kwargs):
        out=super().update_from_output(*args,**kwargs)
        self.snapshot('update')
        return out
    def finish_requests(self,request_ids,finished_status):
        ids=None if request_ids is None else [request_ids] if isinstance(request_ids,str) else list(request_ids)
        self.snapshot('finish_before',finish_ids=ids,finish_status=finished_status.name)
        out=super().finish_requests(ids,finished_status)
        self.snapshot('finish_after',finish_ids=ids,finish_status=finished_status.name)
        return out
