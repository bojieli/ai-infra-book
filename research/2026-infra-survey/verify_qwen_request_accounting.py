"""Verify independent request arithmetic and synchronized corrected expressions."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import html
import re
import json
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
D = ROOT/'research/2026-infra-survey/qwen-request-accounting'


def verify_pd_budget(text):
    """Keep the complete conditional budget together, allowing prose edits."""
    required = ('36 层', '8,192 token', '8 个 KV 头', '128 维', 'BF16',
                '1.125 GiB', '25 GB/s', '48.32 ms', '条件式')
    paragraphs = re.split(r'\n\s*\n|</p>', text)
    visible = [html.unescape(re.sub(r'<[^>]+>', '', p)) for p in paragraphs]
    assert any(all(term in p for term in required) for p in visible), 'Missing or inconsistent conditional Qwen3 PD budget'


def verify():
    proof=json.loads((D/'input-proofs.json').read_text())
    for source in proof['model_configs']:
        b=(ROOT/source['file']).read_bytes()
        assert len(b)==source['bytes'] and hashlib.sha256(b).hexdigest()==source['sha256']
    before=(D/'arithmetic.json').read_bytes()
    subprocess.run([sys.executable,str(D/'arithmetic.py')],check=True,stdout=subprocess.PIPE)
    assert (D/'arithmetic.json').read_bytes()==before
    a=json.loads(before);rows=a['generation_boundaries']
    assert rows[2]['post_prefill_calls']==0
    assert rows[2]['correct_final_pages']==1 and rows[2]['wrong_final_pages']==2
    assert rows[1]['correct_old_history_bytes']==rows[3]['correct_old_history_bytes']
    assert a['pd_transfer']['qwen8_ms']==48.31838208
    # Check our corrected expressions, not concurrent user edits or whole-file hashes.
    for name in ['outlines/02-模型架构.md','outlines/extensions/02-模型架构.md','skeleton.html']:
        assert 'D×H+D(D−1)/2' in (ROOT/name).read_text()
    for name in ['outlines/09-分布式推理.md','outlines/extensions/09-分布式推理.md','skeleton.html']:
        verify_pd_budget((ROOT/name).read_text())
    assert 'DH+D(D−1)/2' in (ROOT/'case-studies/model-resource-accounting.md').read_text()
    report=dict(verified_at=datetime.now(timezone.utc).isoformat(),status='passed',configs=2,
                corrected_files=6,ordinary_request_boundaries=len(rows),
                scope='Selected Qwen3 formulas, request boundaries and synchronized prose; not whole-book or hardware validation.')
    (D/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    return report


if __name__=='__main__':
    print(json.dumps(verify(),ensure_ascii=False))
