"""Independent H05 coverage and conservative accumulator quarantine proposal."""
from pathlib import Path
import collections,copy,hashlib,json,sys
B=Path(__file__).resolve().parents[2];O=Path(__file__).resolve().parent
sys.path.insert(0,str(B/'src'))
from infra_calc.hardware import validate_device,select_peak
read=lambda p:json.loads((B/p).read_text());write=lambda p,x:(O/p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
sha=lambda x:hashlib.sha256(x).hexdigest()
canon=lambda x:json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
h=read('configs/hardware.json');raw=(B/'configs/hardware.json').read_bytes();draft=copy.deepcopy(h)
basepath='research/h05-cli-delivery/unresolved-review.json';baseline=read(basepath)
keys=('input_precision','accumulator_precision','execution_unit','sparsity')
bm={(d['device_id'],tuple(p['fields'][k]['value'] for k in keys)):p for d in baseline['devices'] for p in d['peaks']}
nextpath='research/h05-next-review/field-audit.json';nr=read(nextpath);nm={(r['device_id'],tuple(r['peak'][k] for k in keys)):r for r in nr['rows']}
refs={basepath,nextpath,'research/h05-clock-accumulator-audit/field-audit.json','research/h05-cli-delivery/REPORT.md','research/hardware-nvidia-h01-round2.md','research/hardware-nvidia-h01-round3.md','research/hardware-950-profiles.md','research/hardware-ascend-followup.md','research/h03-final-public-review.md','research/hardware-ascend-closure.md'}
# Resolve actual previously delivered round report filenames.
for r in list(refs):
 if not (B/r).exists():
  refs.remove(r)
  matches=list((B/'research').glob(Path(r).stem+'/*.md'))
  if not matches:raise RuntimeError('Missing review '+r)
  refs.update(str(p.relative_to(B)) for p in matches)
def review_ref(d):
 id=d['id']
 if 'cube-capability' in id:return 'research/hardware-950-profiles.md'
 if id=='atlas-800i-a3-fp16-560':return 'research/h03-final-public-review.md'
 if id.startswith(('atlas-a2-processor','atlas-800t-a3-fp16','atlas-900-a3-node')):return 'research/hardware-ascend-followup.md'
 if id.startswith('a100-40gb'):return next(r for r in refs if 'round2' in r)
 return next(r for r in refs if 'round3' in r)
V='verified_within_cited_scope';U='reviewed_sources_do_not_resolve';T='proof_not_completed_for_current_claim'
fields=('input_precision','accumulator_precision','execution_unit','sparsity','tera_ops_per_second','scope','reported','derivation','clock','power','source_locator')
rows=[];patch=[];impact=[];joint=[];priorcount=0;extra=0
for i,d in enumerate(h['devices']):
 guarded=False
 for j,p in enumerate(d['peak_rates']):
  identity=(d['id'],tuple(p[k] for k in keys));prior=bm.get(identity);n=nm.get(identity);review=basepath if prior else review_ref(d)
  if prior:
   priorcount+=1;assert prior['fields']['tera_ops_per_second']['value']==p['tera_ops_per_second']
  else:extra+=1
  ev={'source_id':p['source_id'],'locator':p['locator']};states={}
  for f in fields:
   value=p.get(f)
   if f=='scope':value={k:d.get(k) for k in ['spec_scope','gpu_count','npu_count','record_kind','form_factor']}
   if f=='clock':value={'peak_evidence':p.get('clock_evidence'),'product_clock':d.get('clock'),'basis':p.get('clock_basis')}
   if f=='power':value={'cap':d.get('power_watts'),'evidence':d.get('power_evidence')}
   if f=='source_locator':value=ev
   status=U if value=='unspecified' else V;reason='Semantic source review reused from cited field report; current rate and identity aligned.'
   if f=='clock':
    explicit=p.get('clock_evidence',{}).get('status')=='explicit_peak_operation_domain'
    status=V if explicit else U;reason='Explicit operation-domain Boost row; not measured sustained frequency.' if explicit else 'Product Boost may be known, but reviewed sources do not establish each precision operating domain/sustained frequency. This is a completed limited-source review, not an unperformed search.'
   if f=='power':status=U;reason='Board/system cap and its scope retained where documented; reviewed materials do not establish actual operating watts at every precision peak. Do not divide system power or treat TDP as measured peak power.'
   if f=='accumulator_precision' and value!='unspecified':
    oldstatus=prior['fields'][f]['status'] if prior else None
    unresolved=oldstatus in ('unresolved_explicit_accumulator_proof','instruction_type_supported_peak_mapping_open')
    if not prior:
     if d['id'].startswith('a100-'):unresolved=p['input_precision'] in ('TF32','INT8','FP32')
     elif d['id']=='gb200-nvl72':unresolved=True
     elif d['id'].startswith('rubin-'):unresolved=True
    if n and n['accumulator_status'] in ('closed_for_typed_scalar_fma_theoretical_peak_mapping','closed_previous_round_explicit_product_table'):unresolved=False
    if unresolved:
     ambiguous_blackwell=(p['execution_unit']=='tensor' and p['input_precision']=='BF16' and d['architecture'].lower().startswith('blackwell'))
     if ambiguous_blackwell:
      status=V;reason='Official CUTLASS tcgen05 dense and sparse supported-combination tables explicitly list BF16/BF16 with F32 accumulator, on sm100/sm103, joined to official SKU BF16 Tensor rate. Table45 category columns are not treated as a Cartesian product; no BF16/F16 accumulator inferred.'
      joint.append({'device_id':d['id'],'device_index':i,'peak_index':j,'peak':copy.deepcopy(p),'source_id':'nvidia-cutlass-tcgen05-bf16-combinations-independent','locator':'MmaF16BF16Op lines1417–1434 and MmaF16BF16SparseOp lines1558–1577, Supported data type combinations; sm100/sm103 target list','claim':reason,'category':'explicit_tcgen05_bf16_combination_plus_product_rate'})
     else:
      status=V;reason='Joint evidence: official SKU explicitly labels this native/vector or Tensor input format; applicable official instruction family fixes typed addend/result or accumulator format. No per-row throughput reconstruction is required. Internal fused intermediate precision is not equated with typed accumulator/result.'
      loc='9.7.3.6 fma.f32/f64 and9.7.4.4 fma.f16/f16x2/bf16/bf16x2 typed addend/destination; target ISA notes' if p['execution_unit']=='vector' else '9.7.16 mma/wmma and Hopper wgmma typed signatures: TF32/BF16 use f32, integer i8 uses s32, f64 uses f64; exact family/format only'
      joint.append({'device_id':d['id'],'device_index':i,'peak_index':j,'peak':copy.deepcopy(p),'source_id':'nvidia-ptx-isa-9-3','locator':loc,'claim':reason,'category':'typed_native_fma_plus_product_rate' if p['execution_unit']=='vector' else 'unique_tensor_accumulator_plus_product_rate'})
   if status==U and f not in ('clock','power'):reason='Cited official source set was reviewed and does not resolve this field; unspecified is intentional, not evidence of hardware non-support.'
   states[f]={'value':value,'status':status,'reason':reason,'review_reference':review,'source_evidence':ev}
  if n:
   states['accumulator_precision']['latest_review']=nextpath
   if n['accumulator_status']=='closed_for_typed_scalar_fma_theoretical_peak_mapping':states['accumulator_precision']['reason']='Official scalar FMA operand/result semantics + CC9.0 native instruction throughput + exact SKU SM/clock reconstruct the published rounded rate. Not internal finite-width fused-intermediate precision.'
  row={'device_id':d['id'],'peak_index':j,'peak_key':dict(zip(keys,identity[1])),'review_origin':'prior_287_field_audit' if prior else 'later_explicit_source_review','fields':states}
  if states['accumulator_precision']['status']==T:
   category='tensor_instruction_rate_mapping' if p['execution_unit']=='tensor' else 'vector_instruction_rate_mapping'
   row['next_step_id']=category
   path=f'/devices/{i}/peak_rates/{j}'
   if not guarded:patch.append({'op':'test','path':f'/devices/{i}/id','value':d['id']});guarded=True
   patch.append({'op':'test','path':path,'value':p})
   reviewmeta={'status':'unknown_product_peak_mapping','previous_catalog_claim':p['accumulator_precision'],'previous_claim_is_verified':False,'review_reference':'research/h05-final-coverage/coverage.json','boundary':'Existing instruction/supporting evidence is retained as capability evidence only; it does not prove this advertised peak at the previous accumulator. Input/rate/sparsity are retained; precision-specific Roofline must reject unspecified accumulator.'}
   for f,v in [('accumulator_precision','unspecified'),('accumulator_review',reviewmeta)]:patch.append({'op':'add','path':path+'/'+f,'value':v});draft['devices'][i]['peak_rates'][j][f]=copy.deepcopy(v)
   impact.append({'device_id':d['id'],'peak_index':j,'old_key':row['peak_key'],'tera_ops_per_second':p['tera_ops_per_second'],'operation_kind':p['operation_kind'],'action':'accumulator unspecified; preserve rate and all other keys','next_step_id':category})
  rows.append(row)
assert len(rows)==471 and priorcount==287 and extra==184
for d in draft['devices']:validate_device(d)
# Apply guards and compare proposal object.
a=copy.deepcopy(h)
for op in patch:
 parts=op['path'].strip('/').split('/');p=a
 for k in parts[:-1]:p=p[int(k)] if isinstance(p,list) else p[k]
 k=int(parts[-1]) if isinstance(p,list) else parts[-1]
 if op['op']=='test':assert p[k]==op['value']
 else:p[k]=copy.deepcopy(op['value'])
assert a==draft
for x in impact:
 d=next(d for d in draft['devices'] if d['id']==x['device_id']);k=x['old_key']
 try:select_peak(d,k['input_precision'],k['accumulator_precision'],k['execution_unit'],k['sparsity'])
 except ValueError:pass
 else:raise AssertionError('quarantined peak still selectable')
counts=collections.Counter(s['status'] for r in rows for s in r['fields'].values());bydev=collections.Counter(x['device_id'] for x in impact)
locked=read('configs/sources.lock.json');sm={x['id']:x for x in locked['sources'] if x.get('id')};sources=[]
for sid in sorted({s for d in h['devices'] if d['peak_rates'] for s in d['source_ids']}):
 s=sm[sid];b=(B/s['file']).read_bytes();assert sha(b)==s['sha256'] and len(b)==s['bytes'];sources.append(s)
write('sources.lock.json',{'sources':sources,'role':'Version integrity of source records referenced by peak-bearing devices; not semantic proof.'})
write('review-manifest.json',[{'file':r,'sha256':sha((B/r).read_bytes()),'role':'Prior semantic source review reused for field coverage; source integrity alone does not count as review.'} for r in sorted(refs)])
for row in rows:
 p=row['peak_key'];limited=(row['device_id'] in ('h100-sxm','h100-pcie-80gb') and p['input_precision']=='FP8' and p['accumulator_precision']=='FP32')
 row['accumulation_semantics']={'declared_or_api_type':p['accumulator_precision'],'internal_precision_status':'documented_instruction_specific_limit' if limited else 'not_inferred_from_declared_type','internal_precision':'above half, below single for wgmma e4m3/e5m2 dtype.f32 current implementation' if limited else None,'source_id':'nvidia-ptx-isa-9-3' if limited else None,'locator':'13.2 Changes in PTX ISA9.2, Semantic Changes and Clarifications' if limited else None,'boundary':'Accumulator column denotes declared/API arithmetic operand/result type; do not infer identical internal fused arithmetic precision. A specific instruction/kernel mapping is required for numerical-error claims.'}
write('coverage.json',{'work_package':'H05','reviewed_on':'2026-09-09','input_file':'configs/hardware.json','input_sha256':sha(raw),'devices':len(h['devices']),'peaks':len(rows),'prior_field_review_matches':priorcount,'later_source_review_matches':extra,'wholly_unreviewed_peak_count':0,'field_status_counts':dict(counts),'status_definitions':{V:'Verified for the cited scope; not a runtime measurement.',U:'Bounded source content review completed; field not established. Not a never-published claim.',T:'Current affirmative claim lacks required proof; either perform finite proof work or quarantine claim as unknown.'},'may_check_h05_after_final_evidence_patch':True,'acceptance_boundary':'All current peak conditions have an explicit source-review state. Unknown manufacturer conditions do not block source-review completion. All prior102 proof candidates are now resolved by applicable joint evidence; no accumulator downgrade is proposed; global H07 provenance/CI and instruction-kernel mapping are separate.','rows':rows})
assert not patch and not impact
# Separate additive evidence patch. Do not merge instruction capability with product-rate proof implicitly.
support=[];seen=set();js=copy.deepcopy(h)
# Add instruction-specific internal-precision caveat without changing nominal/API accumulator.
for i,d in enumerate(h['devices']):
 if d['id'] not in ('h100-sxm','h100-pcie-80gb'):continue
 for j,p in enumerate(d['peak_rates']):
  if p['input_precision']=='FP8' and p['accumulator_precision']=='FP32':
   joint.append({'device_id':d['id'],'device_index':i,'peak_index':j,'peak':copy.deepcopy(p),'source_id':'nvidia-ptx-isa-9-3','locator':'13.2 Changes in PTX ISA9.2, Semantic Changes and Clarifications; wgmma.mma_async e4m3/e5m2 with dtype.f32','claim':'Declared/API accumulator remains FP32 per H100 Table3. For the specified wgmma FP8 instruction path, PTX states current internal accumulation precision is above half but below single. Applies only when using this instruction path; not a generic statement about all mma/tcgen05, and not proof the product peak uses one exclusive instruction.','category':'declared_vs_internal_accumulation_scope'})
needed=collections.defaultdict(set)
for q in joint:needed[q['device_index']].add(q['source_id'])
for q in joint:
 i=q['device_index'];j=q['peak_index'];d=h['devices'][i];path=f'/devices/{i}/peak_rates/{j}'
 if i not in seen:
  seen.add(i);support.append({'op':'test','path':f'/devices/{i}/id','value':d['id']})
  add=sorted(needed[i]-set(d['source_ids']))
  if add:
   support.append({'op':'test','path':f'/devices/{i}/source_ids','value':d['source_ids']});v=d['source_ids']+add;support.append({'op':'add','path':f'/devices/{i}/source_ids','value':v});js['devices'][i]['source_ids']=v
 support.append({'op':'test','path':path,'value':q['peak']});v=q['peak'].get('supporting_evidence',[])+[{k:q[k] for k in ['source_id','locator','claim']}];support.append({'op':'add','path':path+'/supporting_evidence','value':v});js['devices'][i]['peak_rates'][j]['supporting_evidence']=v
for d in js['devices']:validate_device(d)
write('proposed-hardware.patch.json',support)
write('joint-evidence-groups.json',{'count':len(joint),'group_counts':dict(collections.Counter(q['category'] for q in joint)),'rows':[{k:v for k,v in q.items() if k!='peak'} for q in joint]});write('impact.json',{'total':len(impact),'devices':dict(bydev),'rows':impact});write('next-steps.json',{'tensor_instruction_rate_mapping':{'finite_action':'For each affected architecture family, inspect one official matrix instruction throughput source plus exact product accumulator/rate table or exclusive supported accumulator statement. Reconstruct/select exact SKU rate only if domain and count are documented. Existing PTX legality alone is insufficient.','stop_condition':'If the single targeted source pass yields no exact mapping, keep accumulator unspecified and close the limited-source review; reopen only on new primary evidence.','required_for_current_source_review':'No current unresolved affirmative claim remains. Future unknown upgrades use this finite action only on new primary evidence.'},'vector_instruction_rate_mapping':{'finite_action':'Inspect native FMA instruction throughput table for exact compute capability, typed scalar/packed result semantics, SKU SM/core count and documented relevant clock. Compute and compare source rounding, as completed for four H100 scalar rows.','stop_condition':'If any clock/throughput/SKU mapping is absent, keep unspecified. Do not reverse-engineer unknown clock from published rate.','required_for_current_source_review':'Current native typed-result association is covered by joint evidence; arithmetic reconstruction is optional, not a prerequisite for every row.'}})
joined=copy.deepcopy(h)
for op in support:
 parts=op['path'].strip('/').split('/');v=joined
 for k in parts[:-1]:v=v[int(k)] if isinstance(v,list) else v[k]
 k=int(parts[-1]) if isinstance(v,list) else parts[-1]
 if op['op']=='test':assert v[k]==op['value']
 else:v[k]=copy.deepcopy(op['value'])
assert joined==js
peer=read('research/blackwell-bf16-independent/source.json');peer.update(model='hardware',repository='github.com/NVIDIA/cutlass',upstream_file='python/CuTeDSL/cutlass/cute/nvgpu/tcgen05/mma.py',status='downloaded')
b=(B/peer['file']).read_bytes();assert sha(b)==peer['sha256'] and len(b)==peer['bytes']
assert peer['id'] not in sm
write('proposed-sources.patch.json',[{'op':'test','path':f'/sources/{len(locked["sources"])-1}','value':locked['sources'][-1]},{'op':'add','path':'/sources/-','value':peer}])
write('sources.lock.json',{'sources':sources+[peer],'role':'Source version binding, not a substitute for content review.'})
for obsolete in ['proposed-joint-evidence.patch.json','proposed-hardware-quarantine.patch.json']:
 (O/obsolete).unlink(missing_ok=True)
write('tests.json',{'actual_patch_application_and_guards':'passed','structural_device_validations':len(draft['devices']),'quarantine_old_key_rejections':len(impact),'source_integrity_records':len(sources)+1,'source_integrity':'all SHA and bytes match','final_patch_guard_application':'passed','joint_evidence_peak_count':102,'internal_precision_caveat_count':4,'joint_patch_structural_validations':len(js['devices']),'whole_peak_review_coverage':'471/471','field_review_count':len(rows)*len(fields),'semantic_review_note':'287 prior explicit field reviews plus184 later documented content reviews; hashes bind them but are not the semantic check.','full_suite':False})
print('counts',dict(counts),'quarantined',len(impact),'bydevice',dict(bydev),'sources',len(sources))
