class StepWorker:
    def arm_steps(self):
        import time,torch
        self.step_records=[]
        original=self.model_runner.execute_model
        def wrapped(*args,**kwargs):
            scheduler=args[0] if args else kwargs.get('scheduler_output')
            begin,end=torch.cuda.Event(enable_timing=True),torch.cuda.Event(enable_timing=True)
            wall=time.perf_counter();begin.record()
            result=original(*args,**kwargs)
            end.record()
            self.step_records.append((begin,end,dict(host_s=time.perf_counter()-wall,
                total_scheduled_tokens=getattr(scheduler,'total_num_scheduled_tokens',None),
                per_request_scheduled_tokens=dict(getattr(scheduler,'num_scheduled_tokens',{})))))
            return result
        self.original_execute_model=original;self.model_runner.execute_model=wrapped
        return {'armed':True}
    def finish_steps(self):
        import torch
        torch.cuda.synchronize();self.model_runner.execute_model=self.original_execute_model
        return [dict(r,event_ms=begin.elapsed_time(end)) for begin,end,r in self.step_records]
