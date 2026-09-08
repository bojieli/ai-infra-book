#!/usr/bin/env python3
"""Verify source identity and independent examples without executing source code."""
from pathlib import Path
from datetime import datetime, timezone
from fractions import Fraction as F
import hashlib
import json
import zipfile

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'references/framework-history/2026-09-09/tuning-measurement'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def calculate():
    true_us = {'A': 100, 'B': 90}
    drift_us = [0, 10, 20, 30]
    sequences = {}
    for sequence in ['AABB', 'ABBA']:
        observations = {name: [] for name in true_us}
        for slot, name in enumerate(sequence):
            observations[name].append(true_us[name] + drift_us[slot])
        means = {name: sum(values) / len(values) for name, values in observations.items()}
        sequences[sequence] = dict(observations_us=observations, means_us=means,
                                   winner=min(means, key=means.get))
    assert sequences['AABB']['means_us'] == {'A': 105, 'B': 115}
    assert sequences['ABBA']['means_us'] == {'A': 115, 'B': 105}
    assert sequences['AABB']['winner'] == 'A' and sequences['ABBA']['winner'] == 'B'
    # Balance the slot centroids; cancellation requires the stated additive
    # linear-drift model, not arbitrary interference or changing workloads.
    for slope in range(-20, 21):
        a = (100 + 100 + 3 * slope) / 2
        b = (90 + slope + 90 + 2 * slope) / 2
        assert a - b == 10

    threshold = F(27, 35)
    environments = dict(C={'A': 120, 'B': 144}, D={'A': 180, 'B': 99})
    proportions = {F(i, 100) for i in range(101)} | {threshold}
    for p in proportions:
        a = p * environments['C']['A'] + (1-p) * environments['D']['A']
        b = p * environments['C']['B'] + (1-p) * environments['D']['B']
        assert a-b == 81-105*p
        assert (a < b) == (p > threshold)
        assert (a == b) == (p == threshold)

    # This is a dimensional counterexample, not an execution of the artifact.
    unit_scores = {}
    for unit, factor in [('seconds', 1), ('milliseconds', 1000)]:
        scores = {'A': F(1)*factor-F(9, 10), 'B': F(4, 5)*factor-F(1, 2)}
        unit_scores[unit] = dict(scores={k: str(v) for k,v in scores.items()},
                                winner=min(scores, key=scores.get))
    assert unit_scores['seconds']['winner'] == 'A'
    assert unit_scores['milliseconds']['winner'] == 'B'

    cfg = json.loads((ROOT / 'references/outline-checks/2026-09-07/scaling-history/qwen3-8b-config.json').read_text())
    intermediate, tokens, element_bytes = cfg['intermediate_size'], 1024, 2
    assert intermediate == 12288 and cfg['hidden_act'] == 'silu'
    traffic = {}
    for name, width in [('unsharded_model', 2*intermediate), ('benchmark_parameter_12288', intermediate)]:
        output_width = width // 2
        inp, out = tokens*width*element_bytes, tokens*output_width*element_bytes
        traffic[name] = dict(input_width=width, output_width=output_width,
                             input_mib=inp/2**20, output_mib=out/2**20,
                             minimum_interface_mib=(inp+out)/2**20)
    assert traffic['unsharded_model']['minimum_interface_mib'] == 72
    assert traffic['benchmark_parameter_12288']['minimum_interface_mib'] == 36
    return dict(assumptions='Independent teaching times, no measured performance. Linear additive drift only; fixed workload and quality. Traffic is a kernel-boundary budget, not measured HBM transactions.',
                sequences=sequences, linear_drift_slopes_checked=41,
                contention_proportions_checked=len(proportions),
                contention_A_wins_above=str(threshold), dimensional_score_counterexample=unit_scores,
                qwen3_swiglu_bf16_1024_tokens=traffic)


def verify():
    records = json.loads((SOURCE / 'sources.json').read_text())
    reading = json.loads((SOURCE / 'reading.json').read_text())
    assert len(records) == 14 and sum(x['status_code'] == 404 for x in records) == 2
    assert len(reading['derived_files']) == 3 and len(reading['reused_inputs']) == 7
    assert len(reading['scopes']) == 21
    all_records = records + reading['derived_files'] + reading['reused_inputs']
    byid = {x['id']: x for x in all_records}
    assert len(byid) == len(all_records)
    for row in all_records:
        data = (ROOT / row['file']).read_bytes()
        assert len(data) == row['bytes'] and sha(data) == row['sha256']
        if 'archive_file' in row:
            with zipfile.ZipFile(ROOT / row['archive_file']) as archive:
                assert archive.read(row['member']) == data
        if 'git_blob' in row:
            tree = json.loads((ROOT / row['tree_file']).read_text())
            assert not tree['truncated'] and tree['sha'] == row['commit'] == row['ref']
            entry = next(x for x in tree['tree'] if x['path'] == row['repo_path'])
            blob = hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
            assert blob == row['git_blob'] == entry['sha']
        if 'md5' in row:
            assert hashlib.md5(data).hexdigest() == row['md5']
            with zipfile.ZipFile(ROOT / row['file']) as archive:
                assert row['members'] == [dict(name=x.filename, bytes=x.file_size, crc32=x.CRC)
                                          for x in archive.infolist()]
    for scope in reading['scopes']:
        row = byid[scope['source_id']]
        assert row['file'] == scope['file'] and row['sha256'] == scope['sha256']
        data = (ROOT / row['file']).read_bytes()
        mode = scope['mode']
        if mode == 'lines':
            lo, hi = scope['first_line'], scope['last_line']
            lines = data.splitlines(keepends=True)
            assert 1 <= lo <= hi <= len(lines)
            assert sha(b''.join(lines[lo-1:hi])) == scope['selected_sha256']
            continue
        obj = json.loads(data)
        if mode == 'commit_identity':
            assert obj['sha'] == scope['commit'] == scope['values']['sha']
            assert obj['commit']['committer']['date'] == scope['values']['date']
            assert obj['commit']['tree']['sha'] == scope['values']['tree_sha']
        elif mode == 'tree_entries':
            assert not obj['truncated'] and obj['sha'] == scope['commit']
            assert all(x in obj['tree'] for x in scope['entries'])
            assert not any(x['path'] in scope.get('absent_paths', []) for x in obj['tree'])
        elif mode in ['json_fields', 'zenodo_identity']:
            assert all(obj[k] == v for k,v in scope['values'].items())
            if mode == 'zenodo_identity':
                assert obj['metadata']['publication_date'] == scope['publication_date']
                assert obj['files'] == scope['file_metadata']
                zipped = next(x for x in records if x['file'].endswith('.zip'))
                assert obj['files'][0]['checksum'] == 'md5:' + zipped['md5']
        else:
            raise AssertionError(mode)
    report = dict(verified_at=datetime.now(timezone.utc).isoformat(), status='passed',
                  responses=len(records), failed_responses=2, derived_files=3,
                  reused_inputs=7, read_scopes=21, arithmetic=calculate(),
                  downloaded_code_executed=False, hardware_experiments_run=False,
                  scope='Declared source identity/ranges and independent arithmetic; paper checked separately.')
    (ROOT / 'research/2026-infra-survey/tuning-measurement-audit.json').write_text(
        json.dumps(report, ensure_ascii=False, indent=2)+'\n')
    return report


if __name__ == '__main__':
    print(json.dumps(verify(), ensure_ascii=False))
