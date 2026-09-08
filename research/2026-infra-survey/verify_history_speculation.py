#!/usr/bin/env python3
"""Check declared RhymeRL/source scopes and independent teaching arithmetic."""
from datetime import datetime, timezone
from fractions import Fraction as F
from pathlib import Path
import difflib
import hashlib
import json
import subprocess
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[2]
DEST = ROOT / 'references/proceedings/ASPLOS/2026'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check_lines(row):
    lines = (ROOT / row['file']).read_text().splitlines(keepends=True)
    assert all(1 <= a <= b <= len(lines) for a, b in row['ranges'])
    selected = ''.join(''.join(lines[a - 1:b]) for a, b in row['ranges'])
    assert hashlib.sha256(selected.encode()).hexdigest() == row['selection_sha256']


def verify():
    record = json.loads((DEST / 'rhymerl-reading.json').read_text())
    pdf = ROOT / record['pdf_file']
    assert sha(pdf) == record['pdf_sha256']
    assert record['physical_pages'] == list(range(2, 13))
    assert not record['downloaded_code_executed'] and not record['hardware_experiments_run']
    for row in record['page_texts']:
        p = ROOT / row['file']
        raw = subprocess.check_output(['pdftotext', '-' + row['extraction'], '-f',
                                       str(row['page']), '-l', str(row['page']), str(pdf), '-'],
                                      text=True, stderr=subprocess.PIPE)
        assert raw == p.read_text() and sha(p) == row['sha256']
        a, b = row['start_character'], row['end_character']
        assert 0 <= a < b <= len(raw)
        assert hashlib.sha256(raw[a:b].encode()).hexdigest() == row['selected_text_sha256']
        if row['page'] == 4:
            assert raw[a:].startswith('continued after recomputing')
        if row['page'] == 12:
            assert raw[b:].startswith('References')
    assert len(record['viewed_pages']) == 7
    for row in record['viewed_pages']:
        assert row['actually_viewed'] and sha(ROOT / row['file']) == row['sha256']
    sources = json.loads((ROOT / record['crosscheck_sources']).read_text())
    assert len(sources) == len({r['id'] for r in sources}) == 12
    by_id = {r['id']: r for r in sources}
    for row in sources:
        p = ROOT / row['file']
        assert sha(p) == row['sha256'] and p.stat().st_size == row['bytes']
        assert row['reading_status'] != 'downloaded_not_read'
        assert row['status_code'] == (403 if row['id'] == 'rhymerl-publisher' else 200)
    for row in record['crosscheck_scopes']:
        p = ROOT / row['file']
        assert sha(p) == row['sha256'] == by_id[row['source_id']]['sha256']
        if row['kind'] == 'source_lines':
            check_lines(row)
            continue
        out = ROOT / row['text_file']
        assert sha(out) == row['text_sha256']
        if row['kind'] == 'html_selection':
            node = BeautifulSoup(p.read_text(), 'html.parser').select(row['selector'])[row['selector_index']]
            assert node.get_text(' ', strip=True) + '\n' == out.read_text()
        elif row['kind'] == 'json_fields':
            raw = json.loads(p.read_text())
            assert {k: raw[k] for k in row['keys']} == json.loads(out.read_text())
        elif row['kind'] == 'source_diff':
            other = ROOT / row['against_file']
            assert sha(other) == row['against_sha256']
            diff = ''.join(difflib.unified_diff(p.read_text().splitlines(True),
                                               other.read_text().splitlines(True),
                                               fromfile='v0.19.0', tofile='537af2c'))
            assert diff == out.read_text()
        else:
            raise AssertionError(row['kind'])
    for row in record['reused_scopes']:
        p = ROOT / row['file']
        assert sha(p) == row['sha256']
        if row['kind'] == 'source_lines':
            check_lines(row)
        else:
            assert json.loads(p.read_text())['sha'] == row['expected_sha']

    from calculate_history_speculation import calculate
    result = json.loads(Path(__file__).with_name('history-speculation-arithmetic.json').read_text())
    assert calculate() == result and result['exact_distribution_checks'] == 40
    low, high = result['candidates']
    assert F(low['ms_per_output_token_exact']) > 1 > F(high['ms_per_output_token_exact'])
    saving = 1 - F(high['ms_per_output_token_exact'])
    n = high['setup_amortization_token_estimate']
    assert (n - 1) * saving < 2000 <= n * saving
    host = result['host_index']
    assert host['total_tokens'] == host['prompts'] * host['responses_per_prompt'] * host['tokens_per_response']
    assert host['total_tokens'] * 4 == host['raw_token_ids_MiB'] * 2**20
    assert host['index_GiB'] * 2**30 == host['total_tokens'] * 32
    for chapter in ['08-单实例推理.md', '10-训练系统.md']:
        assert 'case-studies/history-drafts-and-rollout.md' in (ROOT / 'outlines' / chapter).read_text()
    return dict(status='passed', verified_at=datetime.now(timezone.utc).isoformat(),
                selected_text_pages=11, actual_page_images=7, source_responses=12,
                successful_responses=11, failed_responses=1, reused_scopes=4,
                exact_distribution_checks=40, arithmetic='passed',
                scope='Declared source integrity and independent IID sampling/cost arithmetic; not full published-paper, framework or GPU validation.')


if __name__ == '__main__':
    report = verify()
    Path(__file__).with_name('history-speculation-audit.json').write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(report, ensure_ascii=False, indent=2))
