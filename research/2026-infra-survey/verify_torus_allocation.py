#!/usr/bin/env python3
"""Check declared Morphlux scopes and small, independent allocation calculations.

Does not import the author artifact, solve its ILP, or simulate a network.
"""
from collections import Counter
from datetime import datetime, timezone
from fractions import Fraction as F
from itertools import combinations
from pathlib import Path
import hashlib
import json
import subprocess
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[2]
DEST = ROOT/'references/framework-history/2026-09-09/torus-allocation'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def digest(text):
    return hashlib.sha256(text.encode()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def arithmetic():
    n, alpha_s = 8, F(5, 1_000_000)
    cases = []
    for tokens in (1024, 1):
        payload = tokens*4096*2
        per_rank = F(2*(n-1), n)*payload
        service = {b: (2*(n-1)*alpha_s+per_rank/(b*10**9)) for b in (25,75)}
        saving = service[25]-service[75]
        extra_setup_s = F(1,10)
        calls = int(extra_setup_s//saving)+1
        assert (calls-1)*saving <= extra_setup_s < calls*saving
        assert per_rank == (14*2**20 if tokens==1024 else 14336)
        assert saving == per_rank*F(2,75*10**9)
        cases.append(dict(tokens=tokens,payload_bytes=payload,per_rank_sent_bytes=int(per_rank),
            model_time_us={str(b):float(t*10**6) for b,t in service.items()},
            model_speed_ratio=float(service[25]/service[75]),saving_us=float(saving*10**6),
            extra_setup_ms=100,first_beneficial_call_count=calls))
    assert cases[0]['first_beneficial_call_count']==256
    strip={(x,y) for x in range(4) for y in range(2)}
    checker={(x,y) for x in range(4) for y in range(4) if (x+y)%2==0}
    windows=[frozenset(((x+dx)%4,(y+dy)%4) for dx in (0,1) for dy in (0,1)) for x in range(4) for y in range(4)]
    def packing(free):
        candidates=[w for w in windows if w<=free]
        maximum=0
        for count in range(1,len(free)//4+1):
            if any(len(set().union(*group))==4*count for group in combinations(candidates,count)):
                maximum=count
        return len(candidates),maximum
    assert len(strip)==len(checker)==8
    assert packing(strip)==(4,2) and packing(checker)==(0,0)
    for dx in range(4):
        for dy in range(4):
            for free,expected in [(strip,(4,2)),(checker,(0,0))]:
                assert packing({((x+dx)%4,(y+dy)%4) for x,y in free})==expected
    return dict(scope='Hypothetical alpha-beta and 16-slot placement examples, not a physical TPU/GPU recommendation or a Morphlux reproduction.',
                participants=n,alpha_us=5,ring_steps=14,collectives=cases,
                placement=dict(free_slots_each=8,request_shape=[2,2],strip_candidate_windows=4,
                    strip_simultaneous_allocations=2,checkerboard_allocations=0,translated_patterns_checked=32),
                cut=dict(directed_flows=4,requested_gb_s_each=25,directed_capacity_gb_s=50,
                    offered_gb_s=100,simultaneous_equal_rate_upper_gb_s=12.5))


def verify():
    proof=read(DEST/'reading.json');rows=read(ROOT/proof['sources_file']);by={r['id']:r for r in rows}
    assert len(rows)==len(by)==proof['source_responses']==18
    assert Counter(r['status_code'] for r in rows)=={200:17,403:1}
    for row in rows:
        path=ROOT/row['file'];assert sha(path)==row['sha256'] and path.stat().st_size==row['bytes']
        assert row['reading_status']!='downloaded_not_read'
    assert len(proof['scopes'])==21
    assert {s['source_id'] for s in proof['scopes']}=={r['id'] for r in rows if r['status_code']==200}
    for scope in proof['scopes']:
        path=ROOT/scope['file'];assert sha(path)==scope['sha256']==by[scope['source_id']]['sha256']
        mode=scope['mode']
        if mode=='full_text':
            path.read_text();continue
        if mode=='lines':
            text=''.join(path.read_text().splitlines(keepends=True)[scope['first_line']-1:scope['last_line']])
        elif mode=='html_selector':
            nodes=BeautifulSoup(path.read_text(),'html.parser').select(scope['selector']);assert len(nodes)==1
            text=nodes[0].get_text(' ',strip=True)+'\n'
            assert text==scope['selected_text']
        elif mode=='heading_siblings':
            h=BeautifulSoup(path.read_text(),'html.parser').find(id=scope['heading_id']);out=[h.get_text(' ',strip=True)]
            for node in h.next_siblings:
                if getattr(node,'name',None) in scope['stop_headings']:break
                if getattr(node,'name',None):out.append(node.get_text(' ',strip=True))
            text='\n'.join(out)+'\n';assert text==scope['selected_text']
        else:
            raw=read(path)
            if mode=='repo_fields':value={k:raw[k] for k in scope['fields']}
            elif mode=='commit_identity':value=dict(sha=raw['sha'],date=raw['commit']['committer']['date'],message=raw['commit']['message'])
            elif mode=='tree_lookup':
                paths=scope['values']['paths'];assert not raw['truncated'] and set(paths)<={x['path'] for x in raw['tree']}
                value=dict(sha=raw['sha'],truncated=raw['truncated'],paths=paths)
            else:raise AssertionError(mode)
            assert value==scope['values'];continue
        assert digest(text)==scope['selected_sha256']
    assert read(DEST/'morphlux-commit.json')['sha']==proof['author_commit']
    for row in rows:
        if 'raw.githubusercontent.com/morphlux/morphlux/' in row['url']:
            assert '/'+proof['author_commit']+'/' in row['url']
    paper=read(ROOT/'references/proceedings/ASPLOS/2026/morphlux-reading.json')
    pdf=ROOT/paper['pdf_file'];assert sha(pdf)==paper['pdf_sha256']
    assert sha(ROOT/paper['archive_text_file'])==paper['archive_text_sha256']
    pages=subprocess.check_output(['pdftotext','-raw',str(pdf),'-'],text=True).split('\f')
    assert sum(bool(p.strip()) for p in pages)==paper['physical_pdf_pages']==16
    assert [p['physical_page'] for p in paper['selected_text_pages']]==list(range(2,12))+[14,15,16]
    for page in paper['selected_text_pages']:assert digest(pages[page['physical_page']-1])==page['sha256']
    assert [p['physical_page'] for p in paper['viewed_pages']]==[5,9,10,15,16]
    for page in paper['viewed_pages']:assert page['actually_viewed'] and sha(ROOT/page['file'])==page['sha256']
    for obj in (paper,proof):assert not obj['downloaded_code_executed'] and not obj['hardware_experiments_run']
    return dict(status='passed',verified_at=datetime.now(timezone.utc).isoformat(),paper_text_pages=13,viewed_paper_images=5,
                source_responses=18,successful_responses=17,http_errors=1,declared_source_scopes=21,arithmetic=arithmetic(),
                scope='Source integrity, selected body/implementation scopes and independent arithmetic; no full-publication or physical-system validation.')


if __name__=='__main__':
    result=verify()
    for name,data in [('torus-allocation-audit.json',result),('torus-allocation-arithmetic.json',result['arithmetic'])]:
        (Path(__file__).parent/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(result,ensure_ascii=False,indent=2))
