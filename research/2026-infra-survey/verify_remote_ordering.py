#!/usr/bin/env python3
"""Verify source scopes and independent ordering/window teaching examples.

Does not import downloaded code or simulate a hardware/coherence protocol.
"""
from datetime import datetime, timezone
from fractions import Fraction as F
from itertools import permutations
from pathlib import Path
import hashlib
import json
import math
import subprocess

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[2]
DEST = ROOT / 'references/framework-history/2026-09-09/remote-ordering'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def arithmetic():
    size, latency, bandwidth, window = 256, F(2, 1_000_000), 40_000_000_000, 128
    assert math.ceil(bandwidth * latency / size) == 313
    window_bound = window * size / latency
    serial_bound = size / F(1, 10_000_000)
    stop_wait = size / latency
    assert window_bound == 16_384_000_000
    assert min(bandwidth, window_bound, serial_bound) == 2_560_000_000
    assert stop_wait == 128_000_000
    # Enumerate every four-event interleaving with an ordered producer.
    # Delivery is always F then D; it does not change the sampled values.
    observed_ready = stale = repaired = acquire_then_data = 0
    for events in permutations(('write_data', 'write_flag', 'read_data', 'read_flag')):
        pos = {event: events.index(event) for event in events}
        if pos['write_data'] > pos['write_flag']:
            continue
        data = flag = 0
        samples = {}
        for event in events:
            if event == 'write_data':
                data = 1
            elif event == 'write_flag':
                flag = 1
            elif event == 'read_data':
                samples['data'] = data
            else:
                samples['flag'] = flag
        if samples['flag'] != 1:
            continue
        observed_ready += 1
        stale += samples['data'] == 0
        invalidated = pos['read_data'] < pos['write_data'] < pos['read_flag']
        revalidated_data = 1 if invalidated else samples['data']
        assert revalidated_data == 1
        repaired += invalidated
        if pos['read_flag'] < pos['read_data']:
            acquire_then_data += 1
            assert samples['data'] == 1
    assert (observed_ready, stale, repaired, acquire_then_data) == (4, 1, 1, 1)
    return dict(required_window=313, window_bound_bytes_s=int(window_bound),
                serial_service_bound_bytes_s=int(serial_bound), stop_wait_bytes_s=int(stop_wait),
                ready_observations_checked=observed_ready, stale_despite_ordered_delivery=stale,
                repaired_by_revalidation=repaired,
                scope='Explicit teaching inputs and four-event observations; not a general memory-model proof or measured throughput.')


def verify():
    proof = read(DEST / 'reading.json')
    rows = read(ROOT / proof['sources_file'])
    failed = read(ROOT / proof['connection_failures_file'])
    by = {r['id']: r for r in rows}
    assert len(rows) == len(by) == proof['source_responses'] == proof['successful_responses'] == 11
    assert len(failed) == proof['no_response_failures'] == 1
    assert len(rows) + len(failed) == proof['attempt_records'] == 12
    assert not failed[0]['response_body_received'] and 'file' not in failed[0]
    assert not proof['downloaded_code_executed'] and not proof['hardware_experiments_run']
    for row in rows:
        path = ROOT / row['file']
        assert row['status_code'] == 200
        assert sha(path) == row['sha256'] and path.stat().st_size == row['bytes']
    assert len(proof['scopes']) == 13
    for scope in proof['scopes']:
        path = ROOT / scope['file']
        assert sha(path) == scope['sha256'] == by[scope['source_id']]['sha256']
        mode = scope['mode']
        if mode == 'full_text':
            path.read_text()
            continue
        selected = ROOT / scope['selected_file']
        assert sha(selected) == scope['selected_sha256']
        if mode == 'text_range':
            assert path.read_text()[scope['start']:scope['end']] == selected.read_text()
        elif mode == 'html_selector':
            nodes = BeautifulSoup(path.read_text(), 'html.parser').select(scope['selector'])
            assert len(nodes) == 1 and nodes[0].get_text(' ', strip=True) + '\n' == selected.read_text()
        else:
            raw = read(path)
            if mode == 'json_fields':
                value = {k: raw[k] for k in scope['fields']}
            elif mode == 'commit_identity':
                value = dict(sha=raw['sha'], date=raw['commit']['committer']['date'],
                             message=raw['commit']['message'].split('\n')[0])
            elif mode == 'tree_lookup':
                assert not raw['truncated']
                assert set(scope['paths']) <= {v['path'] for v in raw['tree']}
                value = dict(sha=raw['sha'], truncated=raw['truncated'], paths=scope['paths'])
            else:
                raise AssertionError(mode)
            assert value == read(selected)
    assert {s['source_id'] for s in proof['scopes']} == set(by)
    for prefix, repo in [('author', 'icsa-caps/efficient-remote-memory-ordering'), ('nvshmem', 'NVIDIA/nvshmem')]:
        commit = proof[prefix + '_commit']
        assert read(DEST / (prefix + '-commit.json'))['sha'] == commit
        for row in rows:
            if 'raw.githubusercontent.com/' + repo + '/' in row['url']:
                assert '/' + commit + '/' in row['url']
    paper = read(ROOT / 'references/proceedings/ASPLOS/2026/remote-ordering-reading.json')
    pdf, txt = ROOT / paper['pdf_file'], ROOT / paper['archive_text_file']
    assert sha(pdf) == paper['pdf_sha256'] and sha(txt) == paper['archive_text_sha256']
    extracted = subprocess.check_output(['pdftotext', '-layout', str(pdf), '-'], text=True)
    assert extracted == txt.read_text()
    pages = extracted.split('\f')
    assert len([p for p in pages if p.strip()]) == paper['physical_pdf_pages'] == 15
    assert [p['physical_page'] for p in paper['selected_text_pages']] == list(range(2, 14))
    for page in paper['selected_text_pages']:
        assert hashlib.sha256(pages[page['physical_page'] - 1].encode()).hexdigest() == page['sha256']
    assert [p['physical_page'] for p in paper['viewed_pages']] == [3, 8, 10]
    for page in paper['viewed_pages']:
        assert page['actually_viewed'] and sha(ROOT / page['file']) == page['sha256']
    assert not paper['downloaded_code_executed'] and not paper['hardware_experiments_run']
    return dict(status='passed', verified_at=datetime.now(timezone.utc).isoformat(),
                paper_text_pages=12, viewed_images=3, source_responses=11, no_response_failures=1,
                declared_scopes=13, arithmetic=arithmetic(),
                scope='Source integrity, declared reading scopes and teaching arithmetic only.')


if __name__ == '__main__':
    result = verify()
    (Path(__file__).parent / 'remote-ordering-audit.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(result, ensure_ascii=False, indent=2))
