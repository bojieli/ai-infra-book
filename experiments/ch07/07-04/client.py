"""Fixed payload RPC comparison over a pre-established local SSH forwarding port."""
import argparse,base64,hashlib,json,platform,random,socket,struct,time
from pathlib import Path
HEADER=struct.Struct('!4sBQI')
NAMES=['json_copy_worker','binary_copy_worker','binary_view_worker','binary_view_inline']

def receive(sock,n):
    data=bytearray(n);view=memoryview(data);at=0
    while at<n:
        count=sock.recv_into(view[at:])
        if not count:raise EOFError
        at+=count
    return data

def vector_send(sock,parts):
    calls=0;parts=[memoryview(p) for p in parts]
    while parts:
        n=sock.sendmsg(parts);calls+=1
        if not n:raise EOFError
        while parts and n>=len(parts[0]):n-=len(parts.pop(0))
        if parts and n:parts[0]=parts[0][n:]
    return calls

def main(args):
    if args.output.exists():raise RuntimeError('Use a fresh client output')
    args.output.mkdir(parents=True)
    rng=random.Random(704);fixtures={}
    for size in [1024,65536,1048576]:
        for trial in range(-2,20):fixtures[size,trial]=rng.randbytes(size)
    plan=[]
    for trial in range(-2,20):
        items=[(size,mode,trial) for size in [1024,65536,1048576] for mode in range(4)];rng.shuffle(items);plan.extend(items)
    env=dict(python=platform.python_version(),platform=platform.platform(),source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        fixture_seed=704,plan=plan,names=NAMES,transport='Mac -> SSH forwarding (Compression=no) -> RTX Linux loopback TCP server; one persistent connection, one in-flight RPC',
        clock='monotonic_ns and process_time_ns; server clock unsynchronized; never subtract across hosts')
    (args.output/'environment.json').write_text(json.dumps(env,indent=2)+'\n')
    with socket.create_connection(('127.0.0.1',args.port),timeout=30) as sock,(args.output/'requests.jsonl').open('w',buffering=1) as log:
        sock.setsockopt(socket.IPPROTO_TCP,socket.TCP_NODELAY,1)
        for rid,(size,mode,trial) in enumerate(plan):
            payload=fixtures[size,trial];expected=hashlib.sha256(payload).hexdigest()
            cpu=time.process_time_ns();start=time.monotonic_ns()
            body=json.dumps(dict(payload=base64.b64encode(payload).decode()),separators=(',',':')).encode() if mode==0 else payload
            encode_end=time.monotonic_ns()
            header=HEADER.pack(b'RPC4',mode,rid,len(body))
            wire=header+body if mode<2 else None
            prepare_end=time.monotonic_ns()
            if wire is not None:sock.sendall(wire);send_calls=None
            else:send_calls=vector_send(sock,[header,body])
            send_end=time.monotonic_ns()
            reply=receive(sock,struct.unpack('!I',receive(sock,4))[0]);receive_end=time.monotonic_ns()
            result=json.loads(reply);assert result['sha256']==expected and result['id']==rid and result['payload_bytes']==size
            end=time.monotonic_ns();cpu_ns=time.process_time_ns()-cpu
            log.write(json.dumps(dict(id=rid,size=size,mode=mode,name=NAMES[mode],trial=trial,warmup=trial<0,payload_sha256=expected,
                start_ns=start,encode_end_ns=encode_end,prepare_end_ns=prepare_end,send_end_ns=send_end,receive_end_ns=receive_end,end_ns=end,
                client_cpu_ns=cpu_ns,request_application_bytes=HEADER.size+len(body),reply_application_bytes=4+len(reply),sendmsg_calls=send_calls,server=result))+'\n')
    print('completed',len(plan),'RPCs',flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--port',type=int,required=True);p.add_argument('--output',type=Path,required=True)
    main(p.parse_args())
