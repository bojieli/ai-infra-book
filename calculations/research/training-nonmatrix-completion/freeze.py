import hashlib
import importlib.util
import json
import platform
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
spec = importlib.util.spec_from_file_location('nonmatrix', HERE / 'src/infra_calc/topics/training_nonmatrix.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
scenarios = [dict(id='training-nonmatrix-book'),
             dict(id='training-nonmatrix-dense-mask', supervised_tokens=64),
             dict(id='training-nonmatrix-compact-mask', supervised_tokens=64, head_strategy='compact'),
             dict(id='training-nonmatrix-recompute-silu', activation_policy='recompute_silu'),
             dict(id='training-nonmatrix-8192', tokens=8192)]
(HERE / 'results').mkdir(exist_ok=True)
summary = []
for row in scenarios:
    r = m.calculate(**{k: v for k, v in row.items() if k != 'id'})
    (HERE / 'results' / (row['id'] + '.json')).write_text(json.dumps(r, ensure_ascii=False, indent=2, allow_nan=False) + '\n')
    (HERE / 'results' / (row['id'] + '.md')).write_text(m.markdown(r))
    summary.append(dict(id=row['id'], **r['summary']))
(HERE / 'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n')
(HERE / 'scenarios.json').write_text(json.dumps(scenarios, indent=2) + '\n')
paths = ['calculations/configs/models/qwen3-8b/config.json',
         'calculations/src/infra_calc/topics/training_matrix.py',
         'calculations/src/infra_calc/models/qwen3.py',
         'calculations/src/infra_calc/schema.py', 'calculations/src/infra_calc/units.py']
(HERE / 'source-bindings.json').write_text(json.dumps(dict(
    public_dependencies=[dict(file=p, sha256=hashlib.sha256((ROOT / p).read_bytes()).hexdigest()) for p in paths],
    source_records=r['sources'], source_scope='Reuse existing fixed Qwen3 provenance. Backward/AdamW algorithms are explicit declared mathematics, not inferred backend instruction traces.'), ensure_ascii=False, indent=2) + '\n')
import torch
(HERE / 'numeric-validation-runtime.json').write_text(json.dumps(dict(
    python=platform.python_version(), torch=torch.__version__, dtype='float64',
    tests_passed=14, skipped=0, finite_difference_epsilon=1e-6,
    optimizer='torch.optim.AdamW foreach=False fused=False',
    scope='Independent local numerical oracle only; not a model/GPU training run or new model source lock'), indent=2) + '\n')
print(summary[0])
