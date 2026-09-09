#!/usr/bin/env python3
"""Offline integrity and coverage checks; run.py executes numerical checks."""
import hashlib
import json
import math
from pathlib import Path
root=Path(__file__).resolve().parent
manifest=json.loads((root/'results/provenance.json').read_text())
for name,digest in manifest['sha256'].items():
    assert hashlib.sha256((root/name).read_bytes()).hexdigest()==digest,name
data=json.loads((root/'results/results.json').read_text())
shapes=[(64,64,64),(128,512,64),(256,128,256),(127,257,65)]
methods=[('ijk',0),('ikj',0)]+[('blocked',b) for b in [8,16,32,64,128,256]]
expected={(m,k,n,method,tile) for m,k,n in shapes for method,tile in methods}
assert len(data['rows'])==32
assert {(r['m'],r['k'],r['n'],r['method'],r['tile']) for r in data['rows']}==expected
for r in data['rows']:
    assert len(r['samples_us'])==9
    assert all(math.isfinite(v) and v>0 for v in r['samples_us'])
    assert math.isfinite(r['max_abs_error'])
assert data['environment']['thread_count']==1
print('Verified hashes and 32 measured configurations; numerical validation was executed by matmul.c.')
