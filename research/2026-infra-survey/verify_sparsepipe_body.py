"""Check Sparsepipe selected scope and exact byte example using archived data."""
from pathlib import Path
import json
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'references/proceedings/MICRO/2024/sparsepipe-body-reading'


def verify():
    assert (BASE / 'paper.pdf').read_bytes() == (BASE.parent / 'parallel-abstracts/paper-088.pdf').read_bytes()
    subprocess.run([sys.executable, str(BASE / 'verify.py')], check=True, capture_output=True)
    result = json.loads((BASE / 'verification.json').read_text())
    assert result['status'] == 'PASS'
    assert result['full_page_text_read_pages'] == list(range(3, 14))
    assert result['partial_page_text_read_pages'] == [14]
    assert result['new_http_requests'] == result['new_full_abstracts'] == 0
    assert result['example_bytes'] == [376, 248, 176]
    return result


if __name__ == '__main__':
    print(json.dumps(verify(), ensure_ascii=False))
