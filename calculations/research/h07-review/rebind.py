"""Guarded H01/H04 rebind for the two explicitly reviewed patches only."""
from pathlib import Path
import json,copy,hashlib,datetime,sys
R=Path(__file__).resolve().parents[2];O=Path(__file__).parent;sys.path.insert(0,str(R/'src'))
from infra_calc.hardware import validate_device
sha=lambda b:hashlib.sha256(b).hexdigest();digest=lambda x:sha(json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode())
read=lambda p:json.loads((R/p).read_text()); hw=read('configs/hardware.json');lock=read('configs/sources.lock.json')['sources'];sl={x.get('id'):x for x in lock}; patch=read('research/h05-next-review/proposed-hardware.patch.json');ap=read('research/h07-review/availability-locator-patch.json')['device_field_updates'];before=copy.deepcopy(hw)
def parent(obj,path):
 ps=path.strip('/').split('/');o=obj
 for p in ps[:-1]:o=o[int(p)] if isinstance(o,list) else o[p]
 return o,int(ps[-1]) if isinstance(o,list) else ps[-1]
for op in patch:
 if op['op']=='test':o,k=parent(before,op['path']);o[k]=copy.deepcopy(op['value'])
replay=copy.deepcopy(before);guards=0
for op in patch:
 o,k=parent(replay,op['path'])
 if op['op']=='test':assert o[k]==op['value'];guards+=1
 else:assert op['op']=='add';o[k]=copy.deepcopy(op['value'])
assert replay==hw
bymap={d['id']:d for d in before['devices']}
for p in ap:
 d=bymap[p['device_id']]; assert d['availability']==p['value']; assert set(p['value'])>={'locator','evidence_scope'}; d['availability'].pop('locator');d['availability'].pop('evidence_scope')
# Restore and replay both independent patches, proving no unrelated changes.
both=copy.deepcopy(before);bm={d['id']:d for d in both['devices']}
for p in ap:bm[p['device_id']]['availability']=copy.deepcopy(p['value'])
for op in patch:
 o,k=parent(both,op['path'])
 if op['op']=='test':assert o[k]==op['value']
 else:o[k]=copy.deepcopy(op['value'])
assert both==hw
report={'schema_version':1,'h05_test_guards':guards,'h05_operations':len(patch),'availability_full_value_guards':len(ap),'both_patches_reproduce_entire_catalog':True,'vendors':{},'patch_hashes':{p:sha((R/p).read_bytes()) for p in ['research/h05-next-review/proposed-hardware.patch.json','research/h05-next-review/proposed-sources.patch.json','research/h07-review/availability-locator-patch.json']}}
updates=[]
for vendor,name,key in [('NVIDIA','h01','sources'),('Apple','h04','source_evidence')]:
 inv=read(f'inventory/{name}-source-review.json'); oldds=sorted([d for d in before['devices'] if d['vendor']==vendor],key=lambda d:d['id']);ds=sorted([d for d in hw['devices'] if d['vendor']==vendor],key=lambda d:d['id']);assert digest(oldds)==inv['device_subset']['sha256'],name
 oldmap={d['id']:digest(d) for d in oldds};assert all(oldmap[r['id']]==r['sha256'] for r in inv['device_subset']['device_sha256'])
 for s in inv[key]:
  row=sl[s['source_id']];assert all(s[k]==row[k] for k in ('file','url','revision','sha256','bytes') if k in s)
  if 'lock_record_sha256'in s:assert digest(row)==s['lock_record_sha256']
 ids=sorted({sid for d in ds for sid in d['source_ids']});sources=[]
 for sid in ids:
  r=sl[sid];b=(R/r['file']).read_bytes();assert sha(b)==r['sha256'] and len(b)==r['bytes'];sources.append({'source_id':sid,**{k:r[k] for k in ('file','url','revision','sha256','bytes')},'lock_record_sha256':digest(r),'verification':'SHA256 and byte count independently verified'})
 for d in ds:validate_device(d)
 history={k:copy.deepcopy(inv[k]) for k in ('device_subset',key,'source_subset_sha256','binding_revalidation') if k in inv};inv.setdefault('binding_history',[]).append(history);inv['device_subset']['sha256']=digest(ds);inv['device_subset']['device_sha256']=[{'id':d['id'],'sha256':digest(d)} for d in ds];inv[key]=sources
 projected=[{k:s[k] for k in ('source_id','file','url','revision','sha256','bytes')} for s in sources];inv['source_subset_sha256']=digest(projected)
 inv['binding_revalidation']={'reviewed_on':'2026-09-09','evidence_file':'research/h07-review/rebinding-evidence.json','previous_device_subset_sha256':history['device_subset']['sha256'],'guarded_prepatch_matches_every_accepted_device_hash':True,'both_patches_reproduce_entire_catalog':True,'scope':'Only already-reviewed H05 evidence/clock/power condition additions and H07 availability locators; numeric rates,precision keys and capacities unchanged.'}
 report['vendors'][vendor]={'device_count':len(ds),'peak_count':sum(len(d['peak_rates']) for d in ds),'previous_sha256':digest(oldds),'current_sha256':digest(ds),'source_count':len(sources),'source_subset_sha256':digest(projected),'new_source_ids':sorted(set(ids)-{s['source_id'] for s in history[key]}),'accepted_per_device_hash_guards':len(ds)};updates.append((R/f'inventory/{name}-source-review.json',inv))
for p,d in updates:p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
(O/'rebinding-evidence.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(report['vendors'],indent=2))
