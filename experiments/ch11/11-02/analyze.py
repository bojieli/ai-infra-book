import hashlib,json
from pathlib import Path
R=Path(__file__).resolve().parent;source=json.loads((R/'sources.json').read_text());texts={}
for s in source['sources']:
 p=R/'sources'/s['file'];assert hashlib.sha256(p.read_bytes()).hexdigest()==s['sha256'];texts[s['file']]=p.read_text()
checks=[
 ('snapshots.md','v0.5.0','snapshot_min_envd','0.5.0'),
 ('snapshots.md','all active connections','snapshot_connections','active connections dropped; reconnect required'),
 ('snapshots.md','One-to-one','resume_identity','same sandbox'),
 ('snapshots.md','One-to-many','snapshot_identity','new sandbox instances from captured state'),
 ('persistence.md','keep_memory=False','filesystem_only','resume reboots; no preserved process memory'),
 ('persistence.md','rolling out region by region','rollout_scope','documented fallback behavior not universally deployed'),
]
records=[]
for file,needle,key,value in checks:
 lines=texts[file].splitlines();hits=[i+1 for i,l in enumerate(lines) if needle in l];assert hits,(file,needle)
 records.append(dict(key=key,documented_value=value,source=file,line_numbers=hits,evidence_kind='documentation_contract',observed_runtime=False))
modes=[
 dict(mode='template_create',files='template-defined baseline',memory='template starting state; not prior live process continuation',identity='new sandbox'),
 dict(mode='pause_resume_default',files='saved filesystem',memory='saved process state',identity='same sandbox'),
 dict(mode='snapshot_spawn',files='captured filesystem',memory='captured process state',identity='new sandbox; original resumes'),
 dict(mode='clean_rebuild',files='declared original baseline only',memory='fresh processes, no previous working memory',identity='new sandbox'),
 dict(mode='filesystem_only_resume',files='saved filesystem',memory='reboot; live memory not preserved',identity='same logical sandbox, rebooted guest'),
]
for m in modes:
 m.update(evidence_kind='protocol_comparison_not_measurement',api_return_s=None,first_tool_completed_s=None,file_check=None,memory_check=None,connection_check=None)
report=dict(status='documentation_reviewed_runtime_pending',contracts=records,comparison=modes,environment=json.loads((R/'availability.json').read_text()),limits='Source hashes pin retrieved documentation, not deployed SDK/template/server version. No E2B timing or state-restoration measurement.')
(R/'summary.json').write_text(json.dumps(report,indent=2)+'\n');print('verified',len(records),'document contracts;',len(modes),'unmeasured modes')
