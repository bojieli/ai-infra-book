#!/usr/bin/env python3
"""Verify selected sources and independent trace-batching teaching budgets."""
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import zipfile

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'references/framework-history/2026-09-09/trace-identification'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def timeline(tasks, arrival_us, gpu_us, group, ordinary=False):
    """Three independent stages; a group is issued only after all tasks arrive."""
    assert tasks % group == 0
    cpu_cost = 8 if ordinary else 7 + group
    cpu_end = gpu_end = 0
    events = []
    for last_task in range(group, tasks + 1, group):
        ready = last_task * arrival_us
        cpu_start = max(ready, cpu_end)
        cpu_end = cpu_start + cpu_cost
        gpu_start = max(cpu_end, gpu_end)
        gpu_end = gpu_start + group * gpu_us
        events.append(dict(last_task=last_task, ready_us=ready,
                           cpu_start_us=cpu_start, cpu_end_us=cpu_end,
                           gpu_start_us=gpu_start, gpu_end_us=gpu_end))
    # Independently use the equal-service tandem-pipeline closed form.
    arrivals = group * arrival_us
    device = group * gpu_us
    groups = tasks // group
    exact = arrivals + cpu_cost + device + (groups - 1) * max(
        arrivals, cpu_cost, device)
    assert gpu_end == exact
    assert sum(e['cpu_end_us'] - e['cpu_start_us'] for e in events) == groups * cpu_cost
    return dict(total_us=gpu_end, cpu_work_us=groups * cpu_cost, events=events)


def calculate():
    cfg = json.loads((ROOT / 'references/outline-checks/2026-09-07/scaling-history/qwen3-8b-config.json').read_text())
    input_bytes = 256 * cfg['hidden_size'] * 2
    assert input_bytes == 2 * 2**20
    # Model an identity distinction, not a CUDA execution or a Legion hash test.
    def signature(slot):
        return (('gate', (slot, 'Wg'), slot + '-g'),
                ('up', (slot, 'Wu'), slot + '-u'),
                ('swiglu', (slot + '-g', slot + '-u'), slot + '-z'),
                ('down', (slot + '-z', 'Wd'), slot + '-y'))
    calls = [signature(s) for s in ['A', 'B', 'A', 'B']]
    assert tuple(op[0] for op in calls[0]) == tuple(op[0] for op in calls[1])
    assert calls[0] != calls[1] and calls[:2] == calls[2:]
    results = {}
    for name, tasks, arrival, gpu in [('short', 4, 4, 4), ('long', 40, 4, 4)]:
        variants = {label: timeline(tasks, arrival, gpu, group, ordinary)
                    for label, group, ordinary in [('ordinary', 1, True),
                                                   ('trace_2', 2, False),
                                                   ('trace_4', 4, False)]}
        results[name] = dict(tasks=tasks, arrival_interval_us=arrival,
                             device_us_per_task=gpu, variants=variants)
    assert [v['total_us'] for v in results['short']['variants'].values()] == [40, 34, 43]
    assert [v['cpu_work_us'] for v in results['short']['variants'].values()] == [32, 18, 11]
    assert [v['total_us'] for v in results['long']['variants'].values()] == [328, 196, 187]
    # Check the start-up/throughput boundary under a small set of changed inputs.
    checks = 0
    for tasks in [4, 8, 40]:
        for arrival in [1, 4]:
            for gpu in [1, 4]:
                for group in [1, 2, 4]:
                    timeline(tasks, arrival, gpu, group, ordinary=(group == 1))
                    checks += 1
    return dict(qwen3_input_mib=input_bytes / 2**20,
                two_input_slots_mib=2 * input_bytes / 2**20,
                identity='Same operation names and shapes, two address signatures, two-call repeat period.',
                pipeline_cases=results, closed_form_checks=checks,
                assumptions='Independent producer, CPU analysis and serial device stages; ordinary analysis 8 us/task, replay preparation 7 us/group + 1 us/task. Groups wait for all described tasks and release device work after group preparation. No cold discovery/capture, memory pressure, intra-group CPU/device overlap or communication. These are teaching assumptions, not measured Apophenia or CUDA Graph timings.')


def verify():
    records = json.loads((SOURCE / 'sources.json').read_text())
    reading = json.loads((SOURCE / 'reading.json').read_text())
    assert len(records) == 3 and all(r['status_code'] == 200 for r in records)
    assert len(reading['derived_files']) == 1 and len(reading['reused_inputs']) == 4
    assert len(reading['scopes']) == 9
    all_records = records + reading['derived_files'] + reading['reused_inputs']
    byid = {r['id']: r for r in all_records}
    assert len(byid) == len(all_records)
    for r in all_records:
        data = (ROOT / r['file']).read_bytes()
        assert len(data) == r['bytes'] and sha(data) == r['sha256']
        if 'archive_member' in r:
            archive = byid[r['archive_source_id']]
            with zipfile.ZipFile(ROOT / archive['file']) as z:
                assert z.read(r['archive_member']) == data
        if 'git_blob' in r:
            tree = json.loads((ROOT / r['tree_file']).read_text())
            assert not tree['truncated'] and tree['sha'] == r['commit']
            entry = next(e for e in tree['tree'] if e['path'] == r['repo_path'])
            assert entry['sha'] == r['git_blob'] == hashlib.sha1(
                b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
    meta = json.loads((SOURCE / 'zenodo-record.json').read_text())
    archive = (SOURCE / 'legion-artifact.zip').read_bytes()
    assert meta['files'][0]['size'] == len(archive)
    assert meta['files'][0]['checksum'] == 'md5:' + hashlib.md5(archive).hexdigest()
    for scope in reading['scopes']:
        r = byid[scope['source_id']]
        assert (r['file'], r['sha256']) == (scope['file'], scope['sha256'])
        data = (ROOT / r['file']).read_bytes()
        if scope['mode'] == 'lines':
            lo, hi = scope['first_line'], scope['last_line']
            lines = data.splitlines(keepends=True)
            assert 1 <= lo <= hi <= len(lines)
            assert sha(b''.join(lines[lo-1:hi])) == scope['selected_sha256']
            continue
        obj = json.loads(data)
        if scope['mode'] == 'tree_entries':
            assert not obj['truncated'] and obj['sha'] == scope['commit']
            assert all(e in obj['tree'] for e in scope['entries'])
        elif scope['mode'] == 'commit_identity':
            assert scope['values'] == dict(sha=obj['sha'], date=obj['commit']['committer']['date'])
        elif scope['mode'] == 'json_fields':
            assert all(obj[k] == v for k, v in scope['values'].items())
        elif scope['mode'] == 'zenodo_identity':
            expected = {k: obj['metadata'][k] for k in ['doi', 'publication_date', 'title', 'creators']}
            expected['files'] = obj['files']
            assert scope['values'] == expected
        else:
            raise AssertionError(scope['mode'])
    report = dict(verified_at=datetime.now(timezone.utc).isoformat(), status='passed',
                  source_responses=3, derived_files=1, reused_inputs=4, read_scopes=9,
                  arithmetic=calculate(), downloaded_code_executed=False,
                  hardware_experiments_run=False,
                  scope='Declared source scopes and teaching arithmetic; paper checked by ASPLOS verifier. Existing user experiments were not rerun or modified.')
    (ROOT / 'research/2026-infra-survey/trace-identification-audit.json').write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    return report


if __name__ == '__main__':
    print(json.dumps(verify(), ensure_ascii=False))
