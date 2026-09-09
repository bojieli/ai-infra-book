"""Independent sender/receiver identity replay and shared-link audit."""
from collections import Counter
from fractions import Fraction as F
from pathlib import Path
from unittest.mock import patch
import importlib.util,json

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('window_candidate',HERE/'calculate.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

def audit(r, delayed_duplicate=None):
 s=r['scenario'];seg=s['segment_bytes'];records=r['transmissions'];byid={t['id']:t for t in records}
 rates={'c2s':F(s['upload_bits_per_second']),'s2c':F(s['download_bits_per_second'])}
 props={'c2s':F(s['forward_propagation_seconds']),'s2c':F(s['reverse_propagation_seconds'])}
 for direction in rates:
  tail=F(0);wire=0;busy=F(0)
  for tx in records:
   if tx['direction']!=direction:continue
   start=max(F(tx['queued_seconds_exact']),tail);end=start+F(8*tx['bytes'])/rates[direction]
   assert F(tx['start_seconds_exact'])==start and F(tx['end_seconds_exact'])==end
   tail=end;wire+=tx['bytes'];busy+=end-start
  assert r['links'][direction]['wire_bytes']==wire
  assert F(r['links'][direction]['busy_seconds_exact'])==busy
  assert F(r['links'][direction]['available_seconds_exact'])==tail
 for name,size in [('upload',s['input_bytes']),('download',s['output_bytes'])]:
  length=lambda p:min(seg,size-p*seg)
  seen=set();prefix=0;peak=0;complete=None
  for a in r['data_arrivals']:
   if a['transfer']!=name:continue
   p=a['packet'];tx=byid[a['transmission']]
   assert not tx['dropped'] and tx['packet']==p and tx['attempt']==a['attempt']
   assert F(a['time_seconds_exact'])==F(tx['end_seconds_exact'])+props[tx['direction']]+(F(3,2) if delayed_duplicate=='data' and a['duplicate'] else 0)
   assert a['duplicate']==(p in seen)
   seen.add(p)
   prefix=0
   while prefix//seg in seen and prefix<size:prefix+=length(prefix//seg)
   unique=sum(length(p) for p in seen);peak=max(peak,unique-prefix)
   assert a['unique_received_bytes']==unique and a['cumulative_prefix_bytes']==prefix
   if prefix==size and complete is None:complete=F(a['time_seconds_exact'])
  sent=set();acked=set();outstanding=0;cwnd=s['initial_window_bytes'];sender_prefix=0;nextp=0
  acks=[a for a in r['ack_arrivals'] if a['transfer']==name];ai=0
  for w in r['window_events']:
   if w['transfer']!=name:continue
   reason=w['reason']
   if reason=='admit_new':
    p=w['packet'];assert p==nextp and p not in sent
    assert outstanding+length(p)<=cwnd
    assert p*seg+length(p)<=sender_prefix+s['receive_window_bytes']
    outstanding+=length(p);sent.add(p);nextp+=1
   elif reason=='ack':
    a=acks[ai];ai+=1;p=a['packet'];tx=byid[a['transmission']]
    assert F(a['time_seconds_exact'])==F(tx['end_seconds_exact'])+props[tx['direction']]+(F(3,2) if delayed_duplicate=='ack' and not a['newly_acked'] else 0)
    assert a['carried_prefix_bytes']==tx['prefix_bytes']
    assert a['newly_acked']==(p not in acked) and p in sent
    assert a['released_unique_bytes']==(0 if p in acked else length(p))
    if p not in acked:
     acked.add(p);outstanding-=length(p);cwnd=min(s['max_window_bytes'],cwnd+min(length(p),s['ack_growth_bytes']))
    before_prefix=sender_prefix
    sender_prefix=max(sender_prefix,a['carried_prefix_bytes'])
    assert a['new_receive_credit_bytes']==sender_prefix-before_prefix
   elif reason=='retransmit':
    assert w['packet'] in sent and w['packet'] not in acked
   elif reason=='blocked':
    p=w['packet'];assert p==nextp
    a=outstanding+length(p)>cwnd;b=p*seg+length(p)>sender_prefix+s['receive_window_bytes']
    assert w['send_window_blocked']==a and w['receive_window_blocked']==b and (a or b)
   else:assert reason=='start'
   assert w['outstanding_unique_bytes']==outstanding and outstanding>=0
   assert w['cwnd_bytes']==cwnd and w['sender_known_prefix_bytes']==sender_prefix
   assert w['advertised_right_edge_bytes']==sender_prefix+s['receive_window_bytes']
   assert w['next_packet']==nextp
  assert ai==len(acks) and sent==acked==seen and outstanding==0 and sender_prefix==size
  t=r['transfers'][name]
  assert F(t['complete_received_seconds_exact'])==complete
  assert t['peak_reorder_buffer_bytes']==peak and t['final_cwnd_bytes']==cwnd
  assert t['unique_received_bytes']==size and t['unique_acked_packets']==len(seen)
  data=[t for t in records if t.get('transfer')==name and t['kind']=='data']
  acktx=[t for t in records if t.get('transfer')==name and t['kind']=='ack']
  assert t['data_wire_bytes']==sum(d['payload_bytes']+s['data_header_bytes'] for d in data)
  assert t['ack_wire_bytes']==len(acktx)*s['ack_bytes']
  assert t['retransmission_wire_bytes']==sum(d['bytes'] for d in data if d['attempt']>1)
 for timer in r['timer_events']:
  tx=byid[timer['transmission']]
  assert F(timer['time_seconds_exact'])==F(tx['end_seconds_exact'])+F(s['rto_seconds'])
  matching=[a for a in r['ack_arrivals'] if a['transfer']==timer['transfer'] and a['packet']==timer['packet'] and F(a['time_seconds_exact'])<=F(timer['time_seconds_exact'])]
  if matching:assert timer['status']=='cancelled_by_ack'
  if timer['status']=='retransmit_once':assert tx['dropped'] and not matching
 expected_recoveries=int(s['drop_upload_packet'] is not None or s['drop_download_packet'] is not None)
 assert r['summary']['recoveries']==expected_recoveries
 assert sum(t['status']=='retransmit_once' for t in r['timer_events'])==expected_recoveries
 assert sum(t.get('retransmission',False) for t in records)==expected_recoveries
 assert F(r['summary']['protocol_quiet_seconds_exact'])==max(F(a['time_seconds_exact']) for a in r['ack_arrivals'])
 app={a['event']:F(a['time_seconds_exact']) for a in r['application_events']}
 assert app['model_start']==F(r['transfers']['upload']['complete_received_seconds_exact'])
 assert app['model_finish']==app['model_start']+F(s['model_seconds'])
 assert F(r['transfers']['download']['start_seconds_exact'])==app['model_finish']
 assert F(r['summary']['complete_final_image_seconds_exact'])==app['download_complete_received']
 assert r['summary']['measured_seconds'] is None and r['summary']['preview_ready_seconds'] is None
 return r

base=dict(input_bytes=19,output_bytes=11,segment_bytes=4,data_header_bytes=1,ack_bytes=1,
 upload_bits_per_second=80,download_bits_per_second=40,forward_propagation_seconds='1/5',reverse_propagation_seconds='3/10',
 initial_window_bytes=4,max_window_bytes=20,receive_window_bytes=20,ack_growth_bytes=4,rto_seconds='100',model_seconds='0')
results=[]
for iw in (4,8,20):
 for rw in (4,8,20):
  for growth in (0,4):
   for loss in (None,0,2,4):
    args=dict(base,initial_window_bytes=iw,receive_window_bytes=rw,ack_growth_bytes=growth,drop_upload_packet=loss)
    r=audit(m.calculate(**args));results.append(dict(scenario=args,summary=r['summary']))
for loss in (0,1,2):
 r=audit(m.calculate(**dict(base,drop_download_packet=loss)));results.append(dict(scenario=r['scenario'],summary=r['summary']))
for key,r in m.build_results().items():
 audit(r);results.append(dict(case=key,summary=r['summary']))
# Inject duplicate receive events through the event queue, without modifying
# candidate source. Delayed duplicate ACK carries an old advertised prefix.
original_push=m.heapq.heappush
for duplicate_kind in ('data','ack'):
 injected=[False]
 def push(queue,item):
  original_push(queue,item)
  time,priority,sequence,kind,data=item
  if kind==duplicate_kind and data[0]=='upload' and data[1]==0 and not injected[0]:
   injected[0]=True
   original_push(queue,(time+F(3,2),priority,sequence+1000000,kind,data))
 with patch.object(m.heapq,'heappush',push):
  duplicate=audit(m.calculate(**base), delayed_duplicate=duplicate_kind)
 assert injected[0]
 clean=m.calculate(**base)
 for transfer in ('upload','download'):
  assert duplicate['transfers'][transfer]['final_cwnd_bytes']==clean['transfers'][transfer]['final_cwnd_bytes']
  assert duplicate['transfers'][transfer]['unique_acked_packets']==clean['transfers'][transfer]['unique_acked_packets']
 if duplicate_kind=='data':
  assert any(a['duplicate'] for a in duplicate['data_arrivals'])
  assert duplicate['transfers']['upload']['ack_wire_bytes']==clean['transfers']['upload']['ack_wire_bytes']+1
 assert any(not a['newly_acked'] for a in duplicate['ack_arrivals'])
 results.append(dict(case='injected_duplicate_'+duplicate_kind,summary=duplicate['summary']))
# ACK deadline tie: data1s +forward2s+ACK1s+reverse3s, timer end+6.
tie=dict(input_bytes=1,output_bytes=1,segment_bytes=1,data_header_bytes=0,ack_bytes=1,
 upload_bits_per_second=8,download_bits_per_second=8,forward_propagation_seconds='2',reverse_propagation_seconds='3',
 initial_window_bytes=1,max_window_bytes=1,receive_window_bytes=1,ack_growth_bytes=0,rto_seconds='6',model_seconds='0')
r=audit(m.calculate(**tie));assert r['summary']['recoveries']==0
assert all(t['status']=='cancelled_by_ack' for t in r['timer_events'])
assert F(r['transfers']['download']['start_seconds_exact'])<F(r['transfers']['upload']['all_unique_acked_seconds_exact'])
# Server response is queued on the same reverse serializer after upload ACK.
uack=next(t for t in r['transmissions'] if t['kind']=='ack' and t['transfer']=='upload')
ddata=next(t for t in r['transmissions'] if t['kind']=='data' and t['transfer']=='download')
assert F(ddata['start_seconds_exact'])==F(uack['end_seconds_exact'])
try:m.calculate(**dict(tie,rto_seconds='5'))
except ValueError as e:assert 'one-loss contract' in str(e)
else:raise AssertionError('Short RTO accepted')
(HERE/'check-independent.json').write_text(json.dumps(dict(status='passed',replay_cases=len(results),
 duplicate_injection_cases=2,ack_timer_tie=True,short_rto_rejected=True,response_before_final_ack=True,cases=results),indent=2)+'\n')
print(f'PASS: {len(results)} identity/link replays incl2 duplicate injections; ACK/timer tie; shortRTO rejection; response shared-link dependency.')
