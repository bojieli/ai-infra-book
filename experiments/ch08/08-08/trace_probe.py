"""Trace-only worker extension; baseline probe.py remains sealed."""
from probe import KVProbe
class TraceProbe(KVProbe):
    def begin_trace(self,label):
        import torch
        torch.cuda.synchronize()
        torch.cuda.profiler.start()
        torch.cuda.nvtx.range_push(label)
    def end_trace(self):
        import torch
        torch.cuda.synchronize()
        torch.cuda.nvtx.range_pop()
        torch.cuda.profiler.stop()
