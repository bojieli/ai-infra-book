import os,json,pathlib,urllib.request,hashlib
root=pathlib.Path('/home/ubuntu/ai-infra-book-experiments/ch08/08-05')
p=root/'weights'/'Qwen3-8B-DFlash-b16'; p.mkdir(parents=True,exist_ok=True)
rev='9b41424b7109f9c5413454f481b09a82b85333f4'
meta=json.load(urllib.request.urlopen('https://huggingface.co/api/models/z-lab/Qwen3-8B-DFlash-b16/revision/'+rev+'?blobs=true'))
(root/'evidence'/'draft-api.json').write_text(json.dumps(meta,indent=2))
files=[x for x in meta['siblings'] if x['rfilename'] in ['config.json','model.safetensors']]
assert sum(x['size'] for x in files)<2*1024**3
assert __import__('shutil').disk_usage(root).free>sum(x['size'] for x in files)+5*1024**3
out=[]
for f in files:
 name=f['rfilename']; dest=p/name
 if not dest.exists():
  urllib.request.urlretrieve('https://huggingface.co/z-lab/Qwen3-8B-DFlash-b16/resolve/'+rev+'/'+name,p/(name+'.part')); (p/(name+'.part')).rename(dest)
 h=hashlib.sha256()
 with dest.open('rb') as stream:
  for b in iter(lambda:stream.read(8*1024**2),b''):h.update(b)
 assert dest.stat().st_size==f['size']
 if f.get('lfs'):assert h.hexdigest()==f['lfs']['sha256']
 out.append({'file':name,'size':dest.stat().st_size,'sha256':h.hexdigest()})
(root/'evidence'/'draft-verified.json').write_text(json.dumps({'revision':rev,'files':out},indent=2))
print(out,flush=True)
