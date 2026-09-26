#!/usr/bin/env python3
"""Validate chapter structure, evidence links, figures, formulas and generated edition."""
from pathlib import Path
from urllib.parse import unquote,urlsplit
import hashlib,json,re,math,xml.etree.ElementTree as ET
import numpy as np
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
import sys;sys.path.insert(0,str(HERE.parent))
from preview_output import preview_path
md=HERE.parent/'05-算子与运行时.md';s=md.read_text();outline=next(p for p in [ROOT/'outlines'/md.name,ROOT/'archive/outlines'/md.name] if p.exists()).read_text();page=preview_path(md).read_text();errors=[]
def check(ok,msg):
 if not ok:errors.append(msg)
heads=lambda t:re.findall(r'^#{2,3} (5\.\d+(?:\.\d+)?) ',t,re.M)
check([h for h in heads(s) if h in set(heads(outline))]==heads(outline),'outline section numbering/order')
check(re.findall(r'^> \*\*实验 (5-\d+)',s,re.M)==[f'5-{i}' for i in range(1,10)],'nine ordered exercises')
check(re.findall(r'^> \*\*实验 (5-\d+) · 核心',s,re.M)==['5-2','5-8','5-9'],'core exercises')
figure_count=len(json.loads((HERE/'figure-index.json').read_text()))
check(len(re.findall(r'^!\[图 5-',s,re.M))==figure_count,'all illustrations')
check(len(re.findall(r'^\*图 5-\d+：',s,re.M))==figure_count,'all external captions')
check(len(re.findall(r'<img ',page))==figure_count,'all embedded images')
check(re.findall(r'^!\[图 (5-\d+)',s,re.M)==[f'5-{i}' for i in range(1,figure_count+1)],'figure reading order')
check(re.findall(r'^\*\*例 (5-\d+)',s,re.M)==[f'5-{i}' for i in range(1,13)],'twelve ordered worked examples')
check(s.index('## 习题与配套实验')<s.index('> **实验 5-1'),'exercises after main exposition')
check(s.index('### 5.6.1 热点占比')<s.index('### 5.6.3 综合案例'),'principle before request case')
check('MATHPLACEHOLDER' not in page,'rendered formulas')
links=0
for u in re.findall(r'\]\(([^)]+)\)',s):
 if re.match(r'\w+:|//',u):continue
 parts=urlsplit(u);p=(md.parent/unquote(parts.path)).resolve();check(p.exists(),'link '+u);links+=1
 if parts.fragment and p.suffix=='.md':check(f'id="{unquote(parts.fragment)}"' in p.read_text() or unquote(parts.fragment) in p.read_text(),'anchor '+u)
refs=set(re.findall(r'\[\^([^\]]+)\](?!:)',s));defs=set(re.findall(r'^\[\^([^\]]+)\]:',s,re.M));check(refs==defs,'footnote definitions')
for name in ['sources.json','manifest.json']:
 for entry in json.loads((HERE/name).read_text())['sources' if name=='sources.json' else 'outputs']:
  p=ROOT/entry['path'];check(hashlib.sha256(p.read_bytes()).hexdigest()==entry['sha256'],'hash '+entry['path'])
for p in HERE.glob('figure-*.svg'):
 tree=ET.parse(p);texts=' '.join(tree.getroot().itertext());check(not re.search(r'图\s*\d+[-－]\d+',texts),'number inside '+p.name)
