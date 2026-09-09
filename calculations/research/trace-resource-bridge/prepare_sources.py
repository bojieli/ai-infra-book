from pathlib import Path
import json,hashlib,shutil
ROOT=Path(__file__).resolve().parent
BOOK=ROOT.parents[2]
ORIGINAL=BOOK/'experiments/ch02/02-08'
DEST=ROOT/'public/sources/trace-resource-bridge'
index=json.loads((ORIGINAL/'source-index.json').read_text())
rows=[]
for entry in index['files']:
 rel=entry['copy']
 if not (rel.startswith('sources/chat/') or rel=='sources/tokenizer_config.json'):continue
 p=ORIGINAL/rel
 if p.suffix not in ('.json','.jsonl','.py','.log'):continue
 raw=p.read_bytes();assert hashlib.sha256(raw).hexdigest()==entry['sha256']
 target=DEST/rel;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
 rows.append(dict(file=rel,origin=str(p.relative_to(BOOK)),sha256=entry['sha256'],bytes=len(raw),copied_at=index['copied_at']))
for rel in ('summary.json','analyze.py','source-index.json'):
 raw=(ORIGINAL/rel).read_bytes();(DEST/rel).write_bytes(raw)
 rows.append(dict(file=rel,origin=str((ORIGINAL/rel).relative_to(BOOK)),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw),scope='existing derived/identity evidence, not new model execution'))
(DEST/'sources.lock.json').write_text(json.dumps(rows,indent=2)+'\n')
