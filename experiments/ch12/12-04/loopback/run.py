import argparse,asyncio,datetime,gzip,hashlib,importlib.metadata,ipaddress,json,platform,random,ssl,time
from pathlib import Path
import h11
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
PAYLOAD=bytes(random.Random(1204).randbytes(65536));HASH=hashlib.sha256(PAYLOAD).hexdigest()
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
   state=self.states.setdefault(e.stream_id,dict(body=bytearray(),headers=None,first_headers=None,first_data=None))
   if isinstance(e,HeadersReceived):state['headers']=[(k.decode(),v.decode()) for k,v in e.headers];state['first_headers']=NOW()
   else:
    if e.data and state['first_data'] is None:state['first_data']=NOW()
    state['body'].extend(e.data)
   if not e.stream_ended:continue
   if self.server:
    data=bytes(state['body']);record=dict(stream=e.stream_id,at=NOW(),bytes=len(data),sha256=hashlib.sha256(data).hexdigest());self.log.append(record)
    self.http.send_headers(e.stream_id,[(b':status',b'200'),(b'content-length',str(len(data)).encode()),(b'content-type',b'application/octet-stream')]);self.http.send_data(e.stream_id,data,end_stream=True);self.transmit();del self.states[e.stream_id]
   else:
    state['end']=NOW();state['future'].set_result(state)
 async def request(self):
  stream=self._quic.get_next_available_stream_id();future=asyncio.get_running_loop().create_future();self.states[stream]=dict(future=future,body=bytearray(),headers=None,first_headers=None,first_data=None)
  send=NOW();self.http.send_headers(stream,[(b':method',b'POST'),(b':scheme',b'https'),(b':authority',b'localhost'),(b':path',b'/echo'),(b'content-length',str(len(PAYLOAD)).encode())]);self.http.send_data(stream,PAYLOAD,end_stream=True);self.transmit()
  result=await asyncio.wait_for(future,20);result=dict(result);del result['future'];del self.states[stream];return send,stream,result

async def h1_event(conn,reader):
 while True:
  event=conn.next_event()
  if event is h11.NEED_DATA:
   data=await reader.read(65536);conn.receive_data(data)
  else:return event

