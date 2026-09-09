"""Finite selective-ID ACK/advertised-prefix window teaching protocol.

This is not TCP/QUIC or any RFC congestion-control implementation.
"""
from fractions import Fraction as F
from collections import Counter
import heapq
import json
from ..sources import read_source, provenance


def number(value,name,positive=False):
    if type(value) not in (int,str):raise ValueError(name+' requires integer/rational string')
    try:out=F(value)
    except (ValueError,ZeroDivisionError) as exc:raise ValueError(name) from exc
    if out<0 or positive and out==0:raise ValueError(name)
    return out


def integer(value,name,minimum=0):
    if type(value) is not int or value<minimum:raise ValueError(name)
    return value


def calculate(input_bytes=30_000_000,output_bytes=5_000_000,segment_bytes=25_000,
              upload_bits_per_second=20_000_000,download_bits_per_second=100_000_000,
              forward_propagation_seconds='1/20',reverse_propagation_seconds='1/20',
              initial_window_bytes=50_000,max_window_bytes=1_000_000,receive_window_bytes=1_000_000,
              ack_growth_bytes=25_000,data_header_bytes=40,ack_bytes=40,rto_seconds='1',
              drop_upload_packet=None,drop_download_packet=None,model_seconds='3/10',
              connection_ready_seconds='0',handshake=None,max_total_packets=10000):
    scenario=locals().copy()
    references=provenance("connection-window-rfc")
    for reference in references:
        read_source(reference["file"])
    for name in ('input_bytes','output_bytes','segment_bytes','initial_window_bytes','max_window_bytes','receive_window_bytes','max_total_packets'):
        integer(scenario[name],name,1)
    for name in ('ack_growth_bytes','data_header_bytes','ack_bytes'):integer(scenario[name],name)
    if max_total_packets>100000:raise ValueError('Hard safety cap100000 packets')
    if initial_window_bytes>max_window_bytes:raise ValueError('Initial window exceeds cap')
    if min(initial_window_bytes,receive_window_bytes)<min(segment_bytes,max(input_bytes,output_bytes)):
        raise ValueError('Both initial windows must fit the largest data segment')
    counts={name:(count+segment_bytes-1)//segment_bytes for name,count in (('upload',input_bytes),('download',output_bytes))}
    if sum(counts.values())>max_total_packets:raise ValueError('Packet count exceeds explicit simulation cap')
    for name,drop in (('upload',drop_upload_packet),('download',drop_download_packet)):
        if drop is not None and (type(drop) is not int or not 0<=drop<counts[name]):raise ValueError('Loss packet-ID outside transfer')
    if drop_upload_packet is not None and drop_download_packet is not None:raise ValueError('At most one deliberately dropped first transmission per request')
    rates={'c2s':number(upload_bits_per_second,'upload rate',True),'s2c':number(download_bits_per_second,'download rate',True)}
    propagation={'c2s':number(forward_propagation_seconds,'forward propagation'),'s2c':number(reverse_propagation_seconds,'reverse propagation')}
    rto=number(rto_seconds,'RTO',True);model=number(model_seconds,'model');ready=number(connection_ready_seconds,'connection ready')
    if handshake is not None:
        if ready!=0:raise ValueError('External-ready time and explicit handshake are alternative inputs')
        if not isinstance(handshake,list) or not handshake or len(handshake)>8:raise ValueError('Handshake requires1..8 sequential messages')
        for row in handshake:
            if not isinstance(row,dict) or set(row)!={'direction','bytes'} or row['direction'] not in rates:raise ValueError('Invalid handshake message')
            integer(row['bytes'],'handshake bytes',1)
    links={'c2s':F(0),'s2c':F(0)};transmissions=[];arrivals=[];acks=[];windows=[];timers=[];application=[]
    queue=[];sequence=0;now=F(0);recovery_count=0;last_ack_event=F(0)
    def enqueue(time,priority,kind,data):
        nonlocal sequence
        sequence+=1;heapq.heappush(queue,(time,priority,sequence,kind,data))
    def wire(direction,count,kind,**identity):
        start=max(now,links[direction]);end=start+F(8*count,rates[direction]);links[direction]=end
        record=dict(id=len(transmissions),kind=kind,direction=direction,bytes=count,
                    queued_seconds_exact=str(now),start_seconds_exact=str(start),end_seconds_exact=str(end),**identity)
        transmissions.append(record)
        return end,end+propagation[direction],record
    # Ordered handshake messages each depend on the previous message arrival.
    for i,row in enumerate(handshake or []):
        now=ready;end,ready,record=wire(row['direction'],row['bytes'],'handshake',message=i)
        record['arrival_seconds_exact']=str(ready)
    connection_ready=ready
    states={}
    for name,size,link,drop in (('upload',input_bytes,'c2s',drop_upload_packet),('download',output_bytes,'s2c',drop_download_packet)):
        states[name]=dict(name=name,size=size,link=link,reverse='s2c' if link=='c2s' else 'c2s',drop=drop,
            count=counts[name],active=False,next_packet=0,cwnd=initial_window_bytes,outstanding=0,
            acked=set(),received=set(),attempts={},sender_prefix=0,receiver_prefix=0,receiver_next=0,
            received_unique=0,peak_reorder_bytes=0,all_received=None,all_acked=None,last_ack=None,start=None)
    def payload(s,p):return min(segment_bytes,s['size']-p*segment_bytes)
    def snapshot(s,reason,**extra):
        windows.append(dict(transfer=s['name'],time_seconds_exact=str(now),reason=reason,
            cwnd_bytes=s['cwnd'],outstanding_unique_bytes=s['outstanding'],sender_known_prefix_bytes=s['sender_prefix'],
            advertised_right_edge_bytes=s['sender_prefix']+receive_window_bytes,receiver_prefix_bytes=s['receiver_prefix'],
            next_packet=s['next_packet'],**extra))
    def transmit(s,p,retransmit=False):
        length=payload(s,p);attempt=s['attempts'].get(p,0)+1;s['attempts'][p]=attempt
        dropped=s['drop']==p and attempt==1
        end,arrival,record=wire(s['link'],length+data_header_bytes,'data',transfer=s['name'],packet=p,
            offset=p*segment_bytes,payload_bytes=length,attempt=attempt,dropped=dropped,retransmission=retransmit)
        if not dropped:enqueue(arrival,1,'data',(s['name'],p,attempt,record['id']))
        enqueue(end+rto,3,'timer',(s['name'],p,attempt,record['id']))
    def pump(s):
        if not s['active']:return
        while s['next_packet']<s['count']:
            p=s['next_packet'];length=payload(s,p)
            if s['outstanding']+length>s['cwnd'] or p*segment_bytes+length>s['sender_prefix']+receive_window_bytes:
                break
            s['outstanding']+=length;s['next_packet']+=1
            snapshot(s,'admit_new',packet=p,payload_bytes=length)
            transmit(s,p)
        if s['next_packet']<s['count']:
            p=s['next_packet'];length=payload(s,p)
            snapshot(s,'blocked',packet=p,send_window_blocked=s['outstanding']+length>s['cwnd'],
                receive_window_blocked=p*segment_bytes+length>s['sender_prefix']+receive_window_bytes)
    enqueue(connection_ready,2,'start','upload')
    processed=0
    while queue:
        now=queue[0][0]
        # Drain all arrivals/ACKs before same-time timers; only then admit new data.
        while queue and queue[0][0]==now:
            _,_,_,kind,data=heapq.heappop(queue);processed+=1
            if processed>sum(counts.values())*20+100:raise ValueError('Finite event budget exceeded')
            if kind=='start':
                s=states[data];s['active']=True;s['start']=now;snapshot(s,'start')
            elif kind=='data':
                name,p,attempt,tx=data;s=states[name];duplicate=p in s['received']
                if not duplicate:
                    s['received'].add(p);s['received_unique']+=payload(s,p)
                    while s['receiver_next'] in s['received']:
                        s['receiver_prefix']+=payload(s,s['receiver_next']);s['receiver_next']+=1
                    s['peak_reorder_bytes']=max(s['peak_reorder_bytes'],s['received_unique']-s['receiver_prefix'])
                arrivals.append(dict(transfer=name,packet=p,attempt=attempt,transmission=tx,time_seconds_exact=str(now),
                    duplicate=duplicate,unique_received_bytes=s['received_unique'],cumulative_prefix_bytes=s['receiver_prefix']))
                end,ack_arrival,record=wire(s['reverse'],ack_bytes,'ack',transfer=name,packet=p,attempt=attempt,prefix_bytes=s['receiver_prefix'])
                enqueue(ack_arrival,0,'ack',(name,p,s['receiver_prefix'],record['id']))
                if s['receiver_prefix']==s['size'] and s['all_received'] is None:
                    s['all_received']=now
                    application.append(dict(event=name+'_complete_received',time_seconds_exact=str(now)))
                    if name=='upload':
                        application.append(dict(event='model_start',time_seconds_exact=str(now)))
                        application.append(dict(event='model_finish',time_seconds_exact=str(now+model)))
                        enqueue(now+model,2,'start','download')
            elif kind=='ack':
                name,p,prefix,tx=data;s=states[name];new=p not in s['acked'];before=s['outstanding'];prefix_before=s['sender_prefix']
                if new:
                    s['acked'].add(p);s['outstanding']-=payload(s,p)
                    s['cwnd']=min(max_window_bytes,s['cwnd']+min(payload(s,p),ack_growth_bytes))
                s['sender_prefix']=max(s['sender_prefix'],prefix);s['last_ack']=now;last_ack_event=now
                acks.append(dict(transfer=name,packet=p,transmission=tx,time_seconds_exact=str(now),newly_acked=new,
                    released_unique_bytes=before-s['outstanding'],new_receive_credit_bytes=s['sender_prefix']-prefix_before,carried_prefix_bytes=prefix))
                snapshot(s,'ack',packet=p,newly_acked=new)
                if len(s['acked'])==s['count'] and s['all_acked'] is None:s['all_acked']=now
            elif kind=='timer':
                name,p,attempt,tx=data;s=states[name]
                if p in s['acked']:status='cancelled_by_ack'
                elif attempt!=s['attempts'][p]:status='obsolete_generation'
                else:
                    if recovery_count or p!=s['drop'] or attempt!=1:
                        raise ValueError(f'Outside finite one-loss contract: effective timeout {name}:{p}, attempt{attempt}; raise RTO or change rates/windows')
                    recovery_count+=1;status='retransmit_once';transmit(s,p,True);snapshot(s,'retransmit',packet=p)
                timers.append(dict(transfer=name,packet=p,attempt=attempt,transmission=tx,time_seconds_exact=str(now),status=status))
        pump(states['upload']);pump(states['download'])
    if any(s['all_received'] is None or s['all_acked'] is None or s['outstanding'] for s in states.values()):
        raise ValueError('Finite protocol stalled without complete receive/ACK')
    transfer_results={}
    for name,s in states.items():
        records=[r for r in transmissions if r.get('transfer')==name]
        data=[r for r in records if r['kind']=='data'];ack=[r for r in records if r['kind']=='ack']
        transfer_results[name]=dict(payload_bytes=s['size'],packet_count=s['count'],start_seconds_exact=str(s['start']),
            complete_received_seconds_exact=str(s['all_received']),all_unique_acked_seconds_exact=str(s['all_acked']),
            last_ack_arrival_seconds_exact=str(s['last_ack']),final_cwnd_bytes=s['cwnd'],peak_reorder_buffer_bytes=s['peak_reorder_bytes'],
            unique_received_bytes=s['received_unique'],unique_acked_packets=len(s['acked']),
            data_wire_bytes=sum(r['bytes'] for r in data),ack_wire_bytes=sum(r['bytes'] for r in ack),
            retransmission_wire_bytes=sum(r['bytes'] for r in data if r['retransmission']))
    link_results={direction:dict(wire_bytes=sum(r['bytes'] for r in transmissions if r['direction']==direction),
        busy_seconds_exact=str(sum((F(8*r['bytes'],rates[direction]) for r in transmissions if r['direction']==direction),F(0))),
        available_seconds_exact=str(links[direction])) for direction in links}
    return dict(calculation='finite-ack-window-image',scenario=scenario,reference_sources=references,transmissions=transmissions,
        data_arrivals=arrivals,ack_arrivals=acks,window_events=windows,timer_events=timers,application_events=application,
        transfers=transfer_results,links=link_results,summary=dict(connection_ready_seconds_exact=str(connection_ready),
        complete_final_image_seconds_exact=str(states['download']['all_received']),
        all_unique_packets_acked_seconds_exact=str(max(s['all_acked'] for s in states.values())),
        protocol_last_ack_seconds_exact=str(last_ack_event),protocol_quiet_seconds_exact=str(last_ack_event),preview_ready_seconds=None,recoveries=recovery_count,
        payload_only_propagation_baseline_seconds_exact=str(connection_ready+F(8*input_bytes,rates['c2s'])+propagation['c2s']+model+F(8*output_bytes,rates['s2c'])+propagation['s2c']),
        bandwidth_delay_product_payload_bytes={d:str(rates[d]*sum(propagation.values())/8) for d in rates},measured_seconds=None),
        assumptions=[
            'Custom finite protocol, not TCP/QUIC/CUBIC/BBR, RFC slow start or adaptive RTO. Windows measure unique payload bytes; each new packet ACK grows cwnd by min(payload,declared increment) up to cap. No loss-window reset.',
            'Two full-duplex FIFO serialization resources include payload+declared headers, ACKs and handshake. Queued reservations are irrevocable; new packet admission reserves unique send credit before its scheduled serialization. No data preemption.',
            'Sender uses only max cumulative prefix carried by arrived ACKs plus fixed receive window. Receiver consumes contiguous prefix into full-file application storage immediately; transport reorder buffer is separate from complete file storage.',
            'Each received packet identity generates one reliable ACK after reverse serialization and propagation. Duplicate arrivals do not add unique bytes; duplicate ACKs cannot release credit or grow the window twice.',
            'Each transmission timer starts at serialization end. At most one selected first transmission drops; exactly one valid recovery allowed. Any unselected timeout or second recovery explicitly rejects parameters outside the finite contract. ACK at exact deadline cancels before timer.',
            'At each event time arrivals/ACKs/timers drain before admitting new data; stable sequence breaks ties within event type. ACK and retransmission reservations precede newly admitted data. Timers consume no physical resource.',
            'Upload full receiver completion starts model without waiting for upload final ACK. Response shares reverse serializer with still-pending upload ACKs; response ACK shares forward serializer. Both links persist across the entire request.',
            'Optional handshake is a declared ordered message graph, not a protocol-name RTT shortcut. External connection-ready time is an alternative. No additional whole RTT is charged.',
            'Same full30MB-input to usable5MB-final boundary; model work is declared, codecs/assembly zero unless included in model. Preview unknown; final receipt and sender ACK completion are different endpoints.',
        ])



def markdown(result):
    """Separate application delivery, ACK completion, and physical wire load."""
    lines=['# 有限ACK窗口与完整图片请求', '', '明确自定义教学协议；不是TCP/QUIC实现。官方RFC用于区分机制边界，不为教学数值背书。', '',
           '| 传输 | 完整接收 s | 全部唯一ACK s | 数据wire bytes | ACK wire bytes | 重传wire bytes |', '| --- | ---: | ---: | ---: | ---: | ---: |']
    for name,row in result['transfers'].items():
        lines.append(f"| {name} | {row['complete_received_seconds_exact']} | {row['all_unique_acked_seconds_exact']} | {row['data_wire_bytes']} | {row['ack_wire_bytes']} | {row['retransmission_wire_bytes']} |")
    lines += ['', '完整成片：'+result['summary']['complete_final_image_seconds_exact']+' 秒；最后ACK：'+result['summary']['protocol_last_ack_seconds_exact']+' 秒。', '',
              *['- '+item for item in result['assumptions']], '', '逐段身份、发送预约、ACK、窗口与定时器记录：', '', '```json',json.dumps(result,ensure_ascii=False,indent=2),'```','']
    return '\n'.join(lines)
