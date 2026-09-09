import argparse,collections,gzip,hashlib,json,statistics
from pathlib import Path
R=Path(__file__).resolve().parent

def overlap(rows,start,end):
 events=sorted([(r[start],1) for r in rows]+[(r[end],-1) for r in rows]);active=peak=0
 for _,delta in events:active+=delta;peak=max(peak,active)
 assert active==0
 return peak

def main(folder):
 D=R/folder;env=json.loads((D/'environment.json').read_text());smoke=env['smoke'];trials=1 if smoke else 3
 assert json.loads((D/'completion.json').read_text())==dict(done=True,requests=54*trials,failures=0,listener_closed=True)
 assert hashlib.sha256((R/'run.py').read_bytes()).hexdigest()==env['source_sha256']
 assert hashlib.sha256((R/'sources/payload.png').read_bytes()).hexdigest()==env['payload_sha256']
 raw=[json.loads(s) for s in (D/'requests.jsonl').read_text().splitlines()];assert len(raw)==54*trials
 formal=[r for r in raw if not r['prewarm']];assert len(formal)==48*trials
 connections={r['id']:r for r in json.loads((D/'connections.json').read_text())};assert len(connections)==12*trials
 server=json.loads((D/'server.json').read_text());assert len(server)==len(raw)
 srv={(s['odcid'],s['stream']):s for s in server};assert len(srv)==len(server)
 for c in connections.values():
  assert c['alpn']=='h3' and not c['session_resumed'] and not c['early_data_accepted']
  assert c['certificate_sha256']==env['certificate_sha256'] and c['start']<=c['ready']<=c['closed']
 for r in raw:
  assert r['valid'] and r['error'] is None and r['sha256']==env['payload_sha256'] and r['bytes']==env['payload_bytes'] and r['decoded']==env['pixels']
  assert r['start']<=r['send']<=r['first_headers']<=r['first_data']<=r['end']<=r['decode_start']<=r['decode_end']<=r['validation_end']
  assert r['odcid']==connections[r['connection']]['odcid']
  s=srv[r['odcid'],r['stream']];assert s['sha256']==r['sha256'] and s['bytes']==r['bytes']
  assert r['send']<=s['receive_start']<=s['receive_end']<=r['end']
 groups=json.loads((D/'groups.json').read_text());order=json.loads((D/'order.json').read_text());assert len(groups)==len(order)==6*trials
 detailed=[]
 for g,o in zip(groups,order):
  assert all(g[k]==v for k,v in o.items())
  rr=sorted([r for r in formal if all(r[k]==g[k] for k in ['trial','topology','warm'])],key=lambda r:r['index']);assert len(rr)==8 and g['errors']==0
  assert [r['index'] for r in rr]==list(range(8))
  expected=4 if g['topology']=='four_parallel' else 1
  assert len(g['connections'])==expected and set(g['connections'])=={r['connection'] for r in rr}
  assert g['setup_start']<=g['connections_ready']<=g['dispatch_start']<=min(r['start'] for r in rr)
  assert g['start']<=g['dispatch_start'] and max(r['validation_end'] for r in rr)<=g['complete']<=g['cleanup_complete']
  pre=[r for r in raw if r['prewarm'] and r['connection'] in g['connections']];assert len(pre)==(expected if g['warm'] else 0)
  if pre:assert max(r['validation_end'] for r in pre)<=g['start']
  if g['topology']=='one_serial':assert all(a['validation_end']<=b['start'] for a,b in zip(rr,rr[1:]))
  elif g['topology']=='four_parallel':assert all(sum(r['connection']==cid for r in rr)==2 for cid in g['connections'])
  client_peak=overlap(rr,'send','end');sr=[srv[r['odcid'],r['stream']] for r in rr];server_peak=overlap(sr,'receive_start','receive_end')
  assert client_peak==(1 if g['topology']=='one_serial' else 8)
  detailed.append(dict(trial=g['trial'],topology=g['topology'],warm=g['warm'],connections=expected,group_ms=(g['complete']-g['start'])*1000,dispatch_to_all_valid_ms=(g['complete']-g['dispatch_start'])*1000,client_transfer_peak=client_peak,server_receiving_peak=server_peak,median_stream_transfer_ms=statistics.median((r['end']-r['send'])*1000 for r in rr),decode_ms_sum=sum((r['decode_end']-r['decode_start'])*1000 for r in rr)))
 qcount=0;drops=collections.Counter()
 for p in D.glob('qlog*.gz'):
  q=json.load(gzip.open(p,'rt'))
  for trace in q['traces']:
   for e in trace['events']:
    if e['name']=='http:frame_parsed' and e['data']['frame']['frame_type']=='headers':qcount+=1
    if e['name']=='transport:packet_dropped':drops[e['data'].get('trigger','unknown')]+=1
 assert qcount==len(raw)
 aggregate=[]
 for topology in ['one_serial','one_parallel','four_parallel']:
  for warm in [False,True]:
   rows=[g for g in detailed if g['topology']==topology and g['warm']==warm]
   aggregate.append(dict(topology=topology,warm=warm,median_group_ms=statistics.median(r['group_ms'] for r in rows),median_dispatch_to_all_valid_ms=statistics.median(r['dispatch_to_all_valid_ms'] for r in rows),client_transfer_peaks=[r['client_transfer_peak'] for r in rows],server_receiving_peaks=[r['server_receiving_peak'] for r in rows]))
 output=dict(formal_requests=len(formal),prewarm_requests=len(raw)-len(formal),all_valid=len(raw),groups=detailed,aggregate=aggregate,qlog_drop_triggers=dict(drops),network_loss_rate=None)
 (R/(folder+'-summary.json')).write_text(json.dumps(output,indent=2)+'\n');print(json.dumps(output['aggregate'],indent=2))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--folder',default='results');a=p.parse_args();main(a.folder)
