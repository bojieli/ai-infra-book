import hashlib,json,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parent
model=json.loads((ROOT/'model.json').read_text());h=hashlib.sha256((ROOT/'model.json').read_bytes()).hexdigest()
assert h==(ROOT/'model.sha256').read_text().strip()
out=ROOT/'results'
for f,digest in json.loads((out/'execution.json').read_text())['source_hashes'].items():
 assert hashlib.sha256((ROOT/f).read_bytes()).hexdigest()==digest
raw=[json.loads(l) for l in (out/'raw.jsonl').read_text().splitlines()]
decisions=[json.loads(l) for l in (out/'decisions.jsonl').read_text().splitlines()]
assert len(raw)==len(decisions)==18
assert len({(r['trial'],r['output_budget'],r['policy']) for r in raw})==18
assert all(r['trial'] in [0,1] and r['output_budget'] in [8,32,128] and r['policy'] in ['cache_first','queue_first','predicted_completion'] for r in raw)
rows=[];reference=None
for r,d in zip(raw,decisions):
 decision=r['decision'];target=r['target'];busy=r['background'];m=target['response']['meta_info']
 assert all(d[k]==v for k,v in decision.items()) and d['model_sha256']==h
 assert decision['time_s']<target['start_s'] and busy['start_s']<target['start_s']<busy['end_s']
 predictions={'31191':max(0,model['busy128_s']*r['output_budget']/128-decision['elapsed_since_busy_submit_s'])+model['warm_after_busy_s'],'31192':model['cold_concurrent_s']}
 assert predictions==decision['predictions_s']
 selected=31191 if r['policy']=='cache_first' else 31192 if r['policy']=='queue_first' else min([31191,31192],key=lambda p:predictions[str(p)])
 assert selected==r['selected_port']==decision['selected_port']
 assert r['decision_load']['31191'][0]['num_reqs']>=1 and r['decision_load']['31192'][0]['num_reqs']==0
 assert busy['response']['meta_info']['completion_tokens']==r['output_budget']
 assert m['completion_tokens']==1 and m['prompt_tokens']==3136 and m['num_retractions']==0
 assert m['cached_tokens']==(3135 if selected==31191 else 0)
 output=target['response'].get('output_ids',target['response']['text'])
 assert output==r['warm']['response'].get('output_ids',r['warm']['response']['text'])
 if reference is None:reference=output
 assert reference==output
 actual=target['end_s']-target['start_s'];prediction=predictions[str(selected)]
 rows.append(dict(trial=r['trial'],policy=r['policy'],output_budget=r['output_budget'],selected_port=selected,prediction_s=prediction,actual_s=actual,error_s=actual-prediction,review=abs(actual-prediction)>model['selected_latency_error_review_s'],cached_tokens=m['cached_tokens'],worker0_waiting_peak=max(s['loads']['31191'][0]['num_waiting_reqs'] for s in r['samples']),pair_completion_s=max(target['end_s'],busy['end_s'])-busy['start_s']))
report=dict(status='observations_verified',model_sha256=h,rows=rows,mean_absolute_error_s=statistics.mean(abs(r['error_s']) for r in rows),review_count=sum(r['review'] for r in rows),all_target_outputs_equal=True,limits='Only selected paths measured; no claim of optimal route or whole-system gain.')
report['groups']=[dict(output_budget=b,policy=p,target_median_s=statistics.median(r['actual_s'] for r in rows if r['output_budget']==b and r['policy']==p),pair_median_s=statistics.median(r['pair_completion_s'] for r in rows if r['output_budget']==b and r['policy']==p),request_hit_rate=sum(r['cached_tokens']>0 for r in rows if r['output_budget']==b and r['policy']==p)/2,token_hit_rate=sum(r['cached_tokens'] for r in rows if r['output_budget']==b and r['policy']==p)/(2*3136)) for b in [8,32,128] for p in ['cache_first','queue_first','predicted_completion']]
report['limits']='Two trials per condition, shared GPU, fixed Agent target; no remote retrieval or quality generalization.'
(ROOT/'summary.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
