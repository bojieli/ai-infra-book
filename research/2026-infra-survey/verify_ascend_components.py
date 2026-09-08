#!/usr/bin/env python3
"""Verify declared component-analysis sources and independent teaching arithmetic."""
from datetime import datetime, timezone
from fractions import Fraction as F
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[2]
D = ROOT / 'references/framework-history/2026-09-09/ascend-components'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read(path):
    return json.loads(path.read_text())


def arithmetic():
    config = read(ROOT / 'references/outline-checks/2026-09-07/scaling-history/qwen3-8b-config.json')
    assert config['intermediate_size'] == 12288
    elements = 1024 * config['intermediate_size']
    input_bytes, output_bytes = elements * 4, elements * 2
    assert (input_bytes + output_bytes) // 2**20 == 72
    single = 64 * 256 * 6
    scratch = 64 * 1024
    assert single // 1024 == 96
    assert (single + scratch) // 1024 == 160
    assert (2 * single + scratch) // 1024 == 256
    assert single + scratch <= 240 * 1024 < 2 * single + scratch
    ideal = F(1, 100) + F(1, 200)
    assert 2 / ideal == F(400, 3)
    for active, expected_e, expected_r in [(40, F(1), F(2, 5)), (80, F(1, 2), F(4, 5))]:
        e, r = F(40, active), F(active, 100)
        assert (e, r) == (expected_e, expected_r) and e * r == F(2, 5)
    # Check the pipeline with task precedence, resource queues, and two slots.
    def pipeline(compute):
        ends = [[F(0)] * 3 for _ in range(8)]
        for i in range(8):
            for stage, duration in enumerate([F(2), compute, F(2)]):
                ready = [F(0)]
                if i: ready.append(ends[i-1][stage])
                if stage: ready.append(ends[i][stage-1])
                if i >= 2 and stage == 0: ready.append(ends[i-2][1])  # input-slot reuse
                if i >= 2 and stage == 1: ready.append(ends[i-2][2])  # output-slot reuse
                ends[i][stage] = max(ready) + duration
        return ends[-1][-1]
    assert pipeline(F(1)) == 19 and pipeline(F(1, 2)) == F(37, 2)
    assert 8 * (2 + 1 + 2) == 40 and 8 * (2 + 2) == 32 > 19
    # Distinguish an algebraic correction from a claimed execution bug.
    u_threshold, r_threshold = F(3, 5), F(4, 5)
    assert u_threshold / r_threshold == F(3, 4)
    assert r_threshold / u_threshold == F(4, 3)
    assert (2 * config['intermediate_size']) % 32 == 0
    return dict(scope='Independent teaching assumptions, no model or NPU execution.',
        qwen_swiglu=dict(input_mib=input_bytes//2**20, output_mib=output_bytes//2**20, total_mib=72),
        buffer_kib=dict(single=96, double=192, scratch=64, single_total=160, double_total=256, available=240),
        mixed_work=dict(ideal_ms=float(ideal*1000), gops_per_second=float(2/ideal)),
        utilization_examples=[dict(active_us=40, efficiency=1, time_ratio=.4), dict(active_us=80, efficiency=.5, time_ratio=.8)],
        pipeline_us=dict(serial=40, independent_engines=float(pipeline(F(1))), faster_compute=float(pipeline(F(1,2))), shared_read_write_lower_bound=32),
        corrected_efficiency_bound='U_threshold/R_threshold')


def verify():
    proof = read(D / 'reading.json')
    sources = read(ROOT / proof['sources_file'])
    assert len(sources) == len({s['id'] for s in sources}) == 6
    assert len(proof['scopes']) == 8
    assert {s['source_id'] for s in proof['scopes']} == {s['id'] for s in sources}
    for source in sources:
        data = (ROOT / source['file']).read_bytes()
        assert source['status_code'] == 200 and len(data) == source['bytes'] and sha(data) == source['sha256']
        if 'commit' in source: assert source['commit'] == proof['fixed_commit']
    for scope in proof['scopes']:
        path = ROOT / scope['file']
        assert sha(path.read_bytes()) == scope['sha256']
        if scope['mode'] == 'lines':
            lines = path.read_text().splitlines(keepends=True)
            lo, hi = scope['first_line'], scope['last_line']
            assert 1 <= lo <= hi <= len(lines)
            assert sha(''.join(lines[lo-1:hi]).encode()) == scope['selected_sha256']
        elif scope['mode'] == 'commit_identity':
            meta = read(path)
            assert dict(sha=meta['sha'], date=meta['commit']['committer']['date'], message=meta['commit']['message']) == scope['values']
            assert meta['sha'] == proof['fixed_commit']
        elif scope['mode'] == 'tree_entries':
            tree = read(path)
            assert not tree['truncated'] and tree['sha'] == scope['sha'] == proof['fixed_commit']
            assert len(scope['entries']) == 4
            for entry in scope['entries']:
                assert entry in tree['tree']
                source = next(s for s in sources if s.get('upstream_path') == entry['path'])
                data = (ROOT / source['file']).read_bytes()
                assert hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest() == entry['sha']
        else: raise AssertionError(scope['mode'])
    assert not proof['downloaded_code_executed'] and not proof['hardware_experiments_run']
    # The conference verifier checks the PDF, exact abstract spans and physical page hashes.
    return dict(status='passed', verified_at=datetime.now(timezone.utc).isoformat(), source_responses=6,
        declared_source_scopes=8, arithmetic=arithmetic(), scope='Declared source identity, content, scope and independent arithmetic; not complete backend/kernel verification.')


if __name__ == '__main__':
    result = verify()
    (Path(__file__).parent / 'ascend-components-audit.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(result, ensure_ascii=False))
