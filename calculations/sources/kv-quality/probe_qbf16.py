"""Controlled experiment: keep Q in BF16 while preserving calibrated FP8 KV."""
from probe import KVProbe
class KVQBF16Probe(KVProbe):
    def disable_q_quantization(self):
        self.observed_query_dtypes={}
        count=0
        for name,m in self.model_runner.model.named_modules():
            if hasattr(m,'query_quant') and m.query_quant is not None:
                m.impl.supports_quant_query_input=False
                original=m.impl.forward
                def wrap(original,name):
                    def forward(layer,query,*args,**kwargs):
                        self.observed_query_dtypes[name]=str(query.dtype)
                        return original(layer,query,*args,**kwargs)
                    return forward
                m.impl.forward=wrap(original,name)
                count+=1
        return count
    def kv_snapshot(self):
        result=super().kv_snapshot()
        result['observed_query_dtypes']=getattr(self,'observed_query_dtypes',{})
        result['query_quantization']=[dict(name=name,enabled=bool(m.query_quant is not None and m.impl.supports_quant_query_input),q_scale=m._q_scale.tolist())
            for name,m in self.model_runner.model.named_modules() if hasattr(m,'query_quant')]
        return result
