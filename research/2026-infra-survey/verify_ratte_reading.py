"""Verify selected Ratte pages and independently derived arithmetic only."""
from pathlib import Path
from fractions import Fraction
import hashlib
import json
import subprocess

ROOT = Path(__file__).resolve().parents[2]
D = ROOT/'references/proceedings/ASPLOS/2025/screening-111-123'


def check(item):
    data = (ROOT/item['file']).read_bytes()
    assert len(data) == item['bytes']
    assert hashlib.sha256(data).hexdigest() == item['sha256']
    return data


def verify():
    proof = json.loads((D/'ratte-reading.json').read_text())
    check(proof['pdf'])
    assert [p['physical_page'] for p in proof['pages']] == [2,3,4,7,8,9,10,11,12]
    for page in proof['pages']:
        n = str(page['physical_page'])
        actual = subprocess.check_output(['pdftotext','-f',n,'-l',n,str(ROOT/proof['pdf']['file']),'-'])
        assert actual == check(page)
    assert [f['physical_page'] for f in proof['figures']] == [12]
    for figure in proof['figures']:
        check(figure)
        assert figure['actually_viewed'] is True
    valid = 1000 * Fraction(11, 1000)
    rates = [Fraction(1000,67), Fraction(1000,191), valid/67]
    assert valid == 11
    # Arbitrary precision arithmetic checks representability, not old MLIR behavior.
    lo, hi = -(2**63), 2**63-1
    result = (lo+1)//-1
    intermediate = lo//-1
    assert result == hi and lo <= result <= hi
    assert intermediate == 2**63 and intermediate > hi
    report = dict(status='passed', selected_body_pages=9, figures_viewed=1,
                  canonical_merge_pending=True, compiler_executed=False,
                  arithmetic=dict(raw_candidates_per_second=float(rates[0]),
                                  ratte_candidates_per_second=float(rates[1]),
                                  baseline_valid_candidates=11,
                                  baseline_valid_per_generation_second=float(rates[2]),
                                  end_to_end_speedup_claimed=False,
                                  valid_i64_result=result, invalid_i64_intermediate=intermediate))
    (D/'ratte-validation.json').write_text(json.dumps(report,indent=2)+'\n')
    return report


if __name__ == '__main__':
    print(json.dumps(verify()))
