import json,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parent;out=ROOT/'results/schedule-search'
if out.exists():raise RuntimeError('Use fresh search directory')
out.mkdir(parents=True);protocol=json.loads((ROOT/'protocol.json').read_text());spent=0;records=[]
configs=[('native',256,4),('compiled',256,4)]+[('schedule',b,w) for b,w in [(128,4),(256,4),(512,4),(1024,4),(2048,8),(4096,8)]]
for index,(kind,block,warps) in enumerate(configs):
 if kind=='schedule' and spent>=protocol['maximum_gpu_event_window_seconds_per_strategy']:break
 file=out/f'{index}-{kind}.json';command=[sys.executable,str(ROOT/'evaluate.py'),'--kind',kind,'--block',str(block),'--warps',str(warps),'--output',str(file)]
 with (out/f'{index}.log').open('w') as log:
  try:subprocess.run(command,stdout=log,stderr=subprocess.STDOUT,timeout=protocol['candidate_process_timeout_seconds'],check=True)
  except Exception as e:records.append(dict(index=index,error=repr(e)));continue
 d=json.loads(file.read_text())
 if kind=='schedule':spent+=d['gpu_event_window_s']
 records.append(dict(index=index,kind=kind,file=file.name,status=d['status'],cumulative_schedule_event_window_s=spent));print(records[-1],flush=True)
(out/'search.json').write_text(json.dumps(dict(records=records,schedule_event_window_s=spent,scope='Sequential evaluation; event-window cap includes compile/host gaps and is conservative, not hardware active-time accounting. Native/compiled baselines outside candidate budget.'),indent=2)+'\n')
