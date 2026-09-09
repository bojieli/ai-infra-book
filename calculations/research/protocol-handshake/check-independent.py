"""Independent RFC-constrained message/byte/timing audit; no TLS execution."""
from fractions import Fraction as F
from pathlib import Path
import hashlib
import importlib.util
import json

ROOT=Path(__file__).resolve().parent


def verify_sources():
    rows=json.loads((ROOT/'sources.lock.json').read_text())
    for row in rows:
        raw=(ROOT/row['file']).read_bytes()
        assert len(raw)==row['bytes'] and hashlib.sha256(raw).hexdigest()==row['sha256']
    return len(rows)


def assert_resources(events):
    """Canonical event: id,direction,start,end,arrival,wire,rate,propagation."""
    by_id={e['id']:e for e in events}
    assert len(by_id)==len(events)
    for e in events:
        assert e['start']>=0
        assert e['end']-e['start']==F(8*e['wire'],e['rate'])
        assert e['arrival']==e['end']+e['propagation']
        for dependency in e.get('dependencies',[]):
            assert e['start']>=by_id[dependency]['arrival']
    for direction in ('c2s','s2c'):
        ordered=sorted((e for e in events if e['direction']==direction),key=lambda e:(e['start'],e['end']))
        assert all(a['end']<=b['start'] for a,b in zip(ordered,ordered[1:]))


def assert_anti_amplification(events,validated_at=None):
    """RFC9000§8.1: only arrived UDP payload counts; no IP/UDP header credit.

    Canonical QUIC events include udp_payload. Count every server datagram
    reservation at start, including a datagram that straddles validation.
    """
    sent=0
    for server in sorted((e for e in events if e['direction']=='s2c'),key=lambda e:e['start']):
        sent+=server['udp_payload']
        if validated_at is not None and server['start']>=validated_at:
            continue
        received=sum(e['udp_payload'] for e in events if e['direction']=='c2s' and e['arrival']<=server['start'])
        assert sent<=3*received,(server['id'],sent,received,validated_at)


def normalize(result):
    p=result['inputs'];events=[]
    for row in result['transmissions']:
        direction=row['direction']
        events.append(dict(id=f"{row['flight']}:{row['packet']}",flight=row['flight'],index=row['packet'],
            direction=direction,start=F(row['start']),end=F(row['end']),arrival=F(row['arrival']),wire=row['wire_bytes'],
            rate=F(str(p[direction+'_bits_per_second'])),propagation=F(str(p[direction+'_propagation_seconds'])),
            udp_payload=row['declared_bytes']))
    return events


def audit(result):
    p=result['inputs'];events=normalize(result);assert_resources(events)
    flights={}
    for e in events:flights.setdefault(e['flight'],[]).append(e)
    def first(name):return min(e['start'] for e in flights[name])
    def last(name):return max(e['arrival'] for e in flights[name])
    milestones=result['milestones']
    for name,value in milestones.items():
        if name.endswith('_received') and name[:-9] in flights:assert F(value)==last(name[:-9])
    if p['mode']!='reused':
        if p['protocol']=='tcp_tls13':
            assert first('syn_ack')>=last('syn')
            assert first('client_hello')>=last('syn_ack')
        assert first('server_flight')>=last('client_hello')
        if 'client_finished' in flights:assert first('client_finished')>=last('server_flight')
        if 'request' in flights:assert first('request')>=max(e['end'] for e in flights['client_finished'])
    if 'accepted_request' in milestones:
        request_flight='early_request' if p['mode']=='early_accept' else 'request'
        assert F(milestones['accepted_request'])==last(request_flight)
        assert F(milestones['application_execution'])>=last(request_flight)
        if p['mode']!='reused' and p.get('application_policy','wait_client_finished')=='wait_client_finished':
            assert F(milestones['application_execution'])>=last('client_finished')
    if 'response' in flights:
        assert first('response')>=F(milestones['application_execution'])+F(str(p.get('model_seconds',0)))
        if p['mode']!='reused':assert first('response')>=max(e['end'] for e in flights['server_flight'])
    if p['protocol']=='quic_v1':
        for e in events:
            if e['flight']=='client_hello' or e['flight']=='server_flight' and e['index']==0:assert e['udp_payload']>=1200
            assert e['wire']==e['udp_payload']+28
        verified=F(0) if p['mode']=='reused' or p.get('address_token_valid',False) else None
        validation_packets=[e for e in events if e['flight'] in ('client_finished','handshake_ack')]
        if verified is None and validation_packets:verified=min(e['arrival'] for e in validation_packets)
        assert_anti_amplification(events,verified)
        if verified is not None and not (p['mode']=='reused' or p.get('address_token_valid',False)):
            assert F(milestones['server_address_validated'])==verified
        if p['mode'].startswith('early_') and 'server_flight_received' in milestones:
            assert max(e['end'] for e in flights['early_request'])<=F(milestones['server_flight_received'])
    summary=result['summary']
    for d in ('c2s','s2c'):assert summary['modeled_wire_bytes_by_direction'][d]==sum(e['wire'] for e in events if e['direction']==d)
    if p['mode']=='early_reject':
        retry=p.get('application_retry_authorized',False)
        assert summary['request_payload_sent_bytes']==p['request_payload_bytes']*(2 if retry else 1)
        assert summary['application_execution_count']==int(retry)
        assert summary['accepted_unique_request_bytes']==(p['request_payload_bytes'] if retry else 0)
        if not retry:assert 'complete_response' not in milestones
    return len(events)


