import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
assert json.loads((ROOT / 'results/execution.json').read_text())['status'] == 'completed'
assert (ROOT / 'summary.json').exists() and (ROOT / 'timings.png').exists()
manifest = ROOT / 'manifest.json'
assert not manifest.exists(), 'Never overwrite a sealed experiment'
files = {}
for p in sorted(ROOT.rglob('*')):
    if p.is_file() and '__pycache__' not in p.parts and p != manifest:
        files[str(p.relative_to(ROOT))] = {'bytes': p.stat().st_size, 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}
manifest.write_text(json.dumps({'files': files}, indent=2) + '\n')
print('sealed', len(files), 'files')
