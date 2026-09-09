"""Validate the bounded EDM/Aqua reading packet, preserving the OS2G gap."""
from pathlib import Path
import json
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'references/proceedings/ASPLOS/2025/parallel-next'


def verify():
    output = subprocess.check_output([sys.executable, str(BASE / 'verify.py')], text=True)
    result = json.loads(output)
    assert result['status'] == 'pass'
    assert result['independently_reextracted_full_primary_abstracts'] == 2
    assert result['archived_pdf_pages'] == 33
    assert result['fresh_pdf_body_pages_reextracted'] == 4
    assert result['unresolved_primary_abstract_dois'] == ['10.1145/3676641.3716265']
    (BASE / 'integration-validation.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    return result


if __name__ == '__main__':
    print(json.dumps(verify(), ensure_ascii=False))
