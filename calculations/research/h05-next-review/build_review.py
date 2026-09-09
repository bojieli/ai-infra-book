"""Build independent guarded proposals; never writes shared configuration."""
import copy,hashlib,json,sys
from pathlib import Path
BASE=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(BASE/'src'))
from infra_calc.hardware import validate_device
OUT=Path(__file__).resolve().parent
sha=lambda b:hashlib.sha256(b).hexdigest()
write=lambda n,x:(OUT/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
raw=(BASE/'configs/hardware.json').read_bytes();h=json.loads(raw);draft=copy.deepcopy(h)
oldlock=json.loads((BASE/'configs/sources.lock.json').read_text());sm={s['id']:s for s in oldlock['sources'] if s.get('id')}
new=[]
for sid,name,url,rev in [('nvidia-h100-nvl-product-brief-h05','h100-nvl-product-brief.pdf','https://www.nvidia.com/content/dam/en-zz/Solutions/Data-Center/h100/PB-11773-001_v01.pdf','PB-11773-001_v01 March14 2024'),('nvidia-cuda-programming-guide-12-8-1-h05','cuda-programming-guide-12.8.1.html','https://docs.nvidia.com/cuda/archive/12.8.1/cuda-c-programming-guide/index.html','CUDA12.8.1 archive')]:
 b=(OUT/name).read_bytes();new.append({'model':'hardware','id':sid,'repository':url.split('/')[2],'revision':rev,'upstream_file':url.split('/')[-1],'url':url,'file':str((OUT/name).relative_to(BASE)),'sha256':sha(b),'bytes':len(b),'downloaded_at':'2026-09-09','status':'downloaded','archive_note':'Official original downloaded and relevant table content reviewed in H05 next review; not measured runtime performance.'})
sourceops=[{'op':'test','path':f'/sources/{len(oldlock["sources"])-1}','value':oldlock['sources'][-1]}]+[{'op':'add','path':'/sources/-','value':s} for s in new]
ops=[];audit=[];recon=[]
NVL=new[0]['id'];GUIDE=new[1]['id'];PTX='nvidia-ptx-isa-9-3'
def change(path,value):
 ops.append({'op':'add','path':path,'value':value})
 parts=path.strip('/').split('/');p=draft
 for k in parts[:-1]:p=p[int(k)] if isinstance(p,list) else p[k]
 k=int(parts[-1]) if isinstance(p,list) else parts[-1];p[k]=copy.deepcopy(value)
for i,d in enumerate(h['devices']):
 if d['id'] not in ['h100-nvl-94gb','h100-sxm','h100-pcie-80gb']:continue
 root=f'/devices/{i}';ops.append({'op':'test','path':root,'value':d})
 extra=NVL if d['id']=='h100-nvl-94gb' else GUIDE
 change(root+'/source_ids',d['source_ids']+[extra])
 if d['id']=='h100-nvl-94gb':
  ev={'source_id':NVL,'locator':'Table1 Product Specifications, printed p3 / physical p7, GPU clocks; P1010 SKU210 NVPN699-21010-0210-xxx','gpu_base_mhz':1080,'gpu_boost_mhz':1785,'status':'exact_product_boost_clock','boundary':'Product Boost only; this brief has no per-precision peak-throughput table or separate Tensor clock domains. Does not establish sustained or per-peak actual operating frequency.'}
  change(root+'/clock',ev)
  change(root+'/power_evidence',{'source_id':NVL,'locator':'Table1 printed p3/physical p7, Total board power:400W maximum/default with cable strapped450W or600W; 300W cable strap selects310W maximum/default','power_kind':'maximum_configurable_board_power','condition':'400W selected profile requires450W/600W cable power strap; not measured watts while achieving advertised peak.'})
 for j,p in enumerate(d['peak_rates']):
  pr=f'{root}/peak_rates/{j}';k={q:p[q] for q in ['input_precision','accumulator_precision','execution_unit','sparsity']};row={'device_id':d['id'],'peak':k,'source_rate':p['tera_ops_per_second']}
  if d['id']=='h100-nvl-94gb':
   change(pr+'/clock_evidence',ev);change(pr+'/clock_basis','Official NVL product Base1080/Boost1785MHz; per-precision peak clock and sustained frequency remain unestablished by PB-11773-001_v01 Table1.')
   row.update(clock_status='product_clock_closed_peak_operating_domain_unknown',accumulator_status='unknown_preserved' if p['accumulator_precision']=='unspecified' else 'product_rate_accumulator_mapping_not_closed',reason='NVL brief supplies product clock but no throughput/accumulator table. Generic Hopper instruction legality cannot establish an exact NVL rate.')
  elif p['execution_unit']=='vector' and p['input_precision'] in ['FP32','FP64']:
   smcount=132 if d['id']=='h100-sxm' else 114;mhz=1980 if d['id']=='h100-sxm' else 1755;throughput=128 if p['input_precision']=='FP32' else 64;value=smcount*throughput*mhz*1e6*2/1e12
   assert round(value,1)==p['tera_ops_per_second']
   formula=f'{smcount} SM * {throughput} FMA results/(SM cycle) * {mhz}e6 cycles/s * 2 FLOPs/FMA / 1e12 = {value} TFLOPS; source rounded to {p["tera_ops_per_second"]}'
   evidence=[{'source_id':GUIDE,'locator':'5.4.1 Table4 Throughput of Native Arithmetic Instructions; Compute Capability9.0 column,32-bit or64-bit floating-point add/multiply/multiply-add','claim':f'Native {p["input_precision"]} multiply-add produces {throughput} results per clock per SM; this is instruction throughput, not merely legal operand types.'},{'source_id':PTX,'locator':'9.7.3.6 #floating-point-instructions-fma, fma.rnd.f32 / fma.rnd.f64 signatures, semantics and Notes','claim':f'Scalar FMA addend and destination use {p["input_precision"]}; result rounds to that precision. Internal fused intermediate is not claimed to be a fixed-width accumulator.'},{'source_id':'nvidia-h100','locator':'Table3 printed39–40: exact SKU SM count, FP32/FP64 non-Tensor Boost domain and peak rows; Table4 p41 CC9.0','claim':formula}]
   change(pr+'/supporting_evidence',p.get('supporting_evidence',[])+evidence);row.update(accumulator_status='closed_for_typed_scalar_fma_theoretical_peak_mapping',clock_status='previous_round_explicit_domain_retained',formula=formula,boundary='Published rounded scalar FMA peak reproduced from official instruction throughput and exact SKU clock/SM count; not a measured kernel rate, and not an internal finite-width fused accumulator assertion.');recon.append({'device_id':d['id'],'precision':p['input_precision'],'sm_count':smcount,'fma_results_per_sm_cycle':throughput,'clock_mhz':mhz,'flops_per_fma':2,'computed_tflops':value,'reported_tflops':p['tera_ops_per_second'],'rounded_match':True})
  elif p['execution_unit']=='tensor' and p['input_precision'] in ['FP8','FP16','BF16']:
   row.update(accumulator_status='closed_previous_round_explicit_product_table',clock_status='previous_round_explicit_domain_retained')
  else:
   row.update(accumulator_status='limited_review_mapping_not_closed',clock_status='explicit_domain' if p.get('clock_evidence',{}).get('status')=='explicit_peak_operation_domain' else 'reviewed_table_domain_unknown',reason='For TF32/INT8/FP64 Tensor, Table3 lacks explicit accumulator heading and this pass did not prove exact instruction-rate binding. For FP16/BF16 vector, typed packed arithmetic exists but the product clock domain is not explicit; no clock inferred from matching arithmetic.')
  audit.append(row)
for d in draft['devices']:validate_device(d)
# Independently apply guarded patches.
def apply(obj,patch):
 obj=copy.deepcopy(obj)
 for op in patch:
  p=obj;parts=op['path'].strip('/').split('/')
  for k in parts[:-1]:p=p[int(k)] if isinstance(p,list) else p[k]
  k=parts[-1]
  if isinstance(p,list) and k=='-':assert op['op']=='add';p.append(op['value']);continue
  if isinstance(p,list):k=int(k)
  if op['op']=='test':assert p[k]==op['value']
  else:p[k]=copy.deepcopy(op['value'])
 return obj
assert apply(h,ops)==draft
sl=apply(oldlock,sourceops);ids=[s['id'] for s in sl['sources'] if s.get('id')];assert len(ids)==len(set(ids))
for d,dd in zip(h['devices'],draft['devices']):
 assert [(p['tera_ops_per_second'],p['input_precision'],p['accumulator_precision'],p['execution_unit'],p['sparsity']) for p in d['peak_rates']]==[(p['tera_ops_per_second'],p['input_precision'],p['accumulator_precision'],p['execution_unit'],p['sparsity']) for p in dd['peak_rates']]
selected=[sm[s] for s in ['nvidia-h100','nvidia-h100-page',PTX]]+new
for s in selected:
 b=(BASE/s['file']).read_bytes();assert sha(b)==s['sha256'];assert len(b)==s['bytes']
write('proposed-hardware.patch.json',ops);write('proposed-sources.patch.json',sourceops);write('sources.lock.json',{'sources':selected});write('vector-rate-reconstruction.json',recon);write('field-audit.json',{'reviewed_on':'2026-09-09','input_sha256':sha(raw),'scope':'H100 SXM/PCIe80/NVL94,47 peaks; no global H05 closure','rows':audit,'can_close':['NVL exact product Base/Boost field','Four H100 SXM/PCIe FP32/FP64 scalar FMA typed-result and theoretical-rate mappings'],'cannot_close':['NVL per-precision peak operating clock','NVL FP16/FP8 accumulator choice at advertised rate','NVL BF16/TF32/INT8/FP32 complete product-rate instruction mapping','H100 SXM/PCIe TF32/INT8/FP64 Tensor exact product-rate instruction mapping','H100 SXM/PCIe FP16/BF16 non-Tensor clock-domain association'],'catalog_unchanged_unknowns':True,'scope_note':'Closed scalar FMA mapping concerns typed addend/destination and rounded instruction-rate peak, not finite-width internal fused intermediate. Existing accumulated-precision fields are not changed.'})
write('tests.json',{'hardware_patch_ops':len(ops),'source_patch_ops':len(sourceops),'guards_and_actual_patch_application':'passed','devices_structurally_validated':len(draft['devices']),'source_hash_and_bytes_verified':len(selected),'peak_values_and_keys_preserved':True,'four_scalar_rate_reconstructions':'all round to official product peaks','full_suite_or_runtime_measurement':False})
print('hardware ops',len(ops),'source ops',len(sourceops),'reviewed',len(audit),'validated',len(draft['devices']))
