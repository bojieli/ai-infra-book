"""Independent packet interval, key-at-start, and resource audit."""
from fractions import Fraction as F
from pathlib import Path
import importlib.util
import hashlib
import json
from collections import Counter

ROOT=Path(__file__).resolve().parent


def partition(intervals,total):
    """Prove exactly-once full coverage, not set union hiding duplicates."""
    cursor=0
    for start,stop in sorted(intervals):
        assert start==cursor and stop>start and stop<=total,(start,stop,cursor,total)
        cursor=stop
    assert cursor==total


def equal_intervals(left,right):
    """Compare coverage multiplicities across differently cut boundaries."""
    cuts=sorted({x for interval in left+right for x in interval})
    for a,b in zip(cuts,cuts[1:]):
        assert sum(x<=a and b<=y for x,y in left)==sum(x<=a and b<=y for x,y in right)


def serial_and_keys(events,key_install):
    # Canonical events: kind,direction,start,end,arrival,wire_bytes,rate,delay,
    # level ('0rtt'/'1rtt') for application packets; range_start/range_stop.
    for e in events:
        assert e['end']-e['start']==F(8*e['wire_bytes'],e['rate'])
        assert e['arrival']==e['end']+e['delay']
        if e['kind']=='application':
            assert e['range_stop']>e['range_start']
            assert (e['level']=='0rtt')==(e['start']<key_install)
    for direction in ('c2s','s2c'):
        rows=sorted((e for e in events if e['direction']==direction),key=lambda e:(e['start'],e['end']))
        assert all(a['end']<=b['start'] for a,b in zip(rows,rows[1:]))


def antiamp(events,validation):
    c=sorted((e for e in events if e['direction']=='c2s'),key=lambda e:e['arrival'])
    sent=0;received=0;i=0
    for e in sorted((e for e in events if e['direction']=='s2c'),key=lambda e:e['start']):
        while i<len(c) and c[i]['arrival']<=e['start']:
            received+=c[i]['udp_payload'];i+=1
        sent+=e['udp_payload']
        if validation is None or e['start']<validation:assert sent<=3*received


def normalize(result):
    p=result['inputs'];out=[]
    for i,e in enumerate(result['transmissions']):
        out.append(dict(id=i,kind='application' if e['kind']=='request' else e['kind'],
            direction=e['direction'],start=F(e['start']),end=F(e['end']),arrival=F(e['arrival']),
            wire_bytes=e['wire_bytes'],udp_payload=e['udp_bytes'],
            rate=F(str(p[e['direction']+'_bits_per_second'])),delay=F(str(p[e['direction']+'_propagation_seconds'])),
            level=e.get('encryption_level'),range_start=e.get('offset'),range_stop=e.get('end_offset')))
    return out


