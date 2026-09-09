#!/usr/bin/env python3
"""Independent, stdlib-only verification of raw safetensors bytes and process logs."""
import hashlib,json,pathlib,struct
R=pathlib.Path(__file__).resolve().parent;O=R/'results'
def sha(x):return hashlib.sha256(x).hexdigest()
def readj(p):return json.loads(p.read_text())
def logs(name):return [json.loads(x) for x in (O/name).read_text().splitlines()]
def tensors(p):
 data=p.read_bytes();n=struct.unpack('<Q',data[:8])[0];header=json.loads(data[8:8+n]);payload=data[8+n:];out={}
 types={'BF16':'torch.bfloat16','F32':'torch.float32','I64':'torch.int64'}
 for k,v in header.items():
  if k=='__metadata__':continue
  a,b=v['data_offsets'];raw=payload[a:b]
  out[k]=dict(shape=v['shape'],dtype=types[v['dtype']],bytes=b-a,sha256=sha(raw))
 return out
rows=readj(O/'baseline.json');summ=[]
for row in rows:
 p=R/'fixtures'/(row['name']+'.png');folder=O/row['name']
 assert sha(p.read_bytes())==row['png_sha256'] and p.stat().st_size==row['png_bytes']
 assert tensors(folder/'processor.safetensors')==row['processor_tensors']
 assert tensors(folder/'vision-all.safetensors')==row['all_tensors']
 assert tensors(folder/'received-raw-vision-all.safetensors')==row['all_tensors']
 for name in ['ec.safetensors','received-ec.safetensors']:
  assert tensors(folder/name)==row['ec_tensors']
  assert sha((folder/name).read_bytes())==row['ec_sha256']
 assert set(row['ec_tensors'])=={'pooler_output','deepstack_0','deepstack_1','deepstack_2','image_grid_thw'}
 summ.append({k:row[k] for k in ['name','png_bytes','ec_file_bytes','encoder_s','processor_s','serialize_s']})
assert rows[0]['processor_tensors']['pixel_values']['shape']==rows[1]['processor_tensors']['pixel_values']['shape']
assert rows[0]['cache_key']!=rows[1]['cache_key']
assert all(rows[0]['ec_tensors'][k]['sha256']!=rows[1]['ec_tensors'][k]['sha256'] for k in ['pooler_output','deepstack_0','deepstack_1','deepstack_2'])
send=[x for x in logs('sender.jsonl') if x['event']=='sent_ack'];recv=[x for x in logs('receiver.jsonl') if x['event']=='received_verified']
assert len(send)==len(recv)==8
for s,r in zip(send,recv):
 assert s['seq']==r['seq'] and s['pid']!=r['pid'] and r['ok']
 assert s['wire_bytes']==r['wire_bytes'] and s['payload_bytes']==r['payload_bytes']
 assert {k:v for k,v in r.items() if k not in ['event','pid','monotonic_ns']}==s['receiver']
assert [r['cache_hit'] for r in recv if r['mode']=='raw']==[False,True,False,False]
supervisor=logs('supervisor.jsonl');exits=[x for x in supervisor if x['event']=='exit'];assert len(exits)==3 and all(x['code']==0 for x in exits)
assert supervisor[-1]['event']=='complete' and supervisor[-1]['aggregate_peak_rss_bytes']<11*1024**3
weights=readj(O/'weights-manifest.json');assert weights['strict'] and weights['keys']==351
source=readj(O/'environment.json')['source_sha256']
if (O/'source-addendum.json').exists(): source.update(readj(O/'source-addendum.json')['sources'])
for p,h in source.items():assert sha((O/'sources'/pathlib.Path(p).name).read_bytes())==h
summary=dict(status='bounded_real_measurement_complete_not_full_12_3',fixtures=summ,transfers=len(recv),all_raw_and_ec_bitwise_equal=True,raw_cache_hits=[r['cache_hit'] for r in recv if r['mode']=='raw'],weight_keys=weights['keys'],vision_parameters=weights['parameters'],peak_rss_bytes=supervisor[-1]['aggregate_peak_rss_bytes'],sender_total_wire_bytes=sum(x['wire_bytes'] for x in send),ack_total_wire_bytes=sum(x['ack_wire_bytes'] for x in send),timing_rows=send)
(O/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps({k:v for k,v in summary.items() if k!='timing_rows'},indent=2))
manifest={str(p.relative_to(R)):dict(bytes=p.stat().st_size,sha256=sha(p.read_bytes())) for p in sorted(R.rglob('*')) if p.is_file() and p.name not in ['manifest.json'] and '__pycache__' not in str(p)}
(R/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
