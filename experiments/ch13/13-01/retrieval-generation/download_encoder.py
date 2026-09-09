"""Download only the pinned small encoder. Never a generator checkpoint."""
import hashlib,json,time,urllib.request
from pathlib import Path
B=Path(__file__).resolve().parent;protocol=json.loads((B/'protocol.json').read_text())
D=B/'encoder';D.mkdir(exist_ok=True)
files=['config.json','model.safetensors','tokenizer.json','tokenizer_config.json','special_tokens_map.json','vocab.txt','README.md','1_Pooling/config.json','sentence_bert_config.json']
rows=[];start=time.monotonic()
for name in files:
 p=D/name;p.parent.mkdir(exist_ok=True)
 url=f'https://huggingface.co/{protocol["encoder"]}/resolve/{protocol["encoder_revision"]}/{name}'
 if not p.exists():
  with urllib.request.urlopen(url,timeout=120) as r,p.open('wb') as f:
   while data:=r.read(1024*1024):f.write(data)
 rows.append(dict(file=name,bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest(),url=url))
assert sum(r['bytes'] for r in rows)<200*1024**2
(D/'manifest.json').write_text(json.dumps(dict(model=protocol['encoder'],revision=protocol['encoder_revision'],download_s=time.monotonic()-start,files=rows),indent=2)+'\n')
print(sum(r['bytes'] for r in rows))
