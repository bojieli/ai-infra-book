"""Check selected primary TAPAS pages and the bounded routing example."""
from pathlib import Path
from fractions import Fraction
import hashlib
import json
import subprocess

ROOT = Path(__file__).resolve().parents[2]
D = ROOT / 'references/proceedings/ASPLOS/2025/serving-113-117'


def check(item):
    b = (ROOT / item['file']).read_bytes()
    assert len(b) == item['bytes']
    assert hashlib.sha256(b).hexdigest() == item['sha256']
    return b


def verify():
    proof = json.loads((D / 'tapas-reading.json').read_text())
    check(proof['pdf'])
    assert [p['physical_page'] for p in proof['pages']] == list(range(5, 12))
    for page in proof['pages']:
        n = str(page['physical_page'])
        actual = subprocess.check_output(['pdftotext', '-f', n, '-l', n,
                                         str(ROOT / proof['pdf']['file']), '-'])
        assert actual == check(page)
    assert [p['physical_page'] for p in proof['figures']] == [8, 11]
    for figure in proof['figures']:
        check(figure)
        assert figure['actually_viewed'] is True
    # Hypothetical profile increments, not a token-to-power model.
    predicted = [96 + 6, 80 + 6]
    times = [Fraction(8, 10), Fraction(13, 10)]
    feasible = [i for i, power in enumerate(predicted) if power <= 100]
    admitted = [i for i in feasible if times[i] <= 1]
    assert predicted == [102, 86] and feasible == [1] and admitted == []
    break_even = Fraction(3) / Fraction(1, 10)
    assert break_even == 30
    assert 30 * Fraction(1, 10) - 3 == 0
    assert 31 * Fraction(1, 10) - 3 > 0
    result = dict(status='passed', selected_body_pages=7, figures_viewed=2,
                  canonical_merge_pending=True, performance_reproduced=False,
                  arithmetic=dict(predicted_row_kw=predicted,
                                  power_feasible_indices=feasible,
                                  deadline_feasible_indices=admitted,
                                  serial_reconfiguration_break_even_requests=int(break_even)))
    (D / 'tapas-validation.json').write_text(json.dumps(result, indent=2)+'\n')
    return result


if __name__ == '__main__':
    print(json.dumps(verify()))