def audit(result):
    p=result['inputs'];t=result['transmissions'];s=result['summary'];m=result['milestones']
    es=normalize(result);keys=F(m['client_1rtt_keys_installed']) if 'client_1rtt_keys_installed' in m else None
    if keys is not None:serial_and_keys(es,keys)
    else:
        assert all(e['level']=='0rtt' for e in es if e['kind']=='application')
    validation=F(0) if p['address_token_valid'] else F(m['server_address_validated']) if 'server_address_validated' in m else None
    antiamp(es,validation)
    validation_packets=[e for e in es if e['kind'] in ('handshake_ack','client_finished')]
    if validation_packets and not p['address_token_valid']:assert validation==min(e['arrival'] for e in validation_packets)
    request=[e for e in t if e['kind']=='request'];response=[e for e in t if e['kind']=='response']
    early=[(e['offset'],e['end_offset']) for e in request if e['encryption_level']=='0rtt']
    normal=[(e['offset'],e['end_offset']) for e in request if e['encryption_level']=='1rtt']
    accepted=[(e['offset'],e['end_offset']) for e in request if e.get('accepted')]
    size=p['request_payload_bytes'];early_bytes=sum(b-a for a,b in early)
    assert early_bytes==s['early_payload_sent_bytes']
    assert sum(b-a for a,b in normal)==s['one_rtt_payload_sent_bytes']
    assert s['request_payload_sent_bytes']==sum(e['payload_bytes'] for e in request)
    if early:partition(early,early_bytes)
    if p['early_result']=='accept' and result['status']=='complete':
        partition(early+normal,size);partition(accepted,size)
        assert s['request_payload_sent_bytes']==size
    elif p['early_result']=='reject':
        assert all(not e.get('accepted') for e in request if e['encryption_level']=='0rtt')
        if p['application_retry_authorized'] and result['status']=='complete':
            partition(normal,size);partition(accepted,size)
            # The already-started early prefix is exactly the duplicated wire
            # range; no uncovered boundary and no duplicate accepted contribution.
            equal_intervals(early,[(a,min(b,early_bytes)) for a,b in normal if a<early_bytes])
            partition([(a-early_bytes,b-early_bytes) for a,b in normal if a>=early_bytes],size-early_bytes)
            assert s['request_payload_sent_bytes']==size+early_bytes
        elif not p['application_retry_authorized']:
            assert not normal and not accepted and s['application_execution_count']==0
            assert 'complete_response' not in m
    for direction,rows in [('c2s',request),('s2c',response)]:
        assert [e['packet_number'] for e in rows]==list(range(len(rows)))
        for e in rows:
            assert e['packet_number_space']=='application' and e['stream_id']==0
            assert e['end_offset']-e['offset']==e['payload_bytes']>0
            assert e['wire_bytes']==e['udp_bytes']+28
            overhead=p['response_overhead_bytes'] if direction=='s2c' else p['zero_rtt_overhead_bytes'] if e['encryption_level']=='0rtt' else p['one_rtt_overhead_bytes']
            assert e['udp_bytes']==e['payload_bytes']+overhead
            assert e['udp_bytes']<=65507
    finishes=[e for e in es if e['kind']=='client_finished']
    if normal:assert min(F(e['start']) for e in request if e['encryption_level']=='1rtt')>=max(e['end'] for e in finishes)
    sf=[e for e in es if e['kind']=='server_flight']
    if response:assert min(F(e['start']) for e in response)>=max(e['end'] for e in sf)
    if result['status']=='complete':
        partition([(e['offset'],e['end_offset']) for e in response],p['response_payload_bytes'])
        assert F(m['complete_request'])==max(F(e['arrival']) for e in request if e.get('accepted'))
        execute=F(m['complete_request'])
        if p['application_policy']=='wait_client_finished':execute=max(execute,F(m['client_finished_received']))
        assert F(m['application_execution'])==execute
        assert F(m['response_ready'])==execute+F(str(p['model_seconds']))
        assert F(m['complete_response'])==max(F(e['arrival']) for e in response)
        assert s['application_execution_count']==1
        assert s['accepted_unique_request_bytes']==size
    for direction in ('c2s','s2c'):
        assert s['modeled_wire_bytes_by_direction'][direction]==sum(e['wire_bytes'] for e in t if e['direction']==direction)
    return dict(packets=len(t),early_bytes=early_bytes,one_rtt_bytes=s['one_rtt_payload_sent_bytes'],
        accepted_bytes=s['accepted_unique_request_bytes'],status=result['status'],
        complete_response=m.get('complete_response'),key_time=m.get('client_1rtt_keys_installed'))


def hand_input(candidate,result='accept',retry=True):
    p=candidate.example();p.update(request_payload_bytes=1168*6,response_payload_bytes=100,
        packet_payload_bytes=1168,zero_rtt_overhead_bytes=32,one_rtt_overhead_bytes=32,response_overhead_bytes=1100,
        c2s_bits_per_second=9824,s2c_bits_per_second=9824,c2s_propagation_seconds='1',s2c_propagation_seconds='1',
        model_seconds='0',early_result=result,application_retry_authorized=retry)
    p['packets']={k:[1200] for k in ('client_hello','client_finished','handshake_ack')};p['packets']['server_flight']=[1200,1200]
    return p


