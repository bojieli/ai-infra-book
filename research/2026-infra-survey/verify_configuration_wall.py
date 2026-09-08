#!/usr/bin/env python3
"""Check the declared paper scope and independent configuration-time examples.

Only reads local artifacts. It does not run author code or model GPU execution.
"""
from datetime import datetime, timezone
from fractions import Fraction
from pathlib import Path
from urllib.parse import unquote, urlsplit
import hashlib
import json
import re
import subprocess

ROOT = Path(__file__).resolve().parents[2]
DEST = ROOT / 'references/proceedings/ASPLOS/2026'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify():
    record = json.loads((DEST / 'configuration-wall-reading.json').read_text())
    pdf = ROOT / record['pdf_file']
    assert sha(pdf) == record['pdf_sha256']
    assert not record['downloaded_code_executed'] and not record['hardware_experiments_run']
    assert record['physical_pages'] == list(range(3, 13))
    selected = []
    for scope in record['text_ranges']:
        page = scope['physical_page']
        raw = subprocess.check_output(
            ['pdftotext', '-raw', '-f', str(page), '-l', str(page), str(pdf), '-'],
            text=True, stderr=subprocess.PIPE)
        if page == 12:
            assert scope['end'] == raw.index('7 Related Work')
        else:
            assert scope['end'] == len(raw)
        part = raw[scope['start']:scope['end']]
        assert hashlib.sha256(part.encode()).hexdigest() == scope['selected_sha256']
        selected.append(part)
    selected_path = ROOT / record['selected_text_file']
    assert selected_path.read_text() == ''.join(selected)
    assert sha(selected_path) == record['selected_text_sha256']
    for view in record['viewed_pages']:
        assert view['actually_viewed'] and sha(ROOT / view['file']) == view['sha256']

    # Recompute from the matrix shape and instruction counts, retaining the typo.
    ops = 2 * 64**3
    compute_cycles = Fraction(ops, 16 * 16 * 2)
    setup_cycles = 160 * 3 * 3
    full_setup_cycles = 935 * 3
    assert compute_cycles == 1024 and setup_cycles == 1440 and full_setup_cycles == 2805
    assert Fraction(ops, 160 * 16) == Fraction(1024, 5)
    page7 = selected[4]
    assert '524,288' in page7 and '525,288' in page7
    corrected_percent = [float(100 * compute_cycles / (compute_cycles + t))
                         for t in [setup_cycles, full_setup_cycles]]

    # Build a two-stage event timeline independently of the closed-form bound.
    # Host prepares the next item while the device executes the previous item.
    checked = 0
    for host in [1, 5, 20, 37]:
        for device in [1, 5, 20, 53]:
            for count in [1, 2, 7, 100]:
                host_done = device_done = 0
                for _ in range(count):
                    host_done += host
                    device_done = max(host_done, device_done) + device
                assert device_done == host + device + (count - 1) * max(host, device)
                assert count * max(host, device) < device_done <= count * (host + device)
                checked += 1
    def pipeline(host, device, count=100):
        return host + device + (count - 1) * max(host, device)
    assert 100 * (20 + 20) == 4000
    assert [pipeline(20, 20), pipeline(20, 5), pipeline(5, 5)] == [2020, 2005, 505]

    phase = json.loads((DEST / 'program131-screening-notes.json').read_text())
    assert phase['new_abstract_orders'] == [131, 133, 136, 139, 146, 151]
    assert phase['new_representative_pdf_pages'] == 102
    assert phase['body_selected_orders'] == [151]
    assert phase['response_status_counts'] == {'403': 24, '200': 6}
    assert not phase['book_outline_changed'] and not phase['skeleton_changed']
    assert phase['actually_viewed_page_count'] == 5
    for key in ['catalog', 'structure']:
        assert sha(ROOT / phase['current_outline_basis'][key]) == phase['current_outline_basis'][key + '_sha256']
    sources = {s['id']: s for s in json.loads((DEST / 'sources.json').read_text())}
    assert len(phase['new_response_ids']) == len(set(phase['new_response_ids'])) == 30
    for sid in phase['new_response_ids']:
        s = sources[sid]; path = ROOT / s['file']
        assert sha(path) == s['sha256'] and path.stat().st_size == s['bytes']
        assert s['reading_status'] != 'downloaded_not_read'

    case = ROOT / record['adoption']['case']
    links = 0
    for target in re.findall(r'\]\(([^)]+)\)', case.read_text()):
        u = urlsplit(target)
        if not u.scheme and u.path:
            assert (case.parent / unquote(u.path)).resolve().is_file(), target
            links += 1
    return dict(status='passed', verified_at=datetime.now(timezone.utc).isoformat(),
                complete_new_abstracts=6, representative_pdf_pages=102,
                selected_body_papers=1, physical_pages_touched=10,
                last_page_scope='§6.2.1 only', viewed_body_pages=3,
                source_responses=30, failed_responses_not_evidence=24,
                pipeline_parameter_cases=checked,
                recomputed_paper_example_percent=corrected_percent,
                case_links_checked=links, downloaded_code_executed=False,
                hardware_experiments_run=False, errors=[])


if __name__ == '__main__':
    result = verify()
    target = Path(__file__).parent / 'configuration-wall-audit.json'
    target.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(result, ensure_ascii=False, indent=2))
