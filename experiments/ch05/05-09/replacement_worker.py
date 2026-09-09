class ReplacementWorker:
    def install_replacement(self):
        from vllm.model_executor.layers.activation import SiluAndMul
        self.replacement_layers=[(name,m,m._forward_method) for name,m in self.model_runner.model.named_modules() if isinstance(m,SiluAndMul)]
        assert len(self.replacement_layers)==36
        return {'layer_names':[n for n,_,_ in self.replacement_layers]}

    def set_replacement(self,mode,audit=False):
        import candidate
        assert mode in ['native','schedule']
        self.replacement_records=[]
        for name,mod,original in self.replacement_layers:
            fn=original if mode=='native' else candidate.run
            if audit:
                def make(label,f):
                    def wrapped(x):
                        y=f(x)
                        self.replacement_records.append(dict(layer=label,mode=mode,shape=list(x.shape),dtype=str(x.dtype)))
                        return y
                    return wrapped
                mod._forward_method=make(name,fn)
            else:mod._forward_method=fn
        return dict(mode=mode,audit=audit,layers=len(self.replacement_layers),
            methods=[dict(layer=n,module=m._forward_method.__module__,name=m._forward_method.__qualname__) for n,m,_ in self.replacement_layers])

    def replacement_snapshot(self):return self.replacement_records
