"""Check fixed-source follow-ups without adding paper-reading credit."""
from pathlib import Path
from hashlib import sha256
import json
import subprocess
import sys

BASE = Path(__file__).resolve().parent

def verify():
    results = {}
    for folder in ('root-dspark-execution', 'parallel-mlx-speculation-body'):
        packet = BASE / folder
        run = subprocess.run([sys.executable, '-B', str(packet / 'verify.py')],
                             capture_output=True, text=True, check=True)
        result = json.loads(run.stdout)
        assert result['status'] == 'passed'
        if folder == 'parallel-mlx-speculation-body':
            manifest = json.loads((packet / 'manifest.json').read_text())
            for item in manifest['files']:
                raw = (packet / item['file']).read_bytes()
                assert len(raw) == item['bytes']
                assert sha256(raw).hexdigest() == item['sha256']
            result['manifest_files_checked'] = len(manifest['files'])
        results[folder] = result
    assert results['root-dspark-execution']['source_files'] == 6
    assert results['parallel-mlx-speculation-body']['source_files'] == 14
    return {'status': 'passed', 'new_paper_abstracts': 0, 'new_paper_body_scopes': 0,
            'scope': 'Static source identity, declared reading ranges, own arithmetic; no upstream execution or performance validation.',
            'packets': results}

if __name__ == '__main__':
    print(json.dumps(verify(), ensure_ascii=False, indent=2))
