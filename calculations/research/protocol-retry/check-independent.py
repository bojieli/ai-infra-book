"""Independent HRR, Retry, PSK and byte-interval audit."""
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



def load_module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module


def audit(r):
    p=r['inputs'];packets=r['transmissions'];m=r['milestones'];s=r['summary'];branch=p.get('handshake_event','none')
    keys=F(m['client_1rtt_keys_installed']) if 'client_1rtt_keys_installed' in m else None
    proof=[e for e in packets if e['direction']=='c2s' and e['kind'] in ('handshake_ack','client_finished')]
    if branch=='retry' and p['retry_integrity_valid'] and p['retry_token_valid']:
        proof += [e for e in packets if e['kind']=='client_hello_retry']
    validation=F(0) if p['address_token_valid'] else min((F(e['arrival']) for e in proof),default=None)
    if validation is not None and not p['address_token_valid']:assert F(m['server_address_validated'])==validation
    canonical=[]
    for e in packets:
        d=e['direction'];start,end,arrival=map(F,(e['start'],e['end'],e['arrival']))
        assert e['wire_bytes']==e['udp_bytes']+28
        assert end-start==F(8*e['wire_bytes'],F(str(p[d+'_bits_per_second'])))
        assert arrival==end+F(str(p[d+'_propagation_seconds']))
        canonical.append(dict(direction=d,start=start,end=end,arrival=arrival,udp_payload=e['udp_bytes']))
        if e['kind']=='request':
            assert e['end_offset']-e['offset']==e['payload_bytes']>0
            assert (e['encryption_level']=='1rtt')==(keys is not None and start>=keys)
            should_accept=(e['encryption_level']=='1rtt' or (p['early_result']=='accept' and branch in ('none','retry')))
            if branch=='retry' and (e['attempt_epoch']==0 or not p['retry_token_valid']):should_accept=False
            if branch in ('psk_unknown_abort','selected_binder_invalid'):should_accept=False
            assert e.get('accepted')==should_accept
        if e['kind']=='retry':assert 'packet_number' not in e
        if e['kind']=='failure':assert e['packet_number_space']=='initial'
    for direction in ('c2s','s2c'):
        rows=sorted((e for e in canonical if e['direction']==direction),key=lambda e:(e['start'],e['end']))
        assert all(a['end']<=b['start'] for a,b in zip(rows,rows[1:]))
        assert s['modeled_wire_bytes_by_direction'][direction]==sum(e['wire_bytes'] for e in packets if e['direction']==direction)
        for space in ('initial','handshake','application'):
            pn=[e['packet_number'] for e in packets if e['direction']==direction and e.get('packet_number_space')==space]
            assert pn==list(range(len(pn)))
    antiamp(canonical,validation)
    request=[e for e in packets if e['kind']=='request'];accepted=[(e['offset'],e['end_offset']) for e in request if e.get('accepted')]
    assert s['request_payload_sent_bytes']==sum(e['payload_bytes'] for e in request)
    assert s['early_payload_sent_bytes']==sum(e['payload_bytes'] for e in request if e['encryption_level']=='0rtt')
    if r['status']=='complete':
        partition(accepted,p['request_payload_bytes'])
        assert s['application_execution_count']==1 and s['accepted_unique_request_bytes']==p['request_payload_bytes']
        response=[e for e in packets if e['kind']=='response'];partition([(e['offset'],e['end_offset']) for e in response],p['response_payload_bytes'])
        assert F(m['complete_request'])==max(F(e['arrival']) for e in request if e.get('accepted'))
        assert F(m['complete_response'])==max(F(e['arrival']) for e in response)
        assert all(e['destination_connection_id']==p['client_scid'] for e in response)
    if branch=='hrr':
        hrr=F(m['hrr_received'])
        assert all(F(e['start'])<hrr for e in request if e['encryption_level']=='0rtt')
        ch2=[e for e in packets if e['kind']=='client_hello_hrr']
        assert all(e['tls_client_hello_identity']=='CH2-no-early-data' for e in ch2)
        assert min(F(e['start']) for e in ch2)>=hrr
        assert not any(e.get('retry_token_bytes',0) for e in ch2)
    if branch=='retry' and p['retry_integrity_valid']:
        ch1=[e for e in packets if e['kind']=='client_hello'];ch2=[e for e in packets if e['kind']=='client_hello_retry']
        assert all(e['initial_key_epoch']==0 for e in ch1)
        assert all(e['initial_key_epoch']==1 for e in ch2)
        assert all(e['tls_client_hello_identity']=='CH1' for e in ch1+ch2)
        assert all(e['source_connection_id']==p['client_scid'] for e in ch1+ch2)
        assert all(e['destination_connection_id']==p['retry_scid'] and e['retry_token_bytes']==p['retry_token_bytes'] for e in ch2)
        assert all(not e.get('accepted') for e in request if e['attempt_epoch']==0)
    if branch in ('selected_binder_invalid','psk_unknown_abort'):
        assert r['status']=='handshake_failed' and not accepted
        assert s['application_execution_count']==0 and 'complete_response' not in m
        failure=F(m['failure_received'])
        assert all(F(e['start'])<failure for e in request)
    return dict(status=r['status'],packets=len(packets),sent_payload=s['request_payload_sent_bytes'],accepted_payload=s['accepted_unique_request_bytes'],execution=s['application_execution_count'],complete_response=m.get('complete_response'))


