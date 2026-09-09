"""Record real checkpoint chunk coordinates and file hashes after execution."""
import hashlib
import json
from pathlib import Path
import sys
from torch.distributed.checkpoint import FileSystemReader

root=Path(sys.argv[1])
checkpoint=root/'checkpoint'
metadata=FileSystemReader(checkpoint).read_metadata()
tensors={}
for key,value in metadata.state_dict_metadata.items():
    tensors[key]=dict(shape=list(value.size),dtype=str(value.properties.dtype),
        chunks=[dict(offsets=list(c.offsets),sizes=list(c.sizes)) for c in value.chunks])
files={p.name:dict(bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
       for p in sorted(checkpoint.iterdir()) if p.is_file()}
(root/'checkpoint-manifest.json').write_text(json.dumps(dict(tensors=tensors,files=files),indent=2)+'\n')
print(json.dumps(dict(tensors=len(tensors),files=len(files),bytes=sum(v['bytes'] for v in files.values()))))
