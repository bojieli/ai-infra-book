"""Offline descriptive statistics of actual searches; never generation quality."""
import argparse,json,statistics
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--retrieval',type=Path,required=True);a=p.parse_args();d=a.retrieval
plan=json.loads((d/'generation-plan.json').read_text());search=json.loads((d/'searches.json').read_text());rows=[]
for ci,c in enumerate(plan['configs']):
 rr=[r for r in search if r['config_id']==ci];req=[r for r in plan['requests'] if r['config_id']==ci]
 assert len(rr)==24*11 and len(req)==24
 ns=sorted(r['search_ns'] for r in rr)
 rows.append(dict(config_id=ci,**c,search_calls=len(rr),median_search_ns=statistics.median(ns),p95_nearest_rank_search_ns=ns[__import__('math').ceil(.95*len(ns))-1],evidence_present=sum(r['evidence_present'] for r in req),queries=24,evidence_present_by_split={s:sum(r['evidence_present'] for r in req if r['split']==s) for s in ['calibration','evaluation']}))
(d/'retrieval-summary.json').write_text(json.dumps(dict(scope='Actual CPU search only; evidence presence is not generated-answer quality',configs=rows),indent=2)+'\n')
print(json.dumps(rows,indent=2))
