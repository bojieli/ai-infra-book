import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
assert json.loads((ROOT / 'results/execution.json').read_text())['status'] == 'completed'
summary = json.loads((ROOT / 'summary.json').read_text())
assert summary['formal_output_checks'] == 48 and summary['warmup_output_checks'] == 16
assert summary['speedup_claim_allowed'] is False
assert (ROOT / 'startup.png').exists() and (ROOT / 'policy-review.json').exists()
p = ROOT / 'manifest.json'
assert not p.exists(), 'Do not overwrite a sealed experiment'
files = {}
for f in sorted(ROOT.rglob('*')):
    if f.is_file() and '__pycache__' not in f.parts and f != p:
        files[str(f.relative_to(ROOT))] = {'bytes': f.stat().st_size, 'sha256': hashlib.sha256(f.read_bytes()).hexdigest()}
p.write_text(json.dumps({'files': files}, indent=2) + '\n')
print('sealed', len(files), 'files')
