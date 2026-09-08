#!/usr/bin/env python3
"""Check selected source scopes and teaching arithmetic; execute no archived code."""
from datetime import datetime, timezone
from fractions import Fraction
from pathlib import Path
import hashlib
import json

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[2]
DIRECTORY = ROOT / 'references/framework-history/2026-09-09/rollout-resources'


def digest(value):
    return hashlib.sha256(value).hexdigest()


def read(path):
    return json.loads(path.read_text())


def field(data, dotted):
    for key in dotted.split('.'):
        data = data[key]
    return data


def check_sources():
    sources = read(DIRECTORY / 'sources.json')
    evidence = read(DIRECTORY / 'reading.json')
    assert len(sources) == evidence['responses'] == 13
    assert len({item['id'] for item in sources}) == 13
    for item in sources:
        raw = (ROOT / item['file']).read_bytes()
        assert item['status_code'] == 200
        assert len(raw) == item['bytes'] and digest(raw) == item['sha256']
    by_id = {item['id']: item for item in sources}
    for scope in evidence['scopes']:
        assert scope['file'] == by_id[scope['id']]['file']
        raw = (ROOT / scope['file']).read_bytes()
        assert digest(raw) == scope['sha256'] == by_id[scope['id']]['sha256']
        kind = scope['kind']
        if kind == 'line_ranges':
            lines = raw.decode().splitlines(keepends=True)
            for span in scope['ranges']:
                assert 1 <= span['start'] <= span['end'] <= len(lines)
                selected = ''.join(lines[span['start'] - 1:span['end']])
                assert digest(selected.encode()) == span['sha256']
        elif kind == 'json_fields':
            data = json.loads(raw)
            assert all(field(data, key) == value for key, value in scope['values'].items())
        elif kind == 'html_selectors':
            soup = BeautifulSoup(raw, 'html.parser')
            for selection in scope['selectors']:
                node = soup.select_one(selection['selector'])
                assert digest(node.get_text(' ', strip=True).encode()) == selection['text_sha256']
        elif kind == 'html_id_parent':
            soup = BeautifulSoup(raw, 'html.parser')
            node = soup.find(id=scope['element_id']).parent
            assert digest(node.get_text(' ', strip=True).encode()) == scope['text_sha256']
            assert soup.title.get_text() == scope['document_title']
        else:
            assert kind == 'full_file'
    for metadata in evidence['reused_metadata']:
        raw = (ROOT / metadata['file']).read_bytes()
        assert digest(raw) == metadata['sha256']
        assert all(field(json.loads(raw), key) == value for key, value in metadata['values'].items())
    paper = read(ROOT / 'references/proceedings/NSDI/2026/distrs-reading.json')
    assert digest((ROOT / paper['pdf']['file']).read_bytes()) == paper['pdf']['sha256']
    manifest = read(ROOT / 'references/proceedings/NSDI/2026/manifest.json')
    entry = next(item for item in manifest['entries'] if item.get('id') == 'nsdi26-zhu-ruidong')
    assert entry['selected_reading'] == paper['reading']
    assert paper['reading']['individual_physical_pages'] == list(range(8, 14))
    for view in paper['images']:
        assert view['actually_viewed']
        assert digest((ROOT / view['file']).read_bytes()) == view['sha256']
    assert not evidence['downloaded_code_executed'] and not evidence['hardware_experiments_run']
    return dict(successful_responses=len(sources), declared_scopes=len(evidence['scopes']),
                paper_pages=6, paper_images=5, page_text_comparison='Checked by verify_archive.py')


def check_arithmetic():
    times = [1] * 9 + [100]
    mean = Fraction(sum(times), len(times))
    survivors = [value - 10 for value in times if value > 10]
    residual = Fraction(sum(survivors), len(survivors))
    assert mean == Fraction(109, 10) and mean - 10 == Fraction(9, 10)
    assert residual == 90
    # Check the entire support, including the boundary at one second.
    for elapsed in range(100):
        survivors = [value - elapsed for value in times if value > elapsed]
        conditional = Fraction(sum(survivors), len(survivors))
        assert conditional == (mean if elapsed == 0 else 100 - elapsed)
    deadline, execution_bound = 120, 100
    latest_start = deadline - execution_bound
    assert latest_start == 20 and 30 + execution_bound - deadline == 10
    assert 64 * 2 - 60 == 68

    def finish(arrivals):
        now = 0
        for arrival in arrivals:
            now = max(now, arrival) + 10
        return now

    assert finish([0, 10, 20]) == 30
    assert finish([20, 20, 20]) == 50
    assert 4 * 8 == 32
    return dict(mean_seconds=float(mean), naive_remaining_seconds=float(mean - 10),
                conditional_remaining_seconds=int(residual), elapsed_values_checked=100,
                latest_start_seconds=latest_start, extra_gpu_seconds=68,
                streaming_completion_seconds=30, batch_completion_seconds=50,
                same_verification_worker_seconds=30, independent_process_capacity=32,
                scope='Hypothetical arithmetic and deterministic event ordering, not a scheduler benchmark')


if __name__ == '__main__':
    report = dict(status='passed', recorded_at=datetime.now(timezone.utc).isoformat(),
                  sources=check_sources(), arithmetic=check_arithmetic(),
                  downloaded_code_executed=False, hardware_experiments_run=False)
    output = ROOT / 'research/2026-infra-survey/reward-scheduling-audit.json'
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(report, ensure_ascii=False, indent=2))
