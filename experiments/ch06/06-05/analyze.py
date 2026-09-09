"""Offline timing/identity verification of actual rank logs; no collective execution."""
from pathlib import Path
import json,hashlib,statistics
B=Path(__file__).resolve().parent
allgroups=[];checks=0
for dataset in ['smoke','formal']:
 r=B/dataset;env=json.loads((r/'environment.json').read_text());completion=json.loads((r/'completion.json').read_text());sup=json.loads((B/(dataset+'-supervisor.json')).read_text())
 assert completion['completed'] and sup['exit_code']==0 and sup['reason'] is None
 assert env['source_sha256']==hashlib.sha256((B/'run.py').read_bytes()).hexdigest()
 assert env['protocol_sha256']==hashlib.sha256((B/'PROTOCOL.md').read_bytes()).hexdigest()
 records={rank:[json.loads(l) for l in (r/f'rank{rank}.jsonl').read_text().splitlines()] for rank in range(4)}
 for rank,rows in records.items():
  ident=json.loads((r/f'rank{rank}-identity.json').read_text());assert ident['input_unchanged'];assert len(rows)==len(env['plan'])
  for i,x in enumerate(rows):
   assert x['index']==i and x['rank']==rank and all(x[k]==v for k,v in env['plan'][i].items());assert x['process_cpu_ns']>=0
   assert x['comm_correct'] is not False and x['compute_correct'] is not False
   m=x['marks'];start=x['start_ns'];end=x['end_ns'];assert start<=end
   if x['mode']!='compute':
    assert start<=m['comm_submit_ns']<=m['comm_submit_return_ns']<=m['comm_callback_ns']<=end
    assert x['comm_min']==x['comm_max']==x['expected_comm']
   else:assert x['comm_correct'] is None
   if x['mode']!='comm':
    assert start<=m['compute_start_ns']<=m['compute_end_ns']<=end
    assert x['output_sha256']==records[rank][next(j for j,q in enumerate(records[rank]) if q['mode']!='comm')]['output_sha256']
   else:assert x['compute_correct'] is None
   checks+=1
 for i,cfg in enumerate(env['plan']):
  rows=[records[rank][i] for rank in range(4)];group=dict(dataset=dataset,index=i,**cfg)
  group.update(start_ns=min(x['start_ns'] for x in rows),end_ns=max(x['end_ns'] for x in rows))
  group['wall_ms']=(group['end_ns']-group['start_ns'])/1e6;group['sum_process_cpu_ms']=sum(x['process_cpu_ns'] for x in rows)/1e6
  group['comm_visible_ms']=max(x['marks']['comm_callback_ns']-x['marks']['comm_submit_ns'] for x in rows)/1e6 if cfg['mode']!='compute' else None
  group['compute_ms']=max(x['marks']['compute_end_ns']-x['marks']['compute_start_ns'] for x in rows)/1e6 if cfg['mode']!='comm' else None
  group['ranks']=[]
  for x in rows:
   m=x['marks'];overlap=max(0,min(m['comm_callback_ns'],m['compute_end_ns'])-max(m['comm_submit_ns'],m['compute_start_ns']))/1e6 if cfg['mode']=='shared' else None
   group['ranks'].append(dict(rank=x['rank'],pid=x['pid'],start_ns=x['start_ns'],end_ns=x['end_ns'],marks=m,visible_interval_overlap_ms=overlap))
  allgroups.append(group)
formal=[g for g in allgroups if g['dataset']=='formal' and not g['warmup']];assert len(formal)==45
summary=[];paired=[]
for n in sorted({g['bytes'] for g in formal}):
 for mode in ['comm','compute','shared']:
  rows=[g for g in formal if g['bytes']==n and g['mode']==mode];assert len(rows)==5
  summary.append(dict(bytes=n,mode=mode,groups=5,wall_median_ms=statistics.median(g['wall_ms'] for g in rows),comm_visible_median_ms=statistics.median(g['comm_visible_ms'] for g in rows) if mode!='compute' else None,compute_median_ms=statistics.median(g['compute_ms'] for g in rows) if mode!='comm' else None,sum_cpu_median_ms=statistics.median(g['sum_process_cpu_ms'] for g in rows)))
 for trial in range(5):
  d={g['mode']:g for g in formal if g['bytes']==n and g['trial']==trial};assert set(d)=={'comm','compute','shared'}
  paired.append(dict(bytes=n,trial=trial,comm_visible_ratio=d['shared']['comm_visible_ms']/d['comm']['comm_visible_ms'],compute_ratio=d['shared']['compute_ms']/d['compute']['compute_ms'],shared_wall_ms=d['shared']['wall_ms'],sum_separate_wall_ms=d['comm']['wall_ms']+d['compute']['wall_ms'],note='Sum of separate runs, not an observed sequential combined run'))
(B/'groups.json').write_text(json.dumps(allgroups,indent=2)+'\n');(B/'paired.json').write_text(json.dumps(paired,indent=2)+'\n')
report=dict(status='verified',rank_rows_checked=checks,formal_groups=45,formal_rank_rows=180,warmup_groups=9,smoke_groups=3,summary=summary,shared_rank_rows_with_visible_overlap=sum(x['visible_interval_overlap_ms']>0 for g in formal if g['mode']=='shared' for x in g['ranks']),limitations=['CPU Gloo loopback, not GPU/NCCL or cross-host','Callback reports visible completion and can lag communication','Shared OS/memory, no CPU affinity or causal hardware-counter attribution','Five paired blocks, not independent production workloads'])
(B/'analysis.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
