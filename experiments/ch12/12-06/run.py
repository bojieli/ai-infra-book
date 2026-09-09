#!/usr/bin/env python3
"""Two single-thread processes, two real loopback TCP sockets; stdlib only."""
import argparse, base64, hashlib, json, os, pathlib, platform, random, resource
import select, socket, struct, subprocess, sys, time
ROOT = pathlib.Path(__file__).resolve().parent

def sha(b): return hashlib.sha256(b).hexdigest()
def pcm(): return b''.join(struct.pack('<h', ((i * 257) % 24001) - 12000) for i in range(24*320))
def encode(m): return (json.dumps(m, sort_keys=True, separators=(',', ':'))+'\n').encode()
def limits():
    # macOS rejects low RLIMIT_AS; bound objects and check observed RSS instead.
    assert usage()["maxrss_bytes"] < 768*1024**2
    resource.setrlimit(resource.RLIMIT_FSIZE, (16*1024**2, 16*1024**2))
def usage():
    r = resource.getrusage(resource.RUSAGE_SELF)
    return dict(maxrss_bytes=r.ru_maxrss if sys.platform=='darwin' else r.ru_maxrss*1024, cpu_s=r.ru_utime+r.ru_stime)
class Log:
    def __init__(self, p): self.f=open(p,'x')
    def __call__(self, event, **kw):
        assert usage()['maxrss_bytes'] < 768*1024**2
        self.f.write(json.dumps(dict(event=event,t_ns=time.monotonic_ns(),pid=os.getpid(),**kw),sort_keys=True)+'\n'); self.f.flush()
def send(s, p, m, log):
    b=encode(m); s.sendall(b); log('send',path=p,msg=m,wire_bytes=len(b),sha=sha(b))
def received(p,m,log):
    b=encode(m); log('recv',path=p,msg=m,wire_bytes=len(b),sha=sha(b))
def close(s,p,log,reason):
    try: s.shutdown(socket.SHUT_RDWR)
    except OSError: pass
    s.close(); log('close',path=p,reason=reason)
def payload(kind, rid, data, **kw):
    return dict(kind=kind,rid=rid,data=base64.b64encode(data).decode(),payload_sha=sha(data),**kw)
TOOL=b'{"id":"tool-1","result":{"temperature_c":23,"unit":"C"}}'
def server(folder, fault):
    limits(); log=Log(folder/'server.jsonl'); listeners={}; conns={}; buffers={}; cancelled=False
    for p in ('A','B'):
        s=socket.socket(); s.bind(('127.0.0.1',0)); s.listen(1); listeners[s]=p
    ports={p:s.getsockname()[1] for s,p in listeners.items()}
    log('listen',ports=ports); print(json.dumps(ports),flush=True)
    try:
        while listeners or conns:
            ready,_,_=select.select(list(listeners)+list(conns),[],[],5)
            if not ready: log('timeout'); break
            for s in ready:
                if s in listeners:
                    c,addr=s.accept(); c.settimeout(5); conns[c]=listeners[s]; buffers[c]=b''
                    log('accept',path=conns[c],peer=list(addr)); continue
                if s not in conns: continue
                p=conns[s]; b=s.recv(65536)
                if not b:
                    log('eof',path=p); close(s,p,log,'peer_eof'); del conns[s]
                    if not conns:
                        return
                    continue
                buffers[s]+=b; assert len(buffers[s])<1024*1024
                while b'\n' in buffers[s]:
                    line,buffers[s]=buffers[s].split(b'\n',1); m=json.loads(line); received(p,m,log)
                    if m['op']=='audio' and m['start']==4 and p=='A' and fault!='none':
                        log('fault',scope=fault)
                        victims=list(conns) if fault=='endpoint' else [s]
                        for v in victims: close(v,conns[v],log,'injected_'+fault); del conns[v]
                        if fault=='endpoint': return
                        break
                    if m['op']=='audio':
                        if cancelled: send(s,p,dict(kind='cancelled',rid=m['rid'],cancel_id='cancel-1'),log)
                        else:
                            for seq in (m['start']+1,m['start']):
                                send(s,p,payload('audio',m['rid'],pcm()[seq*640:(seq+1)*640],seq=seq),log)
                    elif m['op']=='cancel':
                        cancelled=True; log('cancel_apply',path=p,cancel_id=m['cancel_id'])
                        send(s,p,dict(kind='cancel_ack',rid=m['rid'],cancel_id=m['cancel_id']),log)
                    elif m['op']=='tool': send(s,p,payload('tool',m['rid'],TOOL),log)
    finally:
        for s,p in list(conns.items()): close(s,p,log,'cleanup')
        for s,p in listeners.items(): close(s,p,log,'listener_cleanup')
        log('exit',**usage())

