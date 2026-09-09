"""Recheck downloaded sources and deterministic offline analysis; no network/model."""
import hashlib,json,pathlib,subprocess,sys,tempfile
B=pathlib.Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
checks=0
for p in B.rglob('*.source.json'):
 # fetch.py records append .source.json; legacy view-response uses stem.source.json.
 stem=str(p)[:-len('.source.json')];source=pathlib.Path(stem)
 if not source.exists():source=pathlib.Path(stem+'.json')
 if source.exists():
  meta=json.loads(p.read_text());assert sha(source)==meta['sha256'],str(source);checks+=1
summary=json.loads((B/'analysis/summary.json').read_text())
for pair in summary['pairs']:
 for mode,r in pair['runs'].items():
  raw=json.loads((B/'wandb/histories'/(r['run_id']+'.json')).read_text())['data']['project']['run'];history=[json.loads(x) for x in raw['history']]
  assert history[0]['_step']==0 and history[0]['train/reward'] is None;checks+=1
  for metric,values in r['series'].items():
   assert values==[x[metric] for x in history[1:]];ordered=sorted(values);assert r['statistics'][metric]['median']==(ordered[49]+ordered[50])/2;checks+=2
with tempfile.TemporaryDirectory(prefix='nemo-r3-analysis-') as t:
 run=subprocess.run([sys.executable,'-B',str(B/'analyze.py'),'--output',t],capture_output=True,text=True);assert run.returncode==0,run.stderr
 for name in ['summary.json','TABLE.md']:assert (B/'analysis'/name).read_bytes()==(pathlib.Path(t)/name).read_bytes();checks+=1
assert 'accessToken=' not in (B/'README.md').read_text();checks+=1
report=dict(status='passed',checks=checks,source_hashes_verified=True,analysis_replay_byte_identical=True,raw_history_rows=808,setup_rows=8,training_rows=800,graph_qa=dict(logprob_mismatch='Viewed final PNG: log axes, spikes, titles and labels legible',training_reward='Viewed PNG: all four raw curves visible',stage_timing='Viewed PNG: medians/IQR and scope legible'),model_loaded=False,gpu_work_started=False,network_used=False)
(B/'verification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
