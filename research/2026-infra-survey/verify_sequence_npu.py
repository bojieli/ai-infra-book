#!/usr/bin/env python3
"""Verify primary bytes, selected reading scopes and independent budgets."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import subprocess
import sys
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[2]
D = ROOT / 'references/framework-history/2026-09-09/sequence-and-npu'


def verify():
    sources = json.loads((D/'sources.json').read_text())
    assert len(sources) == len({s['id'] for s in sources}) == 26
    byid = {s['id']:s for s in sources}
    failed = {'npu-artifact':504, 'npu-artifact-page':504, 'mllm-current-qnn':404}
    for s in sources:
        b = (ROOT/s['file']).read_bytes()
        assert len(b) == s['bytes'] and hashlib.sha256(b).hexdigest() == s['sha256']
        assert s['status_code'] == failed.get(s['id'],200)
        if 'derived_text' in s:
            t=s['derived_text']; derived=(ROOT/t['file']).read_bytes()
            assert len(derived)==t['bytes'] and hashlib.sha256(derived).hexdigest()==t['sha256']
            article=BeautifulSoup(b,'html.parser').find('article')
            assert (article.get_text('\n',strip=True)+'\n').encode()==derived
    reading=json.loads((D/'reading.json').read_text())
    assert len(reading['sources'])==12
    for r in reading['sources']:
        s=byid[r['source_id']]
        assert r['file']==s['file'] and r['sha256']==s['sha256']
        assert r['text_file']==s.get('derived_text',s)['file']
        lines=(ROOT/r['text_file']).read_text().splitlines(keepends=True)
        assert all(1<=lo<=hi<=len(lines) for lo,hi in r['line_ranges_inclusive'])
        payload=''.join(''.join(lines[lo-1:hi]) for lo,hi in r['line_ranges_inclusive']).encode()
        assert hashlib.sha256(payload).hexdigest()==r['selected_text_sha256']
        assert r['execution']=='not_executed'
    meta=reading['metadata_checks']
    for sid,prefix in [('flexsp-commit','flexsp'),('mllm-main-commit','mllm_current'),('mllm-v1-commit','mllm_v1')]:
        c=json.loads((ROOT/byid[sid]['file']).read_text())
        assert c['sha']==meta[prefix+'_commit']
        assert c['commit']['committer']['date']==meta[prefix+'_commit_date']
    for sid in ['flexsp-readme','flexsp-train','flexsp-cross-entropy','flexsp-pipeline','flexsp-transformer']:
        assert '/'+meta['flexsp_commit']+'/' in byid[sid]['url']
    for sid in ['mllm-aot-fixed-guide','mllm-aot-config','mllm-qwen3-config']:
        assert '/'+meta['mllm_current_commit']+'/' in byid[sid]['url']
    for sid in ['mllm-v1-readme','mllm-v1-qnn']:
        assert '/'+meta['mllm_v1_commit']+'/' in byid[sid]['url']
    before=(D/'arithmetic.json').read_bytes()
    subprocess.run([sys.executable,str(D/'check_arithmetic.py')],check=True,stdout=subprocess.PIPE)
    assert (D/'arithmetic.json').read_bytes()==before
    a=json.loads(before)
    assert a['loss_normalization']['token_mean']==2.75
    assert a['ulysses_payload']['expanded_forward_send_bytes_per_rank']==28*1024**2
    assert a['mobile_kv']['logical_int8_bytes']==112*1024**2
    report=dict(verified_at=datetime.now(timezone.utc).isoformat(),status='passed',source_responses=26,
                failed_responses=3,selected_source_scopes=12,selected_paper_pages=27,body_page_views=14,
                arithmetic='Length distribution, forward all-to-all payload, token weighting, fixed chunks, logical KV and end-to-end budgets passed.',
                scope='Selected primary text and independent arithmetic only; no downloaded code, model, solver, device or cloud execution. Full goal remains active.')
    (ROOT/'research/2026-infra-survey/qa/sequence-npu-phase.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    return report


if __name__=='__main__':
    print(json.dumps(verify(),ensure_ascii=False))