def trial(folder,mode,fault):
    folder.mkdir(); log=Log(folder/'client.jsonl'); start=time.monotonic_ns()
    proc=subprocess.Popen([sys.executable,str(ROOT/'run.py'),'--server',str(folder),'--fault',fault],stdout=subprocess.PIPE,stderr=open(folder/'server.stderr','x'),text=True)
    socks={}; buffers={}; completed=False; error=None; ports={}; seen=set(); pending={}; nextseq=0
    try:
        if not select.select([proc.stdout],[],[],5)[0]: raise TimeoutError('server startup')
        ports=json.loads(proc.stdout.readline())
        for p,port in ports.items():
            s=socket.create_connection(('127.0.0.1',port),5); socks[p]=s; buffers[p]=b''; log('connect',path=p,port=port)
        def exchange(m,count):
            active=list(socks) if mode=='replicate' else [next(iter(socks))] if socks else []
            if not active: raise ConnectionError('no_live_path')
            waits={}; replies=[]
            for p in active: send(socks[p],p,m,log); waits[p]=count
            while waits:
                ready,_,_=select.select([socks[p] for p in waits],[],[],5)
                if not ready: raise TimeoutError('response')
                for s in ready:
                    p=next(p for p,v in socks.items() if v is s); b=s.recv(65536)
                    if not b:
                        log('eof',path=p); close(s,p,log,'peer_eof'); del socks[p]; del waits[p]
                        if mode=='switch' and not replies and socks:
                            q=next(iter(socks)); log('retry',path=q,rid=m['rid']); send(socks[q],q,m,log); waits[q]=count
                        continue
                    buffers[p]+=b; assert len(buffers[p])<1024*1024
                    while b'\n' in buffers[p]:
                        line,buffers[p]=buffers[p].split(b'\n',1); r=json.loads(line); received(p,r,log)
                        assert r['rid']==m['rid']; replies.append(r); waits[p]-=1
                        if waits[p]==0: del waits[p]
            if not replies: raise ConnectionError('no_response')
            return replies
        for seq in range(0,8,2):
            for r in exchange(dict(op='audio',start=seq,rid=f'a{seq}'),2):
                data=base64.b64decode(r['data']); assert sha(data)==r['payload_sha']; k=r['seq']
                if k in seen: log('duplicate',seq=k,bytes=len(data)); continue
                seen.add(k)
                if k!=nextseq: log('out_of_order',seq=k,expected=nextseq)
                pending[k]=data
                while nextseq in pending:
                    d=pending.pop(nextseq); samples=struct.unpack('<320h',d)
                    log('consume',seq=nextseq,bytes=len(d),sha=sha(d),square_sum=sum(x*x for x in samples)); nextseq+=1
        log('interrupt',cancel_id='cancel-1')
        rs=exchange(dict(op='cancel',rid='cancel',cancel_id='cancel-1'),1)
        assert all(r['kind']=='cancel_ack' for r in rs); log('cancel_confirmed')
        assert all(r['kind']=='cancelled' for r in exchange(dict(op='audio',start=8,rid='probe'),1))
        rs=exchange(dict(op='tool',rid='tool'),1)
        assert all(base64.b64decode(r['data'])==TOOL for r in rs)
        log('tool_apply',sha=sha(TOOL),copies=len(rs)); completed=True; log('complete')
    except Exception as e:
        error=f'{type(e).__name__}: {e}'; log('failure',error=error)
    finally:
        for p,s in socks.items(): close(s,p,log,'cleanup')
        try: rc=proc.wait(timeout=3)
        except subprocess.TimeoutExpired: proc.kill(); rc=proc.wait(); log('forced_kill')
    cleanup={}
    for p,port in ports.items():
        s=socket.socket(); s.settimeout(.5); cleanup[p]=s.connect_ex(('127.0.0.1',port)); s.close()
    result=dict(mode=mode,fault=fault,completed=completed,error=error,elapsed_ms=(time.monotonic_ns()-start)/1e6,server_pid=proc.pid,client_pid=os.getpid(),server_exit=rc,ports=ports,cleanup_connect_errno=cleanup,**usage())
    (folder/'result.json').write_text(json.dumps(result,indent=2)); return result

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--output'); ap.add_argument('--smoke',action='store_true'); ap.add_argument('--server'); ap.add_argument('--fault'); a=ap.parse_args()
    if a.server: server(pathlib.Path(a.server),a.fault); return
    limits(); out=ROOT/a.output; out.mkdir(exist_ok=False)
    fixture=pcm(); (out/'fixture.pcm').write_bytes(fixture)
    manifest={p.name:sha(p.read_bytes()) for p in ROOT.iterdir() if p.suffix=='.py' or p.name=='PROTOCOL.md'}
    env=dict(python=sys.version,executable=sys.executable,platform=platform.platform(),machine=platform.machine(),fixture_sha=sha(fixture),source_hashes=manifest,repeats=1 if a.smoke else 5,threads_per_process=1,rss_checked_limit_bytes=768*1024**2,hard_address_space_limit=False,network='127.0.0.1 TCP',started=time.strftime('%Y-%m-%dT%H:%M:%S%z'))
    (out/'environment.json').write_text(json.dumps(env,indent=2))
    records=[]
    for rep in range(env['repeats']):
        conditions=[(m,f) for m in ('replicate','switch') for f in ('none','primary','endpoint')]; random.Random(1206+rep).shuffle(conditions)
        for mode,fault in conditions:
            name=f'{rep:02d}-{mode}-{fault}'; result=trial(out/name,mode,fault); records.append(dict(name=name,**result)); print(name,result['completed'],result['error'],flush=True)
    (out/'index.json').write_text(json.dumps(records,indent=2))
if __name__=='__main__': main()