def main():
    import copy
    spec=importlib.util.spec_from_file_location('candidate',ROOT/'calculate.py');c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
    start_sha=hashlib.sha256((ROOT/'calculate.py').read_bytes()).hexdigest()
    checks={};midpacket=0
    for name,p in c.scenarios().items():checks[name]=audit(c.calculate(p))
    hand=json.loads((ROOT/'hand-oracles.json').read_text())
    for name,result,retry in [('accept','accept',True),('reject_authorized','reject',True),('reject_unauthorized','reject',False)]:
        p=hand_input(c,result,retry);r=c.calculate(p);checks['root-'+name]=audit(r);expected=hand[name]
        s=r['summary'];m=r['milestones']
        assert s['early_payload_sent_bytes']==expected['early_payload_sent']
        assert s['one_rtt_payload_sent_bytes']==expected['normal_payload_sent']
        assert s['request_payload_sent_bytes']==expected['request_payload_sent']
        assert s['accepted_unique_request_bytes']==expected['accepted_unique_payload']
        assert s['application_execution_count']==expected['execution_count']
        for field,key in [('application_execution','application_execution_time'),('complete_response','complete_response_time')]:
            assert (None if field not in m else F(m[field]))==expected[key]
        assert F(m['client_1rtt_keys_installed'])==5
        assert F(m['server_address_validated'])==7
        assert [(F(t['start']),F(t['end'])) for t in r['transmissions'] if t['kind']=='request' and t['encryption_level']=='0rtt']==[(F(a),F(b)) for a,b in hand['timing']['early_send_intervals']]
    # Move serverflight arrival into an already-started packet: finish it with
    # old keys, then controls, then new keys. Both accept and reject matter.
    for result,retry in [('accept',True),('reject',True),('reject',False)]:
        p=hand_input(c,result,retry);p['s2c_propagation_seconds']='1/2'
        r=c.calculate(p);checks['midpacket-'+result+str(retry)]=audit(r)
        keys=F(r['milestones']['client_1rtt_keys_installed'])
        crossing=[t for t in r['transmissions'] if t['kind']=='request' and F(t['start'])<keys<F(t['end'])]
        assert len(crossing)==1 and crossing[0]['encryption_level']=='0rtt';midpacket+=1
    # Tail lengths and rate/asymmetric-delay sweeps independently audited.
    for size in (1,1168,1169,7009,23361):
      for rate in (4912,9824,19648):
       for result in ('accept','reject'):
        p=hand_input(c,result);p.update(request_payload_bytes=size,c2s_bits_per_second=rate)
        r=c.calculate(p);checks[f'tail-{size}-{rate}-{result}']=audit(r)
    # Both antiamp exhaustion and received discarded data credit. Keep a short
    # request so absence of a Handshake ACK genuinely leaves 4800budget blocked.
    for ack in (False,True):
        p=hand_input(c);p.update(request_payload_bytes=1,server_flight_ack=ack)
        p['packets']['server_flight']=[1200]*4
        r=c.calculate(p);checks['budget-'+str(ack)]=audit(r)
        assert (r['status']=='complete')==ack
    root_mid=json.loads((ROOT/'root-midpacket-check.json').read_text())
    for expected in root_mid['checks']:
        p=copy.deepcopy(root_mid['inputs']);p.update(early_result=expected['outcome'],application_retry_authorized=expected['retry'])
        r=c.calculate(p);checks['root-mid-'+expected['outcome']+str(expected['retry'])]=audit(r)
        assert F(r['milestones']['client_1rtt_keys_installed'])==F(expected['keys'])
        assert r['milestones'].get('complete_response')==expected['complete_response']
    source_root=ROOT.parent/'protocol-handshake'
    source_records=json.loads((source_root/'sources.lock.json').read_text())
    for source in source_records:
        raw=(source_root/source['file']).read_bytes()
        assert len(raw)==source['bytes'] and hashlib.sha256(raw).hexdigest()==source['sha256']
    invalid=[]
    for field in ('application_early_data_authorized','application_retry_authorized','valid_psk','early_credentials_valid','address_token_valid','server_flight_ack'):
        p=hand_input(c);p[field]=1;invalid.append(p)
    for field,value in [('application_early_data_authorized',False),('valid_psk',False),('packet_payload_bytes',0),('one_rtt_overhead_bytes',31),('packet_payload_bytes',65507),('request_payload_bytes',10**12),('c2s_bits_per_second',0)]:
        p=hand_input(c);p[field]=value;invalid.append(p)
    p=hand_input(c);p['packets']['client_hello']=[1199];invalid.append(p)
    p=hand_input(c);p['packets']['server_flight']=[1200]*200001;invalid.append(p)
    for p in invalid:
        try:c.calculate(p)
        except ValueError:pass
        else:raise AssertionError('Invalid input accepted')
    assert hashlib.sha256((ROOT/'calculate.py').read_bytes()).hexdigest()==start_sha,'Candidate changed during review'
    report=dict(status='pass',candidate_sha256=hashlib.sha256((ROOT/'calculate.py').read_bytes()).hexdigest(),
                source_hashes_verified=len(source_records),scenario_count=len(checks),scenarios=checks,midpacket_key_cases=midpacket,invalid_inputs_rejected=len(invalid),
                method='Independent exact packet interval multiplicities, key-at-start, PN and directed serializer/antiamp accounting; root hand oracles and actual30MB runs',
                limitations=['Declared packet/dependency model, no crypto/codec/HTTP/congestion/general ACK/PTO execution.'])
    (ROOT/'check-independent.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='scenarios'}))

if __name__=='__main__':main()
