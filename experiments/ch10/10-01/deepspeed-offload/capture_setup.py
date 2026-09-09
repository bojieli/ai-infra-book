import hashlib,importlib.metadata,json,os,shutil,subprocess
from pathlib import Path

p=Path(__file__).parent;s=p/'sources';s.mkdir(exist_ok=True)
dist=importlib.metadata.distribution('deepspeed')
base=Path(dist.locate_file('deepspeed'))
files=['ops/adam/cpu_adam.py','ops/op_builder/cpu_adam.py','ops/op_builder/builder.py',
       'ops/csrc/adam/cpu_adam.cpp','ops/csrc/adam/cpu_adam_impl.cpp',
       'ops/csrc/includes/cpu_adam.h','runtime/zero/offload_config.py']
records=[]
for relative in files:
    src=base/relative;dst=s/relative;dst.parent.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(src,dst)
    records.append(dict(installed=str(src),local=str(dst.relative_to(p)),sha256=hashlib.sha256(dst.read_bytes()).hexdigest()))
cache=p/'setup/torch-extensions'
for src in sorted(cache.rglob('*')):
    if src.name in ['cpu_adam.so','build.ninja']:
        records.append(dict(compiled=str(src),sha256=hashlib.sha256(src.read_bytes()).hexdigest(),bytes=src.stat().st_size))
        shutil.copyfile(src,s/src.name)
(s/'manifest.json').write_text(json.dumps(records,indent=2))
(p/'setup/freeze.txt').write_text(subprocess.check_output([os.sys.executable,'-m','pip','freeze'],text=True))
(p/'setup/gpu-final.txt').write_text(subprocess.check_output(['nvidia-smi','--query-compute-apps=pid,process_name,used_memory','--format=csv'],text=True))
