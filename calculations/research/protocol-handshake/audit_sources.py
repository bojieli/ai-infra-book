"""Verify immutable, previously acquired RFC originals used by the candidate."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def audit():
    rows = json.loads((ROOT / 'sources.lock.json').read_text())
    for row in rows:
        data = (ROOT / row['file']).read_bytes()
        if len(data) != row['bytes'] or hashlib.sha256(data).hexdigest() != row['sha256']:
            raise ValueError('Source changed: ' + row['file'])
    return {'status': 'passed', 'official_rfc_originals': len(rows),
            'verified_bytes': sum(row['bytes'] for row in rows),
            'scope': 'Existing fixed official texts; declared message lengths are not RFC measurements'}


if __name__ == '__main__':
    print(json.dumps(audit(), indent=2))
