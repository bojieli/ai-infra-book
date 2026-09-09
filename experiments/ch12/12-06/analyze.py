#!/usr/bin/env python3
"""Offline acceptance: no imports from transport implementation."""
import argparse, base64, collections, copy, hashlib, json, pathlib, statistics, struct
ROOT=pathlib.Path(__file__).resolve().parent
def digest(b): return hashlib.sha256(b).hexdigest()
def loadlines(p): return [json.loads(x) for x in p.read_text().splitlines()]
def canonical(m): return (json.dumps(m,sort_keys=True,separators=(',',':'))+'\n').encode()
def check(c,s,r,fixture):
    def events(log,e): return [x for x in log if x['event']==e]
    assert r['client_pid']!=r['server_pid'] and r['server_exit']==0
    assert all(x['pid']==r['client_pid'] for x in c)
    assert all(x['pid']==r['server_pid'] for x in s)
    assert len(r['ports'])==2 and len(set(r['ports'].values()))==2
    assert all(v==61 for v in r['cleanup_connect_errno'].values()), 'Mac ECONNREFUSED required'
    assert r['maxrss_bytes']<768*1024**2 and events(s,'exit')[0]['maxrss_bytes']<768*1024**2
    assert not events(c,'forced_kill') and not events(s,'timeout')
    for log in (c,s):
        assert [x['t_ns'] for x in log]==sorted(x['t_ns'] for x in log)
        for e in log:
            if e['event'] not in ('send','recv'): continue
            b=canonical(e['msg']); assert len(b)==e['wire_bytes'] and digest(b)==e['sha']
            m=e['msg']
            if 'data' in m:
                d=base64.b64decode(m['data'],validate=True); assert digest(d)==m['payload_sha']
                if m['kind']=='audio': assert d==fixture[m['seq']*640:(m['seq']+1)*640]
                else: assert d==b'{"id":"tool-1","result":{"temperature_c":23,"unit":"C"}}'
    def frames(log,ev): return collections.Counter((x['path'],canonical(x['msg'])) for x in events(log,ev))
    assert frames(c,'recv')==frames(s,'send'), 'response matching'
    if r['fault']=='endpoint': assert not (frames(s,'recv')-frames(c,'send'))
    else: assert frames(c,'send')==frames(s,'recv'), 'request matching'
    consumed=events(c,'consume'); expected=list(range(4 if r['fault']=='endpoint' else 8))
    assert [x['seq'] for x in consumed]==expected, 'ordered unique consumption'
    for x in consumed:
        data=fixture[x['seq']*640:(x['seq']+1)*640]
        assert x['sha']==digest(data) and x['bytes']==640
        assert x['square_sum']==sum(v*v for v in struct.unpack('<320h',data))
    audio=[x for x in events(c,'recv') if x['msg']['kind']=='audio']
    dup=events(c,'duplicate'); assert len(dup)==len(audio)-len(consumed)
    assert sum(x['bytes'] for x in dup)==640*len(dup)
    assert len(events(c,'out_of_order'))==len(expected)//2
    for start in range(0,len(expected),2):
        for path in ('A','B'):
            seqs=[x['msg']['seq'] for x in audio if x['path']==path and x['msg']['rid']==f'a{start}']
            assert seqs in ([],[start+1,start])
    fault=events(s,'fault'); assert len(fault)==int(r['fault']!='none')
    if fault:
        assert fault[0]['scope']==r['fault']
        closed=[x['path'] for x in events(s,'close') if x['reason']=='injected_'+r['fault']]
        assert set(closed)==({'A','B'} if r['fault']=='endpoint' else {'A'})
        assert {'A'} <= {x['path'] for x in events(c,'eof')}
    assert len(events(c,'retry'))==int(r['mode']=='switch' and r['fault']!='none')
    ok=r['fault']!='endpoint'; assert r['completed']==ok
    if ok:
        assert r['error'] is None and len(events(c,'complete'))==1 and not events(c,'failure')
        interrupt=events(c,'interrupt'); confirmed=events(c,'cancel_confirmed'); assert len(interrupt)==len(confirmed)==1
        ack=[x for x in events(c,'recv') if x['msg']['kind']=='cancel_ack']; assert ack, 'cancel ACK required'
        assert all(x['msg']['cancel_id']=='cancel-1' and interrupt[0]['t_ns']<x['t_ns']<confirmed[0]['t_ns'] for x in ack)
        assert max(x['t_ns'] for x in consumed)<interrupt[0]['t_ns']
        assert not [x for x in audio if x['t_ns']>interrupt[0]['t_ns']]
        assert [x for x in events(c,'recv') if x['msg']['kind']=='cancelled']
        assert len(events(c,'tool_apply'))==1
        for apply in events(s,'cancel_apply'):
            assert not [x for x in events(s,'send') if x['t_ns']>apply['t_ns'] and x['msg']['kind']=='audio']
    else:
        assert not events(c,'complete') and not events(c,'cancel_confirmed') and not events(c,'tool_apply')
        assert len(events(c,'failure'))==1 and r['error'] in ('ConnectionError: no_response', 'ConnectionResetError: [Errno 54] Connection reset by peer')
    t0=events(c,'connect')[0]['t_ns']
    finish=(events(c,'complete') or events(c,'failure'))[0]['t_ns']
    return dict(mode=r['mode'],fault=r['fault'],completed=ok,audio_received_bytes=len(audio)*640,unique_consumed_bytes=len(consumed)*640,duplicate_audio_bytes=len(dup)*640,out_of_order=len(events(c,'out_of_order')),application_ms=(finish-t0)/1e6,cancel_ack_ms=(ack[0]['t_ns']-interrupt[0]['t_ns'])/1e6 if ok else None,application_frame_bytes=sum(x['wire_bytes'] for x in events(c,'send')+events(s,'send')),server_rss=events(s,'exit')[0]['maxrss_bytes'])
