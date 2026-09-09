"""Verify archived source identity and teaching arithmetic; never import it."""
from pathlib import Path
import hashlib
import json

BASE = Path(__file__).resolve().parent
tree = {r['path']: r for r in json.loads((BASE / 'input-tree.json').read_text())['tree']}
sources = json.loads((BASE / 'sources.json').read_text())
for source in sources:
    raw = (BASE / Path(source['file']).name).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == source['sha256']
    blob = hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()
    assert blob == source['git_blob_sha1'] == tree[source['repository_path']]['sha']
    assert len(raw) == source['bytes'] == tree[source['repository_path']]['size']
for record in json.loads((BASE / 'reading-proof.json').read_text())['files']:
    raw = (BASE / Path(record['file']).name).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == record['sha256']
    lines = raw.decode().splitlines(True)
    for scope in record['ranges']:
        lo, hi = scope['lines_inclusive']
        assert 1 <= lo <= hi <= len(lines)
        assert hashlib.sha256(''.join(lines[lo-1:hi]).encode()).hexdigest() == scope['sha256']
budget = json.loads((BASE / 'budget.json').read_text())
rows = budget['logical_rows']
ceiling = lambda n: next(t for t in (8, 16, 32) if t >= n)
assert rows == [7, 3, 2, 2]
assert budget['budget_above_floor'] == sum(rows) - 4 == 10
assert budget['local_tier'] == ceiling(sum(rows)) == 16
assert budget['joint_tier'] == ceiling(max(sum(rows), budget['other_rank_requirement'])) == 32
assert budget['optional_fill_budget_local'] == min(budget['local_tier'], 28) - 4 == 12
assert budget['optional_fill_budget_joint'] == min(budget['joint_tier'], 28) - 4 == 24
print(json.dumps({'status': 'passed', 'source_files': len(sources),
                  'scope': 'Identity, declared reading ranges and own integer budget only; no upstream test or model execution.'}))
