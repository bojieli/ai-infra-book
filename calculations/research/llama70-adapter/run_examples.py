"""Generate local examples with independently verified official source bytes."""
import hashlib,json
from pathlib import Path
from infra_calc.schema import Scenario
import llama70
O=Path(__file__).resolve().parent;B=O.parents[1]
lock=json.loads((O/'sources.lock.json').read_text())['sources']
for row in lock:
    data=(B/row['file']).read_bytes()
    if len(data)!=row['bytes'] or hashlib.sha256(data).hexdigest()!=row['sha256']:
        raise ValueError('Input provenance mismatch: '+row['file'])
c=json.loads((B/'research/f02-70b-inputs/config.json').read_text())
cases=[{'name':'llama70-prefill-8192','batch':1,'history':0,'tokens':8192,'output_head':'last'},
       {'name':'llama70-decode-8192','batch':1,'history':8192,'tokens':1,'output_head':'last'},
       {'name':'llama70-decode-batch8-32768','batch':8,'history':32768,'tokens':1,'output_head':'last'},
       {'name':'llama70-prefill-all-head-512','batch':1,'history':0,'tokens':512,'output_head':'all'}]
(O/'scenarios.json').write_text(json.dumps({'model':llama70.MODEL,'scenarios':cases},indent=2)+'\n')
summary=[]
for case in cases:
    args={k:v for k,v in case.items() if k!='name'};result=llama70.calculate_from_inputs(c,Scenario(**args),lock)
    (O/(case['name']+'.json')).write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    summary.append({'name':case['name'],**result['summary']})
(O/'example-summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
print(json.dumps([{'name':x['name'],'matrix_flops':x['matrix_flops'],'scalar_flops':x['scalar_flops'],'kv_after':x['kv_resident_after_bytes']} for x in summary],indent=2))
