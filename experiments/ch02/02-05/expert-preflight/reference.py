"""Independent NumPy CPU FP64 oracle, no Torch/Triton imports."""
import numpy as np
FP4 = np.array([0,.5,1,1.5,2,3,4,6,-0.,-.5,-1,-1.5,-2,-3,-4,-6],dtype=np.float64)
E8 = np.array([2.**(int(b)-127) if b!=255 else float('nan') for b in range(256)],dtype=np.float64)
def bf(x):
    a=np.asarray(x,dtype=np.float32)
    u=a.view(np.uint32)
    return ((u+np.uint32(0x7fff)+((u>>16)&1))&np.uint32(0xffff0000)).view(np.float32).astype(np.float64)
def dequant(p,s):
    w=np.empty((p.shape[0],p.shape[1]*2),dtype=np.float64)
    w[:,0::2]=FP4[p&15]; w[:,1::2]=FP4[p>>4]
    w.reshape(w.shape[0],-1,32)[:] *= E8[s][:,:,None]
    return w
def reference(x,ids,routes,raw,H,I,limit=10.,factor=1.5):
    M,T=ids.shape
    first=np.zeros((M,T,2*I),dtype=np.float64)
    down=np.zeros((M,T,H),dtype=np.float64)
    activated=np.zeros((M,T,I),dtype=np.float64)
    safe=np.maximum(ids,0)
    for e in range(6):
        rows,slots=np.where(safe==e)
        if not len(rows): continue
        for j,w in enumerate(['w1','w3']):
            d=dequant(raw[f'{e}_{w}_weight'][:I,:H//2],raw[f'{e}_{w}_scale'][:I,:H//32])
            first[rows,slots,j*I:(j+1)*I]=bf(x[rows] @ d.T)
            del d
        g=first[rows,slots,:I]; u=first[rows,slots,I:]
        if limit is not None and limit>0:
            g=np.minimum(g,limit);u=np.clip(u,-limit,limit)
        a=bf((g/(1+np.exp(-g)))*u)
        activated[rows,slots]=a
        d=dequant(raw[f'{e}_w2_weight'][:H,:I//2],raw[f'{e}_w2_scale'][:H,:I//32])
        down[rows,slots]=bf(a @ d.T)
        del d
    masked=bf(down*(ids>=0)[:,:,None])
    product=bf(masked*bf(routes)[:,:,None])
    output=bf(bf(product.sum(axis=1))*factor)
    return dict(reference=output,first=first,activated=activated,down=down,product=product)
def metrics(y,r):
    err=np.abs(y-r); rms=float(np.sqrt(np.mean(r*r))); norm=float(np.linalg.norm(r))
    tol=.02*np.abs(r)+.002*rms
    bad=(err>tol)|~np.isfinite(y)|~np.isfinite(r)
    rel=float(np.linalg.norm(y-r)/norm) if norm else (0. if np.all(y==0) else float('inf'))
    return dict(pass_criteria=bool(not bad.any() and rel<=.01), relative_l2=rel,max_abs=float(err.max()),reference_rms=rms,max_error_over_rms=float(err.max()/rms) if rms else 0.,bad_elements=int(bad.sum()),elements=int(r.size),error_quantiles=np.quantile(err,[0,.5,.9,.99,1]).tolist(),failing_indices=np.argwhere(bad).tolist())
