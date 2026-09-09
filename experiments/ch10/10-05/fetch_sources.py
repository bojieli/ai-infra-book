import pathlib, urllib.request, hashlib, json, datetime
root=pathlib.Path(__file__).resolve().parent
sha=json.loads((root/'sources/tag.json').read_text())['object']['sha']
paths=['README.md','LICENSE','pyproject.toml','megatron/core/pipeline_parallel/schedules.py','megatron/core/pipeline_parallel/p2p_communication.py','megatron/core/parallel_state.py','megatron/core/transformer/transformer_config.py','megatron/core/model_parallel_config.py','megatron/core/QuickStart.md','examples/run_simple_mcore_train_loop.py']
manifest=[]
for path in paths:
 url=f'https://raw.githubusercontent.com/NVIDIA/Megatron-LM/{sha}/{path}'
 dest=root/'sources'/path; dest.parent.mkdir(parents=True,exist_ok=True)
 try:
  with urllib.request.urlopen(url,timeout=30) as r: data=r.read(5_000_001); status=r.status
  assert len(data)<=5_000_000
  dest.write_bytes(data)
  manifest.append(dict(path=path,url=url,status=status,bytes=len(data),sha256=hashlib.sha256(data).hexdigest()))
 except Exception as e: manifest.append(dict(path=path,url=url,error=str(e)))
(root/'sources/manifest.json').write_text(json.dumps(dict(commit=sha,retrieved_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),files=manifest),indent=2))
