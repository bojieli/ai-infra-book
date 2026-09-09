"""Independent trace replay; hand oracles are not calculated by the candidate."""
from fractions import Fraction as F
from pathlib import Path
from collections import defaultdict
import importlib.util, json, sys, hashlib
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[1]/'src'))
spec=importlib.util.spec_from_file_location('candidate',HERE/'calculate.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
from infra_calc.topics import connection_window as public
cases=[]
def audit(r):
 s=r['scenario']; seg=s['segment_bytes']; txs=r['transmissions']; byid={x['id']:x for x in txs}
 rates={'c2s':F(s['upload_bits_per_second']),'s2c':F(s['download_bits_per_second'])}
 props={'c2s':F(s['forward_propagation_seconds']),'s2c':F(s['reverse_propagation_seconds'])}
 for d in rates:
  tail=F(0); busy=F(0); count=0
  for t in txs:
   if t['direction']!=d:continue
   start=max(tail,F(t['queued_seconds_exact'])); end=start+8*t['bytes']/rates[d]
   assert F(t['start_seconds_exact'])==start and F(t['end_seconds_exact'])==end
   tail=end;busy+=end-start;count+=t['bytes']
  assert F(r['links'][d]['available_seconds_exact'])==tail
  assert F(r['links'][d]['busy_seconds_exact'])==busy and r['links'][d]['wire_bytes']==count
 states={};conns={}; acks=iter(r['ack_arrivals']); started=set()
 def length(k,p):return min(seg,(s['input_bytes'] if k[1]=='upload' else s['output_bytes'])-p*seg)
 for w in r['window_events']:
  rid=w['request_id'];name=w['transfer'];k=(rid,name);c=(w['connection_id'],name)
  if rid not in started:
   assert name=='upload' and w['reason']=='start'
   started.add(rid)
   for direction in ('upload','download'):
    ck=(w['connection_id'],direction)
    initial=s['initial_'+direction+'_window_bytes'] or s['initial_window_bytes']
    if ck not in conns:conns[ck]=[initial,0]
    elif s['strategy']=='reuse_reset':conns[ck][0]=initial
   for direction in ('upload','download'):
    assert r['requests'][rid-1]['initial_cwnd_bytes'][direction]==conns[(w['connection_id'],direction)][0]
  st=states.setdefault(k,dict(sent=set(),acked=set(),out=0,prefix=0,next=0));cw=conns[c];reason=w['reason']
  if reason=='admit_new':
   p=w['packet'];n=length(k,p)
   assert p==st['next'] and p not in st['sent']
   assert cw[1]+n<=cw[0] and p*seg+n<=st['prefix']+s['receive_window_bytes']
   st['sent'].add(p);st['out']+=n;cw[1]+=n;st['next']+=1
  elif reason=='ack':
   a=next(acks);assert (a['request_id'],a['transfer'])==k and a['packet']==w['packet']
   t=byid[a['transmission']];p=a['packet'];assert t['kind']=='ack'
   assert (t['request_id'],t['transfer'],t['packet'])==(rid,name,p)
   assert F(a['time_seconds_exact'])==F(t['end_seconds_exact'])+props[t['direction']]
   assert a['carried_prefix_bytes']==t['prefix_bytes'] and p in st['sent']
   new=p not in st['acked'];n=length(k,p) if new else 0
   assert a['newly_acked']==new and a['released_unique_bytes']==n
   st['acked'].add(p);st['out']-=n;cw[1]-=n
   if new:cw[0]=min(s['max_window_bytes'],cw[0]+min(n,s['ack_growth_bytes']))
   pref=max(st['prefix'],a['carried_prefix_bytes']);assert a['new_receive_credit_bytes']==pref-st['prefix'];st['prefix']=pref
  elif reason=='blocked':
   p=w['packet'];n=length(k,p);a=cw[1]+n>cw[0];b=p*seg+n>st['prefix']+s['receive_window_bytes']
   assert w['send_window_blocked']==a and w['receive_window_blocked']==b and (a or b)
  elif reason=='retransmit':assert w['packet'] in st['sent']-st['acked']
  else:assert reason=='start'
  assert w['cwnd_bytes']==cw[0] and w['connection_outstanding_unique_bytes']==cw[1]
  assert w['outstanding_unique_bytes']==st['out'] and w['sender_known_prefix_bytes']==st['prefix']
  assert w['next_packet']==st['next'] and st['out']>=0 and cw[1]>=0
 assert next(acks,None) is None
 seen=defaultdict(set)
 for a in r['data_arrivals']:
  k=(a['request_id'],a['transfer']);p=a['packet'];t=byid[a['transmission']]
  assert (t['request_id'],t['transfer'],t['packet'])==(*k,p)
  assert not t['dropped'] and F(a['time_seconds_exact'])==F(t['end_seconds_exact'])+props[t['direction']]
  assert a['duplicate']==(p in seen[k]);seen[k].add(p)
  prefix=0;i=0
  while i in seen[k]:prefix+=length(k,i);i+=1
  assert a['unique_received_bytes']==sum(length(k,p) for p in seen[k]) and a['cumulative_prefix_bytes']==prefix
 for k,st in states.items():assert st['sent']==st['acked']==seen[k] and st['out']==0
 for timer in r['timer_events']:
  t=byid[timer['transmission']];assert F(timer['time_seconds_exact'])==F(t['end_seconds_exact'])+F(s['rto_seconds'])
  acknowledged=any((a['request_id'],a['transfer'],a['packet'])==(timer['request_id'],timer['transfer'],timer['packet']) and F(a['time_seconds_exact'])<=F(timer['time_seconds_exact']) for a in r['ack_arrivals'])
  if acknowledged:assert timer['status']=='cancelled_by_ack'
  else:assert timer['status']=='retransmit_once' and t['dropped']
 assert r['summary']['total_wire_bytes']==sum(t['bytes'] for t in txs)
 assert r['summary']['unique_input_bytes']==s['request_count']*s['input_bytes']
 assert r['summary']['unique_output_bytes']==s['request_count']*s['output_bytes']
 assert F(r['summary']['protocol_last_ack_seconds_exact'])==max(F(a['time_seconds_exact']) for a in r['ack_arrivals'])
 for i,req in enumerate(r['requests']):
  assert F(req['response_seconds_exact'])==F(req['complete_received_seconds_exact'])-F(req['submit_seconds_exact'])
  if i:
   prev=r['requests'][i-1];end=prev['complete_received_seconds_exact' if s['submit_on']=='complete_received' else 'last_ack_seconds_exact']
   assert F(req['submit_seconds_exact'])==F(end)+F(s['think_seconds'])
  for name in ('upload','download'):
   rows=[t for t in txs if t['request_id']==req['request_id'] and t.get('transfer')==name and t['kind']=='data']
   assert sum(t['payload_bytes'] for t in rows if not t['retransmission'])==(s['input_bytes'] if name=='upload' else s['output_bytes'])
   assert all(t['bytes']==t['payload_bytes']+s['data_header_bytes'] for t in rows)
 cases.append(dict(inputs=s,summary=r['summary']))
 return r

def run():
 oracle=json.loads((HERE/'hand-oracles.json').read_text());base=oracle['quiet_cold_and_warm']['inputs']
 graph=[dict(direction=d,bytes=1) for d in ('c2s','s2c','c2s','s2c')]
 for strategy,expected in oracle['quiet_cold_and_warm']['four_one_byte_alternating_handshake_messages'].items():
  r=audit(m.calculate(**base,strategy=strategy,submit_on='quiet',handshake=graph))
  assert [F(q['complete_received_seconds_exact']) for q in r['requests']]==expected['complete']
  assert [F(q['last_ack_seconds_exact']) for q in r['requests']]==expected['quiet']
 pending=oracle['pending_ack_uses_forward_link']
 for mode,key in [('quiet','quiet_trigger'),('complete_received','received_trigger')]:
  r=audit(m.calculate(**pending['inputs'],handshake=[],submit_on=mode));e=pending[key]
  for field,expected in [('submit_seconds_exact','submit'),('complete_received_seconds_exact','complete'),('last_ack_seconds_exact','quiet')]:
   assert [F(q[field]) for q in r['requests']]==e[expected]
  starts=[F(next(t['start_seconds_exact'] for t in r['transmissions'] if t['kind']=='data' and t['transfer']=='upload' and t['request_id']==i)) for i in range(1,5)]
  assert starts==e['upload_first_wire_start']
 grid=dict(input_bytes=7,output_bytes=5,segment_bytes=2,data_header_bytes=1,ack_bytes=1,upload_bits_per_second=32,download_bits_per_second=16,forward_propagation_seconds='1/5',reverse_propagation_seconds='3/10',initial_window_bytes=2,max_window_bytes=12,receive_window_bytes=12,ack_growth_bytes=2,rto_seconds=100,model_seconds=0)
 for strategy in ('fresh','ticket','reuse_reset','reuse_warm'):
  for mode in ('quiet','complete_received'):
   for rw in (2,12):
    for growth in (0,2):
     for loss in (None,1):
      audit(m.calculate(**dict(grid,receive_window_bytes=rw,ack_growth_bytes=growth),handshake=graph,strategy=strategy,submit_on=mode,drop_upload_packet=loss,loss_request_id=2))
   audit(m.calculate(**grid,handshake=graph,strategy=strategy,submit_on=mode,drop_download_packet=1,loss_request_id=2))
 # Unequal directional windows, zero propagation, think time and retained debt.
 for strategy in ('fresh','ticket','reuse_reset','reuse_warm'):
  for mode in ('quiet','complete_received'):
   for think in (0,2):
    for prop in (0,1):
     audit(m.calculate(**dict(grid,initial_upload_window_bytes=6,initial_download_window_bytes=2,forward_propagation_seconds=prop,reverse_propagation_seconds=prop),handshake=graph,strategy=strategy,submit_on=mode,think_seconds=think))
 debt=audit(m.calculate(**dict(pending['inputs'],max_window_bytes=4,ack_growth_bytes=1),handshake=[],strategy='reuse_reset'))
 submits=[a for a in debt['application_events'] if a['event']=='request_submit']
 assert all(a['outstanding_unique_bytes']['download']==1 for a in submits[1:])
 assert all(a['cwnd_bytes']['download']==1 for a in submits[1:])
 # The prior request ACK arrives after reset, releases its identity, and grows shared credit.
 for rid in range(1,4):
  submit=F(submits[rid]['time_seconds_exact'])
  late=[w for w in debt['window_events'] if w['reason']=='ack' and w['request_id']==rid and w['transfer']=='download' and F(w['time_seconds_exact'])>submit]
  assert late and late[0]['cwnd_bytes']==2 and late[0]['connection_outstanding_unique_bytes']==0
 # Idle time does not silently decay a teaching warm window.
 for strategy in ('fresh','ticket','reuse_reset','reuse_warm'):
  cold=m.calculate(**base,strategy=strategy,submit_on='quiet',handshake=graph)
  idle=audit(m.calculate(**base,strategy=strategy,submit_on='quiet',handshake=graph,think_seconds=2))
  assert F(idle['summary']['complete_final_image_seconds_exact'])-F(cold['summary']['complete_final_image_seconds_exact'])==6
 # One request with same explicit graph exactly agrees with public event core.
 for loss in (None,1):
  p=public.calculate(**grid,handshake=graph,drop_upload_packet=loss)
  r=audit(m.calculate(**grid,handshake=graph,request_count=1,drop_upload_packet=loss))
  for key in ('transmissions','data_arrivals','ack_arrivals','window_events','timer_events','application_events'):
   stripped=[{k:v for k,v in row.items() if k not in ('request_id','connection_id','connection_outstanding_unique_bytes')} for row in r[key]]
   if key=='application_events':stripped=[row for row in stripped if row['event']!='request_submit']
   assert stripped==p[key],key
 # At exact ACK deadline, ACK wins; a shorter unselected timeout must reject.
 tie=dict(pending['inputs'],forward_propagation_seconds=2,reverse_propagation_seconds=3,rto_seconds=6)
 audit(m.calculate(**tie,request_count=1,handshake=[]))
 rejects=0
 for args in [dict(tie,rto_seconds=5),dict(base,request_count=True),dict(base,think_seconds=-1),dict(base,max_total_packets=11),dict(base,loss_request_id=5),dict(base,request_count=1.0)]:
  try:m.calculate(**args,handshake=[])
  except ValueError:rejects+=1
  else:raise AssertionError(('accepted invalid',args))
 result=dict(status='passed',replay_cases=len(cases),invalid_inputs_rejected=rejects,candidate_sha256=hashlib.sha256((HERE/'calculate.py').read_bytes()).hexdigest(),cases=cases)
 (HERE/'independent-review.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='cases'}))
if __name__=='__main__':run()
