"""Check a selected FloatAP body scope against its existing abstract PDF."""
from pathlib import Path
import json
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'references/proceedings/MICRO/2024/floatap-body-reading'

def verify():
    assert (BASE / 'paper.pdf').read_bytes() == (BASE.parent / 'parallel-abstracts-seventh/paper-049.pdf').read_bytes()
    run = subprocess.run([sys.executable, str(BASE / 'verify.py')], capture_output=True, text=True, check=True)
    result = json.loads(run.stdout)
    assert result['status'] == 'PASS'
    assert result['new_http_requests'] == result['new_complete_abstracts'] == 0
    assert result['full_body_text_pages'] == list(range(2, 13))
    assert result['partial_body_text_pages'] == [13]
    assert result['downloaded_code_executed'] is False
    return result

if __name__ == '__main__':
    print(json.dumps(verify(), ensure_ascii=False))
