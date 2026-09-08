#!/usr/bin/env python3
"""Offline source integrity, independent tile counts and recurrence checks."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import math
import subprocess
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[2]
DEST = ROOT / 'references/proceedings/ASPLOS/2026'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify():
    record = json.loads((DEST / 'attenio-reading.json').read_text())
    pdf = ROOT / record['pdf_file']
    assert sha(pdf) == record['pdf_sha256']
    assert record['physical_pages'] == list(range(2, 14))
    for row in record['page_texts']:
        p = ROOT / row['file']
        raw = subprocess.check_output(['pdftotext', '-raw', '-f', str(row['page']), '-l', str(row['page']), str(pdf), '-'], text=True)
        assert raw == p.read_text() and sha(p) == row['sha256']
    for row in record['viewed_pages']:
        assert row['actually_viewed'] and row['physical_page'] in record['physical_pages']
        assert sha(ROOT / row['file']) == row['sha256']
    for row in record['reused_primary_scopes']:
        assert sha(ROOT / row['file']) == row['sha256']
        assert sha(ROOT / row['image_file']) == row['image_sha256']
    sources = json.loads((ROOT / record['crosscheck_sources']).read_text())
    commit = json.loads((DEST / 'attenio-crosschecks/fa259-commit.json').read_text())['sha']
    for row in sources:
        p = ROOT / row['file']
        assert p.stat().st_size == row['bytes'] and sha(p) == row['sha256']
        assert row['status_code'] == 200 and row['read_scope'] != 'pending'
        if p.suffix == '.h':
            assert '/' + commit + '/' in row['url']
    for row in record['crosscheck_scopes']:
        p = ROOT / row['file']
        assert sha(p) == row['sha256']
        if row['kind'] == 'source_lines':
            text = '\n'.join(p.read_text().splitlines()[row['start_line']-1:row['end_line']])+'\n'
        else:
            text = BeautifulSoup(p.read_text(), 'html.parser').select_one(row['selector']).get_text(' ', strip=True)+'\n'
        assert text == (ROOT / row['text_file']).read_text()
        assert sha(ROOT / row['text_file']) == row['text_sha256']

    r = json.loads(Path(__file__).with_name('attention-tiles-arithmetic.json').read_text())
    config = ROOT / r['config_file']
    assert sha(config) == r['config_sha256']
    assert json.loads(config.read_text())['head_dim'] == r['d'] == 128
    n, d, budget = r['n'], r['d'], r['fast_capacity_bytes']
    for row in r['rows']:
        a, b = row['query_rows'], row['kv_rows']
        def buffers(height):
            return [height*d*2, b*d*2, height*b*4, height*d*4, height*3*4]
        assert sum(buffers(a)) == row['live_bytes'] <= budget < sum(buffers(a+1))
        q_starts, k_starts = list(range(0, n, a)), list(range(0, n, b))
        traffic = 0
        for start in q_starts:
            traffic += min(a, n-start)*d*4  # One Q load and one final O store.
            for key_start in k_starts:
                traffic += min(b, n-key_start)*d*4  # K and V each once per Q block.
        assert traffic == row['interface_bytes']
        assert len(q_starts)*len(k_starts) == row['block_pair_updates']
        assert sum(n*d for _ in k_starts[1:]) == row['output_rescale_multiplies']
    assert [row['interface_bytes']//2**20 for row in r['rows']] == [204,304,436]
    assert r['matrix_flops'] == 34359738368
    assert r['compulsory_input_output_bytes'] == 8*2**20
    from calculate_attention_tiles import calculate, online
    assert calculate() == r  # Includes twenty small FP64 blocked/reference comparisons.
    assert math.isclose(online([0, math.log(2)], [[1], [3]], 1)[0], 7/3)
    assert not math.isclose(r['rescale_counterexample']['literal_inverse'], 7/3)
    assert 'acc_o_rowcol(mi, ni) *= scores_scale' in (DEST/'attenio-crosschecks/softmax.h').read_text()
    assert 'Headdim, 128, 128, 4' in (DEST/'attenio-crosschecks/flash_fwd_launch_template.selected.txt').read_text()
    assert 'case-studies/attention-tiles-and-io.md' in (ROOT/'outlines/05-算子与运行时.md').read_text()
    assert not record['downloaded_code_executed'] and not r['hardware_experiments_run']
    return dict(status='passed', verified_at=datetime.now(timezone.utc).isoformat(),
                selected_physical_pages=12, viewed_pages=6, crosscheck_responses=len(sources),
                reused_paper_scopes=2, fp64_examples=len(r['fp64_checks']),
                independent_capacity_traffic_counts='passed',
                upstream_code_executed=False, hardware_experiments_run=False)


if __name__ == '__main__':
    report = verify()
    Path(__file__).with_name('attention-tiles-audit.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2))
