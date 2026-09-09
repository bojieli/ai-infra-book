"""Independent read-only sealed evidence verification; no model calls."""
import hashlib,json,pathlib,sqlite3
B=pathlib.Path(__file__).resolve().parents[4]/'ch11/11-04'
# parents[4] is experiments for this worker directory depth.
B=pathlib.Path(__file__).resolve().parents[4]/'experiments/ch11/11-04' if not B.exists() else B
OUT=pathlib.Path(__file__).resolve().parent
read=lambda p:json.loads(p.read_text())
lines=lambda p:[json.loads(x) for x in p.read_text().splitlines()]
m=read(B/'manifest.json');total=0
for n,v in m['files'].items():
 p=B/n;assert p.stat().st_size==v['bytes'];assert hashlib.sha256(p.read_bytes()).hexdigest()==v['sha256'],n;total+=v['bytes']
assert len(m['files'])==m['file_count']==297 and total==m['total_bytes']==5338435
summary=read(B/'formal/summary.json');counts=dict(paths=0,workers=0,sampled=0,unique=0,duplicates=0,kills=0);rss=[];active=[];peaks=[];rows=[]
for s in summary['results']:
 d=B/'formal'/s['request_id'];ev=lines(d/'manager-events.jsonl');exe=read(d/'execution.json');commits=[e for e in ev if e['kind']=='committed'];first=[e for e in commits if not e['duplicate']]
 with sqlite3.connect(f'file:{d}/manager-snapshot.sqlite?mode=ro&immutable=1',uri=True) as db:
  data=db.execute('SELECT seq,token,eos,attempt FROM tokens ORDER BY seq').fetchall()
 assert len(first)==len(data)
 assert [(e['seq'],e['token'],int(e['eos']),e['attempt']) for e in first]==data
 assert [r[1] for r in data]==s['token_ids']
 assert [r[0] for r in data]==list(range(len(data)))
 assert sum(r[2] for r in data)==1 and data[-1][2]==1
 counts['paths']+=1;counts['workers']+=len(exe);counts['unique']+=len(data)
 for proc in exe:
  a=proc['attempt'];w=d/f'attempt-{a}';gs=lines(w/'generated.jsonl');acks=lines(w/'acks.jsonl');calls=lines(w/'calls.jsonl');counts['sampled']+=len(gs)
  assert all(len(c['offsets'])==36 for c in calls)
  active.extend(c['active_bytes'] for c in calls);peaks.extend(c['peak_bytes'] for c in calls)
  active.extend(g['active_bytes'] for g in gs);peaks.extend(g['peak_bytes'] for g in gs)
  assert proc['leftover']==[]
  if proc['killed']:
   counts['kills']+=1;cut=[e for e in first if e['cut']];assert len(cut)==1
   assert cut[0]['commit_complete']<=proc['killed']<=proc['end']<=exe[1]['start'];assert proc['returncode']==-9
   assert len(gs)==s['cut'];assert not any(x['seq']==s['cut']-1 for x in acks)
   assert [e['count'] for e in ev if e['kind']=='state_read']==[0,s['cut']]
  else:assert proc['returncode']==0 and read(w/'completion.json')['reason']=='stop'
 duplicates=[e for e in commits if e['duplicate']];counts['duplicates']+=len(duplicates)
 assert len(duplicates)==(s['cut'] if s['strategy']=='restart' else 0)
 for e in duplicates:assert (e['token'],int(e['eos']))==tuple(data[e['seq']][1:3])
 rss.extend(r['rss_bytes'] for r in read(d/'resources.json'))
 assert s['quality_passed'] and s['tokens_equal_baseline']
 row=f"|{s['task']}／{s['cut']}|"+{'baseline':'不中断','restart':'从头重做','preserve':'保留前缀'}[s['strategy']]+f"|{s['sampled_tokens']}|{s['unique_tokens']}|{s['duplicate_deliveries']}|{s['wall_s']:.3f}|"
 assert row in (B/'README.md').read_text(),row
 rows.append(row)
assert counts==dict(paths=12,workers=20,sampled=3256,unique=3000,duplicates=256,kills=8)
assert max(rss)==4717379584 and max(active)==4521207816 and max(peaks)==4874725488
report=dict(status='passed',manifest_files=297,manifest_bytes=total,raw_counts=counts,rss_peak=max(rss),mlx_active_peak=max(active),mlx_framework_peak=max(peaks),readme_table_rows_verified=len(rows),scope='Read-only SHA/SQLite/event/timing/count checks; no inference')
(OUT/'independent-checks.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
