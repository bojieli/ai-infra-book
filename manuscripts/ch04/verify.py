#!/usr/bin/env python3
"""Check chapter structure, provenance, figure data, numerical derivations and reading artifacts."""
from pathlib import Path
import hashlib,json,re,math,urllib.parse,xml.etree.ElementTree as ET
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];md=HERE.parent/'04-加速器架构.md';s=md.read_text();outline=next(p for p in [ROOT/'outlines'/md.name,ROOT/'archive/outlines'/md.name] if p.exists()).read_text();errors=[];checks=0

def check(ok,msg):
 global checks
 checks+=1
 if not ok:errors.append(msg)
def load(path):return json.loads((ROOT/path).read_text())
def calc(n):return load('calculations/results/'+n+'.json')
def close(a,b):return math.isclose(a,b,rel_tol=1e-10,abs_tol=1e-8)
def heads(t):return re.findall(r'^#{2,3} (4\.\d+(?:\.\d+)?) ',t,re.M)
check([h for h in heads(outline) if h in set(heads(s))]==[h for h in heads(s) if h in set(heads(outline))],'outline section numbering/order')
check(re.findall(r'\*\*实验 4-(\d+)',s)==list(map(str,range(1,9))),'exercise identities')
check(re.findall(r'\*\*实验 (4-\d+) · 核心',s)==['4-1','4-4','4-5'],'core selection')
check(len(re.findall(r'\*\*例 4-\d+',s))==3,'worked examples')
figs=re.findall(r'!\[[^\]]*\]\((ch04/[^)]+\.svg)\)',s)
index=json.loads((HERE/'figure-index.json').read_text());check(figs==[z['asset'] for z in index],'Figure index matches reading order');check(re.findall(r'^\*图 (4-\d+)',s,re.M)==[z['figure'] for z in index],'Caption sequence')
check(not re.search(r'(?<!提)供数',s),'opaque terminology');check('配图计划' not in s,'unfinished figure placeholder')
for p in [md,*HERE.glob('*.md')]:
 for u in re.findall(r'\]\(([^)]+)\)',p.read_text()):
  v=urllib.parse.urlsplit(u)
  if not v.scheme and v.path:
   target=(p.parent/urllib.parse.unquote(v.path)).resolve()
   if target==HERE/'validation.json':continue  # This run writes the report.
   check(target.exists(),'missing local link '+u)
refs=set(re.findall(r'\[\^([^\]]+)\](?!:)',s));defs=set(re.findall(r'^\[\^([^\]]+)\]:',s,re.M));check(refs==defs,'footnotes mismatch')
for file,key in [('sources.json','sources'),('manifest.json','outputs')]:
 for z in json.loads((HERE/file).read_text())[key]:
  p=ROOT/z['path'];check(p.exists() and hashlib.sha256(p.read_bytes()).hexdigest()==z['sha256'],'hash '+z['path'])
for p in HERE.glob('figure-*.svg'):
 r=ET.parse(p).getroot();text=' '.join(''.join(e.itertext()) for e in r.iter() if e.tag.endswith('}text'))
 check(not re.search(r'图\s*\d+\s*[-−]\s*\d+',text),'embedded caption '+p.name)
check(not json.loads((HERE/'figure-layout-check.json').read_text())['outside_canvas_text'],'outside canvas labels')
m=json.loads((HERE/'math-validation.json').read_text());check(not m['errors'],'KaTeX errors')
for r in json.loads((HERE/'teaching-browser-validation.json').read_text()):
 check(r['width']==r['scrollWidth'] and len(r['images'])==len(figs) and all(i['loaded'] for i in r['images']) and not r['mathErrors'] and not r['brokenAnchors'],'browser rendering')
