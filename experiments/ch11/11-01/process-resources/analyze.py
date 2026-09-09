import hashlib,json,statistics
from pathlib import Path
R=Path(__file__).resolve().parent
E=json.loads((R/'results/environment.json').read_text());assert E['source_sha256']==hashlib.sha256((R/'run.py').read_bytes()).hexdigest()
reference=hashlib.sha256(b'x'*(250000*256)).hexdigest();rows=[]
for path in sorted((R/'results').glob('case*.json')):
 c=json.loads(path.read_text());assert len(c['completed'])==len(c['launch'])==4
 workers=[]
 for pid,v in c['completed'].items():
  assert v['returncode']==0 and not v['stderr'];w=json.loads(v['stdout']);assert w['pid']==int(pid) and w['memory_check']==16384
  assert w['digest']==(None if c['mode']=='wait' else reference)
  assert c['start']<=w['start']<=w['ready']<=w['end']<=v['reaped']<=c['end'];workers.append(w)
 s=c['samples'];assert all(a['at']<=b['at'] for a,b in zip(s,s[1:]))
 rss=[sum(p['rss'] for p in x['processes']) for x in s]
 integral=sum((b['at']-a['at'])*(ra+rb)/2 for a,b,ra,rb in zip(s,s[1:],rss,rss[1:]))/1024**3
 rows.append(dict(index=c['index'],trial=c['trial'],condition=c['mode']+'-'+c['arrival'],wall_s=c['end']-c['start'],child_cpu_s=sum(w['cpu_total'] for w in workers),peak_sampled_rss_mib=max(rss)/1024**2,sampled_rss_gib_s=integral,max_sample_gap_s=max(b['at']-a['at'] for a,b in zip(s,s[1:])),max_launch_lateness_s=max(x['at']-x['scheduled'] for x in c['launch']),workers=workers))
assert len(rows)==9
summary={k:{metric:statistics.median(r[metric] for r in rows if r['condition']==k) for metric in ['wall_s','child_cpu_s','peak_sampled_rss_mib','sampled_rss_gib_s','max_sample_gap_s','max_launch_lateness_s']} for k in sorted(set(r['condition'] for r in rows))}
(R/'summary.json').write_text(json.dumps(dict(rows=rows,medians=summary,validated_workers=36),indent=2)+'\n');print(json.dumps(summary,indent=2))