def simple_oracle(p):
    """External flight-level max-plus for fully validated, no-flight-ACK cases.

    No dependence on candidate event times or callbacks. Declared handshake has
    no congestion/loss; all packets in each flight serialize consecutively.
    """
    quic=p['protocol']=='quic_v1';mode=p['mode'];extra=28 if quic else 0
    d={k:F(str(p[k+'_propagation_seconds'])) for k in ('c2s','s2c')}
    rate={k:F(str(p[k+'_bits_per_second'])) for k in d};links={k:F(0) for k in d}
    def send(name,direction,ready):
        duration=F(8*sum(x+extra for x in p['packets'][name]),rate[direction])
        start=max(links[direction],ready);links[direction]=start+duration
        return links[direction]+d[direction]
    early=mode.startswith('early_')
    if mode=='reused':accepted=send('request','c2s',F(0));sf=None;finished=None
    else:
        tls=F(0) if quic else send('syn_ack','s2c',send('syn','c2s',F(0)))
        hello=send('client_hello','c2s',tls)
        early_received=send('early_request','c2s',tls) if early else None
        sf=send('server_flight','s2c',hello)
        finished=send('client_finished','c2s',sf)
        if mode=='early_accept':accepted=early_received
        elif mode=='early_reject' and not p.get('application_retry_authorized',False):return None,None
        else:accepted=send('request','c2s',sf)
    execute=max(accepted,finished) if mode!='reused' and p.get('application_policy')=='wait_client_finished' else accepted
    complete=send('response','s2c',execute+F(str(p.get('model_seconds',0))))
    return execute,complete


