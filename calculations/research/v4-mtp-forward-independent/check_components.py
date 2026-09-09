"""Independent raw-header recount and MTP composition checks."""
from collections import Counter
from math import prod
from check import c, m, check, checks, HERE, h, d, q, nh, g, o, f, e, k, v, hc
from infra_calc.sources import read_source
import json

index = json.loads(read_source('sources/deepseek-v4-flash/model.safetensors.index.json'))['weight_map']
selected = {name: shard for name, shard in index.items() if name.startswith('mtp.')}
headers = {shard: json.loads(read_source('sources/deepseek-v4-flash/headers/' + shard + '.json')) for shard in set(selected.values())}
raw = {}
for name, shard in selected.items():
    x = headers[shard][name]
    count = prod(x['shape'])
    size = x['data_offsets'][1] - x['data_offsets'][0]
    check('payload:' + name, size == count * {'F32':4,'BF16':2,'F8_E4M3':1,'F8_E8M0':1,'I8':1}[x['dtype']])
    packed = '.ffn.experts.' in name and name.endswith('.weight')
    check('packed interpretation:' + name, (x['dtype'] == 'I8') == packed)
    parameters = 0 if name.endswith('.scale') else count * (2 if packed else 1)
    raw[name] = dict(shape=x['shape'], dtype=x['dtype'], payload_bytes=size, logical_parameters=parameters)
actual = {row['name']: {key:row[key] for key in ('shape','dtype','payload_bytes','logical_parameters')} for row in m.checkpoint()['tensors']}
check('all raw tensor records', actual == raw)
check('complete key count', len(raw) == 1575)
check('raw parameter sum', sum(x['logical_parameters'] for x in raw.values()) == 6610048891)
check('raw payload sum', sum(x['payload_bytes'] for x in raw.values()) == 3593787756)

for b,t,s in ((1,1,0),(2,16,0),(1,129,0),(1,1,128)):
    r=m.calculate(batch=b,tokens=t,start_pos=s)
    n=b*t
    tag=f'{b}/{t}/{s}'
    # Literal router selection/normalization, SwiGLU products, intermediate
    # probability scaling, zero-initialized expert sums and shared output add.
    moe=n*e+n*(3*k-1)+n*(k+1)*f+n*k*f+n*k*h+n*h
    check('MoE scalar:'+tag, r['components']['experts']['non_matrix_summary']['scalar_flops']==moe)
    # Two pre/post branches and one final HC head.
    j=hc*(hc+2)
    iterations=c.get('hc_sinkhorn_iters',20)
    sink=6*hc+2*hc**2+4*hc**2-hc+(2*iterations-1)*(hc*(hc-1)+2*hc**2)
    residual=2*n*((2*hc*h+1)+j+sink+(2*hc-1)*h+(2*hc**2+hc)*h)
    residual+=n*((2*hc*h+1)+4*hc+(2*hc-1)*h)
    check('HC scalar:'+tag, r['components']['hyper_connections']['summary']['scalar_flops']==residual)
    outer=n*(hc+4)*(4*h+1)+n*hc*h
    check('outer norms/add:'+tag,sum(x['scalar_flops'] for x in r['outer_nonmatrix'])==outer)
    # FP8 projection/shared scale application: shared scale product once per
    # output block, followed by multiply/add per output cell and K block.
    fp8=0
    for row in r['fp8_linear_calls']:
        M,K,N=row['rows'],row['input_width'],row['output_width']
        fp8+=M*K+M*(K//128)+M*(N//128)*(K//128)+2*M*N*(K//128)
    routed_quant=n*k*(2*h+f)+n*k*(2*h+f)//128
    routed_scale=3*n*k*(2*f*(h//32)+h*(f//32))
    expected=r['components']['attention']['summary']['accounted_scalar_flops']+moe+residual+outer+fp8+routed_quant+routed_scale
    check('scalar composition:'+tag,r['summary']['accounted_scalar_flops']==expected)
    cells=n*k*(2*h+f)
    check('routed special cells:'+tag,r['routed_activation_quantization_special_ops']==dict(activation_abs_ops=cells,activation_max_comparisons=cells,activation_clamp_comparisons=2*cells,activation_round_scale_calls=cells//128,activation_fp8_cast_elements=cells,activation_e8m0_cast_elements=cells//128))

(HERE/'component-verification.json').write_text(json.dumps(dict(checks=len(checks), names=checks, scope='Raw pinned header recount, MoE/HC/outer/quantization scalar formulas and composition; existing attention subledger is reused, not numerically revalidated here'),indent=2)+'\n')
print(len(checks),'total checks passed')
