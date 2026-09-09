#!/usr/bin/env python3
"""Check the archived phase, not completion of the long-running research goal."""
from pathlib import Path
from urllib.parse import urljoin,urlsplit,unquote
from datetime import datetime,timezone
from bs4 import BeautifulSoup
import hashlib,json,re,subprocess,math,csv
ROOT=Path(__file__).resolve().parents[2];errors=[];stats=[];totalbytes=0;pagination_notes=[]
for year,expected in [(2024,37),(2025,61),(2026,135)]:
 d=ROOT/f'references/proceedings/MLSys/{year}';j=json.loads((d/'manifest.json').read_text());papers=j['papers']
 index=ROOT/'references'/j['index']['file'];data=index.read_bytes()
 assert hashlib.sha256(data).hexdigest()==j['index']['sha256']
 official={urljoin(j['index']['url'],a['href']) for a in BeautifulSoup(data,'html.parser').select('a[href]') if '-Abstract' in a['href']}
 assert len(official)==expected==j['expected_papers']==len(papers)
 assert {p['source_page'] for p in papers}==official
 assert len({p['id'] for p in papers})==expected
 for p in papers:
  assert p['status']=='downloaded',(year,p['id'],p['status'])
  for kind in ['landing','pdf']:
   meta=p[kind];b=(ROOT/'references'/meta['file']).read_bytes()
   assert len(b)==meta['bytes'] and hashlib.sha256(b).hexdigest()==meta['sha256']
   if kind=='pdf':assert b.startswith(b'%PDF-');totalbytes+=len(b)
  t=(ROOT/'references'/p['text']).read_text(errors='replace');assert len(t)>600
  pdfpath=ROOT/'references'/p['pdf']['file'];info=subprocess.check_output(['pdfinfo',str(pdfpath)],text=True,stderr=subprocess.PIPE,timeout=15);assert int(re.search(r'^Pages:\s+(\d+)',info,re.M)[1])==p['pages']
  if t.count('\f')!=p['pages']:
   fresh=subprocess.check_output(['pdftotext','-layout',str(pdfpath),'-'],text=True,stderr=subprocess.PIPE,timeout=30);assert fresh==t
   pagination_notes.append({'id':p['id'],'pdf_pages':p['pages'],'text_formfeeds':t.count('\f'),'note':'Fresh extraction is identical; use PDF page numbers with -f/-l or rendered pages, not formfeed offsets.'})
  assert p['abstract'].strip()
 stats.append({'year':year,'pdfs':expected,'pages':sum(p['pages'] for p in papers),'abstracts_screened':sum('screening' in p for p in papers),'selected_sections_read':sum(p['reading_status']=='selected_sections_read' for p in papers)})
for manifest in [*ROOT.glob('references/interviews/*/**/sources.json'),*ROOT.glob('references/framework-history/*/*/sources.json'),*ROOT.glob('references/proceedings/discovery/*/sources.json'),*ROOT.glob('references/proceedings/catalog-review/*/sources.json'),*ROOT.glob('references/proceedings/*/*/selected-sources.json'),ROOT/'references/proceedings/selected-sources.json']:
 for p in json.loads(manifest.read_text()):
  path=ROOT/p['file'] if p['file'].startswith('references/') else manifest.parent/p['file'];b=path.read_bytes()
  assert len(b)==p['bytes'] and hashlib.sha256(b).hexdigest()==p['sha256']
  if 'derived_text' in p:
   t=p['derived_text'];b=(ROOT/t['file']).read_bytes();assert len(b)==t['bytes'] and hashlib.sha256(b).hexdigest()==t['sha256']
  if isinstance(p.get('initial_fetch'),dict):
   t=p['initial_fetch'];b=(ROOT/t['file']).read_bytes();assert len(b)==t['bytes'] and hashlib.sha256(b).hexdigest()==t['sha256']
files=[ROOT/'case-studies/memory-bandwidth-and-concurrency.md',ROOT/'README.md',ROOT/'references/README.md',*ROOT.glob('research/2026-infra-survey/*.md'),ROOT/'case-studies/multi-lora-serving.md',ROOT/'case-studies/cache-and-reconfiguration.md',ROOT/'case-studies/moe-and-startup.md',ROOT/'case-studies/kernel-and-fleet-efficiency.md',ROOT/'case-studies/framework-evolution.md',ROOT/'references/proceedings/README.md',*ROOT.glob('references/proceedings/*/*/README.md'),*ROOT.glob('references/interviews/*/**/README.md'),*ROOT.glob('references/framework-history/*/*/README.md')]
files.append(ROOT/'case-studies/chunking-and-state-transfer.md')
files.append(ROOT/'case-studies/tensor-codec-and-transfer.md')
files.append(ROOT/'case-studies/parallel-switching-and-state.md')
files.append(ROOT/'case-studies/component-utilization-and-overlap.md')
files.append(ROOT/'case-studies/snapshot-residency-and-first-use.md')
files.append(ROOT/'case-studies/stream-order-and-buffer.md')
files.append(ROOT/'references/proceedings/ISCA/2024/closing/README.md')
files.append(ROOT/'case-studies/resource-sharing-and-placement.md')
files.append(ROOT/'case-studies/rl-state-and-reproducibility.md')
files.append(ROOT/'case-studies/rl-scheduling-and-recovery.md')
files.append(ROOT/'case-studies/graph-execution-tradeoffs.md')
files.append(ROOT/'case-studies/collective-paths-and-diagnosis.md')
files.append(ROOT/'case-studies/remote-ordering-and-completion.md')
files.append(ROOT/'case-studies/reward-deadlines-and-feedback.md')
files.append(ROOT/'case-studies/preemptible-rollout-and-weight-readiness.md')
files.append(ROOT/'case-studies/network-planning-and-collectives.md')
files.append(ROOT/'case-studies/checkpoint-layout-and-loading.md')
files.append(ROOT/'case-studies/communication-tuning.md')
files.append(ROOT/'case-studies/workload-and-provisioning.md')
files.append(ROOT/'case-studies/speculative-execution.md')
files.append(ROOT/'case-studies/rollout-tail-and-sampling.md')
files.append(ROOT/'case-studies/weight-offload-execution.md')
files.append(ROOT/'case-studies/memory-criticality-and-tiering.md')
files.append(ROOT/'case-studies/multimodal-stage-placement.md')
files.append(ROOT/'case-studies/evaluation-and-agent-records.md')
files.append(ROOT/'case-studies/pcie-staging-and-numa.md')
files.append(ROOT/'case-studies/kernel-orchestration-and-quantization.md')
files.append(ROOT/'case-studies/cache-tiers-and-routing.md')
files.append(ROOT/'case-studies/structured-generation.md')
files.append(ROOT/'case-studies/retrieval-and-generation.md')
files.append(ROOT/'case-studies/expert-dispatch-and-resizing.md')
files.append(ROOT/'case-studies/cache-events-and-routing.md')
files.append(ROOT/'case-studies/weight-handoff.md')
files.append(ROOT/'case-studies/buffer-capacity-and-data-movement.md')
files.append(ROOT/'case-studies/host-transfer-and-buffer-lifetime.md')
files.append(ROOT/'case-studies/host-policy-and-dispatch.md')
files.append(ROOT/'case-studies/kv-quantization-and-execution.md')
files.append(ROOT/'case-studies/training-offload-and-casting.md')
files.append(ROOT/'references/framework-history/2026-09-08/training-superchip/README.md')
files.append(ROOT/'references/framework-history/2026-09-09/heterogeneous-pipelines/NOTES.md')
files.append(ROOT/'references/framework-history/2026-09-09/sequence-and-npu/NOTES.md')
files.append(ROOT/'references/framework-history/2026-09-09/spindle-wavefront/NOTES.md')
files.append(ROOT/'case-studies/training-compute.md')
files.append(ROOT/'research/2026-infra-survey/qwen-request-accounting/README.md')
files.extend(ROOT/'outlines/extensions'/name for name in ['04-加速器架构.md', '10-训练系统.md', '12-端边云协同.md'])
files.append(ROOT/'case-studies/model-parallelism.md')
files.append(ROOT/'outlines/extensions/06-超节点.md')
links=0
for p in files:
 for url in re.findall(r'\]\(([^)]+)\)',p.read_text()):
  if re.match(r'https?://|mailto:|app:',url):continue
  u=urlsplit(unquote(url.strip('<>')));path=(p.parent/u.path).resolve() if u.path else p;links+=1
  if not path.exists():errors.append(['missing link',str(p.relative_to(ROOT)),url])
ids=re.findall(r'^\| `([^`]+)`',(ROOT/'outlines/source-map.md').read_text(),re.M);assert len(ids)==len(set(ids))
a=json.loads((ROOT/'research/2026-infra-survey/arithmetic.json').read_text());assert a['adapter_mib']==36*16*(4096+4096+4096+1024)*2/2**20==14.625;assert a['independent_100_requests_kv_gib']==100*8192*147456/2**30==112.5
# Check transfer times, finite buffer lifetimes and independent resource lanes.
c=a['host_transfer_teaching'];cfg=json.loads((ROOT/c['config']).read_text())
assert c['block_bytes']==c['tokens']*cfg['hidden_size']*c['element_bytes']==64*2**20
for item in c['cases']:
 t=c['block_bytes']/item['effective_Bps']*1000;assert math.isclose(t,item['copy_ms'])
 assert math.isclose(item['serial_ms'],c['blocks']*(c['prepare_ms']+t+c['compute_ms']))
 rows=item['timeline'];assert len(rows)==c['blocks']
 expected=c['prepare_ms']+c['blocks']*(t+c['compute_ms']) if item['device_slots']==1 else c['prepare_ms']+t+c['compute_ms']+(c['blocks']-1)*max(c['prepare_ms'],t,c['compute_ms'])
 assert math.isclose(item['pipeline_ms'],expected) and math.isclose(rows[-1]['compute'][1],expected)
 assert item['host_pool_bytes']==c['host_slots']*c['block_bytes'] and item['device_pool_bytes']==item['device_slots']*c['block_bytes']
 for i,row in enumerate(rows):
  assert row['block']==i and row['host_slot']==i%c['host_slots'] and row['device_slot']==i%item['device_slots']
  for stage,duration in [('prepare',c['prepare_ms']),('copy',t),('compute',c['compute_ms'])]:
   assert math.isclose(row[stage][1]-row[stage][0],duration)
   if i:assert row[stage][0]>=rows[i-1][stage][1]-1e-9
  assert row['copy'][0]>=row['prepare'][1] and row['compute'][0]>=row['copy'][1]
  if i>=c['host_slots']:assert row['prepare'][0]>=rows[i-c['host_slots']]['copy'][1]-1e-9
  if i>=item['device_slots']:assert row['copy'][0]>=rows[i-item['device_slots']]['compute'][1]-1e-9
# Independent per-bank request service: queue drain versus modular-address count.
bank=a['bank_layout_teaching'];cfg=json.loads((ROOT/bank['config']).read_text())
assert bank['output_payload_bytes']==bank['tokens']*cfg['intermediate_size']*bank['output_element_bytes']==24*2**20
assert bank['separate_reorder_extra_bytes']==2*bank['output_payload_bytes']==48*2**20
assert bank['tile_rows']==bank['tile_cols']==bank['banks']==32
assert bank['scalar_bytes']==4 and bank['words_per_bank_per_cycle']==1
for item in bank['cases']:
 pitch=item['row_pitch_words'];assert item['allocated_bytes']==bank['tile_rows']*pitch*bank['scalar_bytes']
 for axis in ['row','column']:
  for fixed in range(32):
   addresses=[fixed*pitch+lane if axis=='row' else lane*pitch+fixed for lane in range(32)]
   assert len(set(addresses))==32
   queues=[[] for _ in range(32)]
   for address in addresses:queues[address%32].append(address)
   rounds=0
   while any(queues):
    rounds+=1
    for queue in queues:
     if queue:queue.pop(0)
   assert rounds==item[axis+'_service_rounds']
   assert rounds==(1 if axis=='row' else math.gcd(pitch,32))
