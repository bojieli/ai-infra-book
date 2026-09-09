"""Check pinned assets without loading weights; execute only after resource gate."""
import argparse, importlib.metadata, json, os, shutil, socket, subprocess, sys
from pathlib import Path
from common import BASE, CONFIG, LIMITS, MODEL, PYTHON, SAMPLING, TOOLS, save, sha, snapshot

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--name',default='multikey-001')
    p.add_argument('--execute',action='store_true')
    a=p.parse_args()
    assert Path(a.name).name==a.name and a.name not in ('.','..')
    assert Path(sys.executable).absolute()==PYTHON.absolute(),'Use pinned runtime Python'
    cases=json.loads((BASE/'prepared/cases.json').read_text())
    assert cases['sampling']==SAMPLING
    assert len(cases['cases'])==4
    assert all(len(c['input_ids'])==c['prompt_tokens']==4148 for c in cases['cases'])
    assert max(len(c['input_ids'])+SAMPLING['max_new_tokens'] for c in cases['cases'])<=CONFIG['context_length']
    assert sha(BASE/'tasks.json')==cases['task_sha256']
    versions=json.loads((BASE/'runtime-reference/resolved-serverargs.json').read_text())['versions']
    for name,version in versions.items():assert importlib.metadata.version(name)==version,(name,'version changed')
    for item in json.loads((BASE/'runtime-reference/sources.json').read_text()):
        assert sha(item['path'])==item['sha256'],item['path']
    metadata=json.loads((BASE/'runtime-reference/model-metadata.json').read_text())
    for item in metadata['shards']:
        f=MODEL/item['name'];st=f.stat()
        assert str(f.resolve())==item['target'] and st.st_size==item['bytes'] and st.st_mtime_ns==item['mtime_ns']
    hashes={s['file']:s['sha256'] for s in metadata['small_file_hashes']}
    hashes['tokenizer.json']=cases['tokenizer_sha256']
    for name,digest in hashes.items():assert sha(MODEL/name)==digest,name
    os.environ['CUDA_HOME']=str(TOOLS/'flashinfer-cuda130/nvidia/cu13')
    os.environ['PATH']=os.environ['CUDA_HOME']+'/bin:'+os.environ['PATH']
    from sglang.srt.server_args import ServerArgs
    resolved=ServerArgs(**CONFIG)
    assert resolved.context_length==5120 and resolved.max_total_tokens==5120
    snap=snapshot()
    host=snap['available_bytes']>=LIMITS['start_available_gib']*1024**3
    gpu=snap['gpu_free_mib']>=LIMITS['start_gpu_free_mib']
    with socket.socket() as sock:sock.bind(('127.0.0.1',CONFIG['port']))
    save(BASE/'execution-readiness.json',dict(status='preflight_no_engine',requests_executed=0,
          driver_sha256=sha(__file__),cases_sha256=sha(BASE/'prepared/cases.json'),snapshot=snap,
          requested=CONFIG,versions=versions,host_gate_passed=host,gpu_gate_passed=gpu,
          required_available_bytes=LIMITS['start_available_gib']*1024**3,
          weight_check='Prior fixed metadata identity only; no new tensor read or full shard hashing'))
    print(json.dumps(dict(host_gate_passed=host,gpu_gate_passed=gpu,available_bytes=snap['available_bytes'],execute=a.execute)))
    if not a.execute:return
    assert host and gpu,'Resource gate not met; no model launched'
    out=BASE/'runs'/a.name;out.mkdir(parents=True,exist_ok=False)
    for name in ['common.py','run.py','launch.py','score.py','offload_alias.py']:shutil.copyfile(BASE/name,out/name)
    shutil.copyfile(BASE/'prepared/cases.json',out/'cases.json')
    save(out/'candidate.json',CONFIG);save(out/'small-model-hashes.json',hashes)
    cccl=TOOLS/'sglang0513-venv/lib/python3.10/site-packages/nvidia/cu13/include/cccl'
    assert (cccl/'nv/target').is_file()
    (out/'include-overlay').mkdir();(out/'include-overlay/cccl').symlink_to(cccl,target_is_directory=True)
    (out/'tmp').mkdir()
    save(out/'execution-package-hashes.json',{n:sha(out/n) for n in ['common.py','run.py','launch.py','score.py','offload_alias.py','cases.json','candidate.json']})
    raise SystemExit(subprocess.call([sys.executable,'-B',str(out/'launch.py'),'--out',str(out),'--execute-after-rl'],cwd=out))

if __name__=='__main__':main()
