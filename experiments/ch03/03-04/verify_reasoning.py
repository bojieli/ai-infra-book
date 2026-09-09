import hashlib
import json
from pathlib import Path
import subprocess
import sys
root=Path(__file__).parent
manifest=json.loads((root/'reasoning-raw-manifest.json').read_text())
for name,entry in manifest.items():
    p=root/name
    assert p.stat().st_size==entry['bytes']
    assert hashlib.sha256(p.read_bytes()).hexdigest()==entry['sha256']
subprocess.run([sys.executable,str(root/'compare_reasoning.py')],check=True,stdout=subprocess.DEVNULL)
r=json.loads((root/'reasoning-comparison.json').read_text())['runs']
assert r[1]['agent_finished'] and r[1]['visible_passed']
assert r[1]['value_and_input_passed']==r[1]['independent_cases']==1013
assert r[1]['independent_passed']==710 and r[1]['truncated_rounds']==1
assert r[1]['reasoning_tokens']==2553
print('Verified reasoning trace, same engine/task controls, exact output-token partition, one truncation, and separate value/nonmutation versus aliasing checks.')
