"""Recover source/range integrity after interruption; do not execute Ollama."""
from pathlib import Path
from hashlib import sha256, sha1
import json
import subprocess
import sys

BASE = Path(__file__).resolve().parent
sources = json.loads((BASE / 'sources.json').read_text())
tree = {r['path']: r for r in json.loads((BASE / 'provenance/ollama-tree.json').read_text())['tree']}
reading = json.loads((BASE / 'reading.json').read_text())
assert len(sources) == len(reading['read_files']) == 14
for source in sources:
    raw = (BASE / source['local_file']).read_bytes()
    assert len(raw) == source['bytes']
    assert sha256(raw).hexdigest() == source['sha256']
    blob = sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()
    assert blob == source['actual_git_blob_sha1'] == source['expected_git_blob_sha1']
    assert blob == tree[source['repository_path']]['sha']
    assert source['http_status'] == 200
    assert source['revision'] == reading['revision']
    assert '/' + reading['revision'] + '/' in source['url']
total = 0
for record in reading['read_files']:
    raw = (BASE / record['local_file']).read_bytes()
    assert sha256(raw).hexdigest() == record['sha256']
    lines = raw.decode().splitlines(True)
    assert len(lines) == record['total_lines']
    covered = set()
    for scope in record['read_ranges']:
        lo, hi = scope['first_line'], scope['last_line']
        assert 1 <= lo <= hi <= len(lines)
        assert sha256(''.join(lines[lo-1:hi]).encode()).hexdigest() == scope['sha256']
        covered.update(range(lo, hi+1))
    assert len(covered) == record['read_lines']
    total += len(covered)
assert total == reading['summary']['unique_source_lines'] == 3578
run = subprocess.run([sys.executable, str(BASE / 'round_accounting.py')],
                     capture_output=True, text=True, check=True)
assert json.loads(run.stdout) == json.loads((BASE / 'arithmetic.json').read_text())
print(json.dumps({'status': 'passed', 'source_files': 14, 'agent_declared_read_lines': total,
                  'scope': 'Source identity, declared reading spans and own teaching arithmetic; not proof of full root acceptance, upstream tests or measured performance.'}))
