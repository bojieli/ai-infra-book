#!/usr/bin/env python3
"""Check this survey's actual artifacts, numeric inputs and outline-only integration."""
from pathlib import Path
from datetime import datetime, timezone
from urllib.parse import unquote, urlsplit
import collections
import csv
import hashlib
import json
import math
import re
from bs4 import BeautifulSoup
from PIL import Image

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
ARCHIVE=ROOT/'references/token-cost/2026-09-07'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    sources=json.loads((ARCHIVE/'manifest.json').read_text())
    plan=json.loads((HERE/'source-plan.json').read_text())
    notes=json.loads((HERE/'reading-notes.json').read_text())
    ids=[x['id'] for x in sources]
    assert len(ids)==len(set(ids))==67
    assert set(ids)=={x['id'] for x in plan}=={x['id'] for x in notes}
    assert json.loads((ARCHIVE/'download-errors.json').read_text())==[]
    for x in sources:
        original=ROOT/x['file'];text=ROOT/x['text_file']
        assert original.stat().st_size==x['bytes'],original
        assert sha(original)==x['sha256'],original
        assert sha(text)==x['text_sha256'] and len(text.read_text().strip())>100,text
        if original.suffix=='.pdf':
            assert original.read_bytes().startswith(b'%PDF-') and x['pages']>0,original
    with (ARCHIVE/'sources.tsv').open() as f:
        assert [x['id'] for x in csv.DictReader(f,delimiter='\t')]==ids
    figures=json.loads((ARCHIVE/'figures.json').read_text())
    assert len(figures)==18 and len({x['file'] for x in figures})==18
    for x in figures:
        p=ROOT/x['file'];assert sha(p)==x['sha256'] and p.stat().st_size==x['bytes'],p
        with Image.open(p) as im:im.verify()
    with Image.open(HERE/'figures/price-frontiers.png') as im:im.verify()
    report=(HERE/'report.md').read_text()
    definitions=dict(re.findall(r'^\[([^\]]+)\]: (\S+)',report,re.M))
    references=re.findall(r'\[[^\]\n]+\]\[([^\]\n]+)\]',report)
    assert set(references)<=set(definitions)<=set(ids)
    for x in sources:
        assert definitions[x['id']]==x['url']

    link_count=0
    docs=[HERE/'report.md',HERE/'README.md',HERE/'outline-placement.md',ARCHIVE/'README.md']
    for p in docs:
        # The verification artifact is produced at the end of this same check.
        for target in re.findall(r'\[[^\]\n]+\]\(([^)]+)\)',p.read_text()):
            if urlsplit(target).scheme:continue
            path,_,fragment=target.partition('#')
            resolved=(p.parent/unquote(path)).resolve() if path else p
            if resolved==HERE/'verification.json':continue
            assert resolved.exists(),(p,target)
            if fragment:
                assert re.search(rf'<a id="{re.escape(fragment)}"',resolved.read_text()),(p,target)
            link_count+=1

    integration=json.loads((HERE/'integration.json').read_text())
    html=BeautifulSoup((ROOT/'skeleton.html').read_text(),'html.parser')
    assert len(integration['placeholders'])==18
    for rel,before in integration['outline_before_sha256'].items():
        s=(ROOT/rel).read_text()
        for x in integration['placeholders']:
            if x['outline']==rel:
                assert s.count(x['text'])==1,x['id']
                s=s.replace(x['text']+'\n\n','',1)
        observed=hashlib.sha256(s.encode()).hexdigest()
        if observed!=before:
            # This is a shared, actively edited workspace. Known drift is recorded
            # explicitly, never reported as original-content equality.
            drift=integration.get('concurrent_workspace_changes',{}).get(rel)
            assert drift and observed==drift['current_without_placeholders_sha256'],('unreviewed non-placeholder change',rel)
            assert all((ROOT/p).exists() for p in drift['corroborating_workspace_evidence'])
    for x in integration['placeholders']:
        sub=html.find(id='sec-'+x['section'].replace('.','-'))
        assert sub and x['id'] in sub.get_text(),x['id']
        assert sub.find('a',href='research/token-cost-2023-2026/report.md#'+x['anchor']),x['id']
        assert f'<a id="{x["anchor"]}">' in report
    outlines=list((ROOT/'outlines').glob('[0-9]*.md'))
    s='\n'.join(p.read_text() for p in outlines)
    counts=dict(chapters=len(outlines),sections=len(re.findall(r'^## \d+\.\d+ ',s,re.M)),
                subsections=len(re.findall(r'^### \d+\.\d+\.\d+ ',s,re.M)),
                experiments=len(re.findall(r'^> \*\*实验 ',s,re.M)),
                figures=len(re.findall(r'^> \*\*图 ',s,re.M)))
    assert counts==dict(chapters=13,sections=70,subsections=239,experiments=117,figures=105),counts
    assert s.count('**占位 TC-')==18

    with (HERE/'data/epoch-frontiers.csv').open() as f:rows=list(csv.DictReader(f))
    table=next(t for t in BeautifulSoup((ARCHIVE/'epoch-prices.html').read_text(),'html.parser').find_all('table') if 'Benchmark score' in t.get_text())
    original=[[c.get_text(' ',strip=True) for c in r.find_all('td')] for r in table.find_all('tr') if r.find_all('td')]
    assert len(rows)==len(original)==119
    assert [list(r.values()) for r in rows]==original
    calc=json.loads((HERE/'calculations.json').read_text())
    for x,expected in zip(calc['historical_endpoints'],[20/.07,2/.07,37.5/.18,37.5/.12,37.5/.10]):
        assert math.isclose(x['endpoint_ratio'],expected)
        assert x['start'] in rows and x['end'] in rows
    assert calc['kv_example_gib']==dict(mha=4,gqa=1)
    assert math.isclose(calc['weight_read_lower_bound_ratio'],25.07462686567164)
    assert math.isclose(calc['gemini_launch_blend']['later_over_earlier'],1.511111111111111)
    assert math.isclose(calc['successful_task_cost_hypothetical_ratio'],1.25)
    assert calc['lifecycle_hypothetical_break_even_requests']==500_000_000
    assert math.isclose(calc['speculation_hypothetical'][0]['expected_tokens'],3.3616)
    assert calc['speculation_hypothetical'][1]['speedup']<1
    for number,date in [(6883,'2024-08-03'),(7000,'2024-08-19')]:
        pr=json.loads((ARCHIVE/f'vllm-pr{number}.json').read_text())
        assert pr['merged_at'].startswith(date) and re.fullmatch('[0-9a-f]{40}',pr['merge_commit_sha'])
    result=dict(checked_at=datetime.now(timezone.utc).isoformat(),status='passed',sources=len(sources),
                new_sources=sum(x['acquisition']=='new-download' for x in sources),
                reused_sources=sum(x['acquisition']=='existing-original' for x in sources),
                pdfs=sum(x['file'].endswith('.pdf') for x in sources),original_figures=len(figures),
                historical_rows=len(rows),historical_series=5,report_source_citations=len(set(references)),
                local_links_checked=link_count,placeholders=18,outline_chapters_with_placeholders=9,
                outline_changes='This survey inserts the 18 recorded placeholder paragraphs. Original-content hash equality holds for 7 chapters; separately recorded concurrent changes in chapters 10 and 12 are preserved.',
                concurrent_workspace_changes=integration.get('concurrent_workspace_changes',{}),
                outline_counts=counts,html_sync='All 18 placeholders found in their intended subsection with correct report anchor.',
                numeric_checks='Historical source rows, five endpoint ratios, hardware/KV/speculation/task/lifecycle arithmetic, PR merge dates.',
                limits='Not a GPU reproduction, full-page reading certification, or proof of a universal 1000x cost decline.')
    (HERE/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=='__main__':
    main()
