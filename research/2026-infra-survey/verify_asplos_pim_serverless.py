"""Validate six PIM and serverless primary abstracts with version boundaries."""
from pathlib import Path
import json
import subprocess
import sys

BASE = Path(__file__).resolve().parents[2] / 'references/proceedings/ASPLOS/2025/parallel-pim-serverless'


def verify():
    output = subprocess.check_output([sys.executable, str(BASE / 'verify.py')], text=True)
    result = json.loads(output)
    assert result['status'] == 'pass'
    assert result['freshly_reextracted_unique_doi_primary_abstracts'] == 6
    assert result['archived_pdf_pages'] == 91 and result['selected_body_pages'] == 0
    assert result['unresolved_primary_abstract_dois'] == []
    (BASE / 'integration-validation.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    return result


if __name__ == '__main__':
    print(json.dumps(verify(), ensure_ascii=False))
