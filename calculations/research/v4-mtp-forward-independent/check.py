"""Root review: independent closed forms and alternating-call isolation checks."""
from pathlib import Path
import hashlib
import importlib.util
import json
import sys

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[1]
CANDIDATE = HERE.parent / 'v4-mtp-forward'
sys.path.insert(0, str(PROJECT / 'src'))
spec = importlib.util.spec_from_file_location('mtp_candidate', CANDIDATE / 'calculate.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
from infra_calc.sources import model_config, read_source
from infra_calc.topics import experts, hyper_connections, v4_attention

checks = []
def check(name, condition):
    if not condition:
        raise AssertionError(name)
    checks.append(name)

for row in json.loads((CANDIDATE / 'bindings.json').read_text()):
    check('frozen:' + row['file'], hashlib.sha256((PROJECT / row['file']).read_bytes()).hexdigest() == row['sha256'])
c = model_config(m.MODEL, reference=True)
h, d, q, nh, g, o, f, e, k, v, hc = [c[key] for key in (
    'dim', 'head_dim', 'q_lora_rank', 'n_heads', 'o_groups',
    'o_lora_rank', 'moe_inter_dim', 'n_routed_experts',
    'n_activated_experts', 'vocab_size', 'hc_mult')]
before = [fn(m.MODEL, 1, 1) for fn in (experts.calculate, hyper_connections.calculate, v4_attention.calculate)]
cases = [(b, t, s) for b in (1, 2, 4) for t, s in ((1, 0), (2, 0), (127, 0), (128, 0), (129, 0), (1, 127), (1, 128), (1, 4095))]
for b, t, s in cases:
    r = m.calculate(batch=b, tokens=t, start_pos=s)
    tag = f'{b}/{t}/{s}'
    n = b * t
    # Sum scalar dot-product lengths; independent of candidate's helper tables.
    projection = 2*n*(h*q + q*nh*d + h*d + nh*d*o + g*o*h)
    pairs = sum(min(pos+1, c['window_size']) for pos in range(s, s+t))
    attention = projection + 4*b*nh*d*pairs
    moe = 2*n*h*e + 6*n*h*f*(k + c['n_shared_experts'])
    mix = hc*(hc+2)
    connections = 4*n*hc*h*mix + 2*n*hc*h*hc
    outer = 2*n*h*h*(1+hc)
    head = 2*b*h*v
    check('matrix:' + tag, r['summary']['matrix_flops'] == attention+moe+connections+outer+head)
    check('head:' + tag, r['summary']['shared_last_head_flops'] == head)
    check('window:' + tag, r['state']['valid_window_after_bytes'] == b*min(s+t,c['window_size'])*d*2)
    check('write:' + tag, r['state']['cache_write_bytes'] == b*(1 if s else min(t,c['window_size']))*d*2)
    check('outer rows:' + tag, [x['rows'] for x in r['outer_projections']] == [n, n*hc, b])
    check('no latency:' + tag, r['summary']['latency'] is None)
    check('one MTP:' + tag, r['source_layer_id'] == 43 and r['source_ratio'] == 0 and r['components']['experts']['geometry']['moe_layers'] == [43])
for fn, expected in zip((experts.calculate, hyper_connections.calculate, v4_attention.calculate), before):
    check('shared helper unchanged:' + fn.__module__, fn(m.MODEL, 1, 1) == expected)
check('config unchanged', model_config(m.MODEL, reference=True) == c)
for scene in json.loads((CANDIDATE / 'scenarios.json').read_text()):
    r = m.calculate(**{key:value for key,value in scene.items() if key != 'id'})
    check('frozen replay:' + scene['id'], json.loads(json.dumps(r)) == json.loads((CANDIDATE/'results'/(scene['id']+'.json')).read_text()))
(HERE / 'verification.json').write_text(json.dumps(dict(checks=len(checks), cases=len(cases), names=checks, scope='Root independent formula/replay/isolation audit; not complete source-operation or numerical runtime audit'), indent=2)+'\n')
print(len(checks), 'checks passed;', len(cases), 'boundary scenarios')
