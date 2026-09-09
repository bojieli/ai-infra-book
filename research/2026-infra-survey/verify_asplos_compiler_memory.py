"""Verify the independent Pruner/Relax/vAttention reading package."""
from pathlib import Path
import json
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'references/proceedings/ASPLOS/2025/parallel-followup'


def verify():
    output = subprocess.check_output([sys.executable, str(BASE / 'verify.py'), '--json'])
    report = json.loads(output)
    assert report['passed']
    (BASE / 'integration-validation.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    return report


if __name__ == '__main__':
    print(json.dumps(verify()['stats'], ensure_ascii=False))
