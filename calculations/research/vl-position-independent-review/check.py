"""Execute only three extracted fixed official position methods on tiny CPU tensors."""
from pathlib import Path
import ast,types,itertools,json,hashlib,importlib.util
import torch
from unittest.mock import patch
R=Path(__file__).resolve().parents[2];O=Path(__file__).parent
source=R/'research/vision-encoding/modeling_qwen3_vl.py';tree=ast.parse(source.read_text());names={'get_vision_position_ids','get_rope_index','compute_3d_position_ids'};methods=[n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name in names];assert len(methods)==3
for n in methods:n.decorator_list=[]
module=ast.Module(body=[ast.ImportFrom(module='__future__',names=[ast.alias(name='annotations')],level=0),*methods],type_ignores=[]);env={'torch':torch,'itertools':itertools};exec(compile(ast.fix_missing_locations(module),str(source),'exec'),env)
class Bare:pass
for n in names:setattr(Bare,n,env[n])
bare=Bare();bare.config=types.SimpleNamespace(vision_config=types.SimpleNamespace(spatial_merge_size=2));bare.rope_deltas=None
spec=importlib.util.spec_from_file_location('candidate',R/'research/vl-position-bridge/position_bridge.py');candidate=importlib.util.module_from_spec(spec);spec.loader.exec_module(candidate)
cases=[]
for h in range(1,5):
 for w in range(1,6):
  for tail in [0,2]:
   segments=[{'kind':'text','tokens':3},{'kind':'image','preprocessed_height':h*32,'preprocessed_width':w*32}]
   if tail:segments.append({'kind':'text','tokens':tail})
   cases.append(segments)
cases.append([{'kind':'text','tokens':2},{'kind':'image','preprocessed_height':64,'preprocessed_width':96},{'kind':'text','tokens':3},{'kind':'image','preprocessed_height':128,'preprocessed_width':32}])
for segments in cases:
 token_types=[];grids=[]
 for s in segments:
  if s['kind']=='text':token_types.extend([0]*s['tokens'])
  else:
   h=s['preprocessed_height']//32;w=s['preprocessed_width']//32;token_types.extend([1]*(h*w));grids.append([1,2*h,2*w])
 ids=torch.zeros((1,len(token_types)),dtype=torch.long);tt=torch.tensor([token_types]);grid=torch.tensor(grids);pos,delta=bare.get_rope_index(ids,tt,grid);c=candidate.calculate(segments,4)
 assert pos[:,0,:].tolist()==c['positions'];assert delta.item()==c['summary']['rope_delta'];bare.rope_deltas=delta
 for i,expected in enumerate(c['summary']['decode_rotary_positions']):
  past=types.SimpleNamespace(get_seq_length=lambda i=i:len(token_types)+i)
  actual=bare.compute_3d_position_ids(None,torch.zeros(1,1,1),past_key_values=past);assert actual[:,0,0].tolist()==[expected]*3
bare.rope_deltas=torch.tensor([[-3]]);aranges=[];orig=torch.arange
with patch.object(torch,'arange',side_effect=lambda *a,**kw:(aranges.append(a) or orig(*a,**kw))):
 bare.compute_3d_position_ids(None,torch.zeros(1,1,1),past_key_values=types.SimpleNamespace(get_seq_length=lambda:9))
assert aranges==[(9,10)]
bare.rope_deltas=None;text_only=bare.compute_3d_position_ids(torch.zeros(1,3,dtype=torch.long),torch.zeros(1,3,1))
assert text_only is None
result={'official_cpu_position_cases':len(cases),'official_consumed_decode_comparisons':len(cases)*3,'positions_and_delta_all_match':True,'single_decode_arange_observed':aranges,'text_only_fresh_direct_model_returns_none':text_only is None,'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'candidate_sha256':hashlib.sha256((R/'research/vl-position-bridge/position_bridge.py').read_bytes()).hexdigest(),'scope':'Extracted official methods execute on CPU; no weights, complete model, tokenizer or GPU execution.'};(O/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print(result)
