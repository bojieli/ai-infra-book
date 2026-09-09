import argparse,asyncio,datetime,gzip,hashlib,importlib.metadata,ipaddress,json,platform,random,ssl,time
from pathlib import Path
import io
from PIL import Image
from aioquic.asyncio import connect,serve,QuicConnectionProtocol
from aioquic.h3.connection import H3Connection,H3_ALPN
from aioquic.h3.events import HeadersReceived,DataReceived
from aioquic.quic.configuration import QuicConfiguration
from aioquic.quic.events import HandshakeCompleted,ConnectionTerminated
from aioquic.quic.logger import QuicLogger
from cryptography import x509
from cryptography.hazmat.primitives import hashes,serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.x509.oid import NameOID
R=Path(__file__).resolve().parent
PAYLOAD=(R/'sources/payload.png').read_bytes();HASH=hashlib.sha256(PAYLOAD).hexdigest()
NOW=time.perf_counter

def certificate(out):
 key=ec.generate_private_key(ec.SECP256R1());name=x509.Name([x509.NameAttribute(NameOID.COMMON_NAME,'localhost')]);now=datetime.datetime.now(datetime.timezone.utc)
 cert=(x509.CertificateBuilder().subject_name(name).issuer_name(name).public_key(key.public_key()).serial_number(x509.random_serial_number()).not_valid_before(now-datetime.timedelta(minutes=5)).not_valid_after(now+datetime.timedelta(days=2)).add_extension(x509.SubjectAlternativeName([x509.DNSName('localhost'),x509.IPAddress(ipaddress.ip_address('127.0.0.1'))]),critical=False).add_extension(x509.BasicConstraints(ca=True,path_length=None),critical=True).sign(key,hashes.SHA256()))
 (out/'certificate.pem').write_bytes(cert.public_bytes(serialization.Encoding.PEM));(out/'fixture-private-key.pem').write_bytes(key.private_bytes(serialization.Encoding.PEM,serialization.PrivateFormat.PKCS8,serialization.NoEncryption()))
 return cert.fingerprint(hashes.SHA256()).hex()

class H3(QuicConnectionProtocol):
 def __init__(self,*args,server=False,log=None,**kwargs):
  super().__init__(*args,**kwargs);self.http=H3Connection(self._quic);self.server=server;self.states={};self.handshake=None;self.log=log
 def quic_event_received(self,event):
  if isinstance(event,HandshakeCompleted):self.handshake=dict(at=NOW(),alpn=event.alpn_protocol,session_resumed=event.session_resumed,early_data_accepted=event.early_data_accepted)
  if isinstance(event,ConnectionTerminated):
   for state in self.states.values():
    if 'future' in state and not state['future'].done():state['future'].set_exception(RuntimeError(str(event)))
  for e in self.http.handle_event(event):
   if not isinstance(e,(HeadersReceived,DataReceived)):continue
   state=self.states.setdefault(e.stream_id,dict(body=bytearray(),headers=None,first_headers=None,first_data=None,receive_start=NOW()))
   if isinstance(e,HeadersReceived):state['headers']=[(k.decode(),v.decode()) for k,v in e.headers];state['first_headers']=NOW()
   else:
    if e.data and state['first_data'] is None:state['first_data']=NOW()
    state['body'].extend(e.data)
   if not e.stream_ended:continue
   if self.server:
    data=bytes(state['body']);record=dict(odcid=self._quic.original_destination_connection_id.hex(),stream=e.stream_id,receive_start=state['receive_start'],receive_end=NOW(),bytes=len(data),sha256=hashlib.sha256(data).hexdigest());self.log.append(record)
    self.http.send_headers(e.stream_id,[(b':status',b'200'),(b'content-length',str(len(data)).encode()),(b'content-type',b'application/octet-stream')]);self.http.send_data(e.stream_id,data,end_stream=True);self.transmit();del self.states[e.stream_id]
   else:
    state['end']=NOW();state['future'].set_result(state)
 async def request(self):
  stream=self._quic.get_next_available_stream_id();future=asyncio.get_running_loop().create_future();self.states[stream]=dict(future=future,body=bytearray(),headers=None,first_headers=None,first_data=None)
  send=NOW();self.http.send_headers(stream,[(b':method',b'POST'),(b':scheme',b'https'),(b':authority',b'localhost'),(b':path',b'/echo'),(b'content-length',str(len(PAYLOAD)).encode())]);self.http.send_data(stream,PAYLOAD,end_stream=True);self.transmit()
  result=await asyncio.wait_for(future,20);result=dict(result);del result['future'];del self.states[stream];return send,stream,result

def pixels(data):
 with Image.open(io.BytesIO(data)) as image:
  image.load();rgba=image.convert('RGBA');return dict(format=image.format,size=list(image.size),rgba_sha256=hashlib.sha256(rgba.tobytes()).hexdigest())

