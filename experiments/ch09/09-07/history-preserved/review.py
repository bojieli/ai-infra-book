"""Attribute actual next-turn retrieval to matching, previously generated tokens."""
from pathlib import Path
import json, hashlib, subprocess, sys, tempfile
ROOT=Path(__file__).absolute().parent
analysis=json.loads((ROOT/'analysis.json').read_text()); rows=analysis['rows']; checks=0
with tempfile.TemporaryDirectory() as d:
    out=Path(d)/'analysis.json'
    subprocess.run([sys.executable,str(ROOT/'analyze_history.py'),'--run',str(ROOT/'runs/preserved-001'),'--out',str(out)],check=True,capture_output=True)
    assert out.read_bytes()==(ROOT/'analysis.json').read_bytes();checks+=1
index={(r['rep'],r['condition'],r['turn']):r for r in rows}
pairs=[];transitions=[]
for rep in range(3):
 for turn in range(12):
  base=index[rep,'recompute',turn];local=index[rep,'local-apc',turn];shared=index[rep,'shared-apc',turn]
  pairs.append(dict(rep=rep,turn=turn,local_shared_exact=local['output_ids']==shared['output_ids'],local_recompute_exact=local['output_ids']==base['output_ids'],shared_recompute_exact=shared['output_ids']==base['output_ids']))
for r in rows:
 if r['turn']==11:continue
 nxt=index[r['rep'],r['condition'],r['turn']+1]
 gen_start=r['input_tokens']; end=r['next_history_common_tokens']
 matching_generated=max(0,end-gen_start)
 assert matching_generated<=r['output_tokens']-1;checks+=1
 retrieved=[]
 for start,stop,skip in nxt['operations']['retrieve']['ranges']:
  left=max(start+skip,gen_start);right=min(stop,end)
  if right>left:retrieved.append([left,right])
 count=sum(y-x for x,y in retrieved)
 # Submitted native token-ID hashes and boundaries checked by analyzer.
 transitions.append(dict(rep=r['rep'],condition=r['condition'],from_turn=r['turn'],matching_generated_tokens=matching_generated,full_consumed_prefix=end==gen_start+r['output_tokens']-1,next_retrieve_generated_tokens=count,actual_copy_intersections=retrieved))
completion_checks=0
for tr in transitions:
 if tr['condition']!='shared-apc' or not tr['actual_copy_intersections']:continue
 old=index[tr['rep'],'shared-apc',tr['from_turn']]; nxt=index[tr['rep'],'shared-apc',tr['from_turn']+1]
 def events(row):
  directory=ROOT/'runs/preserved-001'/f"r{row['rep']}-shared-apc"/f"engine{row['engine']}"
  return [e for p in directory.glob('adapter-*.jsonl') for e in map(json.loads,p.read_text().splitlines()) if e['request_id']==row['native_id']]
 before=events(old); after=events(nxt)
 stores=[e for e in before if e['kind']=='store_submit' and e['submitted']]
 store_done=[e['time_s'] for e in before if e['kind']=='store_complete' and e['success']]
 copies=[e for e in after if e['kind']=='retrieve_submit' and e['submitted']]
 copy_done=[e['time_s'] for e in after if e['kind']=='retrieve_complete' and e['success']]
 assert stores and store_done and copies and copy_done
 assert max(store_done)>=max(e['time_s'] for e in stores)
 assert max(store_done)<min(e['time_s'] for e in copies)
 assert max(copy_done)>=max(e['time_s'] for e in copies)
 for lo,hi in tr['actual_copy_intersections']:
  assert any(e['start']<=lo and e['end']>=hi for e in stores)
 completion_checks+=1
result=dict(checks=checks,publication_and_copy_completions_verified=completion_checks,analyzer_checks=analysis['checks'],requests=len(rows),normal_stop=sum(r['normal_stop'] for r in rows),pair_count=len(pairs),local_shared_exact=sum(p['local_shared_exact'] for p in pairs),local_recompute_exact=sum(p['local_recompute_exact'] for p in pairs),shared_recompute_exact=sum(p['shared_recompute_exact'] for p in pairs),pairs=pairs,transitions=transitions,replay_byte_identical=True,scope='Actual native submit copy range intersects immediate prior generated token positions that match frozen next input; store and copy completion ordering checked for every nonempty intersection. No cross-host or live Agent quality inference.')
(ROOT/'review.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k not in ('pairs','transitions')}))
