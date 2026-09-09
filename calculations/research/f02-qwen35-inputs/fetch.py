import json,hashlib,datetime,struct,concurrent.futures
from pathlib import Path
from urllib.request import Request,urlopen
ROOT=Path(__file__).resolve().parent
REV='8472618112abcbd45acbcdc58436aff4233c23f7'
BASE=f'https://huggingface.co/Qwen/Qwen3.5-397B-A17B/resolve/{REV}/'
logs=[];records=[]
def fetch(url,file,revision=REV,byte_range=None):
 p=ROOT/file;p.parent.mkdir(parents=True,exist_ok=True)
 headers={'User-Agent':'ai-infra-book-input-audit/1.0'}
 if byte_range:headers['Range']='bytes='+byte_range
 with urlopen(Request(url,headers=headers),timeout=45) as r:
  status=r.status;cr=r.headers.get('Content-Range')
  if byte_range:
   start,end=map(int,byte_range.split('-'));expected=end-start+1
   if status!=206 or not cr or not cr.startswith(f'bytes {start}-{end}/'):raise ValueError(f'Range refused: {status} {cr}')
   raw=r.read(expected+1)
   if len(raw)!=expected:raise ValueError('Wrong range response length')
  else:
   raw=r.read(20_000_001)
   if len(raw)>20_000_000:raise ValueError('Metadata size cap exceeded')
  logs.append(dict(url=url,file=file,status=status,content_range=cr,bytes=len(raw),range=byte_range,checked_at=datetime.datetime.now(datetime.timezone.utc).isoformat()))
 p.write_bytes(raw)
 row=dict(model='qwen3.5-397b-a17b',repository='Qwen/Qwen3.5-397B-A17B' if 'huggingface.co' in url else 'huggingface/transformers',revision=revision,url=url,file='research/f02-qwen35-inputs/'+file,sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw),status='downloaded')
 if byte_range:row['http_range']='bytes='+byte_range
 records.append(row)
 return raw

def main():
 api=json.loads(fetch('https://huggingface.co/api/models/Qwen/Qwen3.5-397B-A17B/revision/'+REV,'api/model-revision.json'))
 assert api['sha']==REV
 for name in ['config.json','README.md','model.safetensors.index.json','preprocessor_config.json','video_preprocessor_config.json','generation_config.json','tokenizer_config.json']:
  fetch(BASE+name,'model/'+name)
 # The model tree has no implementation. Resolve a concrete Transformers commit,
 # then freeze its tree and source; this is a separate version from the HF model.
 commit=json.loads(fetch('https://api.github.com/repos/huggingface/transformers/commits/cbc1651a032b923da7f4b44b3d0e6f68e6ba6b55','api/transformers-commit.json',revision='API observation'))['sha']
 tree=json.loads(fetch(f'https://api.github.com/repos/huggingface/transformers/git/trees/{commit}?recursive=1','api/transformers-tree.json',revision=commit))
 names=[r['path'] for r in tree['tree'] if '/models/qwen3_5_moe/' in r['path'] and r['path'].endswith('.py')]
 names += ['src/transformers/cache_utils.py','src/transformers/vision_utils.py','src/transformers/modeling_rope_utils.py']
 for path in names:fetch(f'https://raw.githubusercontent.com/huggingface/transformers/{commit}/{path}','transformers/'+path,revision=commit)
 index=json.loads((ROOT/'model/model.safetensors.index.json').read_text())
 shards=sorted(set(index['weight_map'].values()))
 def header(shard):
  raw=fetch(BASE+shard,'prefixes/'+shard+'.length',byte_range='0-7')
  length=struct.unpack('<Q',raw)[0]
  if not 0<length<20_000_000:raise ValueError('Unsafe header length')
  fetch(BASE+shard,'headers/'+shard+'.json',byte_range=f'8-{7+length}')
 with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:list(pool.map(header,shards))
if __name__=='__main__':
 try:main()
 finally:
  (ROOT/'http-evidence.json').write_text(json.dumps(logs,indent=2)+'\n')
  observations=[r for r in records if '/api/' in r['file']]
  immutable=[r for r in records if '/api/' not in r['file']]
  for r in immutable:
   r['upstream_file']=r['url'].split('/resolve/'+r['revision']+'/')[-1] if '/resolve/' in r['url'] else r['url'].split('/'+r['revision']+'/')[-1]
  (ROOT/'source-lock.patch.json').write_text(json.dumps({'sources':sorted(immutable,key=lambda r:r['file'])},indent=2)+'\n')
  (ROOT/'api-observation.lock.json').write_text(json.dumps(observations,indent=2)+'\n')
