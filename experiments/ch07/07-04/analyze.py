import hashlib,json,statistics
from pathlib import Path
r=Path(__file__).parent;out=r/'results'
client=json.loads((out/'client/environment.json').read_text());server=json.loads((out/'server/environment.json').read_text())
for f,env in [('client.py',client),('server.py',server)]:assert env['source_sha256']==hashlib.sha256((r/f).read_bytes()).hexdigest()
rows=[json.loads(x) for x in (out/'client/requests.jsonl').read_text().splitlines()]
server_rows={x['id']:x for x in map(json.loads,(out/'server/requests.jsonl').read_text().splitlines())}
assert len(rows)==len(server_rows)==264
fixtures={};derived=[]
for x in rows:
 s=x['server'];assert s==server_rows[x['id']]
 assert s['sha256']==x['payload_sha256'] and s['payload_bytes']==x['size']
 key=(x['size'],x['trial']);fixtures.setdefault(key,x['payload_sha256']);assert fixtures[key]==x['payload_sha256']
 times=[x[k] for k in ['start_ns','encode_end_ns','prepare_end_ns','send_end_ns','receive_end_ns','end_ns']]
 assert times==sorted(times)
 server_times=[s[k] for k in ['recv_start_ns','recv_end_ns','decode_start_ns','decode_end_ns','submit_ns','worker_start_ns','worker_end_ns','complete_observed_ns']]
 assert server_times==sorted(server_times)
 metrics=dict(total_ms=(times[-1]-times[0])/1e6,encode_ms=(times[1]-times[0])/1e6,
  prepare_ms=(times[2]-times[1])/1e6,send_ms=(times[3]-times[2])/1e6,
  response_wait_ms=(times[4]-times[3])/1e6,verify_ms=(times[5]-times[4])/1e6,client_cpu_ms=x['client_cpu_ns']/1e6,
  server_receive_body_ms=(s['recv_end_ns']-s['recv_start_ns'])/1e6,
  server_decode_ms=(s['decode_end_ns']-s['decode_start_ns'])/1e6,
  server_queue_ms=(s['worker_start_ns']-s['submit_ns'])/1e6,
  server_hash_ms=(s['worker_end_ns']-s['worker_start_ns'])/1e6,
  server_completion_observe_ms=(s['complete_observed_ns']-s['worker_end_ns'])/1e6)
 assert abs(sum(metrics[k] for k in ['encode_ms','prepare_ms','send_ms','response_wait_ms','verify_ms'])-metrics['total_ms'])<1e-8
 derived.append(dict(id=x['id'],size=x['size'],mode=x['mode'],name=x['name'],trial=x['trial'],warmup=x['warmup'],request_application_bytes=x['request_application_bytes'],**metrics))
summary=[]
for size in [1024,65536,1048576]:
 for mode in range(4):
  group=[x for x in derived if x['size']==size and x['mode']==mode and not x['warmup']];assert len(group)==20
  summary.append(dict(size=size,mode=mode,name=client['names'][mode],samples=20,
   median={k:statistics.median(x[k] for x in group) for k in metrics},
   p95_total_ms=sorted(x['total_ms'] for x in group)[18],
   request_application_bytes=group[0]['request_application_bytes']))
# Paired per-trial differences preserve temporal pairing instead of comparing only medians.
pairs=[]
for size in [1024,65536,1048576]:
 for a,b in [(0,1),(1,2),(2,3)]:
  differences=[]
  for trial in range(20):
   va=next(x for x in derived if (x['size'],x['trial'],x['mode'])==(size,trial,a))
   vb=next(x for x in derived if (x['size'],x['trial'],x['mode'])==(size,trial,b))
   differences.append(va['total_ms']-vb['total_ms'])
  pairs.append(dict(size=size,before=client['names'][a],after=client['names'][b],median_saved_ms=statistics.median(differences),positive_pairs=sum(x>0 for x in differences),differences_ms=differences))
(out/'summary.json').write_text(json.dumps(dict(summary=summary,paired_differences=pairs,requests=derived,
 scope='Client phases sum to client latency; server durations overlap client send/wait and must not be added. Application bytes exclude SSH/TCP/IP framing.'),indent=2)+'\n')
for x in summary:print(x['size'],x['name'],round(x['median']['total_ms'],3),round(x['median']['client_cpu_ms'],3),round(x['median']['server_queue_ms']+x['median']['server_completion_observe_ms'],3))
for x in pairs:print(x['size'],x['after'],round(x['median_saved_ms'],3),x['positive_pairs'])
