import hashlib,json,pathlib,urllib.request,os
root=pathlib.Path(os.environ['VERLRL_PRIVATE']); dst=root/'model'; dst.mkdir(exist_ok=True)
revision='7ae557604adf67be50417f59c2c2f167def9a775'
api=json.load(urllib.request.urlopen(f'https://huggingface.co/api/models/Qwen/Qwen2.5-0.5B-Instruct/revision/{revision}'))
manifest=[]; total=0
for entry in api['siblings']:
 name=entry['rfilename'];p=dst/name;p.parent.mkdir(parents=True,exist_ok=True)
 if not p.exists():
  req=urllib.request.urlopen(f'https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct/resolve/{revision}/{name}')
  with p.with_suffix(p.suffix+'.part').open('wb') as f:
   while b:=req.read(2**20):
    f.write(b)
    if f.tell()+total>2*2**30:raise RuntimeError('model exceeds 2GiB')
  p.with_suffix(p.suffix+'.part').rename(p)
 h=hashlib.file_digest(p.open('rb'),'sha256').hexdigest();total+=p.stat().st_size;manifest.append(dict(path=name,bytes=p.stat().st_size,sha256=h)); print(name,p.stat().st_size,h,flush=True)
assert total<=2*2**30
out=pathlib.Path(os.environ['VERLRL_ROOT']);(out/'model-manifest.json').write_text(json.dumps(dict(repo='Qwen/Qwen2.5-0.5B-Instruct',revision=revision,total_bytes=total,files=manifest),indent=2)+'\n')
import pandas as pd
rows=[]
for i,(expression,answer) in enumerate([('1 + 1','2'),('7 + 8','15'),('12 - 5','7'),('3 * 4','12')]):
 rows.append(dict(data_source='short_arithmetic',prompt=[dict(role='user',content=f'Compute {expression}. Reply with only the integer answer.')],ability='math',reward_model=dict(style='rule',ground_truth=answer),extra_info=dict(index=i)))
pd.DataFrame(rows*2).to_parquet(out/'train.parquet',index=False);pd.DataFrame(rows).to_parquet(out/'val.parquet',index=False)
(out/'prompts.json').write_text(json.dumps(rows,indent=2)+'\n')
