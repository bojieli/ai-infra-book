"""Read-only cached model integrity/header and installed execution-source preflight."""
import argparse,hashlib,json,struct,subprocess
from pathlib import Path

ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
a.out.mkdir(parents=True,exist_ok=False)
p=Path('/home/ubuntu/.cache/huggingface/hub/models--deepseek-ai--DeepSeek-V4-Flash-0731/snapshots/7872f01b1d1fe23eabc4c98b48bffcef5a386062')
index=json.loads((p/'model.safetensors.index.json').read_text())
rows=[]
for name in sorted(set(index['weight_map'].values())):
    f=p/name
    with f.open('rb') as stream:
        length=struct.unpack('<Q',stream.read(8))[0]
        assert length<64*1024**2
        header=stream.read(length)
    h=json.loads(header);tensors={k:v for k,v in h.items() if k!='__metadata__'}
    expected={k for k,v in index['weight_map'].items() if v==name}
    assert set(tensors)==expected,(name,'index/header mismatch')
    intervals=sorted(v['data_offsets'] for v in tensors.values())
    assert intervals[0][0]==0
    assert all(x[1]==y[0] for x,y in zip(intervals,intervals[1:]))
    assert intervals[-1][1]+length+8==f.stat().st_size,(name,'truncated/trailing data')
    rows.append(dict(file=name,resolved_path=str(f.resolve()),bytes=f.stat().st_size,
                     tensor_count=len(tensors),header_sha256=hashlib.sha256(header).hexdigest()))
root=Path('/home/ubuntu/ai-infra-book-experiments/tools/sglang0513-venv/lib/python3.10/site-packages/sglang/srt')
source=[]
for name in ['models/deepseek_v4.py','arg_groups/deepseek_v4_hook.py','utils/offloader.py','layers/attention/deepseek_v4_backend.py']:
    body=(root/name).read_bytes();dst=a.out/'sources'/name;dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(body)
    source.append(dict(installed_path=str(root/name),sha256=hashlib.sha256(body).hexdigest()))
for name in ['config.json','model.safetensors.index.json']:(a.out/name).write_bytes((p/name).read_bytes())
result=dict(snapshot=str(p),shards=rows,sources=source,
            integrity_scope='index/header correspondence, contiguous offsets and file length only; full payload SHA not re-read; no inference',
            gpu=subprocess.check_output(['nvidia-smi','--query-compute-apps=pid,process_name,used_memory','--format=csv'],text=True),
            memory=subprocess.check_output(['free','-m'],text=True))
(a.out/'observation.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'checked_shards':len(rows),'indexed_tensors':len(index['weight_map']),'inference_run':False}))
