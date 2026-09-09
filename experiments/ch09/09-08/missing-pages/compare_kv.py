"""Compare BF16 file contents using the fixed layer_first layout."""
import json,hashlib
from pathlib import Path
import numpy as np
root=Path(__file__).resolve().parent
prep=json.loads((root/'preparation.json').read_text());case=prep['cases'][1]
def read(path):return np.fromfile(path,dtype='<u2').reshape(2,36,16,8,128)
a=read(root.parent/'storage-v3'/case['omitted']);b=read(root/'restored-middle.bin')
def compare(a,b):
 af=(a.astype(np.uint32)<<16).view(np.float32);bf=(b.astype(np.uint32)<<16).view(np.float32)
 assert np.isfinite(af).all() and np.isfinite(bf).all()
 return dict(bitwise_equal=bool(np.array_equal(a,b)),different_elements=int(np.count_nonzero(a!=b)),max_abs_difference=float(np.max(np.abs(af-bf))),per_layer_same_fraction=np.mean(a==b,axis=(2,3,4)).tolist())
d=dict(layout=[2,36,16,8,128],full_vs_partial_storage=compare(a,b))
if (root/'device-prefix-v2-page32.bin').exists():
 control=json.loads((root/'results/device-prefix-v2/raw.json').read_text());assert control['requests'][0]['response']['meta_info']['cached_tokens_details']==dict(device=512,host=0,storage=0,storage_backend='HiCacheFile')
 for f,sha in control['source_hashes'].items():assert hashlib.sha256((root/f).read_bytes()).hexdigest()==sha
 reference=json.loads((root/'reference-output.json').read_text())
 assert len(control['requests'])==3
 assert all(r['response']['output_ids']==reference for r in control['requests'])
 expected={f['path']:f['sha256'] for f in control['storage_files']}[case['omitted']]
 assert hashlib.sha256((root/'device-prefix-v2-page32.bin').read_bytes()).hexdigest()==expected
 c=read(root/'device-prefix-v2-page32.bin');d['partial_storage_vs_partial_device']=compare(b,c);d['full_vs_partial_device']=compare(a,c)
(root/'kv-comparison.json').write_text(json.dumps(d,indent=2)+'\n');print(json.dumps({k:{x:y for x,y in v.items() if x!='per_layer_same_fraction'} if isinstance(v,dict) else v for k,v in d.items()}))
