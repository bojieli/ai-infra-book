"""Worker extension for explicit calibration and read-only KV observations."""
class KVProbe:
    def arm_kv_calibration(self):
        count=0
        for m in self.model_runner.model.modules():
            if hasattr(m,'calculate_kv_scales'):
                m.calculate_kv_scales=True;count+=1
        return count
    def kv_snapshot(self):
        import torch
        scales=[]
        for name,m in self.model_runner.model.named_modules():
            if hasattr(m,'_k_scale'):
                scales.append(dict(name=name,k=m._k_scale.tolist(),v=m._v_scale.tolist(),calculate=m.calculate_kv_scales,backend=type(m.impl).__name__))
        tensors=[];storages={}
        for t in self.model_runner.kv_caches:
            storage=t.untyped_storage();storages[str(storage.data_ptr())]=storage.nbytes()
            tensors.append(dict(shape=list(t.shape),dtype=str(t.dtype),logical_bytes=t.numel()*t.element_size(),storage_bytes=storage.nbytes()))
        return dict(scales=scales,kv_tensors=tensors,unique_kv_storage_bytes=sum(storages.values()),
            cuda_allocated=torch.cuda.memory_allocated(),cuda_reserved=torch.cuda.memory_reserved(),
            cuda_peak_allocated=torch.cuda.max_memory_allocated())
