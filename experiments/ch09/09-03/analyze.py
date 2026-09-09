"""Extract published measurements without treating configurations as timings."""
import hashlib,json,re,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parent
sources=json.loads((ROOT/'sources.json').read_text())
for s in sources:
 name={'kt-amx':'kt-amx.md','kt-kernel-guide':'kt-kernel-guide.md','ktransformers-paper':'ktransformers-paper.pdf'}[s['id']]
 assert hashlib.sha256((ROOT/'source-snapshots'/name).read_bytes()).hexdigest()==s['sha256']
text=subprocess.check_output(['pdftotext','-layout',str(ROOT/'source-snapshots/ktransformers-paper.pdf'),'-'],text=True)
page=text.split('\f')[10]
pattern=r'(DS-3|DS-2|QW-2)\s+\((\d+)\+(\d+)\)\s+(\d+\.\d+)\s+(\d+\.\d+)\s+(\d+\.\d+)\s+(\d+\.\d+)'
rows=[];metrics=['HumanEval','MBPP','GSM8K','StrategyQA']
for m in re.finditer(pattern,page):
 model,immediate,deferred,*scores=m.groups();rows.append(dict(model=model,immediate=int(immediate),deferred=int(deferred),scores=dict(zip(metrics,map(float,scores))),source='ktransformers-paper',pdf_page=11,table=2,precision='INT4' if model=='DS-3' else 'INT8',evidence='published_measurement'))
assert len(rows)==6
expected=[[83,71.2,94.8,83],[83,70.2,95.2,82.9],[80.5,67.6,93.3,79.7],[82.5,66.8,92.8,80.4],[65.7,52.4,84.7,83.6],[67.4,53.4,83.4,82.5]]
assert [list(r['scores'].values()) for r in rows]==expected
changes=[]
for model in ['DS-3','DS-2','QW-2']:
 a,b=[r for r in rows if r['model']==model]
 assert a['deferred']==0 and a['immediate']==b['immediate']+b['deferred']
 changes.append(dict(model=model,delta_percentage_points={k:round(b['scores'][k]-a['scores'][k],6) for k in metrics}))
guide=(ROOT/'source-snapshots/kt-kernel-guide.md').read_text()
assert '2x Intel Xeon Gold 6454S' in guide and 'NVIDIA RTX 4090 24GB' in guide
assert '`--kt-gpu-prefill-token-threshold 2048`' in guide and '--kt-gpu-prefill-token-threshold 4096' in guide
assert 'Both baselines implement a Fiddler-style offloading ap-' in text
report=dict(status='published_records_verified',table2=rows,quality_changes=changes,platforms=[dict(id='guide-main',cpu='2x Xeon Gold 6454S',gpu='RTX 4090 24GB',evidence='configuration_example',revision='31985f40bcc40da08107efdb1f81bf88cb38c6b2',not_a_measured_three_path_comparison=True),dict(id='paper-figure3',cpu='1x Xeon Platinum 8452Y, 36 cores',gpu=None,evidence='CPU_MoE_microbenchmark',tokens_per_expert=[1,2,4,8,16,32,64,128,256,512,1024],exact_curve_digitized=False),dict(id='paper-e2e',cpu='2x Xeon Platinum 8452Y, 36 cores/socket, 1TB DDR5/socket',gpus=['A100 40GB for full precision','RTX 4080 16GB for quantized models'],batch_size=1,input='Wikitext',prefill_lengths='32 to 8192',decode_prompt_tokens=32,max_output_tokens=512,evidence='published_measurement',pcie_32_GBs='theoretical peak, not measured effective transfer')],gaps=['same-platform three-path timings by expert shape and tokens/expert','main-platform quantitative NUMA and PCIe measurements','controlled quality confidence intervals and original per-sample outputs','Expert Deferral per-layer dependency and accuracy reproduction'],guide_inconsistency='rationale threshold 2048, Option A command 4096; not silently reconciled',quality_protocol=dict(HumanEval='0-shot pass@1; temperature 0.3; 10 sampling runs',MBPP='3-shot pass@1; greedy',GSM8K='8-shot exact match; greedy',StrategyQA='4-shot exact match; greedy',confidence_intervals='not supplied in Table 2'))
(ROOT/'records.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(dict(status=report['status'],rows=len(rows),quality_changes=changes),ensure_ascii=False))
