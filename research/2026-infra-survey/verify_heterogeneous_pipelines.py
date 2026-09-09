#!/usr/bin/env python3
"""Check archived bytes, declared selected scopes and own small arithmetic."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
D = ROOT / 'references/framework-history/2026-09-09/heterogeneous-pipelines'


def verify():
    sources = json.loads((D / 'sources.json').read_text())
    assert len(sources) == len({s['id'] for s in sources}) == 13
    byid = {s['id']: s for s in sources}
    for s in sources:
        data = (ROOT / s['file']).read_bytes()
        assert len(data) == s['bytes'] and hashlib.sha256(data).hexdigest() == s['sha256']
        assert s['status_code'] == (422 if s['id'] == 'helix-fixed-commit' else 200)
    reading = json.loads((D / 'reading.json').read_text())
    assert len(reading['sources']) == 8
    for r in reading['sources']:
        s = byid[r['source_id']]
        assert r['file'] == s['file'] and r['sha256'] == s['sha256']
        lines = (ROOT / s['file']).read_text().splitlines(keepends=True)
        assert all(1 <= lo <= hi <= len(lines) for lo, hi in r['line_ranges_inclusive'])
        data = ''.join(''.join(lines[lo-1:hi]) for lo, hi in r['line_ranges_inclusive']).encode()
        assert hashlib.sha256(data).hexdigest() == r['selected_text_sha256']
        assert r['execution'] == 'not_executed'
    metadata = reading['metadata_checks']
    repo = json.loads((D / 'repository.json').read_text())
    commit = json.loads((D / 'master-commit.json').read_text())
    assert repo['default_branch'] == metadata['helix_default_branch'] == 'master'
    assert commit['sha'] == metadata['helix_commit']
    assert commit['commit']['committer']['date'] == metadata['helix_commit_date']
    for s in sources:
        if s['id'].startswith('vllm-current-'):
            assert '/' + metadata['vllm_fixed_commit'] + '/' in s['url']
    assert '/v0.10.1/' in byid['vllm-2025-parallel-guide']['url']
    before = (D / 'arithmetic.json').read_bytes()
    # This local teaching script uses only stdlib/config JSON, never archived source code.
    subprocess.run([sys.executable, str(D / 'check_arithmetic.py')], check=True, stdout=subprocess.PIPE)
    assert (D / 'arithmetic.json').read_bytes() == before
    a = json.loads(before)
    assert a['payload_sensitivity']['correct_flow_bound'] == 12000
    assert a['payload_sensitivity']['one_tensor_flow_bound'] == 14000
    assert [c['capacity_only_sequences'] for c in a['kv_capacity_cases']] == [7, 3]
    report = dict(verified_at=datetime.now(timezone.utc).isoformat(), status='passed',
                  source_responses=13, selected_source_scopes=8, selected_paper_pages=15,
                  body_page_views=5, abstract_page_views=3,
                  arithmetic='Qwen3 tensor payload, per-stage KV and 16-cut flow enumeration passed',
                  scope='Static source reading and own arithmetic; no GPU, downloaded code or simulator execution. Long-running goal remains active.')
    (ROOT / 'research/2026-infra-survey/qa/heterogeneous-pipelines-phase.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    return report


if __name__ == '__main__':
    print(json.dumps(verify(), ensure_ascii=False))
