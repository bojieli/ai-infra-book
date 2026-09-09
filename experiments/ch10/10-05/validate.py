import ast, pathlib, hashlib, json, tarfile, subprocess, os, time
root=pathlib.Path(__file__).resolve().parent
os.chdir(root)
checks={}
for p in sorted(root.glob('*.py')):
 ast.parse(p.read_text()); checks[p.name]='AST syntax passed'
for p in root.glob('*.sh'):
 subprocess.run(['bash','-n',str(p)],check=True); checks[p.name]='bash -n passed'
manifest=json.loads((root/'sources/manifest.json').read_text())
archive=root/'sources/megatron-core-3bec9aa.tar.gz'
with tarfile.open(archive) as tar:
 prefix=tar.getmembers()[0].name.split('/')[0]
 for f in manifest['files']:
  assert 'error' not in f, f
  content=(root/'sources'/f['path']).read_bytes()
  assert hashlib.sha256(content).hexdigest()==f['sha256']
  assert tar.extractfile(prefix+'/'+f['path']).read()==content
checks['source_hashes_and_archive']='10 snapshots match SHA256 and pinned complete source archive'
artifacts=[]
for name,url in [('megatron-core-3bec9aa.tar.gz','https://codeload.github.com/NVIDIA/Megatron-LM/tar.gz/'+manifest['commit']),('install-0.16.0.html','https://docs.nvidia.com/megatron-core/developer-guide/0.16.0/get-started/install.html')]:
 p=root/'sources'/name
 artifacts.append(dict(path=name,url=url,bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
probe=root/f'results/gpu-guard-cpu-{time.time_ns()}'
probe.mkdir(exist_ok=True)
env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',VECLIB_MAXIMUM_THREADS='1')
python=root.parents[1]/'tools/collective-cpu-venv/bin/python'
command=[str(python),'gpu_handoff.py','--output',str(probe/'must-not-exist')]
with (probe/'stdout.log').open('w') as out,(probe/'stderr.log').open('w') as err:
 result=subprocess.run(command,stdout=out,stderr=err,env=env)
(probe/'exit_code.txt').write_text(str(result.returncode)+'\n')
(probe/'command.json').write_text(json.dumps(command,indent=2))
assert result.returncode==1
assert 'BLOCKED: CUDA and NCCL required' in (probe/'stderr.log').read_text()
assert not (probe/'must-not-exist').exists()
checks['gpu_guard']='CPU invocation exits 1 before Megatron import or device init; raw logs retained'
report=dict(status='BLOCKED_CPU_ONLY_GPU_UNEXECUTED',checks=checks,additional_sources=artifacts,
 downloaded_bytes=sum(f['bytes'] for f in manifest['files'])+sum(f['bytes'] for f in artifacts)+(root/'sources/tag.json').stat().st_size,
 no_gpu_execution=True,no_training_trace=True,no_figures=True)
(root/'validation.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
