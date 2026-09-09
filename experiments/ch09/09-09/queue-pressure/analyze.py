import hashlib,json,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parent;out=ROOT/'results'
execution=json.loads((out/'execution.json').read_text())
for f,h in execution['source_hashes'].items():assert hashlib.sha256((ROOT/f).read_bytes()).hexdigest()==h
rows=[json.loads(l) for l in (out/'raw.jsonl').read_text().splitlines()];assert len(rows)==6
summaries=[];reference=None
for row in rows:
 r=row['target'];warm=row['warm'];busy=row['background'];m=r['response']['meta_info']
 text=r['response'].get('output_ids',r['response']['text']);expected=warm['response'].get('output_ids',warm['response']['text']);assert text==expected
 if reference is None:reference=text
 assert text==reference and m['completion_tokens']==1 and m['num_retractions']==0
 assert m['prompt_tokens']==len(json.loads((out/'inputs.json').read_text())['target_ids'])
 assert busy['response']['meta_info']['completion_tokens']==128
 assert busy['start_s']<r['start_s']<busy['end_s']
 state=row['decision_load'];assert state['31191'][0]['num_reqs']>=1 and state['31192'][0]['num_reqs']==0
 waiting=max(s['loads']['31191'][0]['num_waiting_reqs'] for s in row['samples'])
 if row['policy']=='cache_first':assert row['selected_port']==31191 and m['cached_tokens']>0 and waiting>=1
 else:assert row['selected_port']==31192 and m['cached_tokens']==0
 summaries.append(dict(trial=row['trial'],policy=row['policy'],elapsed_s=r['end_s']-r['start_s'],pair_completion_s=max(r['end_s'],busy['end_s'])-busy['start_s'],cached_tokens=m['cached_tokens'],prompt_tokens=m['prompt_tokens'],busy_elapsed_s=busy['end_s']-busy['start_s'],busy_remaining_at_dispatch_s=busy['end_s']-r['start_s'],worker0_waiting_peak_sampled=waiting,sample_count=len(row['samples'])))
report=dict(status='observations_verified',rows=summaries,medians={p:statistics.median(r['elapsed_s'] for r in summaries if r['policy']==p) for p in ['cache_first','queue_first']},pair_completion_medians={p:statistics.median(r['pair_completion_s'] for r in summaries if r['policy']==p) for p in ['cache_first','queue_first']},all_target_outputs_equal=True)
(ROOT/'summary.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
