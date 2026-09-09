"""Re-extract selected COMET pages and check independent teaching arithmetic."""
from pathlib import Path
from fractions import Fraction
import hashlib
import json
import subprocess
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[2]
D = ROOT / 'references/proceedings/ASPLOS/2025/serving-113-117'


def check(record, local=False):
    data = ((D if local else ROOT) / record['file']).read_bytes()
    assert len(data) == record['bytes']
    assert hashlib.sha256(data).hexdigest() == record['sha256']
    return data


def verify():
    proof = json.loads((D / 'comet-reading.json').read_text())
    check(proof['pdf'])
    assert [p['physical_page'] for p in proof['pages']] == list(range(4, 13))
    for page in proof['pages']:
        expected = check(page)
        n = str(page['physical_page'])
        actual = subprocess.check_output(['pdftotext', '-f', n, '-l', n,
                                         str(ROOT / proof['pdf']['file']), '-'])
        assert actual == expected
    assert [p['physical_page'] for p in proof['figures']] == [8, 10]
    for figure in proof['figures']:
        check(figure)
        assert figure['actually_viewed'] is True
    for source in json.loads((D / 'comet-additional-sources.json').read_text()):
        check(source, local=True)
        assert source['status_code'] == 200
    doc = proof['official_document']
    soup = BeautifulSoup((ROOT / doc['file']).read_bytes(), 'html.parser')
    extracted = soup.find(id=doc['section_id']).get_text(' ', strip=True) + '\n'
    assert extracted.encode() == check(doc['derived'])
    assert 'mma.sync.aligned.m16n8k16.row.col.dtype.f16.f16.ctype' in extracted
    r = Fraction(1, 4)
    bits = (1-r)*4 + r*8
    time = (1-r)/2 + r
    assert bits == 5 and 16/bits == Fraction(16, 5)
    assert time == Fraction(5, 8) and 1/time == Fraction(8, 5)
    text_tiles = (256//128) * (256//128) * (384//128)
    figure_tiles = (384//128) * (384//128) * (256//128)
    assert text_tiles == 12 and figure_tiles == 18
    # Accuracy units are percentage points; integer tenths avoid float rounding.
    quality_drops = [(686-665)/10, (672-665)/10, (753-741)/10, (749-741)/10]
    assert quality_drops == [2.1, 0.7, 1.2, 0.8]
    result = dict(status='passed', selected_body_pages=9, figures_viewed=2,
                  official_document_sections_extracted=1, canonical_merge_pending=True,
                  arithmetic=dict(activation_payload_bits=float(bits),
                                  fp16_payload_ratio=float(16/bits),
                                  ideal_compute_speedup_over_int8=float(1/time),
                                  text_tiles=text_tiles, figure_tiles=figure_tiles,
                                  quality_drop_percentage_points=quality_drops),
                  downloaded_code_executed=False, performance_reproduced=False)
    (D / 'comet-validation.json').write_text(json.dumps(result, indent=2)+'\n')
    return result


if __name__ == '__main__':
    print(json.dumps(verify()))