def hand_input(c,branch='none',early=False,count=1):
    p=c.example();p.update(handshake_event=branch,send_early=early,
        request_payload_bytes=1168*count,response_payload_bytes=100,packet_payload_bytes=1168,
        zero_rtt_overhead_bytes=32,one_rtt_overhead_bytes=32,response_overhead_bytes=1100,
        c2s_bits_per_second=9824,s2c_bits_per_second=9824,c2s_propagation_seconds=1,s2c_propagation_seconds=1,
        model_seconds=0,server_flight_ack=False)
    for name in ('client_hello','client_finished','handshake_ack','retry','client_hello_retry','hrr','client_hello_hrr','failure'):
        p['packets'][name]=[1200]
    p['packets']['server_flight']=[1200,1200]
    return p


def main():
    import copy
    c=load_module('retry_candidate',ROOT/'calculate.py')
    old=load_module('frozen_stream',ROOT.parent/'protocol-early-stream/calculate.py')
    start_hash=hashlib.sha256((ROOT/'calculate.py').read_bytes()).hexdigest();checks={}
    # Compare every old numeric result and every old transmission field.
    for name,p in old.scenarios().items():
        before=old.calculate(p);after=c.calculate(p)
        for key in ('status','milestones','summary','anti_amplification_blocks'):
            assert before[key]==after[key],(name,key)
        assert len(before['transmissions'])==len(after['transmissions'])
        for a,b in zip(before['transmissions'],after['transmissions']):
            assert all(b[k]==v for k,v in a.items()),(name,a,b)
        checks['old-baseline-'+name]=audit(after)
    for name,p in c.scenarios().items():checks['candidate-'+name]=audit(c.calculate(p))
    hand=json.loads((ROOT/'hand-oracles.json').read_text())
    for branch,key in [('none','baseline'),('hrr','hrr'),('retry','retry'),('psk_unknown_fallback','baseline')]:
      for authorized in (False,True):
        p=hand_input(c,branch);p['application_retry_authorized']=authorized;p['application_early_data_authorized']=False
        if branch=='psk_unknown_fallback':p['valid_psk']=False
        r=c.calculate(p);checks[f'noearly-{branch}-{authorized}']=audit(r)
        expected=hand['normal_one_packet_request'][key]
        assert F(r['milestones']['complete_request'])==expected['complete_request']
        assert F(r['milestones']['complete_response'])==expected['complete_response']
        assert r['summary']['early_payload_sent_bytes']==0
    p=hand_input(c,'retry',True,4);r=c.calculate(p);checks['root-retry-early']=audit(r)
    h=hand['retry_then_early_accept']
    assert r['summary']['early_payload_sent_bytes']==h['total_early_payload_sent']
    assert r['summary']['accepted_unique_request_bytes']==h['accepted_unique_payload']
    assert F(r['milestones']['complete_request'])==10 and F(r['milestones']['complete_response'])==12
    req=[e for e in r['transmissions'] if e['kind']=='request']
    assert [e['packet_number'] for e in req]==h['application_pn']
    assert [(F(e['start']),F(e['end'])) for e in req if e['attempt_epoch']==0]==[(F(a),F(b)) for a,b in h['old_early_send']]
    assert [(F(e['start']),F(e['end'])) for e in req if e['attempt_epoch']==1]==[(F(a),F(b)) for a,b in h['repeated_early_send']]
    assert all(e.get('application_key_epoch',0)==0 for e in req if e['encryption_level']=='0rtt')
    # Fatal signal consumes real reverse time; sender is not omniscient.
    for branch in ('selected_binder_invalid','psk_unknown_abort'):
        p=hand_input(c,branch,True,4);p.update(valid_psk=False,client_credentials_available=True)
        r=c.calculate(p);checks['fatal-latency-'+branch]=audit(r)
        req=[e for e in r['transmissions'] if e['kind']=='request']
        assert [(F(e['start']),F(e['end'])) for e in req]==[(1,2),(2,3),(3,4)]
        assert F(r['milestones']['failure_received'])==4
        assert F(r['summary']['last_modeled_arrival'])==5
        assert r['summary']['accepted_unique_request_bytes']==0
    # ClientHello fits Initial1, but token400 reduces each Initial2 capacity;
    # two Initial2s are required. Validation is first receipt6, full CH at7.
    p=hand_input(c,'retry');p.update(retry_token_bytes=400,client_hello_crypto_bytes=900)
    p['packets']['client_hello_retry']=[1200,1200]
    r=c.calculate(p);checks['token-two-initials']=audit(r)
    assert F(r['milestones']['server_address_validated'])==6
    assert F(r['milestones']['client_hello_retry_received'])==7
    assert F(r['milestones']['complete_response'])==15
    # Invalid-token close interrupts future control packets, not an active one.
    p=hand_input(c,'retry',True,20);p['retry_token_valid']=False;p['packets']['client_hello_retry']=[1200]*10
    r=c.calculate(p);checks['invalid-token-control-stop']=audit(r)
    failure=F(r['milestones']['failure_received'])
    assert all(F(e['start'])<failure for e in r['transmissions'] if e['direction']=='c2s')
    # Invalid integrity discards Retry; no epoch/key/token state change.
    p=hand_input(c,'retry',True,4);p['retry_integrity_valid']=False
    r=c.calculate(p);checks['invalid-integrity-discard']=audit(r)
    assert r['status']=='waiting_unmodeled_recovery'
    assert not any(e['kind']=='client_hello_retry' for e in r['transmissions'])
    assert r['summary']['application_execution_count']==0
    assert all(e.get('attempt_epoch',0)==0 for e in r['transmissions'])
    # All branches under a partial packet at event arrival, and one-byte tails.
    for branch in ('hrr','retry','psk_unknown_fallback'):
      for outcome in ('accept','reject'):
       for authorized in (False,True):
        p=hand_input(c,branch,True,6);p.update(request_payload_bytes=7009,s2c_propagation_seconds='1/2',early_result=outcome,application_retry_authorized=authorized)
        r=c.calculate(p);checks[f'mid-{branch}-{outcome}-{authorized}']=audit(r)
    p=hand_input(c,'retry',True,4);p.update(retry_early_policy='wait_1rtt',application_retry_authorized=False)
    r=c.calculate(p);checks['wait-1rtt-without-app-replay']=audit(r)
    assert r['summary']['one_rtt_payload_sent_bytes']==0 and r['summary']['application_execution_count']==0
    source_root=ROOT.parent/'protocol-handshake'
    sources=json.loads((source_root/'sources.lock.json').read_text())
    for source in sources:
        raw=(source_root/source['file']).read_bytes()
        assert len(raw)==source['bytes'] and hashlib.sha256(raw).hexdigest()==source['sha256']
    invalid=[]
    for name,value in [('retry_token_bytes',0),('retry_token_valid',1),('send_early',1),('handshake_event','hrr+retry'),('client_hello_crypto_bytes',2000)]:
        p=hand_input(c,'retry');p[name]=value;invalid.append(p)
    p=hand_input(c,'retry');p['packets']['retry']=[1200,1200];invalid.append(p)
    p=hand_input(c,'retry');p.update(retry_token_bytes=1160,client_hello_crypto_bytes=100);invalid.append(p)
    p=hand_input(c,'retry');p.update(retry_early_replay_authorized=False,send_early=True);invalid.append(p)
    p=hand_input(c,'selected_binder_invalid');p['packets']['failure']=[1200,1200];invalid.append(p)
    for p in invalid:
        try:c.calculate(p)
        except ValueError:pass
        else:raise AssertionError('Invalid accepted')
    assert start_hash==hashlib.sha256((ROOT/'calculate.py').read_bytes()).hexdigest(),'Candidate changed during run'
    report=dict(status='pass',candidate_sha256=start_hash,source_hashes_verified=len(sources),scenario_count=len(checks),scenarios=checks,
        invalid_inputs_rejected=len(invalid),limitations=['QUIC finite branch and declared metadata audit only; runtime repeated/empty-token Retry, TCP HRR, combined branches, general loss/HTTP are not implemented.'])
    (ROOT/'check-independent.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='scenarios'}))

if __name__=='__main__':main()
