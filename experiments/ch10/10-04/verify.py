"""CPU-only offline SHA and independent replay checks; writes only temporary files."""
import hashlib,json,pathlib,subprocess,sys,tempfile
B=pathlib.Path(__file__).resolve().parent
checks=0
for r in json.loads((B/'sources.json').read_text()):
 data=(B/r['path']).read_bytes();assert len(data)==r['bytes'];assert hashlib.sha256(data).hexdigest()==r['sha256'];checks+=2
with tempfile.TemporaryDirectory(prefix='ch10-04-replay-') as td:
 out=pathlib.Path(td)/'analysis';r=subprocess.run([sys.executable,str(B/'analyze.py'),'--out',str(out)],capture_output=True,text=True);assert r.returncode==0,r.stderr;checks+=1
 for p in (B/'analysis').iterdir():assert p.read_bytes()==(out/p.name).read_bytes();checks+=1
s=json.loads((B/'analysis/summary.json').read_text());assert s['steady_state_step_estimate_s'] is None and s['cross_hardware_speedup'] is None and s['deadline_calibration_eligible'] is False;checks+=1
assert s['raw_text_training_rows'][0]['elapsed_s']==49.4495;checks+=1
m=B/'manifest.json'
if m.exists():
 manifest=json.loads(m.read_text())
 for r in manifest['files']:
  data=(B/r['path']).read_bytes();assert len(data)==r['bytes'];assert hashlib.sha256(data).hexdigest()==r['sha256'];checks+=2
 actual={str(p.relative_to(B)) for p in B.rglob('*') if p.is_file() and p!=m};assert actual=={r['path'] for r in manifest['files']};checks+=1
print(json.dumps(dict(status='PASS',checks=checks,scope='Offline evidence consistency, not successful cross-hardware training experiment')))
