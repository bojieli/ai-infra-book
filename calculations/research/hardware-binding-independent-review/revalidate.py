"""Read-only H01/H04 binding audit; writes only beside this script."""
import copy, hashlib, json, os, pathlib, sys, datetime, collections, subprocess, unittest, importlib.util, io
os.environ['PYTHONDONTWRITEBYTECODE']='1'
sys.dont_write_bytecode=True
ROOT=pathlib.Path('/Users/boj/book/ai-infra-book'); P=ROOT/'calculations'; OUT=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(P/'src'))
from infra_calc.hardware import validate_device
from infra_calc.sources import read_source
sha=lambda b:hashlib.sha256(b).hexdigest()
canon=lambda d:json.dumps(d,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
digest=lambda d:sha(canon(d))
paths=['configs/hardware.json','configs/sources.lock.json','src/infra_calc/hardware.py','src/infra_calc/sources.py','inventory/h01-source-review.json','inventory/h04-source-review.json','research/h05-clock-accumulator-audit/proposed-hardware.patch.json','research/h05-clock-accumulator-audit/source-manifest.json']
raw={f:(P/f).read_bytes() for f in paths}; hw=json.loads(raw[paths[0]]); lock=json.loads(raw[paths[1]])['sources']; byid=collections.defaultdict(list); byfile=collections.defaultdict(list)
for r in lock:
 byid[r.get('id')].append(r); byfile[r['file']].append(r)
def refs(x):
 result=set()
 if isinstance(x,dict):
  for k,v in x.items():
   if k=='source_id':result.add(v)
   elif k=='source_ids':result.update(v)
   else:result.update(refs(v))
 elif isinstance(x,list):
  for v in x:result.update(refs(v))
 return result
e={'schema_version':1,'observed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'repository':str(ROOT),'normalization':'UTF-8 JSON ensure_ascii=False sort_keys=True separators=(comma,colon); devices sorted by id; internal arrays preserved','input_files':{f:sha(b) for f,b in raw.items()},'vendors':{}}
for vendor,name,key in [('NVIDIA','h01','sources'),('Apple','h04','source_evidence')]:
 inv=json.loads((P/f'inventory/{name}-source-review.json').read_text()); ds=sorted([d for d in hw['devices'] if d['vendor']==vendor],key=lambda d:d['id']); expected={d['id']:d['sha256'] for d in inv['device_subset']['device_sha256']}; ids=refs(ds); bindings={r['source_id']:r for r in inv[key]}; checks=[]
 for sid in sorted(ids|set(bindings)):
  rows=byid[sid]; b=bindings.get(sid); c={'source_id':sid,'referenced':sid in ids,'inventory_bound':b is not None,'lock_id_count':len(rows)}
  if len(rows)==1:
   r=rows[0]; data=(P/r['file']).read_bytes(); c.update(file=r['file'],actual_sha256=sha(data),actual_bytes=len(data),lock_file_count=len(byfile[r['file']]),lock_status=r['status'],sha256_matches_lock=sha(data)==r['sha256'],bytes_match_lock=len(data)==r['bytes'])
   try:read_source(r['file']);c['read_source']='passed'
   except Exception as ex:c['read_source']=repr(ex)
   if b:
    c['inventory_field_matches']={k:b[k]==r.get(k) for k in ('file','url','revision','sha256','bytes') if k in b}
    if 'lock_record_sha256' in b:c['lock_record_digest_matches_inventory']=digest(r)==b['lock_record_sha256']
  checks.append(c)
 current=[{'id':d['id'],'sha256':digest(d),'expected_sha256':expected.get(d['id']),'matches_inventory':digest(d)==expected.get(d['id'])} for d in ds]
 for d in ds:validate_device(d)
 v={'device_count':len(ds),'peak_count':sum(len(d['peak_rates']) for d in ds),'current_device_subset_sha256':digest(ds),'inventory_device_subset_sha256':inv['device_subset']['sha256'],'device_subset_matches':digest(ds)==inv['device_subset']['sha256'],'devices':current,'removed_inventory_device_ids':sorted(set(expected)-{d['id'] for d in ds}),'source_count':len(ids),'sources':checks,'validate_device_passed':len(ds)}
 if vendor=='Apple':
  projected=[{k:byid[sid][0][k if k!='source_id' else 'id'] for k in ('source_id','file','url','revision','sha256','bytes')} for sid in sorted(ids)]
  v['source_subset_sha256']=digest(projected);v['source_subset_matches']=digest(projected)==inv['source_subset_sha256']
 e['vendors'][vendor]=v
patch=json.loads(raw[paths[6]]); before=copy.deepcopy(hw)
def parent(obj,path):
 parts=path.strip('/').split('/');o=obj
 for p in parts[:-1]:o=o[int(p)] if isinstance(o,list) else o[p]
 return o,int(parts[-1]) if isinstance(o,list) else parts[-1]
# Restore full original peak objects from test guards, leaving every other field untouched.
for op in patch:
 if op['op']=='test' and isinstance(op['value'],dict):
  o,k=parent(before,op['path']);o[k]=copy.deepcopy(op['value'])
after=copy.deepcopy(before); guards=0; mutations=[]
for op in patch:
 o,k=parent(after,op['path'])
 if op['op']=='test':assert o[k]==op['value'],op['path'];guards+=1
 else:
  assert op['op'] in ('add','replace');assert op['path'].split('/')[-1] in ('clock_evidence','clock_basis','supporting_evidence');o[k]=copy.deepcopy(op['value']);mutations.append(op)
assert after==hw,'Patch reconstruction does not match current hardware'
ni=json.loads(raw[paths[4]]); oldds=sorted([d for d in before['devices'] if d['vendor']=='NVIDIA'],key=lambda d:d['id']); oldmap={d['id']:digest(d) for d in oldds}
recovered= digest(oldds)==ni['device_subset']['sha256'] and all(oldmap[d['id']]==d['sha256'] for d in ni['device_subset']['device_sha256'])
assert recovered,'Pre-patch reconstructed records do not match accepted H01 hashes'
e['h05']={'operations':len(patch),'test_guards_passed':guards,'mutations':len(mutations),'mutation_fields':dict(collections.Counter(op['path'].split('/')[-1] for op in mutations)),'mutations_detail':mutations,'current_catalog_equals_replayed_patch':after==hw,'reconstructed_prepatch_nvidia_sha256':digest(oldds),'reconstructed_prepatch_matches_all_h01_hashes':recovered,'changed_devices':[d['id'] for d in hw['devices'] if d!=next(x for x in before['devices'] if x['id']==d['id'])],'rates_precision_sparsity_scope_and_other_fields_unchanged':True}
manifest=json.loads(raw[paths[7]]);e['h05']['manifest_matches_lock']={r['id']:r==byid[r['id']][0] for r in manifest}
# Bounded existing tests: no H03/H07 tests and no whole-catalog setup.
def module(name):
 spec=importlib.util.spec_from_file_location(name,P/f'tests/{name}.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
m=module('test_hardware_audit'); n=module('test_hardware_expansion'); n.HardwareExpansion.setUpClass=classmethod(lambda cls:None); n.HardwareExpansion.data={'devices':[d for d in hw['devices'] if d['vendor'] in ('NVIDIA','Apple')],'pending_families':hw['pending_families']};n.HardwareExpansion.devices={d['id']:d for d in n.HardwareExpansion.data['devices']}
suite=unittest.defaultTestLoader.loadTestsFromTestCase(m.HardwareAudit)
for name in ['test_apple_memory_is_constrained_by_gpu_bin_and_host','test_desktop_evidence_cannot_be_reassigned_to_another_memory_or_gpu_bin','test_a100_40gb_form_factors_and_b200_per_gpu_power','test_new_system_profiles_preserve_memory_and_sparse_boundaries','test_h100_clock_domains_do_not_spill_into_unspecified_operations']:suite.addTest(n.HardwareExpansion(name))
stream=io.StringIO();result=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite);(OUT/'tests.log').write_text(stream.getvalue());e['tests']={'run':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'success':result.wasSuccessful(),'setup':'Existing HardwareExpansion tests use already read NVIDIA/Apple catalog subset and skip whole-catalog setUpClass to avoid H03 scope.'}
proposal=copy.deepcopy(ni);v=e['vendors']['NVIDIA'];proposal['device_subset']['sha256']=v['current_device_subset_sha256'];proposal['device_subset']['device_sha256']=[{'id':r['id'],'sha256':r['sha256']} for r in v['devices']]
proposal['binding_revalidation']={'reviewed_on':'2026-09-09','reason':'Merged H05 clock/accumulator supporting evidence only: 52 clock_evidence additions, 8 clock_basis replacements, 20 supporting_evidence additions. Reversing guarded peak edits reproduces every accepted NVIDIA device hash and the accepted subset hash. Rates, precision keys, sparsity, resource scope, source bindings and family acceptance unchanged. H05 remains incomplete.','previous_device_subset_sha256':ni['device_subset']['sha256'],'evidence_file':'revalidation.json','review_file':'REVIEW.md'}
(OUT/'proposed-h01-source-review.json').write_text(json.dumps(proposal,ensure_ascii=False,indent=2)+'\n')
e['input_files_unchanged_at_end']={f:sha((P/f).read_bytes())==sha(b) for f,b in raw.items()}
(OUT/'revalidation.json').write_text(json.dumps(e,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:{x:y for x,y in v.items() if x not in ('devices','sources')} for k,v in e['vendors'].items()},indent=2));print(e['h05']['mutation_fields']);print(e['tests']);print('stable',all(e['input_files_unchanged_at_end'].values()))
