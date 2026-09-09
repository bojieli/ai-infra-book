"""Root-only scheduled entry. Every candidate gets fresh output and private caches."""
import argparse,shutil,subprocess,sys
from pathlib import Path
from common import *
def main():
 p=argparse.ArgumentParser();p.add_argument('--name',required=True);p.add_argument('--execute-after-rl',action='store_true',required=True);a=p.parse_args()
 assert Path(a.name).name==a.name and a.name not in ('.','..')
 assert Path(sys.executable).absolute()==PYTHON.absolute(),'Use the pinned private venv Python'
 prepared=BASE/'prepared';assert (prepared/'completion.json').is_file()
 assert json.loads((prepared/'completion.json').read_text())['case_sha256']==sha(prepared/'cases.json')
 versions=json.loads((prepared/'resolved-serverargs.json').read_text())
 assert versions['requested']==CONFIG
 audit=json.loads((prepared/'toolchain-audit.json').read_text())
 assert command([str(TOOLS/'flashinfer-cuda130/nvidia/cu13/bin/nvcc'),'--version'])==audit['nvcc_version']
 assert sha(Path(audit['cccl'])/'nv/target')==audit['cccl_nv_target_sha256']
 for item in audit['cache_seed_files']:
  local_seed=NATIVE/Path(item['path']).relative_to('/home/ubuntu/ai-infra-book-experiments/ch02/02-05/native-layer-probe')
  assert sha(local_seed)==item['sha256'],str(local_seed)
 import importlib.metadata
 for n,v in versions['versions'].items():assert importlib.metadata.version(n)==v,(n,'dependency changed')
 for s in json.loads((prepared/'sources.json').read_text()):assert sha(s['path'])==s['sha256'],s['path']
 metadata=json.loads((prepared/'model-metadata.json').read_text())
 for s in metadata['shards']:
  f=MODEL/s['name'];st=f.stat();assert str(f.resolve())==s['target'] and st.st_size==s['bytes'] and st.st_mtime_ns==s['mtime_ns'],'Cached weight metadata changed; review required'
 hashes={s['file']:s['sha256'] for s in metadata['small_file_hashes']}
 hashes['tokenizer.json']=json.loads((prepared/'tokenizer-evidence.json').read_text())['tokenizer_json_sha256']
 for n,h in hashes.items():assert sha(MODEL/n)==h,n
 out=BASE/'runs'/a.name;out.mkdir(parents=True,exist_ok=False)
 for name in ['common.py','run.py','launch.py','score.py','route_observer.py']:shutil.copyfile(BASE/name,out/name)
 shutil.copyfile(BASE/'compatibility/offload_alias.py',out/'offload_alias.py')
 shutil.copyfile(prepared/'cases.json',out/'cases.json');save(out/'candidate.json',CONFIG);save(out/'small-model-hashes.json',hashes)
 shutil.copytree(prepared,out/'preparation-evidence')
 shutil.copytree(BASE/'reference',out/'reference')
 cccl=TOOLS/'sglang0513-venv/lib/python3.10/site-packages/nvidia/cu13/include/cccl'
 assert (cccl/'nv/target').is_file();assert (TOOLS/'flashinfer-cuda130/nvidia/cu13/bin/nvcc').is_file()
 (out/'include-overlay').mkdir();(out/'include-overlay/cccl').symlink_to(cccl,target_is_directory=True)
 seeds=[]
 for src,dst in [('jit-preflight/tvm-cache','cache/tvm'),('jit-mhc-preflight/tilelang-cache','cache/tilelang')]:
  source=NATIVE/src;assert source.is_dir();shutil.copytree(source,out/dst)
  for f in sorted((out/dst).rglob('*')):
   if f.is_file():seeds.append(dict(file=str(f.relative_to(out)),sha256=sha(f)))
 (out/'tmp').mkdir();save(out/'cache-seeds.json',dict(source=str(NATIVE),files=seeds,weight_files_copied=False))
 save(out/'execution-package-hashes.json',{n:sha(out/n) for n in ['common.py','run.py','launch.py','score.py','offload_alias.py','route_observer.py','cases.json','candidate.json']})
 raise SystemExit(subprocess.call([sys.executable,'-B',str(out/'launch.py'),'--out',str(out),'--execute-after-rl'],cwd=out))
if __name__=='__main__':main()
