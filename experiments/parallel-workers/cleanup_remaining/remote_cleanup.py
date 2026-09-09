from pathlib import Path
import json,subprocess
out=Path(__file__).parent
payload={'candidates':json.loads((out/'candidate-hashes.json').read_text()),'documents':{p:Path(p).read_text() for p in ['experiments/ch03/03-04/README.md','experiments/ch04/04-02/README.md','experiments/ch04/04-02/PROTOCOL.md']},'manifest':json.loads(Path('experiments/ch04/04-02/manifest.json').read_text())}
code=r'''
from pathlib import Path
import hashlib,json,datetime
P=PAYLOAD
base=Path('/home/ubuntu/ai-infra-book-experiments')
def remote(s):return base/Path(s).relative_to('experiments')
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
roots=[base/'ch03/03-04',base/'ch04/04-02']
candidates={remote(s):v for s,v in P['candidates'].items()}
excluded=set(candidates)|{remote(s) for s in P['documents']}|{roots[1]/'manifest.json'}
preserved={str(p):digest(p) for r in roots for p in r.rglob('*') if p.is_file() and p not in excluded}
review=[]
for p,v in candidates.items():
 status='absent' if not p.exists() else ('same_sha' if digest(p)==v['sha256'] else 'different_sha')
 review.append({'path':str(p),'status':status})
for item in review:
 if item['status']=='same_sha':Path(item['path']).unlink()
for r in [roots[0]/'startup-failed',roots[0]/'tokenizer-failed',roots[1]/'compatibility-v1']:
 if r.exists():
  for d in sorted([p for p in r.rglob('*') if p.is_dir()],key=lambda p:len(p.parts),reverse=True):
   if not any(d.iterdir()):d.rmdir()
  if not any(r.iterdir()):r.rmdir()
for s,text in P['documents'].items():remote(s).write_text(text)
m=P['manifest']; r=roots[1]; m['files']={s:{'bytes':(r/s).stat().st_size,'sha256':digest(r/s)} for s in m['files'] if (r/s).is_file()};m['created_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();m['manifest_scope']='Local manifest schema; only files present in remote mirror are indexed.';(r/'manifest.json').write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n')
changed=[s for s,h in preserved.items() if not Path(s).is_file() or digest(Path(s))!=h]
assert not changed,changed
print(json.dumps({'review':review,'deleted_files':sum(x['status']=='same_sha' for x in review),'absent_files':sum(x['status']=='absent' for x in review),'different_sha_files':sum(x['status']=='different_sha' for x in review),'preserved_files_sha256_verified':len(preserved),'preserved_changes':len(changed),'preserved_hashes':preserved,'documents_synced':len(P['documents']),'manifest_entries':len(m['files'])}))
'''.replace('PAYLOAD',repr(payload))
r=subprocess.run(['ssh','rtx-pro','python3 -'],input=code,text=True,capture_output=True)
assert r.returncode==0,r.stderr
report=json.loads(r.stdout);(out/'remote-audit.json').write_text(json.dumps(report,indent=2)+'\n')
counts=json.loads((out/'counts.json').read_text());counts['remote']={k:v for k,v in report.items() if k not in ('review','preserved_hashes')};(out/'counts.json').write_text(json.dumps(counts,indent=2)+'\n');print(counts)
