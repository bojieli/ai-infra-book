"""Measure actual local Fish Speech response bytes, without touching the service."""
import hashlib,http.client,json,struct,time
from pathlib import Path
BASE=Path(__file__).absolute().parent
TEXT=('The experiment is ready. We will measure when the first audio samples arrive. '
      'The next sentence follows the same path. Please keep the connection open until the message ends. '
      'All measurements will be saved so that the result can be checked again.')

def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def health():
    c=http.client.HTTPConnection('127.0.0.1',8123,timeout=30);c.request('GET','/health');r=c.getresponse();assert r.status==200
    d=json.loads(r.read());c.close()
    # Retain deployment identity, not unrelated enrolled voice names or files.
    return {k:d[k] for k in ['status','checkpoint_revision','device','compile_graphs','service_sha256','runtime_executable','runtime_modules']}

def one(out,stream,cancel):
    request=dict(text=TEXT,streaming=stream,chunk_length=80,max_new_tokens=512,top_p=.7,repetition_penalty=1.2,temperature=.7)
    save(out/'request.json',request)
    c=http.client.HTTPConnection('127.0.0.1',8123,timeout=120)
    start=time.perf_counter_ns();wall=time.time_ns();c.request('POST','/v1/tts',json.dumps(request),{'Content-Type':'application/json'})
    r=c.getresponse();headers=time.perf_counter_ns();assert r.status==200
    chunks=[];body=bytearray();cancel_event=None
    with (out/'reads.jsonl').open('w') as f:
        while True:
            data=r.read1(4096);now=time.perf_counter_ns()
            event=dict(index=len(chunks),elapsed_ns=now-start,bytes=len(data),offset=len(body))
            f.write(json.dumps(event)+'\n');f.flush();chunks.append(event);body.extend(data)
            if not data:break
            if cancel and len(body)>=44+1764:
                before=time.perf_counter_ns();r.close();c.close();after=time.perf_counter_ns()
                cancel_event=dict(requested_ns=before-start,client_close_return_ns=after-start,server_ack_ns=None,gpu_stop_ns=None)
                break
    c.close();end=time.perf_counter_ns()
    assert body[:4]==b'RIFF' and body[8:12]==b'WAVE' and body[12:16]==b'fmt ' and body[36:40]==b'data'
    fmt=struct.unpack('<HHIIHH',body[20:36]);assert fmt==(1,1,44100,88200,2,16),fmt
    (out/'response.wav').write_bytes(body)
    save(out/'execution.json',dict(status=r.status,headers=dict(r.getheaders()),start_unix_ns=wall,headers_elapsed_ns=headers-start,end_elapsed_ns=end-start,
        response_bytes=len(body),response_sha256=hashlib.sha256(body).hexdigest(),stream=stream,intentional_cancel=cancel,cancel_event=cancel_event,
        body_complete=not cancel and chunks[-1]['bytes']==0,format=dict(encoding='PCM signed 16-bit little endian',channels=1,sample_rate=44100),
        receiver='HTTPResponse.read1(4096); timestamps are client read completion, not packet/model chunk timestamps'))
    print(out.name,len(body),'cancel' if cancel else 'complete',flush=True)

def main():
    out=BASE/'runs';out.mkdir(exist_ok=False)
    h=health();assert h['service_sha256']=='sha256:'+hashlib.sha256((BASE/'sources/server.py').read_bytes()).hexdigest()
    save(out/'deployment-before.json',h)
    save(out/'driver.json',dict(sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),text=TEXT))
    for i,stream in enumerate([True,False,False,True]):
        d=out/f'{i}-stream-{str(stream).lower()}';d.mkdir();one(d,stream,False)
    d=out/'4-intentional-cancel';d.mkdir();one(d,True,True)
    save(out/'deployment-after.json',health())
if __name__=='__main__':main()
