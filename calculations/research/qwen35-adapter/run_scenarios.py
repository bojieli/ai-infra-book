"""Independent Qwen3.5 delivery scenarios, no shared result regeneration."""
import json,sys
from pathlib import Path
P=Path(__file__).resolve().parent
sys.path.insert(0,str(P.parents[1]/'src'))
from qwen35_forward import calculate
rows=[dict(id='cold-single-token',inputs=dict(tokens=1)),dict(id='cold-single-record-past',inputs=dict(tokens=1,record_past=True)),dict(id='prefill-8192',inputs=dict(tokens=8192)),dict(id='decode-b1',inputs=dict(tokens=1,history=8192)),dict(id='decode-b64',inputs=dict(batch=64,tokens=1,history=8192)),dict(id='prefix-6144-2048',inputs=dict(tokens=2048,history=6144)),dict(id='chunk-tail-65',inputs=dict(tokens=65)),dict(id='decode-record-past',inputs=dict(tokens=1,history=8192,record_past=True))]
(P/'scenarios.json').write_text(json.dumps(rows,indent=2)+'\n')
(P/'results').mkdir(exist_ok=True)
summary=[]
for row in rows:
 r=calculate(**row['inputs']);(P/'results'/f"{row['id']}.json").write_text(json.dumps(r,indent=2)+'\n')
 summary.append(dict(id=row['id'],matrix_work_subtotal=r['summary']['matrix_flops'],scalar_work_subtotal=r['summary']['scalar_flops'],delta_path=r['execution']['linear_path'],conv_path=r['execution']['conv_path'],state=r['state']))
(P/'scenario-summary.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps(summary,indent=2))
