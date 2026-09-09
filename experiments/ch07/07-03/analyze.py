"""Offline audit of frozen public logs; no hardware execution or placement model."""
from pathlib import Path
import json,re,csv,hashlib
from decimal import Decimal as D
P=Path(__file__).resolve().parent
S=P/'sources'
def read(n):return json.loads((S/n).read_text())
def dump(n,x):(P/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
checks=[]
def check(name,ok,**data):
 checks.append(dict(name=name,passed=bool(ok),**data))
 if not ok:raise AssertionError((name,data))
for x in read('index.json'):check('source_sha:'+x['file'],hashlib.sha256((S/x['file']).read_bytes()).hexdigest()==x['sha256'])
body=read('nccl-tests-309.json'); comments=read('nccl-tests-309-comments.json')
other=read('nccl-1403.json'); c1403=read('nccl-1403-comments.json')
selected=[('hgx2',body,None,16,'2.26.2+cuda12.8'),('hgx4',next(x for x in comments if x['id']==2904845294),None,32,'2.26.2+cuda12.8')]
for i in range(2):selected.append((f'corrupt_{i}',other,i,16,'2.22.3+cuda12.5 (author report)'))
for i in range(2):selected.append((f'plugin_swap_{i}',next(x for x in c1403 if x['id']==2290434940),i,16,'2.22.3 (author report)'))
raw=P/'raw';raw.mkdir(exist_ok=True)
records=[]
for rid,obj,index,n,version in selected:
 text=obj['body']
 if index is not None:
  blocks=[m for m in re.finditer(r'```[^\n]*\n(.*?)```',text,re.S) if '#       size' in m.group(1)]
  m=blocks[index]; excerpt=m.group(1); offset=text[:m.start(1)].count('\n')
 else:excerpt=text;offset=0
 (raw/(rid+'.txt')).write_text(excerpt)
 records.append(dict(id=rid,path=f'raw/{rid}.txt',url=obj['html_url'],created_at=obj['created_at'],updated_at=obj['updated_at'],body_line_offset=offset,nranks=n,version=version))
for n in ['23.12','24.06']:
 records.append(dict(id='attachment_'+n,path=f'sources/result_{n}.txt',url=next(x['url'] for x in read('index.json') if x['file']==f'result_{n}.txt'),created_at=next(x['created_at'] for x in c1403 if x['id']==2290371365),nranks=16,version='2.19.3 (author comment; absent from attachment)'))
rows=[];ranks=[];channels=[]
rankrx=re.compile(r'#\s+Rank\s+(\d+) Group\s+(\d+) Pid\s+(\d+) on\s+(\S+) device\s+(\d+) \[([^]]+)\] (.+)')
for rec in records:
 t=(P/rec['path']).read_text();local=[];factor=D(2*(rec['nranks']-1))/D(rec['nranks'])
 rec['footer']=re.findall(r'Out of bounds values\s*:\s*(\d+) (\w+)',t)
 rec['logged_versions']=re.findall(r'NCCL version ([^\n]+)',t)
 rec['nic_inventory_lines']=list(dict.fromkeys(l.split('NET/IB : ',1)[1] for l in t.splitlines() if 'NET/IB : ' in l))
 rec['network_plugins']=sorted(set(re.findall(r'Using network (\S+)',t)))
 rec['command_lines']=[l for l in t.splitlines() if 'mpirun ' in l]
 for ln,line in enumerate(t.splitlines(),1):
  m=rankrx.search(line)
  if m:
   rank,group,pid,host,dev,pci,gpu=m.groups(); ranks.append(dict(run=rec['id'],line=ln,rank=int(rank),host=host,device=int(dev),pci=pci,gpu=gpu))
  if 'Channel ' in line and ' via ' in line:channels.append(dict(run=rec['id'],line=ln,text=line))
  a=line.split()
  if len(a)!=13 or not a[0].isdigit() or a[2]!='float' or a[3]!='sum':continue
  size,count=int(a[0]),int(a[1]);check(f'{rec["id"]}:{ln}:size_count',size==count*4)
  for mode,off in [('out_of_place',5),('in_place',9)]:
   time,alg,bus,wrong=map(D,a[off:off+4]); half=D(10)**D(a[off].find('.')-len(a[off])+1)/2 if '.' in a[off] else D('.5')
   # Printed time and bandwidth are rounded independently. Intersect all implied true-algbw intervals.
   lower=max(D(size)/(time+half)/1000,alg-D('.005'),(bus-D('.005'))/factor,D(0))
   upper=min(D(size)/(time-half)/1000,alg+D('.005'),(bus+D('.005'))/factor)
   check(f'{rec["id"]}:{ln}:{mode}:rounding_consistent',lower<=upper)
   row=dict(run=rec['id'],source=rec['path'],line=ln,mode=mode,size_bytes=size,count=count,nranks=rec['nranks'],time_us=float(time),algbw_GB_s=float(alg),busbw_GB_s=float(bus),wrong=float(wrong),bus_factor=float(factor),row_correct=wrong==0)
   rows.append(row);local.append(row)
 check(rec['id']+':has_rows',len(local)>0)
 rec['rows']=len(local);rec['sizes']=len(local)//2
 rec['all_rows_correct']=all(x['row_correct'] for x in local)
 rec['footer_pass']=rec['footer']==[('0','OK')]
 rec['eligible_curve']=rec['all_rows_correct'] and rec['footer_pass']
 rec['rank_banner_count']=sum(x['run']==rec['id'] for x in ranks)
 if rec['rank_banner_count']:check(rec['id']+':ranks_complete',sorted(x['rank'] for x in ranks if x['run']==rec['id'])==list(range(rec['nranks'])))
 rec['init_complete_ranks']=sorted(set(map(int,re.findall(r'rank (\d+) nranks \d+.*Init COMPLETE',t))))
 rec['max_out_of_place_busbw']=max(x['busbw_GB_s'] for x in local if x['mode']=='out_of_place')
for rid in ['hgx2','hgx4']:check(rid+':32_message_sizes',next(x for x in records if x['id']==rid)['sizes']==32)
with (P/'rows.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
dump('runs.json',records);dump('rank-layout.json',ranks);dump('channel-evidence.json',channels);dump('checks.json',checks)
dump('summary.json',dict(public_runs=len(records),message_rows=len(rows)//2,mode_rows=len(rows),checks=len(checks),all_checks_passed=True,eligible_runs=[x['id'] for x in records if x['eligible_curve']],correct_rows_missing_footer=[x['id'] for x in records if x['all_rows_correct'] and not x['footer_pass']],corrupt_runs=[x['id'] for x in records if not x['all_rows_correct']],no_hardware_executed=True))
print((P/'summary.json').read_text())
