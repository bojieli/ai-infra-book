#!/usr/bin/env python3
"""Verify declared source ranges and independent fusion arithmetic offline."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import subprocess
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[2]
DEST = ROOT / 'references/proceedings/ASPLOS/2026'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify():
    record = json.loads((DEST / 'redfuser-reading.json').read_text())
    pdf = ROOT / record['pdf_file']
    assert sha(pdf) == record['pdf_sha256']
    assert not record['downloaded_code_executed'] and not record['hardware_experiments_run']
    assert record['physical_pages'] == list(range(2, 13)) + [15, 16, 17, 18]
    for row in record['page_texts']:
        p = ROOT / row['file']
        raw = subprocess.check_output(['pdftotext', '-layout', '-f', str(row['page']), '-l', str(row['page']), str(pdf), '-'], text=True, stderr=subprocess.PIPE)
        assert raw == p.read_text() and sha(p) == row['sha256']
    for row in record['viewed_pages']:
        assert row['actually_viewed'] and row['physical_page'] in record['physical_pages']
        assert sha(ROOT / row['file']) == row['sha256']
    sources = json.loads((ROOT / record['crosscheck_sources']).read_text())
    by_id = {s['id']:s for s in sources}
    assert len(sources) == 10
    for row in sources:
        p = ROOT / row['file']
        assert sha(p) == row['sha256'] and p.stat().st_size == row['bytes']
        assert row['status_code'] == 200 and row['reading_status'] != 'downloaded_not_read'
        if 'raw.githubusercontent.com' in row['url']:
            assert record['fixed_commit'] in row['url']
    for row in record['crosscheck_scopes']:
        p = ROOT / row['file']
        assert sha(p) == row['sha256'] == by_id[row['source_id']]['sha256']
        if row['kind'] == 'source_lines':
            assert row['start_line'] == 1 and row['end_line'] == len(p.read_text().splitlines())
            continue
        out = ROOT / row['text_file']; assert sha(out) == row['text_sha256']
        if row['kind'] == 'html_section':
            assert BeautifulSoup(p.read_text(),'html.parser').select_one(row['selector']).get_text(' ',strip=True) + '\n' == out.read_text()
        elif row['kind'] == 'tree_metadata':
            raw = json.loads(p.read_text()); assert not raw['truncated']
            assert [x for x in raw['tree'] if '/redfuser/' in x['path']] == json.loads(out.read_text())
        else:
            raw = json.loads(p.read_text()); selected = {k:raw[k] for k in ['sha','html_url']}
            selected['commit'] = {k:raw['commit'][k] for k in ['message','tree']}
            selected['committer_date'] = raw['commit']['committer']['date']
            assert selected == json.loads(out.read_text()) and selected['sha'] == record['fixed_commit']

    from calculate_fusion_legality import calculate
    result = json.loads(Path(__file__).with_name('fusion-legality-arithmetic.json').read_text())
    assert calculate() == result
    row = result['traffic']
    assert sha(ROOT / row['config_file']) == row['config_sha256']
    aq_reads = a_reads = w_reads = outputs = 0
    for m in range(0,row['M'],row['bm']):
        for n in range(0,row['N'],row['bn']):
            height,width = min(row['bm'],row['M']-m),min(row['bn'],row['N']-n)
            aq_reads += height*row['K']; a_reads += height*row['K']*2
            w_reads += width*row['K']; outputs += height*width*2
    assert aq_reads+w_reads+outputs+row['activation_bytes']+row['quantized_activation_bytes'] == row['materialized_bytes']
    assert a_reads+w_reads+outputs+row['activation_bytes'] == row['fused_same_scale_bytes']
    assert a_reads+w_reads+outputs == row['fused_prefix_scale_bytes']
    cross = DEST / 'redfuser-crosschecks'
    assert '# GenerateOnlineExpr,' in (cross/'quant-input.txt').read_text()
    assert 'rtol=1e-2, atol=1e-1' in (cross/'quant-test.txt').read_text()
    assert 'T.Cast("float8_e4m3fn"' in (cross/'quant-generated.txt').read_text()
    assert 'sp.simplify(eval_func[i, j], force=True)' in (cross/'decompose.txt').read_text()
    assert 'case-studies/fusion-legality-and-precision.md' in (ROOT/'outlines/05-算子与运行时.md').read_text()
    return dict(status='passed', verified_at=datetime.now(timezone.utc).isoformat(),
                selected_text_pages=15, actual_page_images=8, source_responses=10,
                complete_code_files_read=6, readme_read=True, symbolic_and_arithmetic='passed',
                fp64_merge_cases=32, fp8_counterexample='55/56 versus 1',
                main_tensor_mib=[444,620,588],
                scope='Source integrity and declared reading, independent algebra and traffic; no upstream code/GPU execution or full compiler correctness claim.')


if __name__ == '__main__':
    report = verify()
    Path(__file__).with_name('fusion-legality-audit.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
