import pathlib,json,hashlib,statistics,collections,os
ROOT=pathlib.Path(__file__).resolve().parents[1]; dest=ROOT/'results';dest.mkdir(exist_ok=True)
all_results={}; summary={};qa=[]
for mode in ['ar','dflash-7','dflash-15']:
 path=ROOT/'raw'/mode/'events.jsonl'
 if not path.exists():continue
 events=[json.loads(l) for l in path.read_text().splitlines()]
 results=[e for e in events if e['kind']=='result' and e['phase']=='measured'];all_results[mode]={e['request_id']:e for e in results}
 stats=[e['scheduler']['spec_decoding_stats'] for e in events if e['kind']=='stats' and e.get('scheduler') and e['scheduler'].get('spec_decoding_stats')]
 total={k:sum(s[k] for s in stats) for k in ['num_drafts','num_draft_tokens','num_accepted_tokens']}
 phase=None; measured_stats=[]
 for e in events:
  if e['kind']=='submit':phase=e['phase']
  if e['kind']=='stats' and phase=='measured' and e.get('scheduler') and e['scheduler'].get('spec_decoding_stats'):measured_stats.append(e['scheduler']['spec_decoding_stats'])
 measured_total={k:sum(s[k] for s in measured_stats) for k in ['num_drafts','num_draft_tokens','num_accepted_tokens']}

 qa.append({'mode':mode,'success_event':any(e['kind']=='success' for e in events),'measured_results':len(results),'expected_results':16,'all_stats_accepted_le_drafted':all(s['num_accepted_tokens']<=s['num_draft_tokens'] for s in stats)})
 groups=[]
 for c in [1,2]:
  for task in ['short_math','short_lookup','long_math','long_lookup']:
   rr=[e for e in results if e['concurrency']==c and e['task_id']==task]
   if rr:groups.append(dict(concurrency=c,task_id=task,length=task.split('_')[0],n=len(rr),quality_pass=sum(r['quality_pass'] for r in rr),median_ttft_ms=statistics.median(r['ttft_s']*1000 for r in rr),median_wall_ms=statistics.median(r['wall_s']*1000 for r in rr),output_tokens=sum(len(r['token_ids']) for r in rr)))
 memory=[]
 pid=next((e['pid'] for e in events if e['kind']=='preflight'),None)
 for e in events:
  if e['kind']=='gpu_memory':
   for line in e['processes'].splitlines():
    p,m=line.split(',')
    if int(p)==pid:memory.append(int(m))
 summary[mode]={'groups':groups,'stats_including_warmup':total,'stats_measured':measured_total,'sampled_peak_MiB':max(memory,default=None),'failures':[e for e in events if e['kind']=='failure'],'load_wall_s':[e['wall_s'] for e in events if e['kind']=='load_complete']}
comparisons=[]
for mode,rr in all_results.items():
 if mode=='ar':continue
 for rid,r in rr.items():
  base=all_results.get('ar',{}).get(rid)
  comparisons.append({'mode':mode,'request_id':rid,'baseline_present':base is not None,'token_equal':r['token_ids']==base['token_ids'] if base else None,'baseline_quality':base['quality_pass'] if base else None,'draft_quality':r['quality_pass']})
(dest/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2))
(dest/'qa.json').write_text(json.dumps({'runs':qa,'comparisons':comparisons},ensure_ascii=False,indent=2))
rows=['|配置|并发|任务|n|质量通过|TTFT中位ms|完整wall中位ms|','|---|---:|---|---:|---:|---:|---:|']
for mode,s in summary.items():
 for g in s['groups']:rows.append(f"|{mode}|{g['concurrency']}|{g['task_id']}|{g['n']}|{g['quality_pass']}|{g['median_ttft_ms']:.2f}|{g['median_wall_ms']:.2f}|")
(dest/'table.md').write_text('\n'.join(rows)+'\n')
try:
 os.environ['MPLCONFIGDIR']=str(ROOT/'results'/'matplotlib-cache')
 import matplotlib;matplotlib.use('Agg')
 import matplotlib.pyplot as plt
 fig,axes=plt.subplots(1,2,figsize=(12,4.7),sharey=True); markers=['o','s','^']
 for c,ax in zip([1,2],axes):
  for (mode,s),marker in zip(summary.items(),markers):
   gg=[g for g in s['groups'] if g['concurrency']==c]
   ax.plot([g['task_id'].replace('_','\n') for g in gg],[g['median_wall_ms'] for g in gg],marker=marker,label=mode)
  ax.set_yscale('log');ax.set_title(f'Concurrency {c}; 2 repeats per task');ax.legend();ax.grid(alpha=.25)
 axes[0].set_ylabel('Median request wall time (ms, log scale)')
 fig.suptitle('Shared GPU / CPU. Math tasks FAIL strict quality; lookup tasks PASS.',fontsize=11)
 fig.tight_layout();fig.savefig(dest/'wall.png',dpi=160);fig.savefig(dest/'wall.svg');plt.close(fig)
except ImportError as e:(dest/'plot-blocker.txt').write_text(str(e))
print(json.dumps({'summary':summary,'qa':qa,'token_mismatches':[x for x in comparisons if x['token_equal'] is not True]},ensure_ascii=False,indent=2))
