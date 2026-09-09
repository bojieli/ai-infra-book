"""Validate captured PCM/read timings; no inferred DAC playback or GPU cancel."""
import argparse,array,hashlib,json,struct,sys,wave
from pathlib import Path
BASE=Path(__file__).absolute().parent

def analyze():
    results=[];reference=None
    before=json.loads((BASE/'runs/deployment-before.json').read_text());after=json.loads((BASE/'runs/deployment-after.json').read_text());assert before==after
    assert before['service_sha256']=='sha256:'+hashlib.sha256((BASE/'sources/server.py').read_bytes()).hexdigest()
    for d in sorted((BASE/'runs').glob('[0-4]-*')):
        e=json.loads((d/'execution.json').read_text());q=json.loads((d/'request.json').read_text())
        same=dict(q);same.pop('streaming')
        if reference is None:reference=same
        assert same==reference and q['streaming']==e['stream']
        body=(d/'response.wav').read_bytes();reads=[json.loads(s) for s in (d/'reads.jsonl').read_text().splitlines()]
        assert hashlib.sha256(body).hexdigest()==e['response_sha256'] and len(body)==e['response_bytes']
        assert body[:4]==b'RIFF' and body[8:12]==b'WAVE' and body[36:40]==b'data'
        assert struct.unpack('<HHIIHH',body[20:36])==(1,1,44100,88200,2,16)
        pcm=body[44:];assert len(pcm)%2==0
        offset=0;last=0
        for i,r in enumerate(reads):
            assert r['index']==i and r['offset']==offset and last<=r['elapsed_ns']<=e['end_elapsed_ns']
            offset+=r['bytes'];last=r['elapsed_ns']
        assert offset==len(body)
        assert (reads[-1]['bytes']==0)==e['body_complete']
        if not e['stream']:
            assert struct.unpack('<I',body[4:8])[0]==len(body)-8 and struct.unpack('<I',body[40:44])[0]==len(pcm)
        else:assert body[4:8]==body[40:44]==b'\xff'*4
        arrival=[];j=0
        for frame in range(len(pcm)//1764):
            threshold=44+(frame+1)*1764
            while reads[j]['offset']+reads[j]['bytes']<threshold:j+=1
            arrival.append(dict(frame=frame,end_pcm_byte=(frame+1)*1764,available_ns=reads[j]['elapsed_ns'],read_index=j))
        samples=array.array('h',pcm)
        if sys.byteorder!='little':samples.byteswap()
        first_sample=next(r['elapsed_ns'] for r in reads if r['offset']+r['bytes']>=46)
        cancel=e['cancel_event']
        if cancel:
            assert e['intentional_cancel'] and not e['body_complete'] and cancel['requested_ns']<=cancel['client_close_return_ns']<=e['end_elapsed_ns']
            assert cancel['server_ack_ns'] is None and cancel['gpu_stop_ns'] is None
        results.append(dict(name=d.name,stream=e['stream'],intentional_cancel=e['intentional_cancel'],complete=e['body_complete'],
            pcm_bytes=len(pcm),pcm_sha256=hashlib.sha256(pcm).hexdigest(),audio_duration_s=len(pcm)/88200,
            nonzero_samples=sum(v!=0 for v in samples),peak_abs_sample=max(abs(v) for v in samples),
            headers_ms=e['headers_elapsed_ns']/1e6,first_sample_ms=first_sample/1e6,first_20ms_frame_ms=arrival[0]['available_ns']/1e6,
            end_ms=e['end_elapsed_ns']/1e6,frames=arrival,cancel_event=cancel,
            dac_first_play_ms=None,audible_stalls=None,backend_cancel_ms=None,transcription_quality=None))
    assert len(results)==5 and sum(r['complete'] for r in results)==4 and sum(r['intentional_cancel'] for r in results)==1
    assert len({r['pcm_sha256'] for r in results[:4]})==4
    return dict(service=before,request_except_streaming=reference,results=results,
        boundary='Read-completion availability of complete 20 ms PCM frames; no DAC or audio content acceptance, no Queqiao tunnel, no server cancellation acknowledgement.')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,default=BASE/'analysis.json');a=p.parse_args()
    a.out.write_text(json.dumps(analyze(),ensure_ascii=False,indent=2)+'\n')
