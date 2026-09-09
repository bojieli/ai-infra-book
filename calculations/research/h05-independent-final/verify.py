from pathlib import Path
import json,hashlib,copy,sys,collections
R=Path(__file__).resolve().parents[2];O=Path(__file__).parent;sys.path.insert(0,str(R/'src'))
from infra_calc.hardware import catalog
sha=lambda b:hashlib.sha256(b).hexdigest();digest=lambda x:sha(json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode());load=lambda p:json.loads((R/p).read_text())
hw=catalog();patch=load('research/h05-final-coverage/proposed-hardware.patch.json');before=copy.deepcopy(hw)
def parent(o,path):
 ps=path.strip('/').split('/')
 for p in ps[:-1]:o=o[int(p)] if isinstance(o,list) else o[p]
 return o,int(ps[-1]) if isinstance(o,list) else ps[-1]
for op in reversed(patch):
 if op['op']=='test':o,k=parent(before,op['path']);o[k]=copy.deepcopy(op['value'])
after=copy.deepcopy(before);guard=0
for op in patch:
 o,k=parent(after,op['path'])
 if op['op']=='test':assert o[k]==op['value'],op['path'];guard+=1
 else:assert op['op']=='add' and op['path'].split('/')[-1] in ['supporting_evidence','source_ids'];o[k]=copy.deepcopy(op['value'])
assert after==hw
cov=load('research/h05-final-coverage/coverage.json');prebytes=(json.dumps(before,ensure_ascii=False,indent=2)+'\n').encode();assert sha(prebytes)==cov['input_sha256'],'prepatch bytes do not reproduce coverage input'; nvidia=lambda h:sorted([d for d in h['devices'] if d['vendor']=='NVIDIA'],key=lambda d:d['id']);hi=load('inventory/h01-source-review.json');assert digest(nvidia(before))==hi['device_subset']['sha256'];assert {d['id']:digest(d) for d in nvidia(before)}=={d['id']:d['sha256'] for d in hi['device_subset']['device_sha256']}
expected={(d['id'],i):(d,p) for d in hw['devices'] for i,p in enumerate(d['peak_rates'])};assert len(expected)==471 and len(cov['rows'])==471;seen=set();statuses=collections.Counter()
for row in cov['rows']:
 key=(row['device_id'],row['peak_index']);assert key not in seen;seen.add(key);d,p=expected[key];assert row['peak_key']=={k:p[k] for k in ['input_precision','accumulator_precision','execution_unit','sparsity']}
 values={k:p.get(k) for k in ['input_precision','accumulator_precision','execution_unit','sparsity','tera_ops_per_second','reported','derivation']};values.update(scope={k:d.get(k) for k in ['spec_scope','gpu_count','npu_count','record_kind','form_factor']},clock={'peak_evidence':p.get('clock_evidence'),'product_clock':d.get('clock'),'basis':p.get('clock_basis')},power={'cap':d.get('power_watts'),'evidence':d.get('power_evidence')},source_locator={'source_id':p['source_id'],'locator':p['locator']})
 assert set(row['fields'])==set(values)
 for field,v in values.items():
  r=row['fields'][field];assert r['value']==v,(key,field);assert r['status'] in ['verified_within_cited_scope','reviewed_sources_do_not_resolve'];assert r['reason'] and (R/r['review_reference']).is_file();statuses[r['status']]+=1
assert seen==set(expected) and dict(statuses)==cov['field_status_counts']
for a,b in zip(before['devices'],hw['devices']):
 for pa,pb in zip(a['peak_rates'],b['peak_rates']):assert {k:v for k,v in pa.items() if k!='supporting_evidence'}=={k:v for k,v in pb.items() if k!='supporting_evidence'}
manifest=load('research/h05-final-coverage/review-manifest.json')
for r in manifest:assert sha((R/r['file']).read_bytes())==r['sha256']
source_rows=load('research/h05-final-coverage/sources.lock.json')['sources'];lock=load('configs/sources.lock.json')['sources'];sl={s.get('id'):s for s in lock}
for s in source_rows:
 b=(R/s['file']).read_bytes();assert sha(b)==s['sha256'] and len(b)==s['bytes'];assert s['sha256']==sl[s['id']]['sha256']
result={'scope':'Independent finite acceptance of final H05 evidence patch; no old quarantine patch executed','postpatch_hardware_sha256':sha((R/'configs/hardware.json').read_bytes()),'postpatch_sources_lock_sha256':sha((R/'configs/sources.lock.json').read_bytes()),'prepatch_coverage_input_sha256':cov['input_sha256'],'recovered_prepatch_bytes_match':True,'full_catalog_replay_matches':True,'test_guards':guard,'patch_operations':len(patch),'devices':151,'peaks_checked_once':len(seen),'fields_compared_to_current_catalog':sum(statuses.values()),'field_status_counts':dict(statuses),'all_peak_values_keys_raw_derivations_clock_and_power_unchanged':True,'semantic_review_manifest_files_verified':len(manifest),'official_source_originals_verified':len(source_rows),'h01_prepatch_subset_matches_all_device_hashes':True,'postpatch_nvidia_subset_sha256':digest(nvidia(hw))}
(O/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result,indent=2))
