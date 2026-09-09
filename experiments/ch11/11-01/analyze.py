import hashlib,json,statistics
from pathlib import Path
R=Path(__file__).resolve().parent;out=R/'results';env=json.loads((out/'environment.json').read_text())
assert hashlib.sha256((R/'run.py').read_bytes()).hexdigest()==env['source_sha256']
rows=[json.loads(l) for l in (out/'rounds.jsonl').read_text().splitlines()];assert 1<=len(rows)<=12
resource=json.loads((out/'resource-samples.json').read_text());samples=resource['samples'];assert len(samples)>1
for a,b in zip(samples,samples[1:]):
 assert b['t_s']>=a['t_s'] and b['cpu_user_s']>=a['cpu_user_s'] and b['cpu_system_s']>=a['cpu_system_s']
for i,r in enumerate(rows):
 assert r['turn']==i and r['model_start_s']<=r['model_end_s']<=r['tool_start_s']<=r['tool_end_s']
 assert r['model_parent_cpu_s']>=0 and r['tool_parent_cpu_s']>=0 and r['tool_child_cpu_s']>=0
 if i:
  assert r['messages'][:-2]==rows[i-1]['messages']
  assert r['messages'][-2]['content']==rows[i-1]['output_text']
  assert r['messages'][-1]['content']=='Tool result: '+json.dumps(rows[i-1]['tool_result'])
final=json.loads((out/'final.json').read_text());validation=json.loads(final['validation']['stdout'])
assert final['final_code']==(out/'workspace/intervals.py').read_text()
phases={}
for p in ['model','tool','control']:
 ss=[s for s in samples if s['phase']==p]
 phases[p]=dict(samples=len(ss),rss_min_mib=min(s['rss_kib'] for s in ss)/1024 if ss else None,rss_max_mib=max(s['rss_kib'] for s in ss)/1024 if ss else None)
report=dict(status='observations_verified',rounds=len(rows),model_wall_s=sum(r['model_end_s']-r['model_start_s'] for r in rows),tool_wall_s=sum(r['tool_end_s']-r['tool_start_s'] for r in rows),model_controller_cpu_s=sum(r['model_parent_cpu_s'] for r in rows),tool_controller_cpu_s=sum(r['tool_parent_cpu_s'] for r in rows),tool_reaped_child_cpu_s=sum(r['tool_child_cpu_s'] for r in rows),loop_wall_s=final['elapsed_s'],sampling_count=len(samples),sample_gap_median_s=statistics.median(b['t_s']-a['t_s'] for a,b in zip(samples,samples[1:])),sample_gap_max_s=max(b['t_s']-a['t_s'] for a,b in zip(samples,samples[1:])),phases=phases,agent_finished=final['agent_finished'],validation_passed=validation['passed'],visible_cases_passed=sum(c['passed'] for c in validation['cases']),visible_cases=len(validation['cases']),actions=[r['action']['tool'] for r in rows],limits='Controller RSS/CPU only; live model worker and tool-child RSS not captured. Tool CPU includes sampling overhead; no arrival/capacity inference.')
(R/'summary.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
