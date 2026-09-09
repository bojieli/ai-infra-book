"""Create the explicit human-reading declaration and an offline file inventory."""
from pathlib import Path
import json,hashlib,datetime
D=Path(__file__).resolve().parent
sha=lambda b:hashlib.sha256(b).hexdigest()
write=lambda f,x:(D/f).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
paper=next(p for p in json.loads((D/'input-abstracts.json').read_text())['papers'] if p['program_order']==49)
scopes={2:'浮点位串行瓶颈、贡献与前提；全文',3:'CSB／控制与向量存取组织；全文',4:'逻辑与物理 bit slicing、浮点操作背景；全文（以 flow 提取补足 layout 截断）',5:'选择性移位／对齐机制；全文',6:'尾数转换、搜索与归约；全文',7:'乘法复制、式1–2与Listing2；全文',8:'vfmul／vfdot、特殊值与其他函数；全文',9:'微架构修改、表II最终周期、系统／ISA；全文',10:'表III–V、框架未来工作、面积电路和模拟基线；全文',11:'点积峰值、消融、具体模型设置；全文',12:'模型／算子反例、能量与相关工作开头；全文'}
flow={4,6,7,8,9}
texts=[]
for n in range(2,13):
 f=f'page-{n:02d}'+('-flow' if n in flow else '')+'.txt';raw=(D/f).read_bytes();t=raw.decode()
 texts.append({'physical_page':n,'scope':'full_page_text','file':f,'char_range':[0,len(t)],'sha256':sha(raw),'description':scopes[n]})
selected=json.loads((D/'page-13-selection.json').read_text());f=selected['file'];t=(D/f).read_text()
texts.append({'physical_page':13,'scope':'selected_left_column_only','file':f,'char_range':[0,len(t)],'sha256':sha(t.encode()),'selection_recipe':'page-13-selection.json','description':'相关工作延续和结论，止于ACK前；右栏参考文献不纳入正文阅读'})
images={4:['Fig.3','bit-sliced logical/physical organisation'],5:['Fig.4','three-cycle right shift and tags'],6:['Fig.5','Listing1','reduction tree and alignment'],7:['Fig.6','Eq.1','Eq.2','Listing2','replication versus reordered dot'],9:['Fig.7','TableII','extra columns, paths and final cycle equations'],10:['TableIII','TableIV','TableV','data capacity, area-equivalent setup and workloads'],11:['Fig.8','Fig.9','format baseline and ablation scopes'],12:['Fig.10','Fig.11','Fig.12','model/activation slowdowns and energy share']}
claims=[
 ('alignment_state',[3,4,5,6,9],'CSB resident operations still need tag paths, exponent copies, shifts and conversion.'),
 ('multiplication_replication',[7,8,12],'Hybrid multiplication replicates m rows; lower instruction latency alone does not preserve effective vector length.'),
 ('fused_dot',[7,8],'Reorder sums to avoid m-fold input replication; not an HBM-traffic-only argument.'),
 ('final_cycles_and_format',[9,11],'Use final Table II after microarchitecture enhancements, not earlier formulas.'),
 ('capacity_and_memory',[9,10],'9 MiB data/core from structural counts, distributed over110 cores; still80 GB HBM2e/2TB/s.'),
 ('evidence_and_area',[10],'Synthesis plus simulation; Cortex-A53 area proxy and wholeA100 area/SM count allocation; A100 timing theoretical best.'),
 ('workload_limits',[10,11,12],'OPT13B batch256,1024/1024 and sparseattention; underfilled vectors, loadimbalance, activation slowdowns.'),
 ('energy_limits',[12],'240W A100 assumption versus352W modeledFloatAP;62.4%alignment isenergyshare.'),
 ('framework_gap',[9,10],'ManualC/RISCV kernels; BLAS integration futurework, not implementedPyTorch evidence.'),
 ('source_anomalies',[6,7,10],'Listing2 literal finalshift caveat, ResNet18 RNN label retained; noauthorcode correctness conclusion.')]
record={'recorded_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'program_order':49,'doi':paper['doi'],'title':paper['program_title'],'paper_file':'paper.pdf','paper_sha256':paper['source_sha256'],'version_identity':paper['version_identity'],'original_source_url':paper['source_url'],'original_retrieved_at':paper['source_retrieved_at'],'new_http_requests':0,'new_complete_abstracts':0,'available_pdf_physical_pages':14,'full_body_text_pages':list(range(2,13)),'partial_body_text_pages':[13],'unread_body_pages':[1,14],'text_reading':texts,'images_actually_viewed':[{'physical_page':n,'file':f'page-{n:02d}.png','sha256':sha((D/f'page-{n:02d}.png').read_bytes()),'actually_viewed':True,'observations':obs} for n,obs in images.items()],'human_reading_declaration_not_machine_proof':True,'author_source_code_read':False,'downloaded_code_executed':False,'framework_or_gpu_or_simulator_executed':False,'self_written_arithmetic':'budget.py','self_written_offline_verifier':'verify.py','claims':[{'id':i,'physical_pages':p,'bounded_conclusion':c} for i,p,c in claims],'recommendation':{'status':'one_optional_existing_experiment_variant','chapter_anchor':'5.2.1／实验5-2，可回接4.2.5','new_point':'对内部操作数表示的复制计容量与并行位置，融合避开复制。','outline_changed':False,'shared_indices_changed':False,'new_case_or_section_requested':False},'context_snapshots':'context-snapshots.json'}
write('reading.json',record)
write('files.json',[{'file':p.name,'bytes':p.stat().st_size,'sha256':sha(p.read_bytes())} for p in sorted(D.iterdir()) if p.is_file() and p.name not in ['files.json','verification.json']])
print('Wrote reading.json and files.json')