layout=json.loads((HERE/'teaching-layout-validation.json').read_text())+json.loads((HERE/'evolution-layout-validation.json').read_text())
check(len(layout)==len(figs) and all(z['width_pt']==420 and z['min_label_pt']>=11 and not z['text_extent_warnings'] for z in layout),'book-size figure typography')
# Closed forms reconstructed independently of the calculation modules.
for M in [1,256]:
 q=calc(f'projection-qwen3-8b-rtx4090-b{M}')['summary'];F=2*M*4096**2;V=2*(M*4096+4096**2+M*4096)
 for key,value in [('matrix_flops',F),('cold_memory_payload_bytes',V),('arithmetic_intensity_flops_per_byte',F/V),('compute_service_seconds',F/165.2e12),('memory_service_seconds',V/1.008e12),('roofline_lower_bound_seconds',max(F/165.2e12,V/1.008e12))]:check(close(q[key],value),'Q projection '+key)
check(36*2*8*128*2==147456,'KV coefficient');check(147456*8192==1207959552,'KV 8K');check(math.ceil(1.008e12*500e-9/128)==3938 and math.ceil(1.792e12*500e-9/128)==7000 and math.ceil(1.792e12*800e-9/128)==11200,'outstanding transactions')
for n,req in [('rtx4090-n128',3938),('rtx4090-n4096',3938),('rtx5090-n4096',7000),('rtx5090-l800',11200)]:check(calc('window-qwen3-8b-'+n)['summary']['required_transactions']==req,'window result '+n)
check(round(calc('window-qwen3-8b-rtx5090-n4096')['summary']['effective_bandwidth_upper_bytes_per_second']/1.008e12-1,2)==.04,'RTX 5090 window gain')
check(close(1207959552/(128*128/500e-9)*1e3,36.864),'low concurrency ms')
check(math.ceil(15134641792/(2*1e9*100e-6))==75674,'minimum lanes');check(math.ceil(15134641792/(2*1e9*40e-6*.6))==315306,'constrained lanes')
check(20000000/(.5/1e6)==40000000000000,'break-even volume');check(math.ceil(4e13/(10000*.5*31536000))==254,'break-even devices')
d=json.loads((HERE/'figure-data.json').read_text());fa=calc('fa4-qwen8-resource-balance')['scenarios'][:4]
for row,scenario in zip(d['4-4']['service_cycles'],fa):
 expected=[scenario['cycles'][k]['numerator']/scenario['cycles'][k]['denominator'] for k in ['matrix','smem','exp']];check(row==expected,'FA4 plot source')
check(d['4-9']['input_rows']==calc('attention-input-base')['rows'],'pipeline source')
check(d['4-14']['measured_projection']==load('experiments/ch04/04-06/results/projection-summary.json'),'measured plot source')
check(d['4-14']['traffic']==load('experiments/ch04/04-06/results/projection-traffic.json')['rows'],'counter source')
check(d['4-7']['interface_bytes_per_second']==[1.008e12,1.792e12] and d['4-7']['minimum_requests']==[math.ceil(bw*500e-9/128) for bw in d['4-7']['interface_bytes_per_second']],'concurrency thresholds')
for bw,curve in zip(d['4-7']['interface_bytes_per_second'],d['4-7']['bandwidth_upper_bytes_per_second']):
 check(all(close(v,min(bw,n*128/500e-9)) for n,v in zip(d['4-7']['requests'],curve)),'concurrency bandwidth curve')