check(not json.loads((HERE/'figure-layout-check.json').read_text())['text_extent_warnings'],'figure text extents')
# Independent arithmetic and semantic checks support the printed examples.
M,K,N=1024,4096,12288
check(2*(M*K+K*N+M*N)==128*2**20,'minimum bytes')
for b,cap,flow in [(32,8,6168),(64,24,3096),(128,80,1560)]:
 check(2*b*32+2*32*b+4*b*b==cap*1024,'tile capacity')
 check(2*M*K*(N//b)+2*K*N*(M//b)+2*M*N==flow*2**20,'tile traffic')
check(5*24==120 and 3*24==72,'pointwise bytes')
# RTX PRO 6000 (compute capability 12.x): 99 KB = 101,376 bytes of shared memory per thread block.
for b,a,flow in [(1,128,260),(64,82,404),(128,53,624)]:
 size=lambda a:2*a*128+2*b*128+4*a*b+4*a*128+12*a
 check(size(a)<=101376<size(a+1),'attention capacity')
 check(4*8192*128*(1+math.ceil(8192/a))==flow*2**20,'attention traffic')
rng=np.random.default_rng(5);q=rng.normal(size=(7,4));k=rng.normal(size=(11,4));v=rng.normal(size=(11,3));scores=q@k.T/2
weights=np.exp(scores-scores.max(axis=1,keepdims=True));reference=(weights@v)/weights.sum(axis=1,keepdims=True)
for block in [1,3,11]:
 m=np.full(7,-np.inf);l=np.zeros(7);u=np.zeros((7,3))
 for start in range(0,11,block):
  sub=scores[:,start:start+block];new=np.maximum(m,sub.max(axis=1));r=np.exp(m-new);p=np.exp(sub-new[:,None]);l=r*l+p.sum(axis=1);u=r[:,None]*u+p@v[start:start+block];m=new
 check(np.allclose(u/l[:,None],reference,rtol=1e-12,atol=1e-12),'online softmax block '+str(block))
# Added exposition: boundary rereads, double-buffer lifetimes and amortization.
check(32+16+12*16+32*6+12==444,'separate quantization traffic')
check(32+12*32+32*6+12==620,'fused quantization traffic')
check(math.isclose(20-15*(2/3),10),'workload composition threshold')
check(math.isclose(600/(5e-6),120_000_000),'tuning calls to payback')
check(math.isclose(15e-6*1.792e12/2/2**20,12.817382812500002) and round(15e-6*1.792e12/2/2**20,1)==12.8,'graph copy payload threshold (RTX PRO 6000)')
check(round(4*2**20/1.792e12*1e6,1)==2.3 and round(25+4*2**20/1.792e12*1e6,1)==27.3 and round(32*2**20/1.792e12*1e6,1)==18.7 and round(25+32*2**20/1.792e12*1e6,1)==43.7,'graph copy example times')
check(round(15e-6*1008e9/2/2**20,2)==7.21,'graph copy exercise threshold (RTX 4090)')
check(round(64*2**20/64e9*1e3,2)==1.05 and round(32*2**20/64e9*1e3,2)==0.52,'H2D over PCIe Gen5 x16')
# 5.1.5 / 5.3.2: one K tile on one H100 SM (3.35 TB/s and 989.4 TFLOP/s split over 132 SMs).
COPY_US=32768*132/3.35e12*1e6;COMPUTE_US=2097152*132/989.4e12*1e6
check(round(COPY_US,2)==1.29 and round(COMPUTE_US,2)==0.28 and round(COPY_US/COMPUTE_US,1)==4.6 and round(989.4/3.35)==295,'per-SM copy and compute')
check(round(4*(COPY_US+COMPUTE_US),2)==6.28 and round(4*COPY_US+COMPUTE_US,2)==5.44 and round(1-(4*COPY_US+COMPUTE_US)/(4*(COPY_US+COMPUTE_US)),2)==.13,'double buffer example')
figdata=json.loads((HERE/'figure-data.json').read_text())
for mode,end in [('serial',4*(COPY_US+COMPUTE_US)),('double_buffer',4*COPY_US+COMPUTE_US)]:
 events=figdata['5-6'][mode]
 check(math.isclose(max(e['start']+e['duration'] for e in events),end),'timeline completion '+mode)
 for tile in range(4):
  cp=next(e for e in events if e['tile']==tile and e['kind']=='copy')
  comp=next(e for e in events if e['tile']==tile and e['kind']=='compute')
  check(cp['start']+cp['duration']<=comp['start'],'copy before consumption')
  if tile>=2:
   prev=next(e for e in events if e['tile']==tile-2 and e['kind']=='compute')
   check(cp['start']>=prev['start']+prev['duration'],'slot lifetime before reuse')
 for kind in ['copy','compute']:
  ordered=sorted((e for e in events if e['kind']==kind),key=lambda e:e['start'])
  check(all(a['start']+a['duration']<=b['start'] for a,b in zip(ordered,ordered[1:])),'single resource exclusivity')
# 5.5.4 on RTX PRO 6000: projection at 503.8 TFLOP/s, SiLU at 1792 GB/s with 4 bytes per element.
prod=2*64*4096*12288/503.8e12*1e6;consume=64*12288*4/1792e9*1e6
persist_all=json.loads((ROOT/'calculations/results/persistent-tiles-rtxpro6000.json').read_text());persist=persist_all['summary'];persist_scenario=persist_all['scenario']
check(math.isclose(2*5+8*(prod+consume),persist['barrier_finish_ns']/1000),'coarse task completion')
task=(persist_scenario['task_dispatch_ns']+persist_scenario['event_publish_ns'])/1000
check(task==.52,'measured task overhead')
check(math.isclose(5+8*(prod+task)+consume+task,persist['persistent_finish_ns']/1000),'persistent task completion')
check([round(prod,1),round(consume,2),round(prod+task,1),round(consume+task,2),round(2*5+8*(prod+consume)),round(5+8*(prod+task)+consume+task),round(persist['hypothetical_speedup'],1)]==[12.8,1.76,13.3,2.28,126,114,1.1],'persistent printed values')
check(round(5+7*consume-9*task,1)==12.6 and round(7*consume,1)==12.3 and round(9*task,1)==4.7,'persistent saving decomposition')

sync=json.loads((ROOT/'calculations/sources/opentallas/blackwell-sync-latency.json').read_text());w=sync['weight_stream_chain']
check(w['exposed_per_boundary_us']['dynamic_row_claim']==[0.74,1.06] and [round(x,1) for x in w['exposed_per_boundary_us']['fixed_tiles_prefetch_8_rows']]==[1.2,2.3] and round(sum(w['stream_only_us_per_product'])/2)==21,'weight-stream boundary costs')
check(round(sync['boundaries_ns']['cuda_graph_gap_empty_kernels'],-1)==430 and round(sync['boundaries_ns']['pdl_chain'],-1)==370,'graph and PDL gaps')
check(round(persist_scenario['event_publish_ns'],-1)==round(sum(sync['boundaries_ns']['handoff_release_acquire'])/2,-1) and 126<=persist_scenario['task_dispatch_ns']*1<=150,'task costs from measured handoff and atomic')

# Check newly explained thresholds and the actual RMSNorm traffic objects.
check(math.isclose(1560/3096/.4,1.25968992248062),'tile bandwidth reversal')
input_bytes=1024*4096*2;gamma_per_row_bytes=1024*4096*2;output_bytes=input_bytes
partial_bytes=1024*8*4;inverse_bytes=1024*4
fused_bytes=input_bytes+gamma_per_row_bytes+output_bytes
split_bytes=fused_bytes+input_bytes+2*partial_bytes+inverse_bytes+8*inverse_bytes
check(fused_bytes==25165824 and split_bytes==33656832,'RMSNorm input/gamma/output and split exchanges')
check(math.isclose(3.5/1.5,7/3),'two-block softmax example')
check([100*(20+20),20+100*20,100*20+5,5+100*5]==[4000,2020,2005,505],'host pipeline regimes')
dag=figdata['5-16'];computed=[dag['prepare_us']+max(h,dag['branch_B_us'])+dag['finish_us'] for h in dag['branch_A_us']]
check(computed==dag['completion_us']==[80,60],'critical path diagram')
check(10+max(15,90)+10==110,'contention scenario')
# Check the new mechanism diagrams against the equations used in the text.
check(set(figdata)=={f'5-{i}' for i in range(1,18)}|{'reuse_steps','tile_working_set','tile_residency','fusion_path','buffer_slots','attention_storage','sm_residency','warp_pipeline','reduction_order'},'complete stable figure data identifiers')
bank=figdata['5-3']
check([len(set(x)) for x in bank['column_banks']]==[1,32],'bank conflict versus distributed requests')
place={'stride32':lambda r,c:r*32+c,'stride33':lambda r,c:r*33+c,'swizzle':lambda r,c:r*32+(c^r)}
columns={k:{len({f(r,c)%32 for r in range(32)}) for c in range(32)} for k,f in place.items()}
check(columns=={'stride32':{1},'stride33':{32},'swizzle':{32}},'swizzle spreads a column like padding does')
check((32*33*4,32*32*4)==(4224,4096),'padding costs the bytes quoted in the text')
check(figdata['5-4']['segments']*figdata['5-4']['partial_elements']==4096,'split reduction covers one row')
order=figdata['reduction_order'];reduction=json.loads((ROOT/'calculations/results/reduction-order.json').read_text())
check(order['splits']==[1,2,4,8,16,32] and order['width']==4096,'reduction order ladder covers one row')
check([round(v,1) for v in order['offset_ulp'][:4]]==[-175.2,-109.2,-55.2,-9.2],'reduction order distances quoted in the text')
check(order['total_ulp_gap']==166 and order['scale_ulp_gap']==-59 and order['first_output_ulp_gap']==-50,'partition shift propagates to scale and output')
check((order['merge_orders'],order['distinct_merge_results'])==(math.factorial(8),3),'every merge order of eight partial sums')
check(reduction['associativity']['left']==1.0 and reduction['associativity']['right']==1.0+2.0**-23,'associativity counterexample separates the groupings')
check(np.allclose(figdata['5-4']['traffic_MiB'],[fused_bytes/2**20,split_bytes/2**20]),'reduction diagram traffic')
for b,a,traffic,updates in zip(*[figdata['5-8'][k] for k in ['kv_rows','q_rows','traffic_MiB','updates']]):
 check(updates==math.ceil(8192/a)*math.ceil(8192/b),'attention diagram update counts')
graph=figdata['5-13']
check(np.allclose(np.array(graph['prepare_us'])+graph['copy_us']+np.array([graph['compute_us']]*3),graph['completion_us']),'graph-copy time components')
check(np.allclose(figdata['5-15']['completion_us'],[2*5+8*(prod+consume),5+8*(prod+task)+consume+task]),'persistent diagram time components')

# New diagrams must preserve the shared capacity, traffic and lifetime models.
index=json.loads((HERE/'figure-index.json').read_text())
check([int(str(z['number']).split('-')[-1]) for z in index]==list(range(1,figure_count+1)),'index matches caption order')
check(all((HERE/Path(z['asset']).name).with_suffix('.pdf').exists() for z in index),'all figures use revised layout')
layout=json.loads((HERE/'teaching-layout-check.json').read_text())
check(len(layout)==figure_count and all(z['width_pt']==420 and z['min_label_pt']>=11 and not z['text_extent_warnings'] for z in layout),'book-size revised labels and extents')
for z in index:
 check((HERE/Path(z['asset']).name).with_suffix('.pdf').exists(),'print PDF '+z['asset'])
res=figdata['tile_residency']
check(res['budget_KiB']==100 and [res['budget_KiB']//(v+res['reserve_KiB_per_block']) for v in res['working_set_KiB']]==res['resident_sets']==[4,1],'resident working-set capacity bound')
check([100//(32+1),100//(96+1)]==[3,1] and 96<=99,'double-buffered candidates on RTX PRO 6000')
check((100-2*1)//2==49 and 49-32<32 and 49-32>=16,'two resident blocks leave one 16 KiB queue slot')
work=figdata['tile_working_set'];m,n,k=work['tile']
check(work['input_bytes']==[2*m*k,2*k*n] and work['accumulator_bytes']==4*m*n,'working-set labels versus shape')
att=figdata['attention_storage']
check(4*att['L']**2/2**20==att['SP_each_MiB'] and 4*att['SP_each_MiB']==att['SP_write_read_MiB'],'attention intermediates versus dimensions')
check(figdata['buffer_slots']['reuse_A_us']==next(e['start'] for e in figdata['5-6']['double_buffer'] if e['kind']=='copy' and e['tile']==2),'snapshots match full timeline')

# 5.1.5: residency, latency hiding and MMA counts reproduce calculations/results/sm-occupancy-*.json.
sm=json.loads((ROOT/'calculations/results/sm-occupancy-book-tile.json').read_text());res=figdata['sm_residency']
check(res['blocks_by_limit']==sm['residency']['blocks_by_limit']=={'threads':8,'registers':2,'shared_memory':2,'blocks':32},'SM residency limits')
check(res['resident_blocks']==sm['summary']['resident_blocks']==2 and res['resident_warps']==16 and math.isclose(res['occupancy'],.25),'SM occupancy')
check(res['shared_left_bytes']==233472-2*(98304+1024)==34*1024,'shared memory left after two blocks')
check(math.isclose(3.35e12*600e-9/132,sm['summary']['needed_bytes_in_flight_per_sm']) and 16*4*32*16==sm['summary']['available_bytes_in_flight_per_sm']==32768,'Little law bytes in flight')
check(math.isclose(32768/sm['summary']['needed_bytes_in_flight_per_sm'],2.1519283582089552) and sm['latency_hiding']['minimum_resident_warps_to_cover']==8,'latency coverage')
check((128//16)*(128//8)*(64//16)==512==sm['summary']['mma_instructions_per_tile'] and 512*4096==2*128*128*64,'MMA instructions per tile')
acc=json.loads((ROOT/'calculations/results/sm-occupancy-register-accumulator.json').read_text())
check(acc['residency']['blocks_by_limit']=={'threads':8,'registers':2,'shared_memory':6,'blocks':32} and acc['summary']['binding_limits']==['registers'],'accumulator in registers')
slow=json.loads((ROOT/'calculations/results/sm-occupancy-latency-1000ns.json').read_text())
check(not slow['summary']['covers_latency'] and slow['latency_hiding']['minimum_resident_warps_to_cover']==25 and math.isclose(slow['latency_hiding']['coverage_ratio'],16384/25378.78787878788),'latency flip condition')
wp=figdata['warp_pipeline']
check(math.isclose(wp['completion_us'],4*COPY_US+COMPUTE_US) and np.allclose(wp['full_barrier_us'],[COPY_US*i for i in range(1,5)]) and np.allclose(wp['empty_barrier_us'],[COPY_US+COMPUTE_US,2*COPY_US+COMPUTE_US]),'warp pipeline barriers')
for c,k in zip(wp['copies'],wp['computes']):check(c['start']+c['duration']<=k['start'] and c['slot']==k['slot']==c['tile']%2,'copy before compute')
for t in range(2,4):check(wp['copies'][t]['start']>=wp['computes'][t-2]['start']+wp['computes'][t-2]['duration'],'slot freed before refill')
check(2*64*64*2+4*64*64==32768 and 233472//(32768+1024)==6 and 65536//(256*128)==2 and 65536//(256*64)==4,'64x64 tile exercise limits')
# Exercise arithmetic: changed inputs require generalization of the worked examples.
m,n,k=64,128,32
check(2*m*k+2*k*n+4*m*n==44*1024,'rectangular tile exercise capacity')
check(2*M*K*(N//n)+2*K*N*(M//m)+2*M*N==2328*2**20,'rectangular tile exercise traffic')
bytes_saved_per_row=(156-60)*2**20/1024
check(91*bytes_saved_per_row/1.792e12<5e-6<92*bytes_saved_per_row/1.792e12,'fusion overhead exercise integer threshold')
attn_capacity=lambda a:2*a*128+2*2*64*128+4*a*64+4*a*128+12*a
check(attn_capacity(66)<=101376<attn_capacity(67),'attention prefetch exercise capacity')
check(math.ceil(8192/66)==125 and 4+125*4==504,'attention prefetch exercise traffic')
check(math.isclose((.5*3.5+5)/(.5*1.5+1),27/7),'three-block softmax exercise')
check(math.isclose(11-5*.2,10),'shape dispatch exercise threshold')
# A small tiled GEMM with ragged boundaries, preserving the explicit output cast.
a=rng.normal(size=(5,7));w=rng.normal(size=(7,9));out=np.zeros((5,9))
for i in range(0,5,3):
 for j in range(0,9,4):
  acc=np.zeros((min(3,5-i),min(4,9-j)))
  for k0 in range(0,7,2):acc+=a[i:i+3,k0:k0+2]@w[k0:k0+2,j:j+4]
  out[i:i+3,j:j+4]=acc
check(np.allclose(out,a@w,rtol=1e-12,atol=1e-12),'ragged tiled loop')
check(abs(1/(1+math.exp(-1))-1/(1+math.exp(1))-.46211715726)<1e-10,'illegal early activation counterexample')
spec=json.loads((ROOT/'calculations/results/specialization-medium.json').read_text())['specialization_policies']
for r,winner in [(64,'generic'),(65,'bucket'),(89,'bucket'),(90,'specialized')]:check(min(spec,key=lambda z:z['prepare_ns']+r*z['cohort_execution_ns'])['policy']==winner,'specialization threshold '+str(r))
trace=json.loads((ROOT/'experiments/ch05/05-08/results/trace-analysis.json').read_text())['ranges'][:4]
check([z['kernel_count'] for z in trace]==[18,15,18,15],'trace kernel counts')
check([z['launch_api_count']-z['graph_launch_count'] for z in trace]==[18,15,0,0],'trace kernel launch distinction')
report={'status':'passed' if not errors else 'failed','sections':len(re.findall(r'^## 5\.\d+ ',s,re.M)),'subsections':len(re.findall(r'^### 5\.\d+\.\d+ ',s,re.M)),'exercises':9,'worked_examples':12,'figures':figure_count,'local_links':links,'footnotes':len(defs),'han_characters':len(re.findall(r'[\u4e00-\u9fff]',s)),'numerical_checks':'worked-example thresholds; RMSNorm input/gamma traffic; rectangular tile and prefetch exercises; critical path; tile capacity/traffic; quantization rereads; double-buffer dependencies and slot lifetimes; workload and payback thresholds; graph payload limit; persistent task schedule; attention budget; online softmax; ragged GEMM; activation counterexample; specialization thresholds; trace counts','errors':errors}
(HERE/'validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(report,ensure_ascii=False,indent=2));raise SystemExit(bool(errors))
