"""Verify the archived Duplex selected reading without executing its artifact."""
from pathlib import Path
import hashlib
import json
import subprocess

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'references/proceedings/MICRO/2024/duplex-body-reading'

def verify():
    record = json.loads((BASE / 'reading.json').read_text())
    pdf = BASE / record['pdf']
    digest = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
    assert digest(pdf) == record['pdf_sha256']
    canonical = json.loads((BASE.parent / 'public-abstracts.json').read_text())['papers']
    source = next(row for row in canonical if row['program_order'] == 105)
    assert source['pdf_sha256'] == record['pdf_sha256']
    assert source['doi'].lower() == record['doi'].lower()
    assert record['full_text_pages_read'] == [4, 5, 6, 7, 8, 9]
    assert len(record['page_texts']) == 6
    for page, row in zip(record['full_text_pages_read'], record['page_texts']):
        text = BASE / row['file']
        assert digest(text) == row['sha256']
        extracted = subprocess.run(['pdftotext', '-f', str(page), '-l', str(page), str(pdf), '-'], check=True, capture_output=True).stdout
        assert extracted == text.read_bytes()
    assert len(record['images_viewed']) == 1
    image = record['images_viewed'][0]
    assert image['physical_page'] == 9 and digest(BASE / image['file']) == image['sha256']
    assert not record['whole_paper_read'] and not record['downloaded_code_executed']
    assert record['new_abstracts'] == record['new_pdfs'] == 0
    assert not record['implementation_files_read']
    return {'status': 'passed', 'full_text_pages_read': [4, 5, 6, 7, 8, 9], 'visually_read_pages': [9], 'new_abstracts': 0, 'new_pdfs': 0, 'errors': []}

if __name__ == '__main__':
    print(json.dumps(verify()))
