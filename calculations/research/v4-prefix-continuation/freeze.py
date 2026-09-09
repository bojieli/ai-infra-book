"""Generate finite continuation examples and original-source bindings."""
import ast
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
p = HERE / 'src/infra_calc/topics/v4_prefix_continuation.py'
spec = importlib.util.spec_from_file_location('candidate', p)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
(HERE / 'results').mkdir(exist_ok=True)
scenarios = [dict(id='v4-prefix-flash-6144-2048'),
             dict(id='v4-prefix-pro-boundary', model='deepseek-v4-pro', prefix_tokens=125, new_tokens=5),
             dict(id='v4-prefix-flash-batch-boundary', prefix_tokens=127, new_tokens=2, batch=3)]
summary = []
for scene in scenarios:
    r = m.calculate(**{k: v for k, v in scene.items() if k != 'id'})
    (HERE / 'results' / (scene['id'] + '.json')).write_text(json.dumps(r, ensure_ascii=False, indent=2, allow_nan=False) + '\n')
    summary.append(dict(id=scene['id'], summary=r['summary'],
                        boundaries={k: dict(count=len(v), first=v[0] if v else None, last=v[-1] if v else None)
                                    for k, v in r['compression_boundaries'].items()}))
(HERE / 'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n')
(HERE / 'scenarios.json').write_text(json.dumps(scenarios, indent=2) + '\n')
files = []
for model in ('deepseek-v4-flash', 'deepseek-v4-pro'):
    path = ROOT / 'calculations/sources' / model / 'inference/model.py'
    lines = path.read_text().splitlines()
    files.append(dict(file=str(path.relative_to(ROOT)), sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                      excerpts=[dict(start_line=a, end_line=b, text='\n'.join(lines[a-1:b]))
                                for a, b in [(35, 40), (299, 304), (316, 377), (399, 399), (473, 474), (518, 533), (801, 809)]]))
(HERE / 'source-proof.json').write_text(json.dumps(files, ensure_ascii=False, indent=2) + '\n')
print(json.dumps(summary[0], ensure_ascii=False, indent=2))
