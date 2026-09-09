#!/usr/bin/env python3
"""Real pretrained vision CPU execution and separate TCP processes; no language model."""
import os
for k,v in {'CUDA_VISIBLE_DEVICES':'','OMP_NUM_THREADS':'4','MKL_NUM_THREADS':'4','OPENBLAS_NUM_THREADS':'4','HF_HUB_OFFLINE':'1','TRANSFORMERS_OFFLINE':'1','PYTHONDONTWRITEBYTECODE':'1'}.items(): os.environ[k]=v
import argparse,hashlib,inspect,io,json,pathlib,socket,struct,subprocess,sys,time,resource
ROOT=pathlib.Path(__file__).resolve().parent
SNAP=pathlib.Path('/home/ubuntu/.cache/huggingface/hub/models--Qwen--Qwen3-VL-8B-Instruct/snapshots/0c351dd01ed87e9c1b53cbc748cba10e6187ff3b')
OUT=ROOT/'results'; OUT.mkdir(exist_ok=True)
def sha(b): return hashlib.sha256(b).hexdigest()
def dump(p,x): p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def log(event,**kw): print(json.dumps(dict(event=event,pid=os.getpid(),monotonic_ns=time.perf_counter_ns(),**kw)),flush=True)
def tensor_info(t):
 b=t.contiguous().view(torch.uint8).numpy().tobytes()
 return dict(shape=list(t.shape),dtype=str(t.dtype),bytes=len(b),sha256=sha(b))
def init():
 global torch,st
 import torch
 import safetensors.torch as st
 torch.set_num_threads(4);torch.set_num_interop_threads(1)
 torch.use_deterministic_algorithms(True)