async def main(out,smoke):
 out.mkdir(exist_ok=False);fingerprint=certificate(out);expected=pixels(PAYLOAD);server_rows=[];connections=[];records=[];groups=[];next_id=0
 qc=QuicConfiguration(is_client=False,alpn_protocols=H3_ALPN);qc.load_cert_chain(out/'certificate.pem',out/'fixture-private-key.pem')
 server=await serve('127.0.0.1',0,configuration=qc,create_protocol=lambda *a,**k:H3(*a,server=True,log=server_rows,**k));port=server._transport.get_extra_info('sockname')[1]
 env=dict(python=platform.python_version(),platform=platform.platform(),machine=platform.machine(),packages={p:importlib.metadata.version(p) for p in ['aioquic','cryptography','pylsqpack','Pillow']},certificate_sha256=fingerprint,source_sha256=hashlib.sha256((R/'run.py').read_bytes()).hexdigest(),port=port,payload_bytes=len(PAYLOAD),payload_sha256=HASH,pixels=expected,smoke=smoke,server_and_client_same_event_loop=True)
 (out/'environment.json').write_text(json.dumps(env,indent=2))
 async def opening():
  nonlocal next_id
  ident=next_id;next_id+=1;begin=NOW();qlog=QuicLogger();config=QuicConfiguration(is_client=True,alpn_protocols=H3_ALPN,server_name='localhost',verify_mode=ssl.CERT_REQUIRED,cafile=str(out/'certificate.pem'),quic_logger=qlog)
  ctx=connect('127.0.0.1',port,configuration=config,create_protocol=H3,wait_connected=True);protocol=await asyncio.wait_for(ctx.__aenter__(),20)
  record=dict(id=ident,start=begin,ready=NOW(),**protocol.handshake,odcid=protocol._quic.original_destination_connection_id.hex(),certificate_sha256=protocol._quic.tls._peer_certificate.fingerprint(hashes.SHA256()).hex(),local=protocol._transport.get_extra_info('sockname'))
  connections.append(record);return dict(record=record,ctx=ctx,protocol=protocol,qlog=qlog)
 async def closing(conn):
  await conn['ctx'].__aexit__(None,None,None)
  with gzip.open(out/f"qlog-{conn['record']['id']}.json.gz",'wt') as f:json.dump(conn['qlog'].to_dict(),f)
  conn['record']['closed']=NOW()
 async def one(conn,trial,topology,warm,index,prewarm=False):
  rec=dict(trial=trial,topology=topology,warm=warm,index=index,prewarm=prewarm,connection=conn['record']['id'],odcid=conn['record']['odcid'],start=NOW())
  try:
   send,stream,result=await conn['protocol'].request();data=bytes(result.pop('body'));decode_start=NOW();decoded=pixels(data);decode_end=NOW()
   rec.update(send=send,stream=stream,**result,bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),decoded=decoded,decode_start=decode_start,decode_end=decode_end,valid=(data==PAYLOAD and decoded==expected and dict(result['headers']).get(':status')=='200'),error=None,validation_end=NOW())
   if not rec['valid']:(out/f"failed-response-{conn['record']['id']}-{stream}.bin").write_bytes(data)
  except Exception as e:rec.update(error=repr(e),valid=False,validation_end=NOW())
  records.append(rec)
  with (out/'requests.jsonl').open('a') as f:f.write(json.dumps(rec)+'\n')
  return rec
 order=[]
 for trial in range(1 if smoke else 3):
  conditions=[(topology,warm) for topology in ['one_serial','one_parallel','four_parallel'] for warm in [False,True]];random.Random(1205+trial).shuffle(conditions);order.extend(dict(trial=trial,topology=t,warm=w) for t,w in conditions)
 (out/'order.json').write_text(json.dumps(order,indent=2))
 try:
  for c in order:
   topology=c['topology'];warm=c['warm'];trial=c['trial'];setup=NOW();pool=await asyncio.gather(*(opening() for _ in range(4 if topology=='four_parallel' else 1)));ready=NOW()
   if warm:await asyncio.gather(*(one(conn,trial,topology,warm,-1,True) for conn in pool))
   begin=NOW() if warm else setup;dispatch=NOW()
   if topology=='one_serial':rr=[await one(pool[0],trial,topology,warm,i) for i in range(8)]
   else:rr=await asyncio.gather(*(one(pool[i%len(pool)],trial,topology,warm,i) for i in range(8)))
   complete=NOW();await asyncio.gather(*(closing(conn) for conn in pool))
   groups.append(dict(**c,setup_start=setup,connections_ready=ready,start=begin,dispatch_start=dispatch,complete=complete,cleanup_complete=NOW(),connections=[conn['record']['id'] for conn in pool],requests=len(rr),errors=sum(not r['valid'] for r in rr)))
   print(c,'valid',sum(r['valid'] for r in rr),'group_ms',(complete-begin)*1000,flush=True)
 finally:
  server.close();await asyncio.sleep(.05)
  for name,data in [('connections',connections),('groups',groups),('server',server_rows)]: (out/(name+'.json')).write_text(json.dumps(data,indent=2))
  (out/'completion.json').write_text(json.dumps(dict(done=True,requests=len(records),failures=sum(not r['valid'] for r in records),listener_closed=True)))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--smoke',action='store_true');args=p.parse_args();asyncio.run(main(args.output,args.smoke))
