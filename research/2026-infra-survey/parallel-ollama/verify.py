from pathlib import Path
from datetime import datetime,timezone
import json,hashlib
D=Path(__file__).resolve().parent;errors=[]
def sha(b):return hashlib.sha256(b).hexdigest()
def check(r):
 p=D/r['file']
 if not p.is_file():errors.append('missing '+r['file']);return
 b=p.read_bytes()
 if sha(b)!=r['sha256']:errors.append('hash '+r['file'])
 if len(b)!=r['bytes']:errors.append('bytes '+r['file'])
 if 'ranges'in r:
  ls=b.decode().splitlines()
  for z in r['ranges']:
   a,e=z['first'],z['last']
   if not 1<=a<=e<=len(ls):errors.append('range '+r['file'])
   if sha(('\n'.join(ls[a-1:e])+'\n').encode())!=z['range_sha256']:errors.append('rangehash '+r['file'])
sources=json.loads((D/'sources.json').read_text());proof=json.loads((D/'reading-proof.json').read_text())
for r in sources:
 check(r)
 if r['status']!=200 and (r['file'],r['status'])!=('current-renderers-qwen3.go',404):errors.append('http '+r['file'])
for r in proof['selections']+proof['book_snapshots']:check(r)
check(proof['paper']);check(proof['paper']['viewed_image'])
for p in ['0126','0300']:
 if (D/(p+'-envconfig.go')).read_bytes()!=(D/(p+'-envconfig-immutable.go')).read_bytes():errors.append('historical tag mismatch '+p)
for t,h in proof['historical_refs'].items():
 if json.loads((D/(t+'-ref.json')).read_text())['object']!={'sha':h,'type':'commit','url':'https://api.github.com/repos/ollama/ollama/git/commits/'+h}:errors.append('ref '+t)
# Link the current commit to its actual root tree, then verify raw Git blobs.
commit_meta=json.loads((D/'current-commit.json').read_text())
root_sha=commit_meta['commit']['tree']['sha']
root_tree=json.loads((D/'current-root-tree.json').read_text())
if root_tree.get('sha')!=root_sha:errors.append('root tree identity')
if root_tree.get('truncated') is not False:errors.append('truncated root tree')
entries={r['path']:r for r in root_tree.get('tree',[])}
blob_rows=[]
raw_prefix='https://raw.githubusercontent.com/ollama/ollama/'+proof['fixed_current_commit']+'/'
for row in sources:
 if row['status']!=200 or not row['url'].startswith(raw_prefix):continue
 path=row['url'][len(raw_prefix):];entry=entries.get(path);raw=(D/row['file']).read_bytes()
 actual=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
 if not entry or entry.get('type')!='blob' or entry.get('sha')!=actual:errors.append('git blob '+row['file'])
 blob_rows.append(dict(file=row['file'],path=path,git_blob_sha1=actual,matched=bool(entry and entry.get('sha')==actual)))
(D/'git-blob-proof.json').write_text(json.dumps(dict(commit=proof['fixed_current_commit'],root_tree=root_sha,root_tree_response='current-root-tree.json',raw_blobs=blob_rows),indent=2)+'\n')
result=dict(verified_at=datetime.now(timezone.utc).isoformat(),passed=not errors,errors=errors,http_responses=len(sources),http_200=sum(r['status']==200 for r in sources),recorded_404=1,git_blobs_verified=len(blob_rows),selected_read_files=len(proof['selections']),paper_pages_read=1,images_viewed=1,scope='raw bytes, SHA, text ranges and fixed ref consistency; not execution of downloaded tests')
(D/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result));raise SystemExit(bool(errors))
