"""Loopback-only RPC endpoint for an explicitly established SSH tunnel."""
import argparse,base64,hashlib,json,platform,queue,socket,struct,threading,time
from pathlib import Path
HEADER=struct.Struct('!4sBQI')

def receive(sock,n):
    data=bytearray(n);view=memoryview(data);at=0
    while at<n:
        count=sock.recv_into(view[at:])
        if not count:raise EOFError
        at+=count
    return data

def main(args):
    if args.output.exists():raise RuntimeError('Use fresh server output')
    args.output.mkdir(parents=True)
    (args.output/'environment.json').write_text(json.dumps(dict(python=platform.python_version(),platform=platform.platform(),source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),clock='monotonic_ns and thread_time_ns; not synchronized to client'),indent=2)+'\n')
    work=queue.Queue()
    def worker():
        while True:
            item=work.get()
            if item is None:return
            data,done,result=item
            result['worker_start_ns']=time.monotonic_ns();cpu=time.thread_time_ns()
            result['sha256']=hashlib.sha256(data).hexdigest()
            result['worker_cpu_ns']=time.thread_time_ns()-cpu
            result['worker_end_ns']=time.monotonic_ns();done.set()
    thread=threading.Thread(target=worker);thread.start()
    try:
        with socket.socket() as listener,(args.output/'requests.jsonl').open('w',buffering=1) as log:
            listener.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
            listener.bind(('127.0.0.1',args.port));listener.listen(1)
            print('ready',flush=True)
            conn,_=listener.accept()
            with conn:
                conn.settimeout(30);conn.setsockopt(socket.IPPROTO_TCP,socket.TCP_NODELAY,1)
                while True:
                    try:header=receive(conn,HEADER.size)
                    except EOFError:break
                    magic,mode,rid,n=HEADER.unpack(header)
                    assert magic==b'RPC4' and mode in range(4) and n<=2*1024**2
                    recv_start=time.monotonic_ns();body=receive(conn,n);recv_end=time.monotonic_ns()
                    cpu=time.thread_time_ns();decode_start=time.monotonic_ns()
                    if mode==0:data=base64.b64decode(json.loads(body)['payload'],validate=True)
                    elif mode==1:data=bytes(body)
                    else:data=memoryview(body)
                    decode_end=time.monotonic_ns();decode_cpu=time.thread_time_ns()-cpu
                    result=dict(id=rid,mode=mode,body_bytes=n,payload_bytes=len(data),recv_start_ns=recv_start,recv_end_ns=recv_end,
                        decode_start_ns=decode_start,decode_end_ns=decode_end,decode_cpu_ns=decode_cpu)
                    if mode<3:
                        done=threading.Event();result['submit_ns']=time.monotonic_ns()
                        work.put((data,done,result));assert done.wait(20)
                        result['complete_observed_ns']=time.monotonic_ns()
                    else:
                        result['submit_ns']=time.monotonic_ns();result['worker_start_ns']=time.monotonic_ns();cpu=time.thread_time_ns()
                        result['sha256']=hashlib.sha256(data).hexdigest()
                        result['worker_cpu_ns']=time.thread_time_ns()-cpu
                        result['worker_end_ns']=time.monotonic_ns();result['complete_observed_ns']=time.monotonic_ns()
                    encoded=json.dumps(result,separators=(',',':')).encode()
                    conn.sendall(struct.pack('!I',len(encoded))+encoded)
                    log.write(json.dumps(result)+'\n')
    finally:work.put(None);thread.join()

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--port',type=int,required=True);p.add_argument('--output',type=Path,required=True)
    main(p.parse_args())
