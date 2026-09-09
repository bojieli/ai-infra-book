"""Validate the bounded Ollama history handoff without running framework code."""
from pathlib import Path
import json
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'research/2026-infra-survey/parallel-ollama'


def verify():
    # This verifier was authored for this book; it is not downloaded source.
    subprocess.run([sys.executable, str(BASE / 'verify.py')], check=True, capture_output=True)
    local = json.loads((BASE / 'verification.json').read_text())
    assert local['passed'] and not local['errors']
    proof = json.loads((BASE / 'reading-proof.json').read_text())
    pdf = BASE / proof['paper']['file']
    assert pdf.read_bytes() == (ROOT / proof['paper']['original']).read_bytes()
    page = subprocess.check_output(
        ['pdftotext', '-layout', '-f', '11', '-l', '11', str(pdf), '-'],
        stderr=subprocess.PIPE,
    )
    assert page == (BASE / 'qwen3-report-p11.txt').read_bytes()
    result = {
        'status': 'passed',
        'scope': 'Two representative Ollama changes; file and version checks plus Qwen3 p11 primary-text re-extraction. Not complete release history or framework execution.',
        'handoff': local,
        'qwen3_existing_pdf_reused': True,
        'new_conference_papers': 0,
        'framework_tests_executed': False,
    }
    (BASE / 'integration-validation.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    return result


if __name__ == '__main__':
    print(json.dumps(verify(), ensure_ascii=False))
