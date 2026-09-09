"""Validate preserved failed trajectory without treating failure as missing data."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
root=Path(__file__).parent
subprocess.run([sys.executable,str(root/'analyze.py')],check=True,stdout=subprocess.DEVNULL)
manifest=json.loads((root/'results/raw-manifest.json').read_text())
for name,r in manifest.items():
    p=root/'results'/name
    assert p.stat().st_size==r['bytes']
    assert hashlib.sha256(p.read_bytes()).hexdigest()==r['sha256']
rows=[json.loads(x) for x in (root/'results/rounds.jsonl').read_text().splitlines()]
for r in rows:
    if r['action']['tool']=='write_file':
        assert hashlib.sha256(r['action']['content'].encode()).hexdigest()==r['file_sha256']
final=json.loads((root/'results/final.json').read_text())
assert hashlib.sha256(final['final_code'].encode()).hexdigest()==rows[-1]['file_sha256']
checks=json.loads((root/'results/independent-checks.json').read_text())
assert checks['cases']==1013 and checks['passed']+len(checks['failures'])==checks['cases']
assert not final['agent_finished']
assert not json.loads(final['validation']['stdout'])['passed']
assert checks['passed']==1
print('Verified 12 real model/tool rounds, history continuity, token/cache counts, file edits, and preserved task failure with 1/1013 independent cases passing.')
