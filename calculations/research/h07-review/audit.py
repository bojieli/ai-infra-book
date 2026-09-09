"""Read-only H07 structural/provenance verification; writes only adjacent review artifact."""
from pathlib import Path
import json, hashlib, datetime, sys
R=Path(__file__).resolve().parents[2]; sys.path.insert(0,str(R/'src'))
from infra_calc.hardware import catalog
sha=lambda b:hashlib.sha256(b).hexdigest()
hw=catalog(); lock=json.loads((R/'configs/sources.lock.json').read_text())['sources']; byid={x['id']:x for x in lock if x.get('id')}; used={s for d in hw['devices'] for s in d['source_ids']}; checks=[]; issues=[]; pointers=[]
for s in lock:
 if s.get('model')!='hardware':continue
 b=(R/s['file']).read_bytes(); valid=sha(b)==s['sha256'] and len(b)==s['bytes']; assert valid,s['file']
 checks.append({k:s.get(k) for k in ['id','url','revision','file','sha256','bytes']}|{'verified':valid,'used_by_catalog':s.get('id') in used,'role':'author_research_not_device_spec' if s.get('id')=='cloudmatrix384-v3' else 'manufacturer_archive'})
def walk(x,path,device):
 if isinstance(x,dict):
  if 'source_id' in x:
   sid=x['source_id']; row={'device_id':device['id'],'path':path,'source_id':sid,'locator':x.get('locator'),'locked':sid in byid,'in_device_sources':sid in device['source_ids']};pointers.append(row)
   if not row['locked'] or not row['in_device_sources']:issues.append(row|{'issue':'unresolved_reference'})
   elif not row['locator']:issues.append(row|{'issue':'no_inline_locator'})
  for k,v in x.items():walk(v,path+'/'+k,device)
 elif isinstance(x,list):
  for i,v in enumerate(x):walk(v,path+'/'+str(i),device)
for d in hw['devices']:walk(d,'',d)
excluded=json.loads((R/'inventory/excluded-hardware-sources.json').read_text()); assert all(x['id'] not in used for x in excluded)
result={'schema_version':1,'generated_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'H07 current catalog provenance and pinned archive review; structural checks do not independently establish every semantic claim','binding':{'hardware_sha256':sha((R/'configs/hardware.json').read_bytes()),'sources_lock_sha256':sha((R/'configs/sources.lock.json').read_bytes()),'devices':len(hw['devices']),'peaks':sum(len(x['peak_rates']) for x in hw['devices'])},'sources':checks,'source_pointer_count':len(pointers),'source_pointers':pointers,'pointer_issues':issues,'excluded_author_sources':excluded,'summary':{'hardware_archives_verified':len(checks),'catalog_source_ids':len(used),'unresolved_references':sum(x['issue']=='unresolved_reference' for x in issues),'missing_inline_locators':sum(x['issue']=='no_inline_locator' for x in issues),'price_fields_in_catalog':sum(any('price' in k.lower() for k in d) for d in hw['devices']),'measured_performance_fields_in_catalog':sum(any('measured' in k.lower() for k in d) for d in hw['devices']),'availability_records':sum('availability' in d for d in hw['devices'])}}
hardware_sources=sorted([s for s in lock if s.get('model')=='hardware'],key=lambda s:(s.get('id',''),s['file']))
result['binding']['hardware_sources_subset_sha256']=sha(json.dumps(hardware_sources,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode())
result['binding']['hardware_sources_subset_count']=len(hardware_sources)
result['binding']['hardware_sources_normalization']='Full model==hardware lock records sorted(id,file); UTF8 JSON ensure_ascii=False sort_keys=True separators=(comma,colon)'
result['binding']['sources_lock_sha256_role']='Historical whole-lock snapshot; model-only additions do not invalidate hardware-source subset acceptance'
(Path(__file__).parent/'audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result['summary']))