assert bank['padding_extra_bytes']==bank['cases'][1]['allocated_bytes']-bank['cases'][0]['allocated_bytes']==128
assert bank['padding_extra_fraction']==bank['padding_extra_bytes']/bank['cases'][0]['allocated_bytes']==0.03125
# Main-post provenance: do not recursively match recommended posts or subject dates.
fifth=json.loads((ROOT/'references/interviews/2026-09-08/fifth-pass/reading-proof.json').read_text())
for report in fifth['reports']:
 soup=BeautifulSoup((ROOT/report['file']).read_bytes(),'html.parser')
 raw=next(x.get_text() for x in soup.find_all('script') if x.get_text().startswith('window.__INITIAL_STATE__='))
 data=json.JSONDecoder().raw_decode(raw.split('=',1)[1])[0]['prefetchData']['2']['ssrCommonData']['contentData']
 assert (data['uuid'],data['title'],data['userBrief']['nickname'],data[report['time_field']])==(report['uuid'],report['title'],report['author'],report['time_value'])
 expected=data['title']+'\n'+BeautifulSoup(data['content'],'html.parser').get_text('\n',strip=True)+'\n'
 assert (ROOT/report['body_text']['file']).read_text()==expected
assert fifth['screening_summary']['usable_full_main_posts']==3
# Enumerate the tile traversal, independently of the closed-form traffic formula.
c=a['buffer_capacity_teaching'];cfg=json.loads((ROOT/c['config']).read_text())
M,K,N=c['tokens'],cfg['hidden_size'],cfg['intermediate_size']
assert c['shape']==[M,K,N] and c['flops']==2*M*K*N
compulsory=c['input_bytes']*M*K+c['weight_bytes']*K*N+c['output_bytes']*M*N
assert compulsory==c['compulsory_bytes'] and c['flops']/compulsory==c['compulsory_intensity']
for candidate in c['candidates']:
    m,n,k=candidate['tile'];assert M%m==N%n==K%k==0
    a_reads=w_reads=c_writes=flops=peak=0
    for row in range(0,M,m):
        for col in range(0,N,n):
            accumulator=c['accumulator_bytes']*m*n
            for reduction in range(0,K,k):
                a_block=c['input_bytes']*m*k;w_block=c['weight_bytes']*k*n
                a_reads+=a_block;w_reads+=w_block;flops+=2*m*n*k
                peak=max(peak,accumulator+a_block+w_block)
            c_writes+=c['output_bytes']*m*n
    assert (a_reads,w_reads,c_writes)==(candidate['read_a_bytes'],candidate['read_weight_bytes'],candidate['write_output_bytes'])
    assert flops==c['flops'] and peak==candidate['active_buffer_bytes']
    assert a_reads+w_reads+c_writes==candidate['traffic_bytes']
    assert math.isclose(flops/candidate['traffic_bytes'],candidate['intensity'])
