"""Observe actual assignment results. No input/weight/return mutation."""
import functools,gzip,hashlib,json,os,time
from pathlib import Path
def install():
    import vllm.model_executor.layers.fused_moe.experts.triton_moe as module
    if getattr(module,'_book_assignment_observer',False):return
    original=module._prepare_expert_assignment
    @functools.wraps(original)
    def wrapped(topk_ids,config,num_tokens,top_k_num,global_num_experts,expert_map,**kw):
        result=original(topk_ids,config,num_tokens,top_k_num,global_num_experts,expert_map,**kw)
        root=Path(os.environ['BOOK_MOE_OBSERVE_DIR']);state=root/'observer-state.json'
        if not state.exists():return result
        phase=json.loads(state.read_text())
        if 'case_id' not in phase:return result
        import numpy as np
        ids=topk_ids.detach().cpu().numpy()
        sorted_ids,expert_ids,padded=result
        count=int(padded.item());block=int(config['BLOCK_SIZE_M'])
        assert count%block==0
        blocks=expert_ids[:count//block].detach().cpu().tolist()
        sorted_values=None if sorted_ids is None else sorted_ids[:count].detach().cpu().tolist()
        assert bool(np.all((ids>=0)&(ids<global_num_experts)))
        row=dict(case_id=phase['case_id'],pid=os.getpid(),observed_unix=time.time(),num_tokens=num_tokens,
                 top_k=top_k_num,experts=global_num_experts,config=config,kwargs=kw,expert_map_is_none=expert_map is None,
                 topk_shape=list(ids.shape),topk_uint8_sha256=hashlib.sha256(ids.astype(np.uint8).tobytes()).hexdigest(),
                 counts=np.bincount(ids.reshape(-1),minlength=global_num_experts).tolist(),
                 num_tokens_post_padded=count,sorted_buffer_allocated_elements=None if sorted_ids is None else sorted_ids.numel(),
                 expert_buffer_allocated_elements=expert_ids.numel(),expert_block_ids=blocks,sorted_token_ids=sorted_values,
                 observer_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
        with gzip.open(root/(str(os.getpid())+'-assignments.jsonl.gz'),'at') as f:f.write(json.dumps(row,separators=(',',':'))+'\n')
        return result
    module._prepare_expert_assignment=wrapped;module._book_assignment_observer=True
