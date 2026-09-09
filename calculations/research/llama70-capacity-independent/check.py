"""Independent fixed-dimension checks; imports candidate without public writes."""
from pathlib import Path
import contextlib
import hashlib
import importlib.util
import io
import json
import sys
import unittest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
CANDIDATE = ROOT / 'research/llama70-capacity'
sys.path.insert(0, str(ROOT / 'src'))
from infra_calc.topics import capacity_scan as old
spec = importlib.util.spec_from_file_location('infra_calc.topics.capacity_scan', CANDIDATE / 'src/infra_calc/topics/capacity_scan.py')
new = importlib.util.module_from_spec(spec)
spec.loader.exec_module(new)
model = 'deepseek-r1-distill-llama-70b'
r = new.calculate(model)
# Independently enumerate actual checkpoint names and fixed per-matrix geometry.
shapes = {'model.embed_tokens.weight': (128256,8192), 'lm_head.weight': (128256,8192), 'model.norm.weight': (8192,)}
for i in range(80):
    prefix = f'model.layers.{i}.'
    for name, shape in [('self_attn.q_proj',(8192,8192)),('self_attn.k_proj',(1024,8192)),('self_attn.v_proj',(1024,8192)),('self_attn.o_proj',(8192,8192)),('mlp.gate_proj',(28672,8192)),('mlp.up_proj',(28672,8192)),('mlp.down_proj',(8192,28672)),('input_layernorm',(8192,)),('post_attention_layernorm',(8192,))]:
        shapes[prefix+name+'.weight'] = shape
index = json.loads((ROOT / 'sources'/model/'model.safetensors.index.json').read_text())
assert set(shapes) == set(index['weight_map']) and len(shapes) == 723
eligible = {k:v for k,v in shapes.items() if len(v)==2 and k not in ('model.embed_tokens.weight','lm_head.weight')}
assert len(eligible)==560
norms = 161*8192
kept = 2*128256*8192+norms
matrix_elements = sum(n*k for n,k in eligible.values())
assert matrix_elements==68451041280 and kept==2102665216
assert matrix_elements+kept==70553706496
for group in (1, 3, 128, 1000, 32768):
    result = new.calculate(model, group_size=group)
    for fmt in result['storage_formats']:
        bits = fmt['matrix_bits']
        if bits == 16:
            payload,scale = 2*(matrix_elements+kept),0
        else:
            payload = 2*kept + sum(n*((k*bits+7)//8) for n,k in eligible.values())
            scale = sum(n*len(range(0,k,group))*2 for n,k in eligible.values())
        assert (payload,scale)==(fmt['payload_bytes'],fmt['scale_bytes'])
assert new.packed_matrix((3,5),4,4,2)==dict(packed_bytes=9,scale_bytes=12,groups=6)
# Odd row width forbids global packing (15 nibble values globally need8B, per-row9B).
assert new.packed_matrix((3,5),4,4,2)['packed_bytes'] != (15*4+7)//8
kv=80*8*128*2*2*8192
assert kv==2684354560
weight=39500398592
base=weight+2*2**30
thresholds=[base-1,base,base+kv-1,base+kv,base+3*kv-1,base+3*kv]
a=new.calculate(model,capacities=thresholds)
rows=[v for v in a['capacity_comparisons'] if v['matrix_bits']==4]
assert [v['maximum_requests'] for v in rows]==[0,0,0,1,2,3]
assert [v['weights_and_workspace_fit'] for v in rows]==[False,True,True,True,True,True]
b=new.calculate(model,capacities=[48*10**9,48*2**30])
assert [v['maximum_requests'] for v in b['capacity_comparisons'] if v['matrix_bits']==4]==[2,3]
for m in ('qwen3-8b','qwen3-30b-a3b','qwen3-235b-a22b'):
    assert new.calculate(m)==old.calculate(m)
# Exercise existing CLI/report with the candidate injected into its public name.
sys.modules[spec.name]=new
import infra_calc.topics
infra_calc.topics.capacity_scan=new
from infra_calc import cli
buf=io.StringIO()
with contextlib.redirect_stdout(buf):
    cli.main(['capacity-scan','--model',model,'--format','md'])
assert '39500398592' in buf.getvalue() or '39,500,398,592' in buf.getvalue()
(HERE / 'cli-report.md').write_text(buf.getvalue())
suite=unittest.defaultTestLoader.discover(str(CANDIDATE/'tests'),pattern='test_llama70_capacity.py')
test_result=unittest.TextTestRunner().run(suite)
assert test_result.wasSuccessful()
files=[CANDIDATE/'src/infra_calc/topics/capacity_scan.py',CANDIDATE/'tests/test_llama70_capacity.py',ROOT/'src/infra_calc/models/llama70.py',ROOT/'configs/models'/model/'config.json',ROOT/'sources'/model/'model.safetensors.index.json']
result=dict(checkpoint_names=723,eligible_matrices=560,parameters=matrix_elements+kept,kept_bf16_parameters=kept,kv_bytes_8192=kv,group_sizes_checked=[1,3,128,1000,32768],decimal48gb_requests=2,binary48gib_requests=3,original_candidate_tests=test_result.testsRun,qwen_exact_equivalence_models=3,cli_markdown_pass=True,sha256={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files})
(HERE/'results.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