def load_model():
 from transformers import AutoProcessor,AutoConfig
 from transformers.models.qwen3_vl.modeling_qwen3_vl import Qwen3VLVisionModel
 cfg=AutoConfig.from_pretrained(SNAP,local_files_only=True).vision_config
 cfg._attn_implementation='eager'
 t=time.perf_counter()
 model=Qwen3VLVisionModel(cfg)  # CPU creates nonpersistent RoPE buffers normally; ALL parameters replaced below
 wm=json.loads((SNAP/'model.safetensors.index.json').read_text())['weight_map']
 selected={k:v for k,v in wm.items() if k.startswith('model.visual.')}
 assert set(k.removeprefix('model.visual.') for k in selected)==set(model.state_dict())
 state={}; manifest=[]
 from safetensors import safe_open
 for shard in sorted(set(selected.values())):
  with safe_open(SNAP/shard,framework='pt',device='cpu') as f:
   for k in sorted(k for k,v in selected.items() if v==shard):
    x=f.get_tensor(k); name=k.removeprefix('model.visual.')
    assert tuple(x.shape)==tuple(model.state_dict()[name].shape)
    state[name]=x; manifest.append(dict(key=k,shard=shard,**tensor_info(x)))
 result=model.load_state_dict(state,strict=True,assign=True)
 assert not result.missing_keys and not result.unexpected_keys
 for k,x in model.state_dict().items(): assert tensor_info(x)==tensor_info(state[k])
 assert not any(x.is_meta for x in list(model.parameters())+list(model.buffers()))
 model.eval();del state
 processor=AutoProcessor.from_pretrained(SNAP,local_files_only=True)
 dump(OUT/'weights-manifest.json',dict(snapshot=SNAP.name,keys=len(manifest),parameters=sum(x.numel() for x in model.parameters()),tensors=manifest,strict=True))
 log('model_ready',seconds=time.perf_counter()-t,dtype=str(model.dtype),device=str(model.device),maxrss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
 return model,processor

def encode(model,processor,data):
 from PIL import Image
 t=time.perf_counter(); im=Image.open(io.BytesIO(data));im.load();decode=time.perf_counter()-t
 t=time.perf_counter(); pixels=processor.image_processor(images=im,return_tensors='pt'); preprocess=time.perf_counter()-t
 t=time.perf_counter(); pv=pixels['pixel_values'].to(dtype=model.dtype); cast=time.perf_counter()-t
 t=time.perf_counter()
 with torch.inference_mode(): y=model(pv,grid_thw=pixels['image_grid_thw'],return_dict=True)
 encoder=time.perf_counter()-t
 assert len(y.deepstack_features)==3
 allout={'last_hidden_state':y.last_hidden_state.contiguous(),'pooler_output':y.pooler_output.contiguous(),**{f'deepstack_{i}':x.contiguous() for i,x in enumerate(y.deepstack_features)}}
 ec={k:v for k,v in allout.items() if k!='last_hidden_state'}
 ec['image_grid_thw']=pixels['image_grid_thw'].contiguous()
 return pixels,allout,ec,dict(png_decode_s=decode,processor_s=preprocess,input_cast_s=cast,encoder_s=encoder)

def prepare():
 init()
 import transformers, PIL, torchvision,safetensors
 from transformers.models.qwen3_vl import modeling_qwen3_vl as m
 sources=OUT/'sources';sources.mkdir(exist_ok=True)
 from transformers.models.qwen2_vl import image_processing_qwen2_vl as ip
 from transformers.models.qwen3_vl import processing_qwen3_vl as pr
 source_hash={}
 for module in [m,ip,pr]:
  p=pathlib.Path(inspect.getfile(module));b=p.read_bytes();(sources/p.name).write_bytes(b);source_hash[str(p)]=sha(b)
 for name in ['config.json','preprocessor_config.json','processor_config.json','model.safetensors.index.json']:
  if (SNAP/name).exists(): (sources/name).write_bytes((SNAP/name).read_bytes())
 shards=[dict(name=p.name,bytes=p.stat().st_size,blob=p.resolve().name) for p in sorted(SNAP.glob('*.safetensors'))]
 assert sum(x['bytes'] for x in shards)==17534339512
 dump(OUT/'environment.json',dict(snapshot=str(SNAP),shards=shards,python=sys.version,torch=torch.__version__,transformers=transformers.__version__,torchvision=torchvision.__version__,pillow=PIL.__version__,safetensors=safetensors.__version__,source_sha256=source_hash,cpu=pathlib.Path('/proc/cpuinfo').read_text(),threads=torch.get_num_threads(),affinity=sorted(os.sched_getaffinity(0)),device='cpu',attention='eager',torch_config=torch.__config__.show()))
 from PIL import Image,ImageDraw
 fix=ROOT/'fixtures';fix.mkdir(exist_ok=True)
 for name,w,h,version in [('a-v1',256,256,1),('a-v2',256,256,2),('b-v1',320,256,1)]:
  im=Image.new('RGB',(w,h)); pix=im.load()
  for y in range(h):
   for x in range(w): pix[x,y]=((x*7+y*3)%256,(x//16*23+y//16*19)%256,(x^y)%256)
  d=ImageDraw.Draw(im);d.rectangle((20,20,120,80),fill=(40,180,60) if version==1 else (220,35,70));d.text((25,30),f'frame {version}',fill='white')
  im.save(fix/f'{name}.png',compress_level=6)
 model,processor=load_model()
 dump(OUT/'processor-effective.json',processor.image_processor.to_dict())
 identity=dict(snapshot=SNAP.name,config_sha256=sha((SNAP/'config.json').read_bytes()),processor=processor.image_processor.to_dict(),source_sha256=source_hash,dtype='torch.bfloat16',attention='eager',torch=torch.__version__,transformers=transformers.__version__,protocol='vision-ec-v1')
 dump(OUT/'identity.json',identity)
 records=[]
 for p in sorted(fix.glob('*.png')):
  data=p.read_bytes();pixels,allout,ec,times=encode(model,processor,data)
  folder=OUT/p.stem;folder.mkdir(exist_ok=True)
  st.save_file(dict(pixels),folder/'processor.safetensors');st.save_file(allout,folder/'vision-all.safetensors')
  t=time.perf_counter(); payload=st.save(ec);serial=time.perf_counter()-t
  (folder/'ec.safetensors').write_bytes(payload)
  key=sha(data+json.dumps(identity,sort_keys=True).encode())
  row=dict(name=p.stem,png_bytes=len(data),png_sha256=sha(data),cache_key=key,ec_file_bytes=len(payload),ec_sha256=sha(payload),ec_tensors={k:tensor_info(v) for k,v in ec.items()},all_tensors={k:tensor_info(v) for k,v in allout.items()},processor_tensors={k:tensor_info(v) for k,v in pixels.items()},serialize_s=serial,**times)
  records.append(row);log('encoded',**row)
 dump(OUT/'baseline.json',records)
 log('prepare_complete',maxrss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)

def recv_exact(s,n):
 b=bytearray()
 while len(b)<n:
  x=s.recv(n-len(b))
  if not x: raise EOFError('truncated frame')
  b.extend(x)
 return bytes(b)
def send_frame(s,header,payload):
 h=json.dumps(header,sort_keys=True,separators=(',',':')).encode();s.sendall(struct.pack('!IQ',len(h),len(payload))+h+payload)
 return 12+len(h)+len(payload)
def recv_frame(s):
 nh,np=struct.unpack('!IQ',recv_exact(s,12));assert nh<65536 and np<64*1024**2
 h=recv_exact(s,nh);p=recv_exact(s,np)
 return json.loads(h),p,12+nh+np

def receiver():
 init();model,processor=load_model();cache={};rows={x['name']:x for x in json.loads((OUT/'baseline.json').read_text())}
 identity=json.loads((OUT/'identity.json').read_text())
 with socket.socket() as listener:
  listener.bind(('127.0.0.1',0));listener.listen(1);listener.settimeout(120)
  dump(OUT/'ready.json',dict(port=listener.getsockname()[1],pid=os.getpid()))
  with listener.accept()[0] as s:
   s.settimeout(120)
   for seq in range(8):
    start=time.perf_counter();head,payload,wire=recv_frame(s);rx=time.perf_counter()-start
    assert head['seq']==seq and sha(payload)==head['sha256']
    name=head['name'];row=rows[name];hit=False;times={};t=time.perf_counter()
    if head['mode']=='raw':
     key=sha(payload+json.dumps(identity,sort_keys=True).encode());assert key==row['cache_key']
     if key in cache: ec=cache[key];hit=True
     else:
      pixels,allout,ec,times=encode(model,processor,payload)
      assert {k:tensor_info(v) for k,v in allout.items()}==row['all_tensors']
      assert {k:tensor_info(v) for k,v in pixels.items()}==row['processor_tensors']
      cache[key]=ec
      st.save_file(allout,OUT/name/'received-raw-vision-all.safetensors')
    else:
     ec=st.load(payload);(OUT/name/'received-ec.safetensors').write_bytes(payload)
    assert {k:tensor_info(v) for k,v in ec.items()}==row['ec_tensors']
    verified=time.perf_counter()-t
    result=dict(seq=seq,name=name,mode=head['mode'],ok=True,cache_hit=hit,payload_bytes=len(payload),wire_bytes=wire,recv_wait_and_read_s=rx,decode_or_reencode_and_verify_s=verified,**times)
    log('received_verified',**result);send_frame(s,result,b'')
 log('receiver_complete',maxrss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)

def sender():
 ready=json.loads((OUT/'ready.json').read_text())
 with socket.create_connection(('127.0.0.1',ready['port']),timeout=120) as s:
  seq=0
  for name in ['a-v1','a-v1','a-v2','b-v1']:
   for mode in ['raw','ec']:
    p=ROOT/'fixtures'/f'{name}.png' if mode=='raw' else OUT/name/'ec.safetensors'
    payload=p.read_bytes();h=dict(seq=seq,name=name,mode=mode,sha256=sha(payload),protocol='vision-ec-v1')
    start=time.perf_counter();wire=send_frame(s,h,payload);sendtime=time.perf_counter()-start
    ack,body,ackbytes=recv_frame(s);assert not body and ack['ok'] and ack['seq']==seq
    log('sent_ack',seq=seq,name=name,mode=mode,payload_bytes=len(payload),wire_bytes=wire,ack_wire_bytes=ackbytes,sendall_s=sendtime,send_to_verified_ack_s=time.perf_counter()-start,receiver=ack)
    seq+=1
 log('sender_complete')
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('mode',choices=['prepare','receiver','sender']);args=parser.parse_args()
 globals()[args.mode]()
