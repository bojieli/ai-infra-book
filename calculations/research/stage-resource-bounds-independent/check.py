"""Independent closed-form, admission and capacity counterexamples; no shared writes."""
from pathlib import Path
import sys,json,hashlib,copy,math
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'src'))
from infra_calc import topics,hardware
from infra_calc.sources import model_config
CANDIDATE=ROOT/'research/stage-resource-bounds/public/src/infra_calc/topics'
topics.__path__.insert(0,str(CANDIDATE))
from infra_calc.topics import stage_resource_bounds as m
OUT=Path(__file__).resolve().parent
checks=[]
def check(label,condition):
 checks.append(dict(check=label,passed=bool(condition)))

def main():
 c=model_config('qwen3-8b');H=c['hidden_size'];L=c['num_hidden_layers'];Q=c['num_attention_heads']*c['head_dim'];K=c['num_key_value_heads']*c['head_dim'];F=c['intermediate_size'];V=c['vocab_size']
 for b,t,s in [(1,1,0),(1,128,0),(4,1,8192),(3,19,17)]:
  r=m.calculate(batch=b,tokens=t,history=s)
  per_layer=2*b*t*(H*Q+2*H*K+Q*H+3*H*F)+4*b*(t*s+t*(t+1)//2)*Q
  expected=L*per_layer+2*b*H*V
  check(f'qwen independent matrix {b,t,s}',r['baseline_work']['matrix_flops']==expected)
  for layer in r['stages'][1:-1]:check(f'qwen per-layer {b,t,s} {layer["id"]}',sum(o['matrix_flops'] for o in layer['operations'])==per_layer)
 r=m.bounds([{'id':'one','work':{'A':10,'B':1}},{'id':'two','work':{'A':1,'B':10,'unknown':0}}],{'A':1,'B':1})
 check('serial-vs-global strict counterexample',(r['accounted_serial_stage_lower_bound_seconds'],r['accounted_global_max_seconds'])==(20,11))
 r=m.bounds([{'id':'one','work':{'A':10,'unknown':None}}],{'A':2,'unknown':1})
 check('unknown work even with supplied rate',r['accounted_serial_stage_lower_bound_seconds'] is None and r['known_global_max_seconds']==5)
 r=m.bounds([{'id':'one','work':{'A':0,'missing_positive':1}}],{})
 check('unknown-zero versus unknown-positive',r['missing_resources']==['missing_positive'])
 base=m.calculate(tokens=1);rates={k:1e10 for s in base['stages'] for k in s['work'] if k.startswith('special:')}
 required=base['capacity']['comparison_bytes'];device=hardware.select_device('h100-sxm')
 for delta in [-1,0,1]:
  fake=copy.deepcopy(device);fake['memory']['capacity_unit']='GiB';fake['memory']['nominal_capacity']=(required+delta)/2**30
  with patch.object(m.hardware,'select_device',return_value=fake):r=m.calculate(tokens=1,assumed_rates=rates)
  check(f'capacity edge {delta}',r['capacity']['comparison_exceeds_nominal']==(delta<0))
  check(f'capacity bound edge {delta}',(r['summary']['necessary_capacity_not_failed_accounted_bound_seconds'] is None)==(delta<0))
 fake=copy.deepcopy(device);fake['memory']['nominal_capacity']=None
 with patch.object(m.hardware,'select_device',return_value=fake):r=m.calculate(tokens=1,assumed_rates=rates)
 check('unknown capacity must not pass capacity-qualified bound',r['summary']['necessary_capacity_not_failed_accounted_bound_seconds'] is None)
 unknown_capacity_observed=r['capacity'];unknown_capacity_bound=r['summary']['necessary_capacity_not_failed_accounted_bound_seconds']
 fake=copy.deepcopy(device);fake['peak_rates']=[p for p in fake['peak_rates'] if p['input_precision'] in ('TF32','INT8') or p['sparsity']=='structured']
 with patch.object(m.hardware,'select_device',return_value=fake):r=m.calculate(tokens=1)
 check('no TF32 or structured substitute',r['precision_admission']['matrix_bf16']['official_peak'] is None and r['precision_admission']['vector_fp32']['official_peak'] is None)
 for kwargs in [dict(device='gb200-superchip'),dict(assumed_rates={'vector_fp32':True}),dict(stage_interface_bytes=[0])]:
  try:m.calculate(**kwargs)
  except ValueError:check('invalid admission '+str(kwargs),True)
  else:check('invalid admission '+str(kwargs),False)
 for b,t,s in [(1,1,0),(2,1,127)]:
  r=m.calculate(model='deepseek-v4-flash',batch=b,tokens=t,history=s)
  check('V4 runtime cannot fail from checkpoint '+str((b,t,s)),r['capacity']['runtime_status']=='runtime_unknown_checkpoint_comparison')
  for layer in r['stages'][1:-1]:
   ops={o['name']:o for o in layer['operations']}
   for name,o in ops.items():
    if o.get('matrix_flops'):
     expected=('FP32' if 'compress' in name or name=='router' or name.startswith('hc:') else 'BF16' if name in ('wo_a_grouped','index_weights_proj','selected_QK_PV','index_rectangular_QK') else 'FP8')
     check('V4 precision '+str((b,t,s))+layer['id']+name,o['input_precision']==expected and o['sparsity']=='dense' and o['accumulator_precision']=='FP32')
  check('V4 traffic unknown propagation '+str((b,t,s)),r['resource_bounds']['accounted_serial_stage_lower_bound_seconds'] is None)
  assumed={k:1e12 for stage in r['stages'] for k in stage['work'] if k!='interface_bytes'}
  condition=m.calculate(model='deepseek-v4-flash',batch=b,tokens=t,history=s,assumed_rates=assumed,stage_interface_bytes=[1]*len(r['stages']))
  check('V4 caller bytes conditional only '+str((b,t,s)),condition['resource_bounds']['accounted_serial_stage_lower_bound_seconds'] is not None and condition['summary']['full_request_latency_bound_seconds'] is None and condition['summary']['necessary_capacity_not_failed_accounted_bound_seconds'] is None)
 source=CANDIDATE/'stage_resource_bounds.py';raw=source.read_bytes();(OUT/'final.snapshot.py').write_bytes(raw)
 result=dict(candidate_sha256=hashlib.sha256(raw).hexdigest(),checks=len(checks),passed=sum(x['passed'] for x in checks),failed=[x for x in checks if not x['passed']],unknown_capacity_observed=unknown_capacity_observed,unknown_capacity_bound=unknown_capacity_bound)
 (OUT/'verification.json').write_text(json.dumps(result,indent=2)+'\n');(OUT/'checks.json').write_text(json.dumps(checks,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
