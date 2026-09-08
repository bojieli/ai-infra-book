#!/usr/bin/env python3
"""Check declared source scopes and independent memory-placement examples.

Never imports archived source or executes its scripts, kernels or models.
"""
from collections import Counter
from datetime import datetime, timezone
from fractions import Fraction as F
from pathlib import Path
import hashlib
import json
import subprocess
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[2]
DEST = ROOT / 'references/framework-history/2026-09-09/memory-tiering'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def digest(text):
    return hashlib.sha256(text.encode()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def arithmetic():
    byte_count = 3 * 4096 * 12288 * 2
    assert byte_count == 288 * 2**20
    size_gib = F(byte_count, 2**30)
    times_ms = {b: max(size_gib / b, size_gib / 24) * 1000 for b in (100, 40, 8)}
    assert times_ms[100] == times_ms[40] == F(375, 32)
    assert times_ms[8] == F(1125, 32)
    migration_ms = size_gib / 8 * 1000
    rows = []
    for lead_ms in (0, 16, 40):
        exposed = {b: max(F(0), t - lead_ms) for b, t in times_ms.items()}
        saving = exposed[8] - exposed[40]
        first_beneficial = int(migration_ms // saving) + 1 if saving else None
        if first_beneficial is not None:
            assert first_beneficial * saving > migration_ms
            assert (first_beneficial - 1) * saving <= migration_ms
        rows.append(dict(lead_ms=lead_ms, exposed_ms={str(b): float(t) for b,t in exposed.items()},
                         saving_per_use_ms=float(saving), first_beneficial_reuse_count=first_beneficial))
    assert rows[1]['first_beneficial_reuse_count'] == 2
    assert rows[2]['first_beneficial_reuse_count'] is None
    # A separate sensitivity example for the empirical load-latency assumption:
    # local share x; fixed MLP and request count, NOT full application latency.
    def service(x):
        return x * (100 + 300*x*x) + (1-x) * (200 + 300*(1-x)**2)
    x = F(5, 9)
    assert service(x) == F(2000, 9)
    assert service(0) == 500 and service(1) == 400 and service(F(1,2)) == 225
    for i in range(101):
        q = F(i, 100)
        assert service(q) - service(x) == 900 * (q-x)**2
        # Artifact remote fraction y must be substituted as x=1-y.
        y = 1-q
        assert service(q) == (1-y)*(100+300*(1-y)**2)+y*(200+300*y*y)
        assert 200-100*q >= 100  # without load inflation all-local minimizes mean
    return dict(scope='Hypothetical service bounds and overlap/migration sensitivity; no hardware measurement or paper-speedup reproduction.',
                weight_bytes=byte_count, h2d_gib_s=24,
                transfer_lower_ms={str(b):float(t) for b,t in times_ms.items()},
                migration_lower_ms=float(migration_ms), lead_sensitivity=rows,
                interleave_sensitivity=dict(local_share=float(x),mean_service_ns=float(service(x)),
                    scope='Illustrative quadratic latency curves; fixed MLP and request fraction assumptions, not a universal queueing law.'))


def verify():
    proof = read(DEST/'reading.json')
    rows = read(ROOT/proof['sources_file']); by = {r['id']:r for r in rows}
    assert len(rows) == len(by) == proof['source_responses'] == 17
    assert Counter(r['status_code'] for r in rows) == {200:15,429:2}
    assert not proof['downloaded_code_executed'] and not proof['hardware_experiments_run']
    for row in rows:
        path = ROOT/row['file']
        assert sha(path) == row['sha256'] and path.stat().st_size == row['bytes']
        assert row['reading_status'] != 'downloaded_not_read'
    assert len(proof['scopes']) == 15
    assert {s['source_id'] for s in proof['scopes']} == {r['id'] for r in rows if r['status_code']==200}
    for scope in proof['scopes']:
        path = ROOT/scope['file']
        assert sha(path) == scope['sha256'] == by[scope['source_id']]['sha256']
        if scope['mode'] == 'full_text':
            path.read_text()
        elif scope['mode'] == 'html_sections':
            soup = BeautifulSoup(path.read_text(),'html.parser')
            for section in scope['sections']:
                nodes = soup.select(section['selector']); assert len(nodes)==1
                text = nodes[0].get_text(' ',strip=True)+'\n'
                assert text == section['text'] and digest(text) == section['sha256']
        elif scope['mode'] == 'pdf_pages':
            pages = subprocess.check_output(['pdftotext','-raw',str(path),'-'],text=True).split('\f')
            for page in scope['pages']:
                assert digest(pages[page['physical_page']-1]) == page['sha256']
        elif scope['mode'] == 'metadata':
            raw = read(path)
            if 'commit.committer.date' in scope['fields']:
                value = dict(sha=raw['sha'],date=raw['commit']['committer']['date'],message=raw['commit']['message'])
            elif 'selected_paths' in scope['fields']:
                paths=scope['values']['paths']
                assert not raw['truncated'] and set(paths)<={r['path'] for r in raw['tree']}
                value=dict(sha=raw['sha'],truncated=raw['truncated'],paths=paths)
            else:
                value={k:raw[k] for k in scope['fields']}
            assert value==scope['values']
        else:
            raise AssertionError(scope['mode'])
    for repo in ('pact','camp'):
        commit=proof[repo+'_commit']
        assert read(DEST/(repo+'-commit.json'))['sha']==commit
        for row in rows:
            if f'raw.githubusercontent.com/MoatLab/{repo.upper()}/' in row['url']:
                assert '/'+commit+'/' in row['url']
    for scope in proof['reused_scopes']:
        path=ROOT/scope['file']; assert sha(path)==scope['sha256']
        text=''.join(path.read_text().splitlines(keepends=True)[scope['first_line']-1:scope['last_line']])
        assert digest(text)==scope['selected_sha256']
    page_count=image_count=0
    for name,expected,images in [('pact',[4,5,6,7,8,9,10,13,14],[4,6,14]),('camp',list(range(4,14)),[7,9,10,12,13])]:
        paper=read(ROOT/f'references/proceedings/ASPLOS/2026/{name}-reading.json')
        pdf=ROOT/paper['pdf_file']; assert sha(pdf)==paper['pdf_sha256']
        assert sha(ROOT/paper['archive_text_file'])==paper['archive_text_sha256']
        pages=subprocess.check_output(['pdftotext','-raw',str(pdf),'-'],text=True,stderr=subprocess.PIPE).split('\f')
        assert sum(bool(p.strip()) for p in pages)==paper['physical_pdf_pages']
        assert [p['physical_page'] for p in paper['selected_text_pages']]==expected
        for page in paper['selected_text_pages']:
            assert digest(pages[page['physical_page']-1])==page['sha256']; page_count+=1
        assert [p['physical_page'] for p in paper['viewed_pages']]==images
        for page in paper['viewed_pages']:
            assert page['actually_viewed'] and sha(ROOT/page['file'])==page['sha256']; image_count+=1
        assert not paper['downloaded_code_executed'] and not paper['hardware_experiments_run']
    return dict(status='passed',verified_at=datetime.now(timezone.utc).isoformat(),paper_body_pages=page_count,
                viewed_paper_images=image_count,source_responses=len(rows),successful_responses=15,http_errors=2,
                source_scopes=len(proof['scopes']),reused_scopes=len(proof['reused_scopes']),arithmetic=arithmetic(),
                scope='Source integrity, declared selected reading and independent teaching arithmetic; not a paper or engine reproduction.')


if __name__=='__main__':
    result=verify()
    for name,data in [('memory-tiering-audit.json',result),('memory-tiering-arithmetic.json',result['arithmetic'])]:
        (Path(__file__).parent/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(result,ensure_ascii=False,indent=2))