# Teaching counterfactuals: preserve exact integer boundaries before rounding prose.
weight=16381470720;workspace=2*2**30;kv=147456*8192
check((24e9-weight-workspace)//kv==4 and (24e9-weight-workspace)//(2*kv)==2,'24 GB request boundary')
check(256*16/(8*64)==8 and 64*8==512,'MoE padded work')
check(32+64<=96 and 2*32+64>96 and 3*32<=96,'input and accumulator capacity')
check(close(64*2**20/32e9*1e3,2.097152) and close(64*2**20/1.008e12*1e6,66.57625396825397),'host and GPU transfers')
b2,a3=json.loads((HERE/'teaching-data.json').read_text())['die_locality']['cases']
check(close(b2['remote_ms'],32*2**30/4e12*1e3) and close(b2['overlapped_ms'],b2['split_ms']),'B200 die path')
check(close(a3['remote_ms'],32*2**30/270e9*1e3) and close(a3['split_ms'],32*2**30/1.6e12*1e3) and close(a3['activation_us'],64*2**20/270e9*1e6),'910C die path')
check(math.ceil(4e13/(10000*.5*31536000/2))==508,'half-year break-even')
check(math.floor(d['4-12']['active_weight_bytes']/d['4-12']['kv_bytes_per_request'])+1==13,'integer KV crossing')
for payload,row in zip(d['4-11']['payload_bytes'],d['4-11']['total_us']):
 check(all(close(t,2+payload/r*1e6) for t,r in zip(row,d['4-11']['one_way_bytes_per_second'])),'message serialization')
for (n,mode),wall,dram in zip(d['4-14']['display_conditions'],d['4-14']['wall_us'],d['4-14']['dram_read_mib']):
 measured=next(r for r in d['4-14']['measured_projection'] if r['device']=='cuda' and r['m']==n and r['mode']==mode)
 counter=next(r for r in d['4-14']['traffic'] if r['m']==n and r['mode']==mode)
 check(wall==measured['wall_median_us'] and dram==counter['totals']['dram__bytes_op_read.sum']/2**20,'time/traffic condition alignment')
# Reconstruct the six added diagrams from dimensions and byte counts.
q=d['4-1'];check(q['weight_bytes']==4096**2*2 and q['weight_bytes_per_row']==[4096**2*2//m for m in q['rows']],'reuse diagram')
q=d['4-3'];check(q['assignments']==64*8 and q['padded_rows']==[e*math.ceil(r/16)*16 for e,r in zip(q['experts'],q['rows_per_expert'])],'expert padding diagram')
q=d['4-6']
for row in q['cases']:
 expected=16381470720+2*2**30+row['requests']*row['context_multiplier']*147456*8192
 check(row['total_bytes']==expected,'capacity diagram bytes')
 check((expected<=q['capacity_bytes'])==(row['requests']!=5),'capacity diagram boundary')
q=d['4-8'];check(q['payload_bytes']==128*256 and q['address_span_bytes']==127*8192+256 and q['row_stride_bytes']==8192 and q['read_bytes_per_row']==256 and q['rows']==128,'layout diagram')
q=d['4-10'];check(q['cases']==json.loads((HERE/'teaching-data.json').read_text())['die_locality']['cases'],'locality diagram')
q=d['4-13'];check(q['rows']==list(range(1,257)),'time curve row range')
for rows,tc,tm in zip(q['rows'],q['compute_us'],q['memory_us']):
 check(close(tc,2*rows*4096**2/165.2e12*1e6) and close(tm,2*(4096**2+2*rows*4096)/1.008e12*1e6),'time curve '+str(rows))

# Independent tick simulation for the newly derived minimum-slot examples.
td=json.loads((HERE/'teaching-data.json').read_text())
def simulate(slots,compute,latency):
 issued=[]; starts={}; ends={}; issue_free=0; compute_free=0; next_compute=0; owners=[None]*slots
 for t in range(5000):
  for slot,owner in enumerate(owners):
   if owner is not None and ends.get(owner)==t:owners[slot]=None
  if len(issued)<4 and t>=issue_free:
   i=len(issued);slot=i%slots
   if owners[slot] is None:
    owners[slot]=i;issued.append((t,t+64+latency));issue_free=t+64
  if next_compute<len(issued) and t>=compute_free and t>=issued[next_compute][1]:
   starts[next_compute]=t;ends[next_compute]=t+compute;compute_free=t+compute;next_compute+=1
  if next_compute==4 and t==ends[3]:
   return [(issued[i][0],issued[i][1],starts[i],ends[i]) for i in range(4)]
 raise AssertionError('simulation failed to finish')
for family in ['baseline','matrix_double','longer_latency']:
 for row in td[family]:
  expected=simulate(row['input_slots'],row['compute_ticks'],row['extra_latency_ticks'])
  actual=[(r['issue_start'],r['data_ready'],r['compute_start'],r['compute_end']) for r in row['chunks']]
  check(actual==expected and row['finish_tick']==expected[-1][-1],'independent slot schedule '+family+str(row['input_slots']))
check([r['finish_tick'] for r in td['baseline']]==[1280,768,704,704],'minimum baseline slots')
check([r['finish_tick'] for r in td['matrix_double']]==[1024,576,512,448],'minimum accelerated slots')
check(d['4-9']['displayed_schedules']==td['baseline'][:3],'three-slot figure data')
for n in [178,179]:
 F=2*n*4096**2;V=2*(4096**2+2*n*4096)
 check((F/165.2e12>V/1.008e12)==(n==179),'Roofline integer boundary '+str(n))
check(31<1e12/32e9<=32,'upload reuse threshold')
check(109*8192<2e-6*450e9<110*8192,'message-size threshold')
check(5*kv*.9<24e9-weight-workspace,'capacity thought exercise')
check(close(64*2**20/270e9*1e6,248.55134814814815),'locality activation exchange')
md8=td['measured_decode'];check(close(md8['bound_ms'],16344770560/1.792e12*1e3) and md8['measured_ms']==25.83 and round(md8['fraction'],3)==.353,'measured decode fraction')
en=td['energy'];check([round(c['mac_breakeven_W'],1) for c in en['calls']]==[155.1,10.7] and [round(c['rtx_mJ'],1) for c in en['calls']]==[25.8,19.6],'projection energy')
check([round(x['joules'],2) for x in en['decode_step']]==[7.30,5.24],'decode step energy')
check(td['groq_kv']=={'chip_sram_bytes':220*2**20,'one_request':6,'eight_requests':42,'eight_requests_32k':168,'weights_bf16':72},'Groq chip counts')
# 4.3.2-4.4.4: L2 and synchronisation figures and prose come from the measured excerpt.
sync=load('calculations/sources/opentallas/blackwell-sync-latency.json')
import sys;sys.path[:0]=[str(HERE),str(HERE.parent)]
from sync_figures import ladder_rows
check([r[1] for r in ladder_rows(sync)]==[7,131,365.5,663,1004],'sync ladder values')
ghz=sync['device']['sm_clock_ghz'];check(sync['device']['sms']==188 and sync['device']['l2_mib']==128,'device L2 and SMs')
check(round(340/ghz/5)*5==120 and round(390/ghz/5)*5==135 and sync['l2']['load_round_trip_cycles']==[338,392],'L2 round trip range')
check(sync['l2']['hit_latency_between_processes_cycles']==[354,870],'L2 variation')
check(round(sum(sync['boundaries_cycles']['handoff_release_acquire'])/2,-1)==1050 and round(sum(sync['boundaries_ns']['handoff_release_acquire'])/2,-1)==370,'handoff cycles and ns')
check(round(sum(sync['boundaries_ns']['handoff_no_fence'])/2,-1)==140,'no-fence handoff')
check(sync['boundaries_ns']['pdl_chain']==366 and round(1900/ghz,-1)==660 and sync['all_sm_barrier_breakdown_cycles']['arrive_fence']==460,'all-SM barrier')
check(round(sync['l2']['same_line_all_sms_8_warps_cycles']/sync['l2']['private_line_per_sm_cycles'])==9,'hot line ratio')
check(sync['bandwidth_bytes_per_cycle_per_sm']=={'local_shared_memory':36,'l2':6.9,'distributed_shared_memory':1.3},'DSMEM bandwidth')
check(38083/sync['boundaries_ns']['all_sm_gather_with_vector_fp32_16kib']>10,'cluster exchange slower than L2')
report={'status':'passed' if not errors else 'failed','chapter':4,'sections':7,'subsections':24,'exercises':7,'worked_examples':3,'figures':len(figs),'math_expressions':m['expressions'],'chinese_characters':len(re.findall(r'[\u4e00-\u9fff]',s)),'checks':checks,'errors':errors}
(HERE/'validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(report,ensure_ascii=False,indent=2));raise SystemExit(bool(errors))