def main():
    import copy
    spec=importlib.util.spec_from_file_location('candidate',ROOT/'calculate.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    sources=verify_sources();checks={};total=0
    for name,p in m.scenarios().items():
        r=m.calculate(p);total+=audit(r);checks[name]=r['status']
    for protocol in ('tcp_tls13','quic_v1'):
        for mode in ('fresh','resume','early_accept','early_reject','reused'):
            for policy in ('immediate','wait_client_finished'):
                p=m.example(protocol,mode);p.update(address_token_valid=True,server_flight_ack=False,application_policy=policy)
                r=m.calculate(p);total+=audit(r);execution,complete=simple_oracle(p)
                assert F(r['milestones']['application_execution'])==execution
                assert F(r['milestones']['complete_response'])==complete
                checks[f'oracle-{protocol}-{mode}-{policy}']='pass'
    # Anti-amplification equality3600 and inability to use future or wire credit.
    for sizes,ack,complete in (([1200]*3,False,True),([1200]*4,False,False),([1200]*4,True,True),([1200,1200,1228],False,False)):
        p=m.example();p['packets']['server_flight']=sizes;p['server_flight_ack']=ack
        r=m.calculate(p);total+=audit(r)
        assert (r['status']=='complete')==complete
        if not complete:
            assert sum(t['declared_bytes'] for t in r['transmissions'] if t['direction']=='s2c')<=3600
            assert r['pending_packets']
        checks['budget-'+str(sizes)+'-'+str(ack)]='pass'
    # Early serialization ends before keys but request reaches server AFTER the
    # whole server flight reaches client. Server flight must not wait for tail.
    p=m.example(mode='early_accept');p['c2s_bits_per_second']=20000
    p['packets']['early_request']=[160];p['request_payload_bytes']=100
    # Initial itself takes~0.49s; early finishes~0.56s, SF arrives~0.59s.
    r=m.calculate(p);total+=audit(r)
    sf=[e for e in normalize(r) if e['flight']=='server_flight']
    er=[e for e in normalize(r) if e['flight']=='early_request']
    assert min(e['start'] for e in sf)<max(e['arrival'] for e in er)
    checks['early_tail_arrives_after_server_flight']='pass'
    # Discarded 0RTT datagrams still earn received-UDP amplification credit.
    p=m.example(mode='early_reject');p['server_flight_ack']=False
    p['packets']['early_request']=[400];p['packets']['server_flight']=[1200]*4
    r=m.calculate(p);total+=audit(r)
    assert r['status']=='complete'
    fourth=next(e for e in normalize(r) if e['flight']=='server_flight' and e['index']==3)
    early_arrival=next(e['arrival'] for e in normalize(r) if e['flight']=='early_request')
    assert fourth['start']>=early_arrival
    checks['rejected_early_counts_only_after_receipt']='pass'
    # Immediate execution cannot bypass antiamp with a large1RTT response;
    # application bytes may be ready but server transmission needs validation.
    p=m.example(mode='early_accept');p['packets']['response']=[5032]
    p['response_payload_bytes']=5000;p['payload_bytes_by_packet']['response']=[5000]
    r=m.calculate(p);total+=audit(r)
    assert min(e['start'] for e in normalize(r) if e['flight']=='response')>=F(r['milestones']['server_address_validated'])
    checks['server_response_waits_for_budget_validation']='pass'
    for protocol in ('tcp_tls13','quic_v1'):
        p=m.example(protocol,'early_accept');floor=62 if protocol=='tcp_tls13' else 32
        for name in ('request','early_request','response'):
            p['packets'][name]=[sum(p['payload_bytes_by_packet'][name])+floor]
        r=m.calculate(p);total+=audit(r)
        checks[protocol+'-declared-overhead-equality']='pass'
    invalid=[]
    for protocol in ('tcp_tls13','quic_v1'):
        for name in ('valid_psk','early_credentials_valid','application_early_data_authorized'):
            p=m.example(protocol,'early_accept');p[name]=1;invalid.append((name,p))
        p=m.example(protocol,'early_accept');p['application_early_data_authorized']=False;invalid.append(('no_early_app_permission',p))
        p=m.example(protocol,'early_accept');p['packets']['early_request']=[101 if protocol=='quic_v1' else 120];invalid.append(('impossible_early_payload',p))
    for which in ('client_hello','server_flight'):
        p=m.example();p['packets'][which][0]=1199;invalid.append(('small_initial',p))
    p=m.example(mode='early_accept');p['packets']['early_request']=[60000];p['request_payload_bytes']=100; p['c2s_bits_per_second']=20000;invalid.append(('early_crosses_keys',p))
    for protocol in ('tcp_tls13','quic_v1'):
        for flight in ('request','early_request','response'):
            p=m.example(protocol,'early_accept');floor=62 if protocol=='tcp_tls13' else 32
            p['packets'][flight]=[sum(p['payload_bytes_by_packet'][flight])+floor-1]
            invalid.append(('insufficient_declared_overhead-'+flight,p))
        p=m.example(protocol,'early_accept');p['payload_bytes_by_packet']['early_request']=[99]
        invalid.append(('payload_distribution_sum',p))
    for name,p in invalid:
        try:m.calculate(p)
        except ValueError:pass
        else:raise AssertionError('Invalid accepted: '+name)
    hand=json.loads((ROOT/'hand-oracles.json').read_text())
    for name,expected in hand['example_complete_response_seconds'].items():
        protocol,mode=name.split('-',1);r=m.calculate(m.example(protocol,mode))
        assert F(r['milestones']['complete_response'])==F(expected)
        checks['root-hand-'+name]='pass'
    report=dict(status='pass',source_hashes_verified=sources,scenarios=checks,transmissions_audited=total,
                invalid_cases_rejected=len(invalid),candidate_sha256=hashlib.sha256((ROOT/'calculate.py').read_bytes()).hexdigest(),
                scope='RFC-constrained declared packet graph and arithmetic, not packet parser, cryptography, HTTP profile, full transport or runtime validation.')
    (ROOT/'check-independent.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='scenarios'}))

if __name__=='__main__':main()