# Expert dispatch: enumerate all integer allocations, then account for transfer
# bottlenecks and gradient collectives independently of the prose examples.
c=a['expert_dispatch_resizing_teaching'];cfg=json.loads((ROOT/c['config']).read_text())
matrices=[(cfg['hidden_size'],cfg['moe_intermediate_size'])]*2+[(cfg['moe_intermediate_size'],cfg['hidden_size'])]
params=sum(m*n for m,n in matrices)
assert params==c['single_expert_parameters'] and 2*params==c['bf16_expert_bytes']==c['flops_per_expert_row']
assert c['top_k']==cfg['num_experts_per_tok'] and c['replicated_expert_rows']<=c['logical_tokens']
rows=c['fixed_rank_rows'];hot=c['replicated_expert_rows']
allocations=[[rows[0]+x,rows[1]+hot-x,*rows[2:]] for x in range(hot+1)]
assert allocations[hot//2]==c['uniform_rank_rows'] and allocations[0]==c['balanced_rank_rows']
assert min(map(max,allocations))==max(c['balanced_rank_rows'])==sum(c['balanced_rank_rows'])//4
assert sum(rows)+hot==c['logical_tokens']*c['top_k']
for key in ['uniform','balanced']:
    flops=max(c[key+'_rank_rows'])*sum(2*m*n for m,n in matrices)
    assert math.isclose(flops/c['effective_flops_per_second']*1000,c[key+'_matrix_ms'])
margin_us=(c['uniform_matrix_ms']-c['balanced_matrix_ms'])*1000
assert c['dispatch_extra_us'][0]<margin_us<c['dispatch_extra_us'][1]
payload=sum(c['bf16_expert_bytes'] for _ in range(c['moves']))
assert payload==c['move_payload_bytes'] and math.isclose(payload/c['critical_link_bytes_per_second']*1000,c['move_lower_bound_ms'])
assert c['exposed_reconfiguration_ms']>=c['move_lower_bound_ms']
assert c['exposed_reconfiguration_ms']/c['saved_per_step_ms']==c['break_even_steps']
assert [h*c['saved_per_step_ms']-c['exposed_reconfiguration_ms'] for h in c['horizons']]==c['net_saved_ms']
total=cfg['num_hidden_layers']*cfg['num_experts']*c['bf16_expert_bytes'];assert total==c['routed_total_bytes']
assert total//c['new_ranks']==c['new_rank_weight_bytes']
added=sum(c['new_rank_weight_bytes'] for _ in range(c['new_ranks']-c['old_ranks']))
assert added==c['added_ranks_weight_bytes'] and math.isclose(added/c['aggregate_transfer_bytes_per_second'],c['added_ranks_transfer_bound_s'])
assert c['gradient_bytes']==4*params and c['gradient_chunk_bytes']*c['gradient_gaps']==c['gradient_bytes']
def ring_send(size,ranks):
    return sum(size/ranks for phase in range(2) for step in range(ranks-1))
assert ring_send(c['gradient_bytes'],c['gradient_dp_ranks'])==c['ring_send_bytes']
for size,key in [(c['gradient_bytes'],'whole_gradient_ms'),(c['gradient_chunk_bytes'],'chunk_gradient_ms')]:
    t=ring_send(size,c['gradient_dp_ranks'])/c['critical_link_bytes_per_second']*1000+c['gradient_collective_start_ms']
    assert math.isclose(t,c[key])
assert 1<c['chunk_gradient_ms']<c['gradient_gap_ms']<c['whole_gradient_ms']
assert math.isclose(c['gradient_gaps']*c['chunk_gradient_ms']-c['whole_gradient_ms'],(c['gradient_gaps']-1)*c['gradient_collective_start_ms'])
proof=json.loads((ROOT/'references/framework-history/2026-09-08/ep-reconfiguration/reading-proof.json').read_text())
assert len(proof['records'])==17 and not proof['downloaded_code_executed']
for record in proof['records']:
    data=(ROOT/record['file']).read_bytes();assert hashlib.sha256(data).hexdigest()==record['sha256']
    for lo,hi in record['read_scope'].get('line_ranges_inclusive',[]):assert 1<=lo<=hi<=len(data.decode().splitlines())
# Independently enumerate each ring round and the two physical legs of each staged transfer.
c=a['pcie_staging_teaching'];cfg=json.loads((ROOT/c['config']).read_text());n=c['ranks']
assert c['input_bytes']==c['tokens']*cfg['hidden_size']*c['element_bytes']
assert c['chunk_bytes']*n==c['input_bytes'] and c['rounds']==2*(n-1)
for candidate in c['cases']:
 dram=[0,0];socket={(0,1):0,(1,0):0};sent=[0]*n;received=[0]*n;payload=0
 ring=candidate['ring'];assert sorted(ring)==list(range(n))
 for phase in ('reduce_scatter','all_gather'):
  for step in range(n-1):
   for i,src in enumerate(ring):
    dst=ring[(i+1)%n];host=candidate['buffer_numa_per_edge'][i];b=c['input_bytes']//n
    sent[src]+=b;received[dst]+=b;payload+=b;dram[host]+=2*b
    for u,v in [(c['gpu_numa'][src],host),(host,c['gpu_numa'][dst])]:
     if u!=v:socket[u,v]+=b
 assert sent==received==[c['per_gpu_per_direction_bytes']]*n
 assert payload==c['logical_outbound_bytes'] and sum(dram)==c['dram_aggregate_bytes']==2*payload
 assert dram==candidate['dram_bytes'] and [socket[0,1],socket[1,0]]==candidate['socket_direction_bytes']
 bw=c['effective_bytes_per_second']
 bound=max(max(sent+received)/bw['pcie_per_gpu_per_direction'],max(dram)/bw['dram_per_numa_read_plus_write'],max(socket.values())/bw['socket_per_direction'])
 assert math.isclose(bound*1000,candidate['resource_bound_ms'])
proof=json.loads((ROOT/'references/framework-history/2026-09-08/pcie-staging/reading-proof.json').read_text())
for record in proof['records']:
 data=(ROOT/record['file']).read_bytes();assert hashlib.sha256(data).hexdigest()==record['sha256']
 for lo,hi in record['read_scope'].get('line_ranges_inclusive',[]):assert 1<=lo<=hi<=len(data.decode().splitlines())
# Kernel orchestration: declared tensor traffic and lifetime accounting.
c=a['kernel_orchestration_teaching'];cfg=json.loads((ROOT/c['config']).read_text())
assert c['intermediate_size']==cfg['intermediate_size'] and c['tensor_parallel_size']==1
t=c['tokens'];d=cfg['intermediate_size'];assert d%c['group_size']==0
sizes={'input':t*2*d*c['input_dtype_bytes'],'activation':t*d*c['input_dtype_bytes'],'quant':t*d*c['quant_dtype_bytes'],'scale':t*(d//c['group_size'])*c['scale_bytes']}
assert [sizes[k] for k in ['input','activation','quant','scale']]==[c[k] for k in ['input_gate_up_bytes','intermediate_bytes','quant_output_bytes','scale_output_bytes']]
# A dataflow ledger and an allocation/free timeline independently check traffic and liveness.
dataflow={'unfused':[(['input'],['activation']),(['activation'],['quant','scale'])],'fused':[(['input'],['quant','scale'])]}
for mode,kernels in dataflow.items():
 traffic=sum(sizes[x] for reads,writes in kernels for x in reads+writes)
 assert traffic==c[f'{mode}_logical_traffic_bytes']
 live={'input'};peak=sizes['input']
 for i,(reads,writes) in enumerate(kernels):
  assert set(reads)<=live
  live.update(writes);peak=max(peak,sum(sizes[x] for x in live))
  future_reads={x for later_reads,_ in kernels[i+1:] for x in later_reads}
  live={x for x in live if x in future_reads or x in ['quant','scale']}
 assert live=={'quant','scale'} and peak==c[f'{mode}_live_payload_peak_bytes']
assert c['traffic_saved_bytes']==c['unfused_logical_traffic_bytes']-c['fused_logical_traffic_bytes']==2*sizes['activation']
assert c['live_payload_peak_saved_bytes']==c['unfused_live_payload_peak_bytes']-c['fused_live_payload_peak_bytes']
assert math.isclose(c['traffic_saved_service_us_prefill'],c['traffic_saved_bytes']/c['teaching_effective_bandwidth_Bps']*1e6)
assert math.isclose(c['traffic_saved_service_us_decode_T1'],c['traffic_saved_service_us_prefill']/t)
historical=c['paper_candy_figure12']
assert len(historical['original_kernels_us'])==3 and len(historical['reorganized_kernels_us'])==4
for mode in ['original','reorganized']:assert math.isclose(sum(historical[f'{mode}_kernels_us']),historical[f'{mode}_total_us'])
proof=json.loads((ROOT/'references/framework-history/2026-09-08/kernel-orchestration/reading-proof.json').read_text())
for record in proof['records']:
 data=(ROOT/record['file']).read_bytes();assert hashlib.sha256(data).hexdigest()==record['sha256']
 for lo,hi in record['read_scope'].get('line_ranges_inclusive',[]):assert 1<=lo<=hi<=len(data.decode().splitlines())
# Fixed public assessment literals are parsed, never imported or executed.
# Cache tiering: bind byte counts to the model and independently compare ready times.
c=a['cache_tiers_routing_teaching'];cfg=json.loads((ROOT/c['config']).read_text())
assert c['tensor_parallel_size']==1
fragment=c['logical_block_tokens']*cfg['num_key_value_heads']*cfg['head_dim']*c['kv_dtype_bytes']
pieces=[fragment for layer in range(cfg['num_hidden_layers']) for kind in ('K','V')]
assert fragment==c['split_fragment_bytes'] and len(pieces)==c['fragments_per_logical_block']
assert sum(pieces)==c['contiguous_block_bytes']
assert c['logical_blocks']*c['logical_block_tokens']==c['prefix_tokens']
assert len(pieces)*c['logical_blocks']==c['split_fragments']
assert sum(pieces)*c['logical_blocks']==c['prefix_bytes']==c['kv_bytes_per_token']*c['prefix_tokens']
hot=c['assumed_queue_a_s']+c['assumed_cached_tail_to_first_token_s']
cold=c['assumed_queue_b_s']+c['assumed_recompute_to_first_token_s']
assert math.isclose(hot,c['hot_a_ttft_s']) and math.isclose(cold,c['cold_b_ttft_s'])
def cache_ready_ttft(remote_rate):
 ready=c['assumed_lookup_s']
 for rate in (remote_rate,c['assumed_host_gpu_Bps']):ready+=c['prefix_bytes']/rate
 return max(ready,c['assumed_queue_b_s'])+c['assumed_cached_tail_to_first_token_s']
for rate,expected in zip(c['assumed_remote_Bps'],c['remote_b_ttft_s']):assert math.isclose(cache_ready_ttft(rate),expected)
threshold=c['remote_break_even_Bps'];assert math.isclose(cache_ready_ttft(threshold),cold)
assert cache_ready_ttft(threshold*.9)>cold>cache_ready_ttft(threshold*1.1)
assert c['remote_payload_Bps']==c['requests_per_second']*c['prefix_bytes']
proof=json.loads((ROOT/'references/framework-history/2026-09-08/cache-routing/reading-proof.json').read_text())
for record in proof['records']+proof['reused_records']:
 data=(ROOT/record['file']).read_bytes();assert hashlib.sha256(data).hexdigest()==record['sha256']
 for lo,hi in record['read_scope'].get('line_ranges_inclusive',[]):assert 1<=lo<=hi<=len(data.decode().splitlines())
 if 'derived_text' in record:
  item=record['derived_text'];data=(ROOT/item['file']).read_bytes()
  assert len(data)==item['bytes'] and hashlib.sha256(data).hexdigest()==item['sha256']
  for lo,hi in record['read_scope'].get('derived_text_line_ranges_inclusive',[]):assert 1<=lo<=hi<=len(data.decode().splitlines())
# Weight handoff: count logical matrices, enumerate resource lifetimes and EP ownership.
c=a['weight_handoff_teaching'];cfg=json.loads((ROOT/c['dense_config']).read_text())
assert cfg['model_type']=='qwen3' and not cfg['tie_word_embeddings'] and not cfg.get('attention_bias',False)
h=cfg['hidden_size'];hd=cfg['head_dim'];qh=cfg['num_attention_heads']*hd;kvh=cfg['num_key_value_heads']*hd
matrices=[(cfg['vocab_size'],h)]*2
per_layer=[(h,qh),(h,kvh),(h,kvh),(qh,h)]+[(h,cfg['intermediate_size'])]*3
params=sum(x*y for x,y in matrices)+cfg['num_hidden_layers']*(sum(x*y for x,y in per_layer)+2*h+2*hd)+h
assert params==c['dense_parameters'] and params*c['dtype_bytes']==c['dense_weight_bytes']
resources={'trainer':c['trainer_resident_gib'],'weights':c['dense_weight_bytes']/2**30,'kv':c['kv_pool_gib'],'runtime':c['runtime_gib']}
stages=[['trainer','runtime'],['trainer','weights','runtime'],['weights','runtime'],['weights','kv','runtime']]
peaks=[sum(resources[k] for k in stage) for stage in stages]
assert math.isclose(max(peaks),c['staged_peak_gib']) and math.isclose(peaks[-1],c['rollout_peak_gib'])
assert math.isclose(sum(resources.values()),c['naive_peak_gib'])
assert c['staged_peak_gib']<c['usable_gib']<c['naive_peak_gib']
assert math.isclose(2*c['dense_weight_bytes']/c['host_gpu_Bps'],c['old_backup_roundtrip_seconds'])
cfg=json.loads((ROOT/c['moe_config']).read_text());expert=3*cfg['hidden_size']*cfg['moe_intermediate_size']*c['dtype_bytes']
assert expert==c['expert_bf16_bytes']
owners=[[e for e in range(cfg['num_experts']) if e%c['inference_ep']==r] for r in range(c['inference_ep'])]
assert sorted(e for group in owners for e in group)==list(range(cfg['num_experts']))
rank_bytes=[len(group)*expert*cfg['num_hidden_layers'] for group in owners]
assert len(set(rank_bytes))==1 and rank_bytes[0]==c['per_rank_routed_bytes'] and sum(rank_bytes)==c['total_routed_bytes']
for quantity,rate,expected in [(c['total_routed_bytes'],c['consumer_Bps'],c['full_receive_seconds']),(rank_bytes[0],c['consumer_Bps'],c['sharded_receive_seconds']),(sum(rank_bytes),c['producer_count']*c['producer_Bps'],c['producer_seconds'])]:assert math.isclose(quantity/rate,expected)
assert c['producer_seconds']>c['sharded_receive_seconds']
layer=expert*cfg['num_experts'];assert layer==c['full_expert_layer_bytes'] and 2*layer/2**30==c['two_full_layer_gib']
vocab=cfg['vocab_size']*cfg['hidden_size']*c['dtype_bytes'];assert vocab==c['unsliced_vocab_bytes']
assert 2*layer/c['inference_ep']/2**20==c['expert_only_two_receive_mib']
assert 2*max(vocab,layer/c['inference_ep'])/2**30==c['two_vocab_receive_gib']
proof=json.loads((ROOT/'references/framework-history/2026-09-08/weight-handoff/reading-proof.json').read_text())
assert len(proof['records'])==17 and not proof['downloaded_code_executed']
for record in proof['records']:
 data=(ROOT/record['file']).read_bytes();assert hashlib.sha256(data).hexdigest()==record['sha256']
 for lo,hi in record['read_scope'].get('line_ranges_inclusive',[]):assert 1<=lo<=hi<=len(data.decode().splitlines())
 if 'derived_text' in record:
  meta=record['derived_text'];data=(ROOT/meta['file']).read_bytes();assert len(data)==meta['bytes'] and hashlib.sha256(data).hexdigest()==meta['sha256']
  for lo,hi in record['read_scope'].get('derived_text_line_ranges_inclusive',[]):assert 1<=lo<=hi<=len(data.decode().splitlines())
# Cache-event freshness: enumerate a two-point distribution and its actual p99.
c=a['cache_events_routing_teaching'];base=a[c['base_case']]
hit=c['queue_a_ms']+c['hit_tail_ms'];miss=c['queue_a_ms']+c['recompute_ms']
cold=c['queue_b_ms']+c['recompute_ms']
assert (hit,miss,cold)==(c['hit_a_ms'],c['miss_a_ms'],c['cold_b_ms'])
n=c['sample_size'];nhit=round(n*c['reuse_probability'])
sample=sorted([hit]*nhit+[miss]*(n-nhit))
assert math.isclose(sum(sample)/n,c['mean_a_ms'])
assert sample[math.ceil(.99*n)-1]==c['p99_a_ms']>c['slo_ms']>c['p99_b_ms']==cold
assert math.isclose((miss-cold)/(miss-hit),c['break_even_probability'])
copy_ms=base['prefix_bytes']/c['host_gpu_Bps']*1000
assert math.isclose(copy_ms,c['host_copy_ms'])
assert math.isclose(max(c['queue_a_ms'],copy_ms)+c['hit_tail_ms'],c['prefetch_a_ms'])
assert math.isclose(c['queue_a_ms']+copy_ms+c['hit_tail_ms'],c['serial_copy_a_ms'])
assert c['replay_batch_capacity']/c['assumed_batches_per_second']==c['replay_window_seconds']
proof=json.loads((ROOT/'references/framework-history/2026-09-08/cache-events/reading-proof.json').read_text())
assert len(proof['records'])==15 and not proof['downloaded_code_executed']
for record in proof['records']:
 data=(ROOT/record['file']).read_bytes();assert hashlib.sha256(data).hexdigest()==record['sha256']
 for lo,hi in record['read_scope'].get('line_ranges_inclusive',[]):assert 1<=lo<=hi<=len(data.decode().splitlines())
# Structured generation: packed-mask capacity and the pre-sampling dependency join.
c=a['structured_generation_teaching'];cfg=json.loads((ROOT/c['config']).read_text())
assert c['tensor_parallel_size']==1 and c['vocab_size']==cfg['vocab_size']
assert c['mask_word_bits']==8*c['mask_word_bytes']
words,tail=divmod(cfg['vocab_size'],c['mask_word_bits'])
row=(words+bool(tail))*c['mask_word_bytes']
assert row==c['mask_row_bytes'] and row*c['batch']==c['mask_batch_bytes']
assert c['logits_bytes']==c['batch']*cfg['vocab_size']*c['logits_dtype_bytes']
assert c['logits_mask_read_write_bytes']==sum([c['logits_bytes'],c['logits_bytes']])
for payload,rate,service in [('mask_batch_bytes','assumed_host_gpu_Bps','mask_transfer_service_us'),('logits_mask_read_write_bytes','assumed_hbm_Bps','logits_rw_service_us')]:
 assert math.isclose(c[payload]/c[rate]*1e6,c[service])
cpu=sum(c['assumed_cpu_mask_per_request_us'] for _ in range(c['batch']))/1000
assert math.isclose(cpu,c['cpu_serial_ms'])
assert math.isclose(cpu+c['assumed_gpu_forward_ms'],c['serial_before_transfer_and_sampling_ms'])
assert math.isclose(max(cpu,c['assumed_gpu_forward_ms']),c['ideal_overlapped_before_transfer_and_sampling_ms'])
spec_rows=sum(c['draft_tokens']+1 for _ in range(c['batch']))
assert spec_rows==c['spec_mask_rows'] and spec_rows*row==c['spec_mask_capacity_bytes']
proof=json.loads((ROOT/'references/framework-history/2026-09-08/structured-generation/reading-proof.json').read_text())
for record in proof['records']+proof['reused_records']:
 data=(ROOT/record['file']).read_bytes();assert hashlib.sha256(data).hexdigest()==record['sha256']
 for lo,hi in record['read_scope'].get('line_ranges_inclusive',[]):assert 1<=lo<=hi<=len(data.decode().splitlines())
 if 'derived_text' in record:
  item=record['derived_text'];data=(ROOT/item['file']).read_bytes()
  assert len(data)==item['bytes'] and hashlib.sha256(data).hexdigest()==item['sha256']
  for lo,hi in record['read_scope'].get('derived_text_line_ranges_inclusive',[]):assert 1<=lo<=hi<=len(data.decode().splitlines())
# Retrieval choices change the actual matrices and the downstream state.
c=a['retrieval_generation_teaching'];cfg=json.loads((ROOT/c['config']).read_text())
d=cfg['hidden_size'];kv=cfg['num_key_value_heads']*cfg['head_dim'];f=cfg['intermediate_size']
shapes=[(d,d),(d,kv),(d,kv),(d,d),(d,f),(d,f),(f,d)]*cfg['num_hidden_layers']
matrix_parameters=sum(rows*cols for rows,cols in shapes)
assert matrix_parameters==c['body_matrix_parameters'] and c['batch']==1 and not c['prefix_cache_hit']
for row in c['cases']:
 t=c['base_input_tokens']+row['documents']*c['tokens_per_document'];assert t==row['tokens']
 assert row['linear_flops']==sum(2*t*r*s for r,s in shapes)
 assert row['causal_attention_flops']==sum(range(1,t+1))*cfg['num_hidden_layers']*cfg['num_attention_heads']*4*cfg['head_dim']
 assert row['kv_bytes']==t*2*cfg['num_hidden_layers']*kv*c['kv_dtype_bytes']
 assert math.isclose(row['prefill_work_estimate_s'],(row['linear_flops']+row['causal_attention_flops'])/c['assumed_prefill_effective_Fps'])
 assert math.isclose(row['sequential_retrieval_prefill_s'],row['assumed_retrieval_s']+row['prefill_work_estimate_s'])
x,y=c['cases']
assert math.isclose(c['prefill_saved_s'],y['prefill_work_estimate_s']-x['prefill_work_estimate_s'])
assert math.isclose(c['extra_retrieval_s'],x['assumed_retrieval_s']-y['assumed_retrieval_s'])
assert math.isclose(c['ready_time_saved_s'],c['prefill_saved_s']-c['extra_retrieval_s'])
def rag_ready(row,rate):return row['assumed_retrieval_s']+(row['linear_flops']+row['causal_attention_flops'])/rate
threshold=c['prefill_rate_break_even_Fps'];assert math.isclose(rag_ready(x,threshold),rag_ready(y,threshold))
assert rag_ready(x,threshold*.9)<rag_ready(y,threshold*.9) and rag_ready(x,threshold*1.1)>rag_ready(y,threshold*1.1)
v=c['vector_scan'];assert v['corpus_bytes']==v['vectors']*v['dimension']*v['stored_element_bytes']
assert v['pointwise_dot_flops_per_query']==2*v['vectors']*v['dimension']
for batch,intensity in zip(v['query_batches'],v['dot_intensity_flops_per_byte']):assert math.isclose(intensity,batch*v['pointwise_dot_flops_per_query']/v['corpus_bytes'])
for service,rate in [('host_scan_service_s','assumed_host_link_Bps'),('near_scan_service_s','assumed_near_memory_Bps')]:assert math.isclose(v[service],v['corpus_bytes']/v[rate])
assert v['query_broadcast_bytes']==sum(v['dimension']*v['stored_element_bytes'] for _ in range(v['shards']))
assert v['partial_result_bytes']==sum(v['score_bytes']+v['id_bytes'] for _ in range(v['shards']*v['partial_topk']))
assert v['faiss_flat_fp32_bytes']==v['vectors']*v['dimension']*4==2*v['corpus_bytes']
# Fixed public assessment literals are parsed, never imported or executed.
import ast
c=a['evaluation_records_teaching'];p=c['takehome'];proof=json.loads((ROOT/p['proof']).read_text());const=proof['takehome']['ast_literal_constants']
src=ROOT/'references/interviews/2026-09-08/fourth-pass/takehome-problem.py'
assert src.read_bytes()==src.with_name('takehome-frozen.py').read_bytes()
parsed={}
for n in ast.parse(src.read_text()).body:
 if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id in const:parsed[n.targets[0].id]=ast.literal_eval(n.value)
assert json.loads(json.dumps(parsed))==const and const['N_CORES']==1
assert p['node_visits']==p['batch']*p['rounds'] and p['per_node']==proof['takehome']['nondebug_ops_per_node']
assert p['loop_cycles']==p['node_visits']*sum(p['per_node'].values())
assert p['baseline_cycles']==p['loop_cycles']+p['setup_and_pause_cycles']==147734
for kind,value in p['same_instructions_resource_bounds'].items():assert value==math.ceil(p['node_visits']*p['per_node'][kind]/const['SLOT_LIMITS'][kind])
assert p['one_scalar_node_load_per_visit_bound']==math.ceil(p['node_visits']/const['SLOT_LIMITS']['load'])
assert p['scratch_bytes']==const['SCRATCH_SIZE']*4
for report in proof['reports']:
 html=BeautifulSoup((ROOT/report['file']).read_text(),'html.parser');raw=next(x.get_text() for x in html.find_all('script') if x.get_text().startswith('window.__INITIAL_STATE__='))
 data=json.JSONDecoder().raw_decode(raw.split('=',1)[1])[0]['prefetchData']['2']['ssrCommonData']['contentData']
 assert data['uuid']==report['uuid'] and data['title']==report['title'] and data['createdAt']==report['createdAt'] and data['userBrief']['nickname']==report['author']
assert len({x['author'] for x in proof['reports']})==1
idx=BeautifulSoup((ROOT/'references/interviews/2026-09-08/fourth-pass/anthropic-em-index.html').read_text(),'html.parser')
emdata=json.loads(idx.find('script',id='__NEXT_DATA__').get_text())
def find_em_record(x):
 if isinstance(x,dict):
  if x.get('id')==9144:return x
  children=x.values()
 elif isinstance(x,list):children=x
 else:return None
 for child in children:
  found=find_em_record(child)
  if found:return found
emrecord=find_em_record(emdata)
assert emrecord['asked_on']==proof['anthropic_em']['asked_on']=='2026-04-01'
assert emrecord['created_at']==proof['anthropic_em']['created_at']
e=c['agent_events'];rate=e['tasks_per_second']*e['events_per_task'];arrival=rate*e['payload_bytes_per_event']
assert rate==e['events_per_second'] and arrival==e['arrival_bytes_per_second']
assert e['backlog_events']==rate*e['outage_seconds'];assert e['backlog_bytes']==e['backlog_events']*e['payload_bytes_per_event'];assert e['backlog_mib']==e['backlog_bytes']/2**20
for mib,secs in zip(e['payload_buffer_mib'],e['fill_seconds']):assert math.isclose(secs,mib*2**20/arrival)
assert e['net_drain_bytes_per_second']==e['restored_departure_bytes_per_second']-arrival>0
assert math.isclose(e['drain_seconds'],e['backlog_bytes']/e['net_drain_bytes_per_second'])
assert math.isclose(e['no_new_arrivals_drain_seconds'],e['backlog_bytes']/e['restored_departure_bytes_per_second'])
assert e['sampled_expected_bytes_per_second']==arrival*e['sample_fraction']
questions=re.findall(r'^\| (I\d+) ',(ROOT/'research/2026-infra-survey/interview-directions.md').read_text(),re.M)
assert questions==[f'I{i:02}' for i in range(1,22)]
from verify_interview_sixth import verify as verify_interview_sixth
verify_interview_sixth()
from verify_interview_seventh import verify as verify_interview_seventh
verify_interview_seventh()
from verify_interview_ninth import verify as verify_interview_ninth
interview_ninth = verify_interview_ninth()
from verify_interview_tenth import verify as verify_interview_tenth
interview_tenth = verify_interview_tenth()
c=a['kv_compression_teaching'];assert c['baseline_seconds']==c['assumed_ttft_seconds']+c['baseline_tokens']/c['baseline_tokens_per_second'];assert c['compressed_seconds']==c['assumed_ttft_seconds']+c['compressed_tokens']/c['compressed_tokens_per_second']
c=a['reconfiguration_teaching'];assert math.isclose(c['break_even_remaining_steps'],c['transition_seconds']/(c['old_step_seconds']-c['new_step_seconds']));assert c['old_total_seconds']==c['remaining_steps']*c['old_step_seconds'];assert c['new_total_seconds']==c['transition_seconds']+c['remaining_steps']*c['new_step_seconds']
c=a['plan_reuse_teaching'];assert c['per_layer_total_microseconds']==c['layers']*c['assumed_plan_microseconds'];assert c['shared_plan_microseconds']==c['assumed_plan_microseconds']
c=a['moe_teaching'];cfg=json.loads((ROOT/c['config']).read_text());w=3*cfg['hidden_size']*cfg['moe_intermediate_size']*2;assert c['expert_bf16_bytes']==w and c['expert_mib']==w/2**20==36;assert c['all_experts_layer_gib']==cfg['num_experts']*w/2**30==4.5
for m,v in c['expected_active_experts'].items():assert math.isclose(v,cfg['num_experts']*(1-(1-cfg['num_experts_per_tok']/cfg['num_experts'])**int(m)))
assert math.isclose(c['m8_expected_weight_gib'],c['expected_active_experts']['8']*w/2**30);assert c['m8_same_experts_weight_mib']==cfg['num_experts_per_tok']*w/2**20==288
assert c['one_replica_per_layer_per_gpu_gib']==cfg['num_hidden_layers']*w/2**30==3.3046875;assert c['eight_replicas_per_gpu_gib']==8*w/2**30==.28125
p=c['padding'];assert p['actual_rows']==sum(p['tokens']);assert p['nonempty_blockwise_rows']==sum(math.ceil(x/p['tile_rows'])*p['tile_rows'] for x in p['tokens']);assert p['all_experts_max_rows']==len(p['tokens'])*math.ceil(max(p['tokens'])/p['tile_rows'])*p['tile_rows']
c=a['startup_teaching'];assert math.isclose(c['break_even_execution_steps'],c['extra_prepare_seconds']/c['critical_path_saved_per_execution_step_seconds'])
c=a['ring_teaching'];n=c['ranks'];assert math.isclose(c['estimated_microseconds'],(2*(n-1)*c['alpha_seconds']+2*(n-1)/n*c['bytes_per_rank']/c['effective_one_way_bytes_per_second'])*1e6)
c=a['attention_tile_teaching'];m,n,d=c['m'],c['n'],c['d'];assert all(x%128==0 for x in (m,n,d));assert c['flops']==4*m*n*d
assert c['smem_bytes']==2*((m//128)*(n//128)*256*d+(m//128)*(d//128)*128*n);assert c['exponential_ops']==m*n
assert c['mma_cycles']==c['flops']/c['mma_flops_per_cycle'];assert c['smem_cycles']==c['smem_bytes']/c['smem_bytes_per_cycle'];assert c['exp_cycles']==c['exponential_ops']/c['exp_ops_per_cycle']
assert c['resource_lower_bound_cycles']==max(c['mma_cycles'],c['smem_cycles'],c['exp_cycles']);assert c['matrix_only_double_throughput_bound_cycles']==max(c['mma_cycles']/2,c['smem_cycles'],c['exp_cycles']);assert c['m256_cycles']==[2*c['mma_cycles'],2*c['smem_cycles'],2*c['exp_cycles']]
c=a['fleet_goodput_teaching'];C=c['capacity_gpu_seconds'];A=c['all_required_resources_ready_gpu_seconds'];G=c['saved_progress_execution_gpu_seconds'];I=c['ideal_compute_gpu_seconds'];assert C==c['gpus']*c['wall_seconds'];assert 0<I<=G<=A<=c['individually_allocated_gpu_seconds']<=C
assert math.isclose(c['individual_allocation_ratio'],c['individually_allocated_gpu_seconds']/C);assert math.isclose(c['sg'],A/C) and math.isclose(c['rg'],G/A) and math.isclose(c['pg'],I/G);assert math.isclose(c['mpg'],I/C) and math.isclose(c['sg']*c['rg']*c['pg'],c['mpg'])
c=a['chunk_attention_teaching'];cfg=json.loads((ROOT/c['config']).read_text());s=c['input_tokens'];q=c['chunk_tokens'];assert s%q==0
# Count per-query visible keys independently of the closed-form chunk equation.
assert c['first_pairs']==sum(range(1,q+1));assert c['last_pairs']==sum(range(s-q+1,s+1));assert c['total_pairs']==sum(range(1,s+1))
assert math.isclose(c['last_to_first_ratio'],c['last_pairs']/c['first_pairs']);assert c['total_attention_matmul_flops']==4*cfg['num_hidden_layers']*cfg['num_attention_heads']*cfg['head_dim']*c['total_pairs']
c=a['prefill_queue_teaching'];D=c['single_card_seconds'];K=c['tp_speedup'];assert c['pp_stages']==2;assert math.isclose(c['tp_capacity_rps'],K/D) and math.isclose(c['pp_capacity_rps'],2/D)
for rate,values in c['at_rates'].items():
 rate=float(rate);tp_service=D/K;stage_service=D/2;assert rate*tp_service<1 and rate*stage_service<1
 # M/D/1 Wq = lambda E[S^2] / (2(1-rho)); PP adds both stage execution times.
 assert math.isclose(values['tp_mean_seconds'],tp_service+rate*tp_service**2/(2*(1-rate*tp_service)))
 assert math.isclose(values['pp_mean_seconds'],D+rate*stage_service**2/(2*(1-rate*stage_service)))
c=a['kv_transfer_teaching'];cfg=json.loads((ROOT/c['config']).read_text());payload=c['tokens']*cfg['num_hidden_layers']*2*cfg['num_key_value_heads']*cfg['head_dim']*c['bytes_per_element'];bw=c['effective_one_way_bytes_per_second'];assert c['kv_bytes']==payload
assert math.isclose(c['isolated_transfer_seconds'],payload/bw);assert math.isclose(c['rate_capacity_rps'],bw/payload)
for rate,traffic in c['at_rates_bytes_per_second'].items():assert traffic==float(rate)*payload
c=a['nano_batch_teaching'];cfg=json.loads((ROOT/c['config']).read_text());params=3*cfg['hidden_size']*cfg['intermediate_size'];assert params==c['ffn_parameters'];assert c['matmul_flops']==2*c['batch_tokens']*params
assert c['unsplit_logical_weight_mib']==params*c['weight_bytes_per_element']/2**20;assert c['split_logical_weight_mib']==c['microbatches']*c['unsplit_logical_weight_mib'];assert c['microbatches']==2
N=c['network_or_memory_half_ms'];C=c['compute_half_ms'];assert math.isclose(c['unsplit_ms'],c['network_or_memory_full_ms']+c['compute_full_ms']);assert math.isclose(c['split_serial_ms'],2*(N+C))
assert math.isclose(c['ideal_overlap_ms'],N+max(N,C)+C);assert math.isclose(c['interfering_overlap_ms'],N+c['assumed_joint_overlap_ms']+C);assert c['ideal_overlap_ms']<c['unsplit_ms']<c['interfering_overlap_ms']<c['split_serial_ms']
c=a['multi_nic_teaching'];n=c['nic_count'];b=c['nic_effective_one_way_GBps'];limits=c['path_GBps'];assert limits['direct']==b and limits['shared_pcie']==min(n*b,c['shared_gpu_pcie_GBps']);assert limits['relay']==b+min((n-1)*b,c['shared_relay_link_GBps']);assert limits['fabric_limited_relay']==min(limits['relay'],c['fabric_GBps_variant'])
for path,bw in limits.items():assert math.isclose(c['payload_ms'][path],c['kv_bytes']/(bw*1e9)*1e3)
assert c['kv_bytes']==a['kv_transfer_teaching']['kv_bytes']
c=a['ollama_slots_teaching'];cfg=json.loads((ROOT/c['config']).read_text());per_slot=c['context_tokens_per_independent_slot']*cfg['num_hidden_layers']*2*cfg['num_key_value_heads']*cfg['head_dim']*c['kv_bytes_per_element']/2**30
for slots,gib in c['logical_kv_gib'].items():assert gib==int(slots)*per_slot
assert c['delta_gib']==c['logical_kv_gib']['4']-c['logical_kv_gib']['1']
c=a['rl_logprob_teaching'];assert c['correct_ratio']==math.exp(c['current_logprob']-c['behavior_logprob'])==1
assert math.isclose(c['wrong_ratio'],math.exp(c['current_logprob']-c['wrong_recomputed_denominator_logprob']));assert c['wrong_ratio']>c['clip_upper']
assert c['route_uint16_bytes']==c['tokens']*c['moe_layers']*c['top_k']*2==6*2**20;assert c['route_int32_bytes']==2*c['route_uint16_bytes']
c=a['rl_supply_teaching'];assert c['rates_unit']=='trajectories_per_second';assert c['filter_location']=='after_verifier_before_learner'
assert math.isclose(c['accepted_supply_upper_bound'],min(c['learner_capacity'],min(c['generator_capacity'],c['verifier_capacity'])*(1-c['post_verifier_reject_fraction'])))
# A mirrored question list is a second acquisition, not another interview sample.
c=a['rl_coscheduling_teaching'];A,B=c['phase_seconds']['A'],c['phase_seconds']['B'];assert sum(A)==sum(B)==c['solo_cycle_seconds'];assert A[0]==B[1] and A[1]==B[0]
assert c['complementary_cycle_seconds']==max(sum(A),sum(B),A[0]+B[0],A[1]+B[1]);assert c['two_A_lower_bound_seconds']==max(sum(A),2*A[0],2*A[1])
assert math.isclose(c['allowed_cycle_seconds'],c['solo_cycle_seconds']*c['slowdown_allowance'])
for kind,overhead in c['switch_seconds_per_phase'].items():assert c['cycle_seconds'][kind]==c['complementary_cycle_seconds']+2*overhead
assert c['cycle_seconds']['warm']<c['allowed_cycle_seconds']<c['cycle_seconds']['cold'];assert c['host_required_gib']==sum(c['host_states_gib'])+c['host_reserve_gib']>c['host_capacity_gib']
assert c['single_copy_seconds']==c['model_parameters']*c['weight_bytes_per_parameter']*8/c['slow_link_effective_bps'];assert c['four_copy_seconds']==4*c['single_copy_seconds']
c=a['rl_recovery_teaching'];prefix=c['rollout_seconds']+c['failed_update_elapsed_seconds']+c['detection_seconds']+c['restore_seconds'];assert c['whole_task_seconds']==prefix+c['rollout_seconds']+c['train_seconds'];assert c['preserved_rollout_seconds']==prefix+c['train_seconds'];assert c['saved_seconds']==c['whole_task_seconds']-c['preserved_rollout_seconds']==c['rollout_seconds']
assert math.isclose(c['checkpoint_over_work_ratio'],c['blocking_checkpoint_seconds']/(c['rollout_seconds']+c['train_seconds']))
# Original post and mirror represent the same question source.
c=a['graph_selection_teaching'];cfg=json.loads((ROOT/c['config']).read_text());assert c['ordinary_us']==c['device_work_us']+c['exposed_launch_gaps_us'];base=c['device_work_us']+c['graph_launch_us']+c['metadata_us']
for tokens,b in c['input_bytes'].items():
 assert b==int(tokens)*cfg['hidden_size']*c['element_bytes'];assert math.isclose(c['extra_copy_us'][tokens],2*b/c['hbm_traffic_bytes_per_second']*1e6);assert math.isclose(c['graph_copy_us'][tokens],base+c['extra_copy_us'][tokens])
assert c['graph_indirect_us']==base+c['indirection_overhead_us'];assert c['graph_copy_us']['256']<c['graph_indirect_us']<c['ordinary_us']<c['graph_copy_us']['2048']
saved=(c['ordinary_us']-c['graph_indirect_us'])*1e-6;n=c['minimum_profitable_replays'];assert (n-1)*saved<=c['extra_setup_seconds']<n*saved
extra=c['padded_tokens']-c['real_tokens'];assert c['ffn_extra_flops']==2*extra*3*cfg['hidden_size']*cfg['intermediate_size'];assert math.isclose(c['ffn_extra_fraction'],extra/c['real_tokens'])
c=a['qwen_tp_collective_teaching'];cfg=json.loads((ROOT/c['config']).read_text());assert c['layers']==cfg['num_hidden_layers']
for tokens,b in c['input_bytes'].items():assert b==int(tokens)*cfg['hidden_size']*c['element_bytes']
n=c['ranks'];launch=2*(n-1)*c['alpha_seconds'];transfer=2*(n-1)/n*c['input_bytes']['1']/c['effective_one_way_bytes_per_second'];calls=c['layers']*c['allreduces_per_layer']
assert math.isclose(c['collective_seconds'],launch+transfer);assert math.isclose(c['model_collective_seconds'],calls*(launch+transfer))
assert math.isclose(c['saved_if_bandwidth_doubles_seconds'],calls*transfer/2);assert math.isclose(c['saved_if_alpha_halves_seconds'],calls*launch/2)
c=a['inflight_reads_teaching'];B=c['target_effective_bytes_per_second'];T=c['completion_seconds'];m=c['payload_bytes']
assert c['required_inflight']==math.ceil(B*T/m);assert c['double_latency_required_inflight']==math.ceil(B*2*T/m);assert c['window_bytes_per_second']==c['available_inflight']*m/T
c=a['collective_arrival_teaching'];assert c['complete_ms']==max(c['ready_ms'])+c['post_ready_exchange_ms']
for ready,wait in zip(c['ready_ms'],c['observed_wait_ms']):assert math.isclose(ready+wait,c['complete_ms'])
assert c['half_exchange_complete_ms']==max(c['ready_ms'])+c['post_ready_exchange_ms']/2;assert c['no_skew_complete_ms']==c['post_ready_exchange_ms']
c=a['megascale_historical_recalculation'];assert (ROOT/c['source']).exists()
for g,dp,batch in zip(c['gpu_counts'],c['dp_replicas'],c['sequences_per_dp_replica']):assert dp==g//(c['tp']*c['pp']) and batch==c['global_batch']//dp
assert math.isclose(c['speedup'],c['step_seconds'][0]/c['step_seconds'][1]);assert math.isclose(c['scaling_efficiency'],c['speedup']/(c['gpu_counts'][1]/c['gpu_counts'][0]));assert math.isclose(c['idealized_days'],c['training_tokens']/c['reported_tokens_per_second']/86400)
# Physical path counts and exogenous periodic-demand examples, not measured performance.
c=a['network_phase_teaching'];assert c['average_total_bytes_per_second']==c['jobs']*c['per_job_bytes_per_second']*c['burst_ms']/c['period_ms']==16e9
assert c['overlap_excess_bytes_per_second']==c['jobs']*c['per_job_bytes_per_second']-c['link_bytes_per_second']==30e9
assert c['overlap_queue_bytes']==c['overlap_excess_bytes_per_second']*c['burst_ms']/1000==600e6
assert c['empty_input_drain_ms']==c['overlap_queue_bytes']/c['link_bytes_per_second']*1000==12
assert math.isclose(c['unshifted_score'],1-c['overlap_queue_bytes']/(c['period_ms']/1000*c['link_bytes_per_second']))
assert c['offset_ms']==c['burst_ms'] and 2*c['burst_ms']<=c['period_ms'];assert c['shifted_peak_bytes_per_second']==c['per_job_bytes_per_second']<=c['link_bytes_per_second'];assert c['shifted_queue_bytes']==0 and c['shifted_score']==1
assert c['drift_queue_bytes']==c['drift_overlap_ms']/1000*c['overlap_excess_bytes_per_second']==150e6
assert c['cycle_residue_ms']==sum(c['cycle_relative_offsets_ms'])%c['period_ms']==60
c=a['torus_route_teaching'];n=c['nodes'];assert n==16 and c['rounds']==3
cfg=json.loads((ROOT/c['config']).read_text());assert c['input_bytes']==c['activation_tokens']*cfg['hidden_size']*c['activation_element_bytes']==8*2**20
for name,rounds in c['algorithms'].items():
 assert [r['round'] for r in rounds]==list(range(3))
 for s,r in enumerate(rounds):
  counts={};assert [q['rank'] for q in r['routes']]==list(range(n));assert r['message_bytes']==c['input_bytes']//2**(s+1)
  rho=sum((-2)**i for i in range(s+1))
  for route in r['routes']:
   u=route['rank'];v=route['peer'];assert v==(u^(1<<s) if name=='recursive' else (u+(rho if u%2==0 else -rho))%n)
   path=route['path'];assert path[0][0]==u and path[-1][1]==v;assert len(path)==min((u-v)%n,(v-u)%n)==r['hops_per_message']
   for i,(src,dst) in enumerate(path):
    assert (dst-src)%n in [1,n-1];assert i==0 or path[i-1][1]==src;counts[(src,dst)]=counts.get((src,dst),0)+1
  assert r['directed_link_messages']==[dict(link=list(k),messages=v) for k,v in sorted(counts.items())]
  assert r['peak_link_messages']==max(counts.values());assert r['injected_bytes']==n*r['message_bytes'];assert r['physical_link_bytes']==sum(counts.values())*r['message_bytes'];assert r['peak_link_bytes']==max(counts.values())*r['message_bytes']
  assert math.isclose(r['serialization_lower_bound_us'],r['peak_link_bytes']/c['link_effective_one_way_bytes_per_second']*1e6)
assert [r['peak_link_messages'] for r in c['algorithms']['recursive']]==[1,2,4]
assert [r['peak_link_messages'] for r in c['algorithms']['swing']]==[1,1,2]
assert [r['physical_link_bytes']/2**20 for r in c['algorithms']['recursive']]==[64,64,64]
assert [r['physical_link_bytes']/2**20 for r in c['algorithms']['swing']]==[64,32,48]

# Weight offload: model matrices, actual buffer subtraction, and independent expert indicators.
c=a['weight_offload_teaching'];q=json.loads((ROOT/c['dense_config']).read_text());e=json.loads((ROOT/c['moe_config']).read_text())
assert c['ffn_bytes']==(2*q['hidden_size']*q['intermediate_size']+q['intermediate_size']*q['hidden_size'])*2
assert c['offloaded_layer_indices']==[i for i in range(q['num_hidden_layers']) if i%4==3]
assert c['gross_offloaded_bytes']==sum(c['ffn_bytes'] for _ in c['offloaded_layer_indices'])
assert c['kv_8k_bytes']==8192*2*q['num_hidden_layers']*q['num_key_value_heads']*q['head_dim']*2
for row in c['buffers']:
 assert row['buffer_bytes']==row['slots']*c['ffn_bytes']
 assert row['net_saved_bytes']==c['gross_offloaded_bytes']-row['buffer_bytes']
 assert (row['whole_8k_kv'],row['remainder_bytes'])==divmod(row['net_saved_bytes'],c['kv_8k_bytes'])
for rate,ms in zip(c['effective_copy_gib_per_second'],c['copy_service_ms']):assert math.isclose(ms,c['gross_offloaded_bytes']/2**30/rate*1000)
assert math.isclose(c['one_ffn_copy_ms'],c['ffn_bytes']/2**30/c['effective_copy_gib_per_second'][0]*1000)
assert math.isclose(c['four_decode_requests_transfer_upper_tokens_per_second'],4000/c['copy_service_ms'][0])
assert math.isclose(c['prefill_2048_amortized_copy_ms'],c['copy_service_ms'][0]/2048)
excluded_one=math.comb(e['num_experts']-1,e['num_experts_per_tok'])/math.comb(e['num_experts'],e['num_experts_per_tok'])
cold=e['num_experts']-c['hot_gpu_experts'];ep=3*e['hidden_size']*e['moe_intermediate_size']
for row in c['expert_cases']:
 m=row['tokens'];distinct=sum(1-excluded_one**m for _ in range(cold));tasks=m*e['num_experts_per_tok']*cold/e['num_experts']
 assert math.isclose(distinct,row['expected_cold_experts']) and math.isclose(tasks,row['expected_cold_tasks'])
 assert math.isclose(row['weight_bytes'],distinct*ep*2) and math.isclose(row['flops'],tasks*ep*2)
 assert math.isclose(row['dram_ms'],row['weight_bytes']/2**30/c['dram_gib_per_second']*1000)
 assert math.isclose(row['cpu_compute_ms'],row['flops']/(c['cpu_tflops']*1e12)*1000)
 assert math.isclose(row['cpu_resource_lower_bound_ms'],max(row['dram_ms'],row['cpu_compute_ms']))
 assert math.isclose(row['h2d_ms'],row['weight_bytes']/2**30/c['effective_copy_gib_per_second'][0]*1000)
 assert math.isclose(row['gpu_compute_ms'],row['flops']/(c['gpu_tflops']*1e12)*1000)
 assert math.isclose(row['serial_h2d_gpu_ms'],row['h2d_ms']+row['gpu_compute_ms'])
 assert row['activation_roundtrip_bytes']==2*m*e['hidden_size']*2
assert c['expert_cases'][0]['dram_ms']>c['expert_cases'][0]['cpu_compute_ms']
assert c['expert_cases'][1]['dram_ms']<c['expert_cases'][1]['cpu_compute_ms']
for cards,total,per in zip(c['pr29941_card_counts'],c['pr29941_total_request_rates'],c['pr29941_per_card_request_rates']):assert math.isclose(total/cards,per)
# RL tail: enumerate both independent draws and verify capacity/critical paths.
c=a['rollout_tail_teaching'];o=c['oversampling'];assert o['target']==o['prompts']*o['responses']
assert o['submitted']==int(o['prompts']*o['factor'])*int(o['responses']*o['factor'])
assert math.isclose(o['extra_fraction'],o['submitted']/o['target']-1)
x=c['selection'];p=x['long_probability'];draws=[(x['fast_seconds'],1-p,False),(x['slow_seconds'],p,True)]
single=sum(t*q for t,q,_ in draws);race=slot=long=0
for t1,p1,l1 in draws:
 for t2,p2,l2 in draws:
  q=p1*p2;t=min(t1,t2);race+=q*t;slot+=q*2*t;long+=q*(l1 and l2)
assert math.isclose(single,x['single_expected_seconds']) and math.isclose(race,x['race_expected_seconds'])
assert math.isclose(slot,x['race_expected_slot_seconds']) and math.isclose(long,x['selected_long_probability'])
cfg=json.loads((ROOT/c['config']).read_text());k=c['kv'];assert k['bytes_per_token']==2*cfg['num_hidden_layers']*cfg['num_key_value_heads']*cfg['head_dim']*2
for n,total,per in zip(k['lengths'],k['total_gib'],k['per_replica_gib']):
 assert math.isclose(k['trajectories']*n*k['bytes_per_token']/2**30,total)
 assert math.isclose(total/k['remaining_replicas'],per)
assert k['per_replica_gib'][0]<=k['kv_budget_gib_per_replica']<k['per_replica_gib'][1]
t=c['stream'];assert t['baseline_seconds']==t['rollout_seconds']+t['full_gradient_seconds']+t['final_sync_update_seconds']
assert t['remaining_gradient_on_all_gpus_seconds']*2==t['full_gradient_seconds']==t['half_gradient_on_half_gpus_seconds']
for delay,result in zip(t['migration_and_delay_seconds'],t['stream_seconds']):
 early=t['early_half_ready_seconds']+delay+t['half_gradient_on_half_gpus_seconds']
 assert result==max(t['rollout_seconds']+delay,early)+t['remaining_gradient_on_all_gpus_seconds']+t['final_sync_update_seconds']
g=c['gradient'];all_grads=[v for n,v in zip(g['local_sample_counts'],g['local_mean_gradients']) for _ in range(n)]
assert sum(all_grads)/len(all_grads)==g['weighted_mean']
assert sum(g['local_mean_gradients'])/len(g['local_mean_gradients'])==g['unweighted_mean']
x=c['paper_checks'];assert math.isclose(x['table3_speedup'],x['table3_baseline_seconds']/x['table3_adaptive_seconds'])
assert math.isclose(x['speedup_relative_increase'],x['table2_next_speedup']/x['table2_previous_speedup']-1)
assert math.isclose(x['time_relative_reduction'],1-x['table2_previous_speedup']/x['table2_next_speedup'])
# Speculative budget: enumerate stop positions independently from cumulative-survival sum.
c=a['speculative_budget_teaching'];cfg=json.loads((ROOT/c['config']).read_text())
for name,rec in c['scenarios'].items():
 expected=[]
 for p,k in zip(c['conditional_acceptance_probabilities'],rec['draft_limits']):
  pmf=[p**accepted*(1-p) for accepted in range(k)]+[p**k]
  assert math.isclose(sum(pmf),1)
  expected.append(sum((accepted+1)*prob for accepted,prob in enumerate(pmf)))
 assert all(math.isclose(x,y) for x,y in zip(expected,rec['expected_output_per_request']))
 assert math.isclose(sum(expected),rec['expected_output_per_round'])
 assert rec['committed_budget_query_rows']==sum(k+1 for k in rec['draft_limits'])
 computed=28 if name=='cap_accept' else rec['committed_budget_query_rows'];assert rec['computed_query_rows']==computed
 tier=min(t for t in c['graph_tiers'] if t>=computed);assert rec['graph_rows']==tier
 assert math.isclose(rec['assumed_round_ms'],c['fixed_ms']+c['ms_per_executed_row']*tier)
 assert math.isclose(rec['expected_total_tokens_per_second'],sum(expected)*1000/rec['assumed_round_ms'])
for rows,flops in c['ffn_matmul_flops_at_graph_rows'].items():assert flops==3*2*int(rows)*cfg['hidden_size']*cfg['intermediate_size']
assert c['shared_graph_rows']==min(t for t in c['graph_tiers'] if t>=max(c['dp_peer_query_rows'],c['scenarios']['compact']['computed_query_rows']))
assert c['scenarios']['compact']['expected_total_tokens_per_second']>c['scenarios']['full']['expected_total_tokens_per_second']>c['scenarios']['cap_accept']['expected_total_tokens_per_second']
assert math.isclose(c['sglang_2025_overlap_relative_improvement'],c['sglang_2025_overlap_tokens_per_second']/c['sglang_2025_baseline_tokens_per_second']-1)
# Same request multiset, different temporal composition; independent integer counts.
c=a['workload_mix_teaching'];A,B=c['classes']['A'],c['classes']['B'];duration=c['window_seconds'];Pcap=c['assumed_prefill_input_tokens_per_second_per_instance'];Dcap=c['assumed_decode_output_tokens_per_second_per_instance']
for name,windows in c['traces'].items():
 assert sum(sum(w) for w in windows)==c['total_requests']==2*duration*c['request_rate_rps']
 assert all(sum(w)==duration*c['request_rate_rps'] for w in windows)
 assert all(sum(w[i] for w in windows)==c['requests_per_class'] for i in (0,1))
 for field in ['input','output']:
  assert sum(w[0]*A[field+'_tokens']+w[1]*B[field+'_tokens'] for w in windows)/c['total_requests']==c['global_mean_'+field+'_tokens']
for key,counts in [('uniform',c['traces']['uniform'][0]),('shifted_first',c['traces']['shifted'][0]),('shifted_second',c['traces']['shifted'][1])]:
 rec=c['rates'][key]
 for field in ['input','output']:assert math.isclose(rec[field],(counts[0]*A[field+'_tokens']+counts[1]*B[field+'_tokens'])/duration)
 assert math.isclose(rec['P'],rec['input']/Pcap) and math.isclose(rec['D'],rec['output']/Dcap)
assert c['mean_candidate_P']==math.ceil(c['rates']['uniform']['P']);assert c['mean_candidate_D']==math.ceil(c['rates']['uniform']['D'])
capacity=c['mean_candidate_D']*Dcap;assert c['decode_capacity_output_tokens_per_second']==capacity
backlog=0
for counts in c['traces']['shifted']:
 backlog=max(0,backlog+counts[0]*A['output_tokens']+counts[1]*B['output_tokens']-duration*capacity)
assert backlog==c['second_window_end_output_token_backlog']==79872
assert math.isclose(c['second_window_excess_output_tokens_per_second'],c['rates']['shifted_second']['output']-capacity)
assert c['no_further_work_drain_seconds']==backlog/capacity==13
assert c['fixed_window_candidate_P']==math.ceil(max(x['P'] for x in c['rates'].values()))
assert c['fixed_window_candidate_D']==math.ceil(max(x['D'] for x in c['rates'].values()))
assert c['second_window_reconfigured_P']*Pcap>c['rates']['shifted_second']['input'] and c['second_window_reconfigured_D']*Dcap>c['rates']['shifted_second']['output']
# Communication tuning: workload-derived sizes, concurrent join, and search payback.
c=a['communication_tuning_teaching'];cfg=json.loads((ROOT/c['config']).read_text())
assert cfg['intermediate_size']%c['tp']==0 and cfg['hidden_size']%c['tp']==0
assert c['allreduce_input_bytes']==c['tokens']*cfg['hidden_size']*c['bytes_per_element']==8*2**20
assert c['ffn_matmul_flops_per_rank']==3*2*c['tokens']*cfg['hidden_size']*(cfg['intermediate_size']//c['tp'])==38654705664
for v in c['configurations'].values():
 assert v['joined_ms']==max(v['concurrent_compute_ms'],v['concurrent_communication_ms'])
 assert v['concurrent_compute_ms']>=c['isolated_compute_ms'] and v['concurrent_communication_ms']>=v['isolated_communication_ms']
A,B=c['configurations']['A'],c['configurations']['B']
assert math.isclose(c['isolated_communication_speedup_B_over_A'],A['isolated_communication_ms']/B['isolated_communication_ms'])
assert math.isclose(c['joined_slowdown_B_over_A'],B['joined_ms']/A['joined_ms'])
saved=B['joined_ms']-A['joined_ms'];assert math.isclose(saved,c['saved_per_joined_fragment_ms'])
threshold=c['strict_break_even_executions'];assert (threshold-1)*saved<=c['extra_tuning_ms']<threshold*saved
for n,net in c['net_saved_ms_at_remaining_executions'].items():assert math.isclose(net,int(n)*saved-c['extra_tuning_ms'])
assert math.isclose(c['corresponding_time_reduction_fraction'],1-1/c['reported_paper_speedup'])
# Logical tensor resharding and bounded asynchronous checkpoint production.
c=a['checkpoint_layout_teaching'];cfg=json.loads((ROOT/c['config']).read_text());rows,cols=c['shape'];assert (rows,cols)==(cfg['intermediate_size'],cfg['hidden_size'])
assert c['parameter_count']==rows*cols;assert c['weight_bytes']==rows*cols*c['weight_element_bytes']==96*2**20
assert c['model_and_optimizer_bytes']==rows*cols*(c['weight_element_bytes']+c['fp32_optimizer_arrays']*c['optimizer_element_bytes'])==672*2**20
assert c['source_shard_bytes']==c['weight_bytes']/c['source_tp']==24*2**20;assert c['target_shard_bytes']==c['weight_bytes']/c['target_tp']==12*2**20
end=0;source_coverage={r:[] for r in range(c['source_tp'])}
for r,shard in enumerate(c['target_shards']):
 assert shard['rank']==r;lo,hi=shard['global_rows'];assert lo==end and hi-lo==rows//c['target_tp'];end=hi
 assert shard['source_rank']==lo//(rows//c['source_tp']);assert shard['source_byte_offset']==(lo-shard['source_rank']*(rows//c['source_tp']))*cols*c['weight_element_bytes'];assert shard['bytes']==c['target_shard_bytes']
 source_coverage[shard['source_rank']].append((shard['source_byte_offset'],shard['source_byte_offset']+shard['bytes']))
assert end==rows
for pieces in source_coverage.values():assert sorted(pieces)==[(0,12*2**20),(12*2**20,24*2**20)]
c=a['checkpoint_pipeline_teaching'];assert c['weights_bytes']==c['rounded_parameters']*c['weight_bytes_per_parameter']==16e9
assert c['checkpoint_bytes']==c['rounded_parameters']*(c['weight_bytes_per_parameter']+c['optimizer_arrays']*c['optimizer_bytes_per_array_element'])==112e9
assert c['upload_seconds']==c['checkpoint_bytes']/c['storage_effective_bytes_per_second']==14
assert c['state_generation_bytes_per_second']==[c['checkpoint_bytes']/t for t in c['snapshot_period_seconds']]==[11.2e9,5.6e9]
assert c['unbounded_queue_growth_bytes_per_second']==[max(0,v-c['storage_effective_bytes_per_second']) for v in c['state_generation_bytes_per_second']]==[3.2e9,0]
assert c['api_return_seconds']==[t+c['blocking_stage_seconds'] for t in c['snapshot_capture_seconds']]
assert c['durable_seconds']==[t+c['upload_seconds'] for t in c['api_return_seconds']]==[34.5,54.5]
assert c['double_bandwidth_durable_seconds']==[t+c['upload_seconds']/2 for t in c['api_return_seconds']]==[27.5,47.5]
assert c['last_recoverable_capture_seconds']==[max(cap for cap,done in zip(c['snapshot_capture_seconds'],times) if done<c['failure_seconds']) for times in [c['durable_seconds'],c['double_bandwidth_durable_seconds']]]==[20,40]

# Original post and mirror represent the same question source.
proof_dir=ROOT/'references/interviews/2026-09-08/third-pass';proof=json.loads((proof_dir/'question-provenance-check.json').read_text())
doc=BeautifulSoup((proof_dir/proof['original']).read_text(),'html.parser')
for el in doc(['script','style']):el.decompose()
visible=' '.join(doc.get_text(' ',strip=True).split());blocks=json.loads((proof_dir/proof['mirror']).read_text())['tweet']['article']['content']['blocks']
assert proof['ordered_question_items']==sum(x['type']=='ordered-list-item' for x in blocks)==35
assert proof['blocks']==[{'block_key':x['key'],'visible_original_contains_text':' '.join(x['text'].split()) in visible} for x in blocks]
assert all(x['visible_original_contains_text'] for x in proof['blocks'])
for year in [2025,2026]:
 rows=list(csv.DictReader((ROOT/f'research/2026-infra-survey/screening-mlsys-{year}.tsv').open(),delimiter='\t'));papers=json.loads((ROOT/f'references/proceedings/MLSys/{year}/manifest.json').read_text())['papers'];assert [int(row['number']) for row in rows]==list(range(1,len(rows)+1))
 assert len(rows)==sum('screening' in p for p in papers)
 for row in rows:
  p=papers[int(row['number'])-1];assert p['screening']['basis']=='title_and_full_abstract';assert p['screening']['decision']==row['decision'] and p['screening']['reason']==row['reason'];assert (p['reading_status']=='selected_sections_read')==('selected_reading' in p)
# Bind multimodal payloads to the fixed model configuration; capacity is not access volume.
c=a['multimodal_stage_teaching'];cfg=json.loads((ROOT/c['config']).read_text());pre=json.loads((ROOT/c['preprocessor']).read_text());v=cfg['vision_config'];t=cfg['text_config'];h,w=c['processed_image_hw']
assert v['patch_size']==pre['patch_size']==16 and v['spatial_merge_size']==pre['merge_size']==2
assert pre['size']['shortest_edge']<=h*w<=pre['size']['longest_edge'] and h%(v['patch_size']*v['spatial_merge_size'])==w%(v['patch_size']*v['spatial_merge_size'])==0
assert c['temporal_grid']==1 and c['patches']==c['temporal_grid']*(h//v['patch_size'])*(w//v['patch_size'])
assert c['visual_tokens']==c['patches']//v['spatial_merge_size']**2==400
assert t['hidden_size']==v['out_hidden_size']==2560
assert c['main_embedding_bytes']==c['visual_tokens']*v['out_hidden_size']*c['element_bytes']
assert c['full_encoder_bytes']==c['main_embedding_bytes']*(1+len(v['deepstack_visual_indexes']))==8192000
assert c['full_encoder_mib']==c['full_encoder_bytes']/2**20
assert c['image_upload_seconds']==8*c['compressed_image_bytes']/c['uplink_effective_bits_per_second']
assert c['encoder_upload_seconds']==8*c['full_encoder_bytes']/c['uplink_effective_bits_per_second']
assert math.isclose(c['dc_encoder_transfer_ms'],1000*c['full_encoder_bytes']/c['dc_effective_oneway_bytes_per_second'])
kv=2*t['num_hidden_layers']*t['num_key_value_heads']*t['head_dim']*c['element_bytes']
assert c['kv_bytes_per_position']==kv and c['image_positions_kv_mib']==kv*c['visual_tokens']/2**20
assert c['four_image_ec_mib']==c['images_per_request']*c['full_encoder_mib']
assert c['four_image_kv_mib']==c['images_per_request']*c['image_positions_kv_mib']
assert c['total_input_kv_mib']==(c['images_per_request']*c['visual_tokens']+c['extra_text_positions'])*kv/2**20
pool=c['pool'];assert pool['ec_bytes_per_request']==c['images_per_request']*c['full_encoder_bytes'];assert pool['link_capacity_rps']==pool['shared_link_bytes_per_second']/pool['ec_bytes_per_request']
for plan in pool['plans'].values():
 assert plan['e_gpus']+plan['pd_gpus']==pool['total_gpus']
 for hit,rate in plan['at_hit_fraction'].items():
  limits=[plan['e_gpus']*pool['encoder_miss_images_per_second_per_gpu']/(c['images_per_request']*(1-float(hit))),plan['pd_gpus']*pool['pd_requests_per_second_per_gpu'],pool['link_capacity_rps']]
  assert math.isclose(rate,min(limits))
j=c['joint_timing'];assert j['ideal_no_interference_ms']==max(j['decode_solo_ms'],j['encode_solo_ms'])<j['step_budget_ms']<j['assumed_joint_ms']<j['serial_ms']==j['decode_solo_ms']+j['encode_solo_ms']
d=c['dlo_report_recalculation'];assert math.isclose(d['throughput_ratio'],(d['outputs_per_wave'][0]/d['wave_seconds'][0])/(d['outputs_per_wave'][1]/d['wave_seconds'][1]));assert math.isclose(d['wave_latency_ratio'],d['wave_seconds'][0]/d['wave_seconds'][1])
# Physical pages for newly selected MLSys readings; formfeed offsets are unreliable.
for catalog in ROOT.glob('references/proceedings/MLSys/*/manifest.json'):
 for paper in json.loads(catalog.read_text())['papers']:
  reading=paper.get('selected_reading',{});hashes=reading.get('page_text_sha256',{})
  if hashes:
   assert sorted(map(int,hashes))==reading['physical_pdf_pages']
   for page,expected in hashes.items():
    data=subprocess.check_output(['pdftotext','-f',page,'-l',page,str(ROOT/'references'/paper['pdf']['file']),'-'],timeout=30)
    assert hashlib.sha256(data).hexdigest()==expected

paper_proof=json.loads((ROOT/'references/framework-history/2026-09-08/structured-generation/paper-reading.json').read_text())
xgrammar=next(p for p in json.loads((ROOT/'references/proceedings/MLSys/2025/manifest.json').read_text())['papers'] if p['pdf']['file']==paper_proof['pdf']['file'])
assert paper_proof['reading']==xgrammar['selected_reading'] and paper_proof['pdf']==xgrammar['pdf']
figure=paper_proof['figure_view'];assert hashlib.sha256((ROOT/figure['file']).read_bytes()).hexdigest()==figure['sha256']

usenix_reading=[]
for screening in sorted(ROOT.glob('research/2026-infra-survey/screening-*.tsv')):
 match=re.fullmatch(r'screening-(osdi|nsdi)-(202[456])\.tsv',screening.name)
 if not match:continue
 venue,year=match[1].upper(),int(match[2]);directory=ROOT/f'references/proceedings/{venue}/{year}';j=json.loads((directory/'manifest.json').read_text());papers=[p for p in j['entries'] if p.get('entry_type')=='paper']
 raw=(ROOT/'references'/j['index']['file']).read_bytes();assert hashlib.sha256(raw).hexdigest()==j['index']['sha256'];official={}
 for article in BeautifulSoup(raw,'html.parser').select('article.node-paper'):
  title=article.select_one('h2 a[href]');desc=article.select_one('.field-name-field-paper-description-long')
  if title and desc:official[urljoin(j['index']['url'],title['href'])]=desc.get_text('\n',strip=True)
 rows=list(csv.DictReader(screening.open(),delimiter='\t'));assert [int(r['number']) for r in rows]==list(range(1,len(rows)+1));assert len(rows)==sum('screening' in p for p in papers)
 compared=0;differences=[]
 for row,p in zip(rows,papers):
  assert p['abstract']==official[p['source_page']] and p['abstract'].strip();assert p['first_page_title_verified']
  assert p['screening']['basis']=='title_and_full_abstract';assert p['screening']['decision']==row['decision'] and p['screening']['reason']==row['reason'];assert (p['reading_status']=='selected_sections_read')==('selected_reading' in p)
  if 'selected_reading' not in p:continue
  r=p['selected_reading'];assert r['individual_physical_pages']==[x['individual_page'] for x in r['page_text_comparison']];assert r['volume_physical_pages']==[x['volume_page'] for x in r['page_text_comparison']]
  for pair in r['page_text_comparison']:
   assert pair['volume_page']==p['volume_start_page']+pair['individual_page']-2
   for kind,pdf in [('individual',ROOT/r['individual_pdf']),('volume',directory/'volume.pdf')]:
    n=pair[f'{kind}_page'];text=subprocess.check_output(['pdftotext','-raw','-f',str(n),'-l',str(n),str(pdf),'-'],text=True,timeout=30);assert hashlib.sha256(re.sub(r'\s+','',text).encode()).hexdigest()==pair[f'{kind}_normalized_text_sha256']
   assert pair['match']==(pair['individual_normalized_text_sha256']==pair['volume_normalized_text_sha256']);compared+=1
   if not pair['match']:
    assert r.get('version_note');differences.append({'id':p['id'],'individual_page':pair['individual_page'],'volume_page':pair['volume_page'],'note':r['version_note']})
 usenix_reading.append({'venue':venue,'year':year,'abstracts_screened':len(rows),'selected_sections_read':sum('selected_reading' in p for p in papers),'selected_pages_compared':compared,'documented_text_differences':differences})
# Check aggregate prose against the six authoritative catalogs and physical PDFs.
usenix_catalog_papers=0;usenix_volume_pages=0
for venue in ['OSDI','NSDI']:
 for year in [2024,2025,2026]:
  directory=ROOT/f'references/proceedings/{venue}/{year}'
  catalog=json.loads((directory/'manifest.json').read_text())
  usenix_catalog_papers+=sum(p.get('entry_type')=='paper' for p in catalog['entries'])
  info=subprocess.check_output(['pdfinfo',str(directory/'volume.pdf')],text=True,stderr=subprocess.PIPE,timeout=15)
  usenix_volume_pages+=int(re.search(r'^Pages:\s+(\d+)',info,re.M)[1])
summary=(ROOT/'references/proceedings/README.md').read_text()
assert int(re.search(r'六卷包含 (\d+) 篇正式论文',summary)[1])==usenix_catalog_papers
assert int(re.search(r'整卷共 ([\d,]+) 个 PDF 页面',summary)[1].replace(',',''))==usenix_volume_pages
discovery=[]
for f in ROOT.glob('references/proceedings/discovery/*/program-index.json'):
 j=json.loads(f.read_text())
 for group in j['programs']:
  assert hashlib.sha256((ROOT/group['source_file']).read_bytes()).hexdigest()==group['source_sha256'];assert group['count']==len(group['entries']);assert all(p['reading_status']=='program_entry_extracted_not_screened' for p in group['entries'])
 discovery.append({'index':str(f.relative_to(ROOT)),'programs':len(j['programs']),'program_entries':sum(g['count'] for g in j['programs']),'reading_tracked_in_venue_manifests':True})
from verify_catalogs import verify as verify_catalogs
catalog_review=verify_catalogs()
from verify_asplos2025 import verify as verify_asplos2025
asplos2025_metadata=verify_asplos2025()
from verify_asplos2025_public import verify as verify_asplos2025_public
asplos2025_public=verify_asplos2025_public()
from verify_heterogeneous_pipelines import verify as verify_heterogeneous_pipelines
heterogeneous_pipelines=verify_heterogeneous_pipelines()
from verify_sequence_npu import verify as verify_sequence_npu
sequence_npu=verify_sequence_npu()
from verify_qwen_request_accounting import verify as verify_qwen_request_accounting
qwen_request_accounting=verify_qwen_request_accounting()
from verify_spindle import verify as verify_spindle
spindle=verify_spindle()
from verify_ascend_components import verify as verify_ascend_components
ascend_components=verify_ascend_components()
from verify_snapshot_residency import verify as verify_snapshot_residency
snapshot_residency=verify_snapshot_residency()
from verify_tuning_measurement import verify as verify_tuning_measurement
tuning_measurement=verify_tuning_measurement()
from verify_lora_admission import verify as verify_lora_admission
lora_admission=verify_lora_admission()
from verify_nonlinear_resources import verify as verify_nonlinear_resources
nonlinear_resources=verify_nonlinear_resources()
from verify_trace_identification import verify as verify_trace_identification
trace_identification=verify_trace_identification()
from verify_pipellm_preparation import verify as verify_pipellm_preparation
pipellm_preparation=verify_pipellm_preparation()
from verify_isca2024 import verify as verify_isca2024
isca2024=verify_isca2024()
from verify_isca2025 import verify as verify_isca2025
isca2025=verify_isca2025()
from verify_kv_quantization import verify as verify_kv_quantization
kv_quantization=verify_kv_quantization()
from verify_hybrid_state import verify as verify_hybrid_state
hybrid_state=verify_hybrid_state()
from verify_micro2024 import verify as verify_micro2024
micro2024=verify_micro2024()
from verify_micro2025 import verify as verify_micro2025
micro2025=verify_micro2025()
from verify_asplos2026 import verify as verify_asplos2026
asplos2026=verify_asplos2026()
abstracts_screened_total=sum(p['abstracts_screened'] for p in stats)+sum(p['abstracts_screened'] for p in usenix_reading)+catalog_review['asplos2024']['abstracts_screened']+asplos2025_public['primary_abstracts_screened']+isca2024['primary_abstracts_screened']+isca2025['primary_abstracts_screened']+micro2024['primary_abstracts_screened']+micro2025['primary_abstracts_screened']
selected_reading_total=sum(p['selected_sections_read'] for p in stats)+sum(p['selected_sections_read'] for p in usenix_reading)+catalog_review['asplos2024']['selected_sections_read']+asplos2025_public['selected_sections_read']+isca2024['selected_sections_read']+isca2025['selected_sections_read']+micro2024['selected_sections_read']+micro2025['selected_sections_read']
abstracts_screened_total+=asplos2026['primary_abstracts_screened']
selected_reading_total+=asplos2026['selected_sections_read']
report={'verified_at':datetime.now(timezone.utc).isoformat(),'scope':'Archived and screened phases only; long-running goal remains active. USENIX full physical-volume audit is separate; selected pages checked here.','mlsys':stats,'usenix_reading':usenix_reading,'usenix_catalog_totals':{'papers':usenix_catalog_papers,'volume_pages':usenix_volume_pages,'summary_prose_matches':True},'pdf_bytes':totalbytes,'new_document_local_links':links,'source_map_rows':len(ids),'arithmetic':'passed','pagination_notes':pagination_notes,'conference_entry_discovery':discovery,'catalog_review':catalog_review,'asplos2025_metadata':asplos2025_metadata,'asplos2025_public':asplos2025_public,'abstracts_screened_total':abstracts_screened_total,'selected_reading_total':selected_reading_total,'errors':errors}
report['isca2024']=isca2024
report['isca2025']=isca2025
report['micro2024']=micro2024
report['micro2025']=micro2025
report['asplos2026']=asplos2026
report['kv_quantization']=kv_quantization
report['hybrid_state']=hybrid_state
report['ascend_components']=ascend_components
report['snapshot_residency']=snapshot_residency
report['tuning_measurement']=tuning_measurement
report['lora_admission']=lora_admission
report['nonlinear_resources']=nonlinear_resources
report['trace_identification']=trace_identification
report['pipellm_preparation']=pipellm_preparation
report['interview_ninth']=interview_ninth
report['interview_tenth']=interview_tenth
(Path(__file__).parent/'archive-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(report,ensure_ascii=False,indent=2));assert not errors
