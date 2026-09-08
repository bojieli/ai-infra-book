#!/usr/bin/env python3
"""Check declared source scopes and independent evaluation/deployment arithmetic.

Does not import downloaded source, run a model, or validate GPU performance.
"""
from datetime import datetime, timezone
from fractions import Fraction as F
from pathlib import Path
import hashlib
import json
import subprocess

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[2]
DEST = ROOT / 'references/framework-history/2026-09-08/optimization-validation'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def arithmetic():
    base, a, b = (F(100), F(100)), (F(10), F(200)), (F(50), F(50))
    score_a = sum(x / y for x, y in zip(base, a)) / 2
    score_b = sum(x / y for x, y in zip(base, b)) / 2
    assert score_a == F(21, 4) > score_b == 2
    equal_a, equal_b = sum(base) / sum(a), sum(base) / sum(b)
    assert equal_a == F(20, 21) < 1 < equal_b == 2
    # Enumerate invocation frequencies independently of the closed-form crossing.
    for nx in range(101):
        p = F(nx, 100)
        total_a = nx * a[0] + (100 - nx) * a[1]
        total_b = nx * b[0] + (100 - nx) * b[1]
        assert (total_a < total_b) == (p > F(15, 19))
    assert (9 * a[0] + a[1]) / 10 == 29
    dispatched = (min(a[0], b[0]) + min(a[1], b[1])) / 2
    assert dispatched == 30 and 50 - dispatched == 20
    setup_seconds, saving_seconds = 600, F(20, 1_000_000)
    assert setup_seconds / saving_seconds == 30_000_000
    # Synthetic numerical-contract example, not a model-quality test.
    errors = [F(2)] * 2 + [F(0)] * 18
    bad = sum(e > 1 and e / F(1, 100_000_000) > F(3, 10) for e in errors)
    matched = F(len(errors) - bad, len(errors))
    assert matched == F(9, 10) and matched >= F(9, 10) and matched < F(19, 20)
    return dict(arithmetic_mean_scores=[str(score_a), str(score_b)],
                equal_frequency_speedups=[str(equal_a), str(equal_b)],
                selection_crossing='15/19', frequencies_checked=101,
                dispatched_mean_us=30, maximum_dispatch_overhead_us_exclusive=20,
                break_even_calls_at_zero_dispatch_cost=30_000_000,
                synthetic_matched_fraction=str(matched),
                scope='Explicit teaching inputs and serial time budget; not measured kernel or model performance.')


def verify():
    proof = read(DEST / 'reading.json')
    rows = read(ROOT / proof['sources_file'])
    by = {r['id']: r for r in rows}
    assert len(rows) == len(by) == proof['source_responses'] == 20
    assert sum(r['status_code'] == 200 for r in rows) == proof['successful_responses'] == 19
    assert by['looprag-dataset']['status_code'] == 401
    assert not proof['downloaded_code_executed'] and not proof['hardware_experiments_run']
    for r in rows:
        path = ROOT / r['file']
        assert sha(path) == r['sha256'] and path.stat().st_size == r['bytes']
    for s in proof['scopes']:
        path = ROOT / s['file']
        assert sha(path) == s['sha256'] == by[s['source_id']]['sha256']
        mode = s['mode']
        if mode == 'full_text':
            path.read_text()
            continue
        selected = ROOT / s['selected_file']
        assert sha(selected) == s['selected_sha256']
        if mode == 'text_range':
            assert path.read_text()[s['start']:s['end']] == selected.read_text()
        elif mode == 'html_selector':
            nodes = BeautifulSoup(path.read_text(), 'html.parser').select(s['selector'])
            assert len(nodes) == 1 and nodes[0].get_text(' ', strip=True) + '\n' == selected.read_text()
        else:
            raw = read(path)
            if mode == 'json_fields':
                value = {k: raw[k] for k in s['fields']}
            elif mode == 'commit_identity':
                value = {'sha': raw['sha'], 'commit.committer.date': raw['commit']['committer']['date'],
                         'commit.message': raw['commit']['message'].split('\n')[0]}
            elif mode == 'tree_paths':
                value = {'sha': raw['sha'], 'truncated': raw['truncated'],
                         'paths': [v['path'] for v in raw['tree'] if v['path'].endswith('.py') and
                                   v['path'].startswith(('flashinfer_bench/bench/', 'flashinfer_bench/data/', 'flashinfer_bench/apply/'))]}
                assert not raw['truncated']
            else:
                raise AssertionError(mode)
            assert value == read(selected)
    assert len(proof['scopes']) == 22
    assert {s['source_id'] for s in proof['scopes']} == {r['id'] for r in rows if r['status_code'] == 200}
    for sid, key in [('flashinfer-commit', 'framework_commit'), ('starter-commit', 'contest_commit')]:
        assert read(ROOT / by[sid]['file'])['sha'] == proof[key]
    for r in rows:
        if 'raw.githubusercontent.com/flashinfer-ai/flashinfer-bench/' in r['url']:
            assert '/' + proof['framework_commit'] + '/' in r['url']
        if 'raw.githubusercontent.com/flashinfer-ai/flashinfer-bench-starter-kit/' in r['url']:
            assert '/' + proof['contest_commit'] + '/' in r['url']
    paper = read(ROOT / 'references/proceedings/ASPLOS/2026/looprag-reading.json')
    assert sha(ROOT / paper['pdf_file']) == paper['pdf_sha256']
    text = ROOT / paper['archive_text_file']
    assert sha(text) == paper['archive_text_sha256']
    extracted = subprocess.check_output(['pdftotext', '-layout', str(ROOT / paper['pdf_file']), '-'], text=True)
    assert extracted == text.read_text()
    pages = extracted.split('\f')
    assert len([p for p in pages if p.strip()]) == paper['physical_pdf_pages'] == 22
    assert [r['physical_page'] for r in paper['selected_text_pages']] == list(range(4, 14)) + list(range(18, 23))
    for r in paper['selected_text_pages']:
        assert hashlib.sha256(pages[r['physical_page'] - 1].encode()).hexdigest() == r['sha256']
    assert [p['physical_page'] for p in paper['viewed_pages']] == [8, 10, 18, 21]
    for p in paper['viewed_pages']:
        assert p['actually_viewed'] and sha(ROOT / p['file']) == p['sha256']
    assert not paper['downloaded_code_executed'] and not paper['hardware_experiments_run']
    result = arithmetic()
    return dict(status='passed', verified_at=datetime.now(timezone.utc).isoformat(),
                selected_paper_pages=15, viewed_page_images=4, source_responses=20,
                successful_responses=19, declared_text_or_metadata_scopes=22,
                arithmetic=result, scope='Declared source integrity and independent teaching arithmetic; no model/GPU or complete engine validation.')


if __name__ == '__main__':
    result = verify()
    (Path(__file__).parent / 'optimization-evaluation-audit.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(result, ensure_ascii=False, indent=2))
