"""Check declared GraphPipe pages and the sample-based activation example."""
from pathlib import Path
import hashlib
import json
import math
import subprocess

ROOT = Path(__file__).resolve().parents[2]
D = ROOT / 'references/proceedings/ASPLOS/2025/screening-129-135'


def check(record):
    data = (ROOT / record['file']).read_bytes()
    assert len(data) == record['bytes'] and hashlib.sha256(data).hexdigest() == record['sha256']
    return data


def verify():
    proof = json.loads((D / 'graphpipe-reading.json').read_text())
    check(proof['pdf'])
    assert [p['physical_page'] for p in proof['pages']] == list(range(3, 10))
    for p in proof['pages']:
        n = str(p['physical_page'])
        data = subprocess.check_output(['pdftotext', *p['extraction_flags'], '-f', n, '-l', n, str(ROOT/proof['pdf']['file']), '-'])
        assert data == check(p)
    assert [p['physical_page'] for p in proof['figures']] == [3, 8, 9]
    for p in proof['figures']:
        check(p)
        assert p['actually_viewed']
    a = json.loads((D/'graphpipe-arithmetic.json').read_text())
    for key in ('uniform', 'per_stage'):
        r = a[key]
        assert r['resident_samples'] == r['resident_microbatches'] * r['samples_per_microbatch']
        assert r['activation_mib'] == r['resident_samples'] * a['saved_activation_per_sample_mib']
    assert a['saved_mib'] == a['uniform']['activation_mib'] - a['per_stage']['activation_mib'] == 128
    assert math.isclose(a['saved_fraction'], a['saved_mib']/a['uniform']['activation_mib'])
    result = dict(status='passed', selected_body_pages=7, viewed_body_pages=3,
                  activation_mib=[768, 640], saved_mib=128, measured_performance=False,
                  downloaded_code_executed=False, new_outline_sections=0)
    (D/'graphpipe-validation.json').write_text(json.dumps(result, indent=2) + '\n')
    return result


if __name__ == '__main__':
    print(json.dumps(verify()))
