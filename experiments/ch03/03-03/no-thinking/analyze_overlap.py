"""Observed process-lifetime overlap; does not claim measured GPU utilization."""
import json
from pathlib import Path
R=Path(__file__).resolve().parent
obs=json.loads((R/'process-clock-observation.json').read_text())
raw=[json.loads(s) for s in (R/'results/raw.jsonl').read_text().splitlines()]
# Linux proc start time is ticks since boot. Convert using contemporaneous
# CLOCK_BOOTTIME minus CLOCK_MONOTONIC. This records process existence, not kernels.
boot_minus_mono=obs['boottime_s']-obs['monotonic_s']
processes=[]
for p in obs['processes']:
 if not p['exists']:continue
 birth=p['start_ticks_since_boot']/obs['clock_ticks_per_s']-boot_minus_mono
 groups=[];candidate_count=0
 for g in raw:
  status='before_process_start' if g['scored_at']<=birth else 'straddles_process_start' if g['start']<birth else 'after_process_start'
  count=sum(c['end']>birth for c in g['candidates']);candidate_count+=count
  groups.append(dict(group=g['group'],policy=g['policy'],trial=g['trial'],task=g['task'],start=g['start'],end=g['scored_at'],status=status,candidates_ending_after_process_start=count))
 processes.append(dict(pid=p['pid'],birth_monotonic_s=birth,candidates_ending_after_process_start=candidate_count,groups=groups))
offsets=[c['metrics']['arrival_time']-c['metrics']['queued_ts'] for g in raw for c in g['candidates']]
report=dict(scope='Process lifetime overlap only; no per-process GPU kernel/utilization trace. Do not attribute all latency differences to strategy.',tick_resolution_s=1/obs['clock_ticks_per_s'],boottime_minus_monotonic_s=boot_minus_mono,observed_wall_minus_monotonic_s=obs['wall_epoch_s']-obs['monotonic_s'],engine_arrival_minus_queued_offsets_s=dict(min=min(offsets),max=max(offsets)),own_engine_pid=3601362,own_engine_absent=not next(p for p in obs['processes'] if p['pid']==3601362)['exists'],processes=processes)
(R/'overlap-summary.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k!='processes'},indent=2))
for p in processes:print('pid',p['pid'],'candidates ending after birth',p['candidates_ending_after_process_start'],'groups',[(g['group'],g['status']) for g in p['groups']])
