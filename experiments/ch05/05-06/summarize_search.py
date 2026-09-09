import hashlib,json,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parent;folder=ROOT/'results/schedule-search-v2'
search=json.loads((folder/'search.json').read_text());rows=[]
for r in search['records']:
 if 'file' not in r:continue
 d=json.loads((folder/r['file']).read_text())
 for f,h in d['source_hashes'].items():assert hashlib.sha256((ROOT/f).read_bytes()).hexdigest()==h
 if d['status']!='passed':continue
 assert [x['t'] for x in d['rows']]==[1,7239]
 times={str(x['t']):statistics.median(x['samples_us']) for x in d['rows']}
 rows.append(dict(index=r['index'],kind=d['kind'],block=d['block'],warps=d['warps'],median_us=times,score_us=sum(times.values()),gpu_event_window_s=d['gpu_event_window_s'],wall_s=d['wall_s'],different_elements={str(x['t']):x['different_elements'] for x in d['rows']}))
candidates=[r for r in rows if r['kind']=='schedule'];assert candidates
winner=min(candidates,key=lambda r:(r['score_us'],r['index']))
result=dict(rows=rows,selected_schedule=winner,scope='Selection on search shapes only; no heldout or agent result. Sequential shared GPU; not a verified exclusive timing window.',budget=search['schedule_event_window_s'])
(ROOT/'results/schedule-summary.json').write_text(json.dumps(result,indent=2)+'\n')
for r in rows:print(r)
