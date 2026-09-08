#!/usr/bin/env python3
"""Independent budget arithmetic and pinned-source checks; no source execution."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import math

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'references/framework-history/2026-09-09/snapshot-residency'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def calculate():
    # MiB unless otherwise specified. Common 2 GiB source is excluded from
    # the 64 GiB local budget and accounted for separately in every variant.
    count, template, touched, written, metadata, hot = 100, 2048, 512, 128, 4, 256
    assert written + hot <= touched <= template
    local_mib = {
        'full_copy': template + metadata,
        'access_copy': touched + metadata,
        'shared_read_only': written + metadata,
        'shared_with_hot_copy': written + hot + metadata,
    }
    local_gib = {k: count * v / 1024 for k, v in local_mib.items()}
    capacity = {k: 64 * 1024 // v for k, v in local_mib.items()}
    assert local_gib == dict(full_copy=200.390625, access_copy=50.390625,
                            shared_read_only=12.890625, shared_with_hot_copy=37.890625)
    assert capacity == dict(full_copy=31, access_copy=127,
                           shared_read_only=496, shared_with_hot_copy=168)
    for key, n in capacity.items():
        assert n * local_mib[key] <= 64 * 1024 < (n + 1) * local_mib[key]

    # Physical traffic after CPU-cache effects, not the logical address span.
    task_read_gib, arrival_rate, path_gib_s = 64 / 1024, 200, 32
    traffic = task_read_gib * arrival_rate
    bandwidth_ceiling = path_gib_s / task_read_gib
    cpu_ceiling = 32 / 0.05
    assert traffic == 12.5 and bandwidth_ceiling == 512 and cpu_ceiling == 640

    # Exact address coverage: 64 separate 4 KiB pages, one in each 2 MiB block.
    small_page, large_page = 4096, 2 ** 21
    offsets = [i * large_page for i in range(64)]
    def covered_bytes(addresses, granule):
        return len({a // granule for a in addresses}) * granule
    sparse = {str(g): covered_bytes(offsets, g) for g in [small_page, large_page]}
    dense_offsets = range(0, 64 * 2 ** 20, small_page)
    dense = {str(g): covered_bytes(dense_offsets, g) for g in [small_page, large_page]}
    assert sparse == {'4096': 256 * 1024, '2097152': 128 * 2 ** 20}
    assert set(dense.values()) == {64 * 2 ** 20}
    service_ms = {k: v / 2 ** 30 * 1000 for k, v in sparse.items()}
    assert service_ms == {'4096': 0.244140625, '2097152': 125.0}

    # A semantic counterexample for moving normalization across a reduction.
    def norm(v, eps):
        denom = math.sqrt(sum(x * x for x in v) / len(v) + eps)
        return [x / denom for x in v]
    wrong_moves = []
    for eps in [0.0, 1e-6]:
        after = norm([1.0, 1.0], eps)
        before = [a + b for a, b in zip(norm([1.0, 0.0], eps), norm([0.0, 1.0], eps))]
        assert all(not math.isclose(a, b, rel_tol=1e-3) for a, b in zip(after, before))
        wrong_moves.append(dict(epsilon=eps,reduce_then_norm=after,norm_then_reduce=before))
    return dict(assumptions='Independent teaching inputs, no measured cloud or paper performance.',
                environments=count, common_snapshot_gib=2, local_mib_per_environment=local_mib,
                local_gib_total=local_gib, local_64gib_capacity_ceiling=capacity,
                physical_read_gib_s=traffic, bandwidth_tasks_s_ceiling=bandwidth_ceiling,
                cpu_tasks_s_ceiling=cpu_ceiling, sparse_fetch_bytes=sparse,
                dense_fetch_bytes=dense, sparse_service_ms_lower_bound=service_ms,
                reduction_normalization_counterexamples=wrong_moves)


def verify():
    records = json.loads((SOURCE / 'sources.json').read_text())
    reading = json.loads((SOURCE / 'reading.json').read_text())
    assert len(records) == len({s['id'] for s in records}) == 6
    assert len(reading['scopes']) == 10
    byid = {s['id']: s for s in records}
    tree = json.loads((SOURCE / 'e2b-tree.json').read_text())
    assert tree['sha'] == reading['fixed_commit'] and not tree['truncated']
    for s in records:
        b = (ROOT / s['file']).read_bytes()
        assert s['status_code'] == 200 and len(b) == s['bytes'] and sha(b) == s['sha256']
        if 'repo_path' in s:
            entry = next(x for x in tree['tree'] if x['path'] == s['repo_path'])
            blob = hashlib.sha1(b'blob ' + str(len(b)).encode() + b'\0' + b).hexdigest()
            assert s['commit'] == reading['fixed_commit'] and blob == entry['sha'] == s['git_blob']
    for scope in reading['scopes']:
        s = byid[scope['source_id']]
        assert s['file'] == scope['file'] and s['sha256'] == scope['sha256']
        data = (ROOT / scope['file']).read_bytes()
        if scope['mode'] == 'lines':
            lines = data.splitlines(keepends=True)
            lo, hi = scope['first_line'], scope['last_line']
            assert 1 <= lo <= hi <= len(lines)
            assert sha(b''.join(lines[lo-1:hi])) == scope['selected_sha256']
        elif scope['mode'] == 'commit_identity':
            commit = json.loads(data)
            assert commit['sha'] == scope['values']['sha'] == reading['fixed_commit']
            assert commit['commit']['committer']['date'] == scope['values']['date']
        elif scope['mode'] == 'tree_entries':
            assert all(x in tree['tree'] for x in scope['entries'])
        else:
            raise AssertionError(scope['mode'])
    report = dict(verified_at=datetime.now(timezone.utc).isoformat(), status='passed',
                  responses=len(records), read_scopes=len(reading['scopes']), arithmetic=calculate(),
                  scope='Declared source ranges and independent arithmetic only; paper pages checked by ASPLOS verifier.',
                  downloaded_code_executed=False, hardware_experiments_run=False)
    (ROOT / 'research/2026-infra-survey/snapshot-residency-audit.json').write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    return report


if __name__ == '__main__':
    print(json.dumps(verify(), ensure_ascii=False))
