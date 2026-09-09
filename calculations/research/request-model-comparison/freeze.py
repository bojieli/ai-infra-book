import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
spec = importlib.util.spec_from_file_location('comparison', HERE / 'src/infra_calc/topics/request_model_comparison.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
scenarios = [dict(id='request-four-models-book'),
             dict(id='request-four-models-first-output', new_tokens=1, output_tokens=1),
             dict(id='request-four-models-prefix-boundary', prefix_tokens=125, new_tokens=3, output_tokens=4),
             dict(id='request-four-models-prefix-6144-2048', prefix_tokens=6144, new_tokens=2048, output_tokens=4)]
(HERE / 'results').mkdir(exist_ok=True)
summary = []
for row in scenarios:
    r = m.calculate(**{k: v for k, v in row.items() if k != 'id'})
    (HERE / 'results' / (row['id'] + '.json')).write_text(json.dumps(r, ensure_ascii=False, indent=2, allow_nan=False) + '\n')
    (HERE / 'results' / (row['id'] + '.md')).write_text(m.markdown(r))
    summary.append(dict(id=row['id'], rows=[dict(model=x['model'], **x['summary']) for x in r['comparisons']]))
(HERE / 'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n')
(HERE / 'scenarios.json').write_text(json.dumps(scenarios, indent=2) + '\n')
deps = []
for name in ('k3_forward', 'state', 'v4_forward', 'v4_prefix_continuation'):
    p = ROOT / 'calculations/src/infra_calc/topics' / (name + '.py')
    deps.append(dict(file=str(p.relative_to(ROOT)), sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
p = ROOT / 'calculations/src/infra_calc/models/qwen3.py'
deps.append(dict(file=str(p.relative_to(ROOT)), sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
(HERE / 'integration.json').write_text(json.dumps(dict(public_dependencies=deps, tests=9, scenarios=4), indent=2) + '\n')
print([(x['model'], x['matrix_flops'], x['final_state_resident_bytes']) for x in summary[0]['rows']])
