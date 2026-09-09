#!/usr/bin/env python3
"""Seal final evidence; no model execution and no self-referential hash."""
import hashlib,json,pathlib,datetime
r=pathlib.Path(__file__).resolve().parent
summary=json.loads((r/'analysis/summary.json').read_text())
cleanup=json.loads((r/'final-cleanup.json').read_text())
assert summary['status']=='minimal_real_loop_verified' and summary['control_nonzero_updates']==2
assert not cleanup['remaining_owned_pids']
files=[]
for p in sorted(r.rglob('*')):
 if p==r/'manifest.json':continue
 if p.is_symlink():files.append(dict(path=str(p.relative_to(r)),symlink_target=str(p.readlink())))
 elif p.is_file():
  with p.open('rb') as f:digest=hashlib.file_digest(f,'sha256').hexdigest()
  files.append(dict(path=str(p.relative_to(r)),bytes=p.stat().st_size,sha256=digest))
manifest=dict(schema_version=2,created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),experiment='10-8',status=summary['status'],control_verified_nonzero_updates=2,main_official_optimizer_calls=2,main_nonzero_policy_gradient_updates=0,quality_improvement_claim=False,full_experiment_complete=False,local_bytes=sum(f.get('bytes',0) for f in files),files=files,source=dict(repository='https://github.com/verl-project/verl',commit='d040717b21af2e23e8e789a3e354cff2394ae2de',archive_sha256='d61367ad5ec56aa110043fa9cff74be4aa9bfd7fd864bedb5cccc827bbb3dfc7',lock_sha256=hashlib.sha256((r/'environment/uv.lock').read_bytes()).hexdigest(),private_checkout='/home/ubuntu/ai-infra-book-experiments/tools/verl-private/verl-project-verl-d040717',patch_manifest='patch/sources.json',explicit_dependency_override=json.loads((r/'numpy-override.json').read_text())),model=json.loads((r/'model-manifest.json').read_text()),remote_private_allocated_bytes=cleanup['private_allocated_bytes'],remaining_owned_pids=[],final_runs=['main','control'],exclusions=['manifest self hash','large model/wheels/private venv retained only remotely'],remaining_scope=['recovery/preemption/asynchronous/normalization extensions','full V4','final cross-session paper audit'])
assert manifest['local_bytes']<150*2**20
assert manifest['remote_private_allocated_bytes']<25*2**30
assert manifest['source']['lock_sha256']=='d30f7e35c9f077c3c27aae1012711a753939db81a9a2cf4bcdbdf03fab59d0a9'
(r/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps({'files':len(files),'local_bytes':manifest['local_bytes'],'remote_private_bytes':manifest['remote_private_allocated_bytes']}))
