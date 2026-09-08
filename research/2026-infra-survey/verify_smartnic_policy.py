#!/usr/bin/env python3
"""Verify declared Wave/ghOSt reading and independent resource arithmetic."""
from datetime import datetime, timezone
from fractions import Fraction as F
from pathlib import Path
import hashlib
import json
import subprocess
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[2]
DEST = ROOT / 'references/framework-history/2026-09-09/smartnic-policy'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def digest(text):
    return hashlib.sha256(text.encode()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def arithmetic():
    # Independent linear service model, not reconstructed Wave measurements.
    original, available = 30, 32
    threshold = 1-F(original, available)
    gain = {str(d): F(available, original)*(1-d) for d in (F(2,100), F(8,100))}
    assert threshold == F(1,16)
    assert gain['1/50'] == F(392,375) and gain['2/25'] == F(368,375)
    # Reuse chapter 11's declared 3 core-seconds, 2 GiB, 30 seconds per task.
    baseline_cpu = F(original,3)
    offload_cpu = F(available,3)*(1-F(2,100))
    env600, env720 = F(600,2*30), F(720,2*30)
    assert min(baseline_cpu,env600) == min(offload_cpu,env600) == 10
    assert min(offload_cpu,env720) == F(784,75)
    exposed = [max(F(0),F(3,4)-work) for work in (F(1),F(1,5))]
    assert exposed == [0,F(11,20)]
    # Check latency versus throughput denominators separately.
    assert F(6,4)-1 == F(1,2) and 1-F(4,6) == F(1,3)
    return dict(scope='Independent teaching model; no source code, policy, model or hardware execution.',
        core_budget=dict(total=available,original_task_cores=original),
        loss_threshold_percent=float(100*threshold),
        throughput_ratios={k:float(v) for k,v in gain.items()},
        tasks_per_second=dict(original_cpu=float(baseline_cpu),offloaded_cpu=float(offload_cpu),environment_600_gib=float(env600),environment_720_gib=float(env720),combined_600_gib=float(min(offload_cpu,env600)),combined_720_gib=float(min(offload_cpu,env720))),
        exposed_read_microseconds=[float(v) for v in exposed],
        serial_4_plus_1_plus_1=dict(time_increase_percent=50,throughput_decrease_fraction='1/3'))


def verify():
    proof=read(DEST/'reading.json'); rows=read(ROOT/proof['sources_file'])
    assert len(rows)==len({r['id'] for r in rows})==8
    for row in rows:
        p=ROOT/row['file']
        assert row['status_code']==200 and row['reading_status']=='declared_scopes_read'
        assert sha(p)==row['sha256'] and p.stat().st_size==row['bytes']
    assert len(proof['scopes'])==10 and len(proof['reused_scopes'])==2
    assert {s['source_id'] for s in proof['scopes']}=={r['id'] for r in rows}
    for s in proof['scopes']+proof['reused_scopes']:
        p=ROOT/s['file'];assert sha(p)==s['sha256']
        if s['mode']=='full_text':continue
        if s['mode']=='lines':
            text=''.join(p.read_text().splitlines(keepends=True)[s['first_line']-1:s['last_line']])
            assert digest(text)==s['selected_sha256']
        elif s['mode']=='html_selector':
            nodes=BeautifulSoup(p.read_text(),'html.parser').select(s['selector']);assert len(nodes)==1
            text=nodes[0].get_text(' ',strip=True)+'\n'
            assert text==s['selected_text'] and digest(text)==s['selected_sha256']
        elif s['mode']=='json_fields':
            d=read(p);assert {k:d[k] for k in s['fields']}==s['values']
        elif s['mode']=='commit_identity':
            d=read(p);assert dict(sha=d['sha'],date=d['commit']['committer']['date'],message=d['commit']['message'])==s['values']
        else:raise AssertionError(s['mode'])
    paper=read(ROOT/'references/proceedings/ASPLOS/2026/wave-reading.json')
    pdf=ROOT/paper['pdf_file'];assert sha(pdf)==paper['pdf_sha256']
    assert sha(ROOT/paper['archive_text_file'])==paper['archive_text_sha256']
    pages=subprocess.check_output(['pdftotext','-layout',str(pdf),'-'],text=True).split('\f')
    assert sum(bool(p.strip()) for p in pages)==18
    assert [p['physical_page'] for p in paper['selected_text_pages']]==list(range(2,15))
    for p in paper['selected_text_pages']:assert digest(pages[p['physical_page']-1])==p['sha256']
    assert [p['physical_page'] for p in paper['viewed_pages']]==[6,10,11,12,14]
    for p in paper['viewed_pages']:assert p['actually_viewed'] and sha(ROOT/p['file'])==p['sha256']
    for obj in (proof,paper):assert not obj['downloaded_code_executed'] and not obj['hardware_experiments_run']
    return dict(status='passed',verified_at=datetime.now(timezone.utc).isoformat(),paper_text_pages=13,viewed_paper_images=5,source_responses=8,declared_source_scopes=10,reused_scopes=2,arithmetic=arithmetic(),scope='Source integrity and declared reading; not complete Wave/kernel verification, model execution or full-book audit.')


if __name__=='__main__':
    result=verify()
    for name,data in [('smartnic-policy-audit.json',result),('smartnic-policy-arithmetic.json',result['arithmetic'])]:
        (Path(__file__).parent/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(result,ensure_ascii=False,indent=2))
