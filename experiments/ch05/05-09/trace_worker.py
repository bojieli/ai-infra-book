from replacement_worker import ReplacementWorker
class TraceWorker(ReplacementWorker):
    def begin_trace(self,label):
        import torch
        original=self.model_runner.execute_model
        self.trace_step=0
        def wrapped(*args,**kwargs):
            step=self.trace_step;self.trace_step+=1
            torch.cuda.nvtx.range_push(f'model-step-{step}')
            try:return original(*args,**kwargs)
            finally:torch.cuda.nvtx.range_pop()
        self.model_runner.execute_model=wrapped
        torch.cuda.synchronize();torch.cuda.profiler.start();torch.cuda.nvtx.range_push(label)
    def end_trace(self):
        import torch
        torch.cuda.synchronize();torch.cuda.nvtx.range_pop();torch.cuda.profiler.stop()
        return {'model_steps':self.trace_step}
