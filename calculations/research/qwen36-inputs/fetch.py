import json,hashlib,datetime,struct,concurrent.futures,subprocess,re
from pathlib import Path
from urllib.request import Request,urlopen
ROOT=Path(__file__).resolve().parent
REV='995ad96eacd98c81ed38be0c5b274b04031597b0'
BASE=f'https://huggingface.co/Qwen/Qwen3.6-35B-A3B/resolve/{REV}/'
logs=[];records=[]
def fetch(url,file,revision=None,byte_range=None):
 revision=revision or REV
 p=ROOT/file;p.parent.mkdir(parents=True,exist_ok=True)
 cap=20_000_000
 if byte_range:
  start,end=map(int,byte_range.split('-'));cap=end-start+1
 header_path=p.with_name(p.name+'.http.tmp')
 cmd=['curl','-sS','-L','--fail','--retry','2','--max-time','90','--max-filesize',str(max(cap,2048)),'-D',str(header_path)]
 if byte_range:cmd+=['--range',byte_range]
 cmd+=[url]
 proc=subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 raw=proc.stdout.read(cap+1)
 if len(raw)>cap:
  proc.kill();raise ValueError('Size cap exceeded')
 error=proc.stderr.read().decode();rc=proc.wait()
 if rc:raise RuntimeError(error)
 blocks=re.split(r'\r?\n\r?\n',header_path.read_text())
 blocks=[x for x in blocks if x.startswith('HTTP/')]
 last=blocks[-1];status=int(last.splitlines()[0].split()[1]);rh={}
 for line in last.splitlines()[1:]:
  if ':' in line:
   k,v=line.split(':',1);rh[k.lower()]=v.strip()
 cr=rh.get('content-range')
 if byte_range and (status!=206 or not cr or not cr.startswith(f'bytes {start}-{end}/') or len(raw)!=cap):raise ValueError(f'Range refused {status} {cr} {len(raw)}')
 logs.append(dict(url=url,file=file,status=status,content_range=cr,bytes=len(raw),range=byte_range,checked_at=datetime.datetime.now(datetime.timezone.utc).isoformat()))
 header_path.unlink()
 p.write_bytes(raw)
 row=dict(model='qwen3.6-35b-a3b',repository='Qwen/Qwen3.6-35B-A3B' if 'huggingface.co' in url else 'huggingface/transformers',revision=revision,url=url,file='research/qwen36-inputs/'+file,sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw),status='downloaded')
 if byte_range:row['http_range']='bytes='+byte_range
 records.append(row)
 return raw

def main():
 global REV, BASE
 api=json.loads(fetch('https://huggingface.co/api/models/Qwen/Qwen3.6-35B-A3B/revision/'+REV,'api/model-revision.json'))
 REV=api['sha']
 BASE=f'https://huggingface.co/Qwen/Qwen3.6-35B-A3B/resolve/{REV}/'
 print('HF revision:',REV,flush=True)
 for name in ['config.json','README.md','model.safetensors.index.json','preprocessor_config.json','video_preprocessor_config.json','generation_config.json','tokenizer_config.json','LICENSE']:
  fetch(BASE+name,'model/'+name)
 # The model tree has no implementation. Resolve a concrete Transformers commit,
 # then freeze its tree and source; this is a separate version from the HF model.
 commit=json.loads(fetch('https://api.github.com/repos/huggingface/transformers/commits/cbc1651a032b923da7f4b44b3d0e6f68e6ba6b55','api/transformers-commit.json',revision='API observation'))['sha']
 tree=json.loads(fetch(f'https://api.github.com/repos/huggingface/transformers/git/trees/{commit}?recursive=1','api/transformers-tree.json',revision=commit))
 names=[r['path'] for r in tree['tree'] if '/models/qwen3_5_moe/' in r['path'] and r['path'].endswith('.py')]
 names += ['src/transformers/cache_utils.py','src/transformers/masking_utils.py','src/transformers/vision_utils.py','src/transformers/modeling_rope_utils.py']
 for path in names:fetch(f'https://raw.githubusercontent.com/huggingface/transformers/{commit}/{path}','transformers/'+path,revision=commit)
 index=json.loads((ROOT/'model/model.safetensors.index.json').read_text())
 shards=sorted(set(index['weight_map'].values()))
 def header(shard):
  raw=fetch(BASE+shard,'prefixes/'+shard+'.length',byte_range='0-7')
  length=struct.unpack('<Q',raw)[0]
  if not 0<length<20_000_000:raise ValueError('Unsafe header length')
  fetch(BASE+shard,'headers/'+shard+'.json',byte_range=f'8-{7+length}')
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:list(pool.map(header,shards))
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
