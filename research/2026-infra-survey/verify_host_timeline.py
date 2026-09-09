"""Check archived host scheduling evidence and a teaching DAG, without frameworks."""
from pathlib import Path
import json
import subprocess
import sys

BASE = Path(__file__).resolve().parent / 'parallel-host-timeline'


def verify():
    subprocess.run([sys.executable, str(BASE / 'verify.py')], check=True, capture_output=True)
    result = json.loads((BASE / 'verification.json').read_text())
    assert result['status'] == 'PASS'
    assert result['selected_text_files'] == 16 and result['git_blobs'] == 13
    assert not result['framework_tests_run'] and not result['network_used_by_verifier']
    assert result['timeline_cpu_gpu_completion'] == [[24, 40, 64], [12, 40, 52], [24, 40, 46]]
    return result


if __name__ == '__main__':
    print(json.dumps(verify(), ensure_ascii=False))
