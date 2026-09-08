#!/usr/bin/env python3
"""Check declared paper/source scopes and finite speculative-preparation budgets."""
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import re
import subprocess

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'references/framework-history/2026-09-09/pipellm-swap'
PAPER = ROOT / 'references/proceedings/ASPLOS/2025/pipellm'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def calculate():
    cfg = json.loads((ROOT / 'references/outline-checks/2026-09-07/scaling-history/qwen3-8b-config.json').read_text())
    block = 8192 * cfg['hidden_size'] * 2
    assert block == 64 * 2**20
    stages = ['prepare', 'host_copy', 'h2d', 'consume']
    durations = [8, 2, 2, 10]
    stage_end = [0] * 4
    # Two slots for each boundary; retain each until its reader finishes.
    private_free = [0, 0]
    host_free = [0, 0]
    device_free = [0, 0]
    events = []
    for i in range(8):
        slot = i % 2
        starts = [max(stage_end[0], private_free[slot])]
        ends = [starts[0] + durations[0]]
        for j, free in [(1, host_free[slot]), (2, device_free[slot]), (3, 0)]:
            starts.append(max(ends[j-1], stage_end[j], free))
            ends.append(starts[j] + durations[j])
        private_free[slot], host_free[slot], device_free[slot] = ends[1:]
        stage_end = ends
        events.append(dict(block=i+1, slot=slot, **{
            stage: dict(start_ms=starts[j], end_ms=ends[j])
            for j, stage in enumerate(stages)}))
    # Independently check every dependency, stage exclusivity and reuse lifetime.
    for i, event in enumerate(events):
        for j, stage in enumerate(stages):
            assert event[stage]['end_ms'] - event[stage]['start_ms'] == durations[j]
            if j:
                assert event[stage]['start_ms'] >= event[stages[j-1]]['end_ms']
            if i:
                assert event[stage]['start_ms'] >= events[i-1][stage]['end_ms']
        if i >= 2:
            for writer, reader in zip(stages, stages[1:]):
                assert event[writer]['start_ms'] >= events[i-2][reader]['end_ms']
    total = events[-1]['consume']['end_ms']
    assert total == sum(durations) + 7 * max(durations) == 92
    assert 8 * (durations[0] + durations[2] + durations[3]) == 160
    assert 8 * durations[1] == 16
    assert 10 * durations[0] == 8 * durations[3] == 80
    assert 12 * durations[0] == 96 > 8 * durations[3]
    return dict(block_mib=block / 2**20, stages_ms=dict(zip(stages, durations)),
                serial_on_demand_ms=160, prepared_pipeline_ms=total,
                extra_host_copy_service_ms=16, slots_per_boundary=2,
                private_result_mib=128, host_transfer_mib=128, device_input_mib=128,
                total_temporary_mib=384, events=events,
                useful_fraction_necessary_steady_state=0.8,
                preparation_service_for_eight_useful_blocks_ms={'ten_prepared': 80, 'twelve_prepared': 96},
                assumptions='Equal 64 MiB blocks; independent stages with stated concurrent service times; future data known and validated, sufficient CPU resources, two slots at each boundary. Baseline requests the next preparation only after consumption. Original inputs/model state excluded from temporary capacity. No model, crypto or CUDA execution. Useful-work fraction is not sequence prediction accuracy; resource-work bounds do not give finite error-case completion time.')


def verify():
    records = json.loads((SOURCE / 'sources.json').read_text())
    reading = json.loads((SOURCE / 'reading.json').read_text())
    assert len(records) == 9 and all(r['status_code'] == 200 for r in records)
    assert len(reading['reused_inputs']) == 5 and len(reading['scopes']) == 16
    all_records = records + reading['reused_inputs']
    byid = {r['id']: r for r in all_records}
    assert len(byid) == len(all_records)
    for r in all_records:
        data = (ROOT / r['file']).read_bytes()
        assert len(data) == r['bytes'] and sha(data) == r['sha256']
        if 'git_blob' in r:
            tree = json.loads((ROOT / r['tree_file']).read_text())
            assert not tree['truncated'] and tree['sha'] == r['commit']
            entry = next(e for e in tree['tree'] if e['path'] == r['repo_path'])
            assert entry['sha'] == r['git_blob'] == hashlib.sha1(
                b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
    for scope in reading['scopes']:
        r = byid[scope['source_id']]
        assert (scope['file'], scope['sha256']) == (r['file'], r['sha256'])
        data = (ROOT / r['file']).read_bytes()
        if scope['mode'] == 'lines':
            lo, hi = scope['first_line'], scope['last_line']
            lines = data.splitlines(keepends=True)
            assert 1 <= lo <= hi <= len(lines)
            assert sha(b''.join(lines[lo-1:hi])) == scope['selected_sha256']
        elif scope['mode'] == 'commit_identity':
            obj = json.loads(data)
            assert scope['values'] == dict(sha=obj['sha'], date=obj['commit']['committer']['date'])
        elif scope['mode'] == 'tree_entries':
            obj = json.loads(data)
            assert not obj['truncated'] and obj['sha'] == scope['commit']
            assert obj['tree'] == scope['entries']
        else:
            raise AssertionError(scope['mode'])
    originals = json.loads((PAPER / 'sources.json').read_text())
    assert len(originals) == 1
    paper = originals[0]
    data = (ROOT / paper['file']).read_bytes()
    assert paper['status_code'] == 200 and len(data) == paper['bytes'] and sha(data) == paper['sha256']
    info = subprocess.check_output(['pdfinfo', str(ROOT / paper['file'])], text=True)
    assert int(re.search(r'^Pages:\s+(\d+)', info, re.M)[1]) == paper['pdf_pages'] == 15
    text = subprocess.check_output(['pdftotext', '-layout', str(ROOT / paper['file']), '-'])
    derived = paper['derived_text']
    assert text == (ROOT / derived['file']).read_bytes()
    assert len(text) == derived['bytes'] and sha(text) == derived['sha256']
    first = subprocess.check_output(['pdftotext', '-f', '1', '-l', '1', str(ROOT / paper['file']), '-'], text=True)
    assert '10.1145/3669940.3707224' in first and 'PipeLLM' in first
    proof = json.loads((PAPER.parent / 'pipellm-reading.json').read_text())
    representative = proof['paper']['representative_pdf']
    assert sha((ROOT / representative['file']).read_bytes()) == representative['sha256'] == 'd2bedd62175ef6b9fa77f5db04e35009dfb146407e266dc6c9608a66b56879c6'
    assert proof['reading']['physical_pdf_pages'] == list(range(1, 14))
    assert [f['physical_page'] for f in proof['figures']] == [4, 6, 9, 10, 11, 12]
    # Page text and actual-view hashes are also checked by the conference verifier.
    report = dict(verified_at=datetime.now(timezone.utc).isoformat(), status='passed',
                  source_responses=9, reused_inputs=5, read_scopes=16,
                  additional_author_pdf_pages=15, selected_paper_pages=13,
                  actual_page_image_views=6, arithmetic=calculate(),
                  downloaded_code_executed=False, hardware_experiments_run=False,
                  scope='Declared sources, original preservation and independent finite teaching schedule; not paper reproduction or security validation.')
    (ROOT / 'research/2026-infra-survey/pipellm-preparation-audit.json').write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    return report


if __name__ == '__main__':
    print(json.dumps(verify(), ensure_ascii=False))
