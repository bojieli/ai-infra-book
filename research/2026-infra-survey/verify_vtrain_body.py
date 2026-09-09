"""Verify the archived vTrain selected reading without executing its artifact."""
from pathlib import Path
from fractions import Fraction
import hashlib
import json
import subprocess

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'references/proceedings/MICRO/2024/vtrain-body-reading'

def verify():
    record = json.loads((BASE / 'reading.json').read_text())
    pdf = BASE / record['pdf']
    digest = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
    assert digest(pdf) == record['pdf_sha256']
    canonical = json.loads((BASE.parent / 'public-abstracts.json').read_text())['papers']
    source = next(row for row in canonical if row['program_order'] == 12)
    assert source['pdf_sha256'] == record['pdf_sha256']
    assert source['doi'].lower() == record['doi'].lower()
    assert record['full_text_pages_read'] == [4, 5, 6, 7]
    assert len(record['page_texts']) == 4
    for page, row in zip(record['full_text_pages_read'], record['page_texts']):
        text = BASE / row['file']
        assert digest(text) == row['sha256']
        extracted = subprocess.run(['pdftotext', '-f', str(page), '-l', str(page), str(pdf), '-'], check=True, capture_output=True).stdout
        assert extracted == text.read_bytes()
    assert len(record['images_viewed']) == 1
    image = record['images_viewed'][0]
    assert image['physical_page'] == 7 and digest(BASE / image['file']) == image['sha256']
    assert not record['whole_paper_read'] and not record['downloaded_code_executed']
    assert record['new_abstracts'] == record['new_pdfs'] == 0
    arithmetic = record['teaching_arithmetic']
    k = Fraction(arithmetic['k'])
    assert Fraction(arithmetic['equal_at_k']) == Fraction(20, 18)
    assert 70 + 30 * k == Fraction(arithmetic['A_ms'])
    assert 90 + 12 * k == Fraction(arithmetic['B_ms'])
    return {'status': 'passed', 'full_text_pages_read': [4, 5, 6, 7], 'visually_read_pages': [7], 'new_abstracts': 0, 'new_pdfs': 0, 'errors': []}

if __name__ == '__main__':
    print(json.dumps(verify()))
