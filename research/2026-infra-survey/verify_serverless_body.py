"""Check Dilu/Medusa selected pages and loading-path arithmetic, not execution."""
from pathlib import Path
import json
import subprocess
import sys

BASE = Path(__file__).resolve().parents[2] / 'references/proceedings/ASPLOS/2025/serverless-body-reading'


def verify():
    subprocess.run([sys.executable, str(BASE / 'verify.py')], check=True, capture_output=True)
    result = json.loads((BASE / 'validation.json').read_text())
    assert result['status'] == 'pass'
    assert result['original_pdf_pages_reextracted'] == 17
    assert result['new_abstracts'] == result['new_pdfs'] == 0
    assert {r['program_order'] for r in result['formal_identity_checks']} == {171, 172}
    manifest = json.loads((BASE.parent / 'manifest.json').read_text())
    formal = {p['program_order']: p for p in manifest['papers']}
    for record in json.loads((BASE / 'reading-records.json').read_text())['records']:
        expected = [' '.join([a.get('given', ''), a.get('family', '')]).strip() for a in formal[record['program_order']]['author_metadata']]
        assert record['authors'] == expected
    return result


if __name__ == '__main__':
    print(json.dumps(verify(), ensure_ascii=False))