def analyze(folder):
    env=json.loads((folder/'environment.json').read_text()); fixture=(folder/'fixture.pcm').read_bytes()
    expected=b''.join(struct.pack('<h',((i*257)%24001)-12000) for i in range(24*320))
    assert fixture==expected and digest(fixture)==env['fixture_sha']
    for name,h in env['source_hashes'].items():
        assert any(p.exists() and digest(p.read_bytes())==h for p in (ROOT/name,ROOT/'sources-v1'/name)), name+' source missing'
    rows=[]; mutation_seed=None
    index=json.loads((folder/'index.json').read_text()); counts=collections.Counter((x['mode'],x['fault']) for x in index)
    assert counts==collections.Counter({(m,f):env['repeats'] for m in ('replicate','switch') for f in ('none','primary','endpoint')})
    for item in index:
        d=folder/item['name']; r=json.loads((d/'result.json').read_text()); assert all(item[k]==v for k,v in r.items())
        c=loadlines(d/'client.jsonl'); s=loadlines(d/'server.jsonl'); rows.append(dict(name=item['name'],**check(c,s,r,fixture)))
        if r['mode']=='replicate' and r['fault']=='none': mutation_seed=(c,s,r)
    rejected=[]
    for kind in ('duplicate_consume','missing_cancel_ack','corrupt_payload'):
        c,s,r=copy.deepcopy(mutation_seed)
        if kind=='duplicate_consume':
            pos=next(i for i,e in enumerate(c) if e['event']=='consume'); c.insert(pos,copy.deepcopy(c[pos]))
        elif kind=='missing_cancel_ack': c=[e for e in c if not(e['event']=='recv' and e['msg']['kind']=='cancel_ack')]
        else:
            e=next(e for e in c if e['event']=='recv' and 'data' in e['msg']); e['msg']['data']='AAAA'
        try: check(c,s,r,fixture)
        except (AssertionError,ValueError): rejected.append(kind)
        else: raise AssertionError('mutation accepted: '+kind)
    groups=[]
    for m,f in counts:
        rs=[r for r in rows if r['mode']==m and r['fault']==f]
        groups.append(dict(mode=m,fault=f,n=len(rs),completed=sum(r['completed'] for r in rs),median_application_ms=statistics.median(r['application_ms'] for r in rs),duplicate_audio_bytes=sorted(set(r['duplicate_audio_bytes'] for r in rs)),application_frame_bytes=sorted(set(r['application_frame_bytes'] for r in rs))))
    summary=dict(accepted=len(rows),expected_failures=sum(not r['completed'] for r in rows),mutation_rejected=rejected,groups=groups,rows=rows)
    (ROOT/(folder.name+'-summary.json')).write_text(json.dumps(summary,indent=2)); print(json.dumps({k:v for k,v in summary.items() if k!='rows'},indent=2))
if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('--folder',default='results'); a=ap.parse_args(); analyze(ROOT/a.folder)
