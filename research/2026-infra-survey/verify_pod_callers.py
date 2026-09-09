"""Verify fixed source identities and declared partial caller reading."""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[2]
D = ROOT / 'references/framework-history/2026-09-09/pod-callers'


def verify():
    sources = json.loads((D / 'sources.json').read_text())
    assert len(sources) == 9
    for s in sources:
        b = (ROOT / s['file']).read_bytes()
        assert s['status_code'] == 200 and len(b) == s['bytes']
        assert hashlib.sha256(b).hexdigest() == s['sha256']
        if 'repo_path' in s:
            commit = json.loads((D / (s['framework'] + '-commit.json')).read_text())
            tree = json.loads((D / (s['framework'] + '-root-tree.json')).read_text())
            assert tree['truncated'] is False
            assert commit['sha'] == s['commit'] and tree['sha'] == commit['commit']['tree']['sha']
            blobs = {r['path']: r['sha'] for r in tree['tree'] if r['type'] == 'blob'}
            assert hashlib.sha1(b'blob ' + str(len(b)).encode() + b'\0' + b).hexdigest() == blobs[s['repo_path']]
    reading = json.loads((D / 'reading.json').read_text())
    for r in reading['records']:
        b = (ROOT / r['file']).read_bytes()
        assert hashlib.sha256(b).hexdigest() == r['sha256']
        lines = b.splitlines(keepends=True)
        for span in r['ranges']:
            assert 1 <= span['first'] <= span['last'] <= len(lines)
            assert hashlib.sha256(b''.join(lines[span['first']-1:span['last']])).hexdigest() == span['sha256']
    searched = [r['file'] for r in reading['records']] + reading['search_only_files']
    assert all(symbol not in (ROOT / f).read_text() for f in searched for symbol in reading['searched_symbols'])
    result = dict(status='passed', source_responses=9, partial_files_read=2,
                  declared_read_ranges=6, search_only_files=1,
                  repository_wide_absence_claim=False, downloaded_code_executed=False,
                  new_paper_reading_credit=0)
    assert sum(len(r['ranges']) for r in reading['records']) == result['declared_read_ranges']
    (D / 'validation.json').write_text(json.dumps(result, indent=2) + '\n')
    return result


if __name__ == '__main__':
    print(json.dumps(verify()))