async def main(out,smoke):
 out.mkdir(exist_ok=False);fingerprint=certificate(out);(out/'payload.bin').write_bytes(PAYLOAD)
 server_rows=[];server_errors=[];h1_writers=set();h3_server_rows=[]
 sc=ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER);sc.minimum_version=sc.maximum_version=ssl.TLSVersion.TLSv1_3;sc.set_alpn_protocols(['http/1.1']);sc.load_cert_chain(out/'certificate.pem',out/'fixture-private-key.pem')
 cc=ssl.create_default_context(cafile=str(out/'certificate.pem'));cc.minimum_version=cc.maximum_version=ssl.TLSVersion.TLSv1_3;cc.set_alpn_protocols(['http/1.1'])
 async def h1_server(reader,writer):
  h1_writers.add(writer);conn=h11.Connection(h11.SERVER)
  try:
   while True:
    body=bytearray();headers=None
    while True:
     event=await h1_event(conn,reader)
     if isinstance(event,h11.ConnectionClosed):return
     if isinstance(event,h11.Request):headers=[(k.decode(),v.decode()) for k,v in event.headers]
     elif isinstance(event,h11.Data):body.extend(event.data)
     elif isinstance(event,h11.EndOfMessage):break
    server_rows.append(dict(at=NOW(),bytes=len(body),sha256=hashlib.sha256(body).hexdigest(),headers=headers,peer=writer.get_extra_info('peername')))
    for event in [h11.Response(status_code=200,headers=[(b'content-length',str(len(body)).encode()),(b'content-type',b'application/octet-stream')]),h11.Data(data=body),h11.EndOfMessage()]:writer.write(conn.send(event))
    await writer.drain();conn.start_next_cycle()
  except Exception as e:server_errors.append(repr(e))
  finally:writer.close();await writer.wait_closed();h1_writers.discard(writer)
 tcp=await asyncio.start_server(h1_server,'127.0.0.1',0,ssl=sc);tcp_port=tcp.sockets[0].getsockname()[1]
 qc=QuicConfiguration(is_client=False,alpn_protocols=H3_ALPN);qc.load_cert_chain(out/'certificate.pem',out/'fixture-private-key.pem')
 udp=await serve('127.0.0.1',0,configuration=qc,create_protocol=lambda *a,**k:H3(*a,server=True,log=h3_server_rows,**k));udp_port=udp._transport.get_extra_info('sockname')[1]
 env=dict(python=platform.python_version(),platform=platform.platform(),machine=platform.machine(),openssl=ssl.OPENSSL_VERSION,packages={p:importlib.metadata.version(p) for p in ['aioquic','h11','cryptography','pylsqpack']},certificate_sha256=fingerprint,source_sha256=hashlib.sha256((R/'run.py').read_bytes()).hexdigest(),tcp_port=tcp_port,udp_port=udp_port,payload_bytes=len(PAYLOAD),payload_sha256=HASH,smoke=smoke,server_and_client_same_event_loop=True)
 (out/'environment.json').write_text(json.dumps(env,indent=2));connections=[];rows=[];groups=[];next_id=0
 async def open_conn(proto):
  nonlocal next_id
  ident=next_id;next_id+=1;begin=NOW()
  if proto=='h1':
   reader,writer=await asyncio.wait_for(asyncio.open_connection('127.0.0.1',tcp_port,ssl=cc,server_hostname='localhost'),20);obj=writer.get_extra_info('ssl_object');ready=NOW()
   record=dict(id=ident,protocol=proto,start=begin,ready=ready,alpn=obj.selected_alpn_protocol(),tls=obj.version(),cipher=obj.cipher(),session_resumed=obj.session_reused,certificate_sha256=hashlib.sha256(obj.getpeercert(binary_form=True)).hexdigest(),local=writer.get_extra_info('sockname'))
   conn=dict(record=record,reader=reader,writer=writer,h11=h11.Connection(h11.CLIENT))
  else:
   qlog=QuicLogger();config=QuicConfiguration(is_client=True,alpn_protocols=H3_ALPN,server_name='localhost',verify_mode=ssl.CERT_REQUIRED,cafile=str(out/'certificate.pem'),quic_logger=qlog)
   ctx=connect('127.0.0.1',udp_port,configuration=config,create_protocol=H3,wait_connected=True);protocol=await asyncio.wait_for(ctx.__aenter__(),20);ready=NOW();record=dict(id=ident,protocol=proto,start=begin,ready=ready,**protocol.handshake,local=protocol._transport.get_extra_info('sockname'))
   conn=dict(record=record,ctx=ctx,protocol=protocol,qlog=qlog)
  connections.append(record);return conn
 async def close_conn(conn):
  if conn['record']['protocol']=='h1':conn['writer'].close();await conn['writer'].wait_closed()
  else:
   await conn['ctx'].__aexit__(None,None,None)
   with gzip.open(out/f"qlog-{conn['record']['id']}.json.gz",'wt') as f:json.dump(conn['qlog'].to_dict(),f)
  conn['record']['closed']=NOW()
 async def request(conn):
  if conn['record']['protocol']=='h3':return await conn['protocol'].request()
  c=conn['h11'];send=NOW()
  for e in [h11.Request(method='POST',target='/echo',headers=[('Host','localhost'),('Content-Length',str(len(PAYLOAD)))]),h11.Data(data=PAYLOAD),h11.EndOfMessage()]:conn['writer'].write(c.send(e))
  await conn['writer'].drain();state=dict(body=bytearray(),first_headers=None,first_data=None,headers=None)
  while True:
   e=await asyncio.wait_for(h1_event(c,conn['reader']),20)
   if isinstance(e,h11.Response):state['first_headers']=NOW();state['headers']=[(':status',str(e.status_code))]+[(k.decode(),v.decode()) for k,v in e.headers]
   elif isinstance(e,h11.Data):
    if state['first_data'] is None:state['first_data']=NOW()
    state['body'].extend(e.data)
   elif isinstance(e,h11.EndOfMessage):state['end']=NOW();c.start_next_cycle();return send,None,state
   elif isinstance(e,h11.ConnectionClosed):raise RuntimeError('premature close')
 async def group(trial,proto,reuse,concurrency,count,warmup=False):
  begin=NOW();opened=[];gr=[]
  async def lane(lane_id):
   conn=None
   for index in range(lane_id,count,concurrency):
    rec=dict(trial=trial,protocol=proto,reuse=reuse,concurrency=concurrency,index=index,lane=lane_id,warmup=warmup,start=NOW())
    try:
     fresh=conn is None or not reuse
     if fresh:conn=await open_conn(proto);opened.append(conn)
     send,stream,result=await request(conn);data=bytes(result.pop('body'));rec.update(connection=conn['record']['id'],fresh=fresh,connection_ready=conn['record']['ready'] if fresh else rec['start'],send=send,stream=stream,**result,bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),valid=(data==PAYLOAD and dict(result['headers']).get(':status')=='200'),validation_end=NOW(),error=None)
    except Exception as e:rec.update(error=repr(e),valid=False,validation_end=NOW())
    gr.append(rec);rows.append(rec)
    with (out/'requests.jsonl').open('a') as f:f.write(json.dumps(rec)+'\n')
  await asyncio.gather(*(lane(i) for i in range(concurrency)));complete=NOW()
  await asyncio.gather(*(close_conn(c) for c in opened));groups.append(dict(trial=trial,protocol=proto,reuse=reuse,concurrency=concurrency,warmup=warmup,start=begin,requests_complete=complete,cleanup_complete=NOW(),requests=len(gr),errors=sum(not r['valid'] for r in gr)))
 try:
  for proto in ['h1','h3']:await group(-1,proto,False,1,1,True)
  order=[]
  for trial in range(1 if smoke else 3):
   conditions=[(proto,reuse,c) for proto in ['h1','h3'] for reuse in [False,True] for c in [1,4]];random.Random(1204+trial).shuffle(conditions)
   order.extend(dict(trial=trial,protocol=p,reuse=r,concurrency=c) for p,r,c in conditions)
  (out/'order.json').write_text(json.dumps(order,indent=2))
  for c in order:await group(c['trial'],c['protocol'],c['reuse'],c['concurrency'],4 if smoke else 8)
 finally:
  tcp.close();await tcp.wait_closed();udp.close()
  for writer in list(h1_writers):writer.close()
  await asyncio.sleep(.05)
  for name,data in [('connections',connections),('groups',groups),('h1-server',server_rows),('h3-server',h3_server_rows),('server-errors',server_errors)]: (out/(name+'.json')).write_text(json.dumps(data,indent=2))
  (out/'completion.json').write_text(json.dumps(dict(done=True,requests=len(rows),failures=sum(not r['valid'] for r in rows),listeners_closed=True)))
 print(json.dumps(dict(requests=len(rows),failures=sum(not r['valid'] for r in rows),server_errors=server_errors)))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--smoke',action='store_true');args=p.parse_args();asyncio.run(main(args.output,args.smoke))
