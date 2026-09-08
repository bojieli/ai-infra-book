#!/usr/bin/env python3
"""Check selected sources and independent format/rounding arithmetic; no models."""
from collections import Counter
from datetime import datetime, timezone
from fractions import Fraction as F
from pathlib import Path
import hashlib
import json
import math
import subprocess
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[2]
DEST = ROOT / 'references/framework-history/2026-09-09/metadata-quantization'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def digest(text):
    return hashlib.sha256(text.encode()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def arithmetic():
    config = read(ROOT / 'references/outline-checks/2026-09-07/scaling-history/qwen3-8b-config.json')
    h, intermediate = config['hidden_size'], config['intermediate_size']
    assert (h, intermediate) == (4096, 12288)
    values = h * intermediate
    # Independently enumerate complete blocks in each output row.
    groups = sum(h // 32 for _ in range(intermediate))
    assert groups * 32 == values
    bf16, mx, metadata = values * 2, groups * 17, groups * 18
    nv = (values // 16) * 9 + 4  # one explicitly assumed FP32 tensor scale
    assert (bf16, mx, metadata) == (96*2**20, F(51, 2)*2**20, 27*2**20)
    assert nv == metadata + 4
    assert F(metadata-mx, mx) == F(1, 17)
    weight_candidates = (values // 8) * 3 * 4 * 8
    assert weight_candidates == 603979776
    activation = [dict(token_rows=t,values=t*h,candidate_value_pairs=t*h*12) for t in (1,1024)]
    assert activation[1]['candidate_value_pairs'] == 50331648
    fp4 = [F(x) for x in (0, F(1,2), 1, F(3,2), 2, 3, 4, 6)]
    fp6 = [F(j,8) for j in range(8)] + [F(2**e)*(1+F(j,8)) for e in range(3) for j in range(8)]
    x = [F(41,10), F(24,5)] + [F(0)]*6
    def nearest(value, grid):
        return min(enumerate(grid), key=lambda pair:(abs(value-pair[1]), pair[0]%2))[1]
    base = [nearest(v,fp4) for v in x]
    assert base[:2] == [4,4]
    low, high, mismatch = list(base), list(base), list(base)
    low[0], high[1], mismatch[0] = nearest(x[0],fp6), nearest(x[1],fp6), nearest(x[1],fp6)
    def sse(y):return sum((a-b)**2 for a,b in zip(x,y))
    assert (sse(base),sse(low),sse(high),sse(mismatch)) == (F(13,20),F(13,20),F(1,20),F(29,20))
    # An elementary counterexample to the formulas as printed, not an OCP test.
    amax = 7
    printed_rtne = math.floor(math.log2(round(amax)/4))
    printed_ceil = math.ceil(math.log2(amax/6))
    assert (printed_rtne,printed_ceil) == (0,1)
    return dict(scope='Independent format payload, lifetime and exact rational examples; not model quality, framework execution or hardware speed measurements.',
        model='Qwen3-8B',weight_shape=[intermediate,h],weight_values=values,groups_32=groups,
        weight_bytes=dict(bf16=bf16,mxfp4=mx,m2xfp=metadata,nvfp4_with_one_fp32_scale=nv),
        extra_metadata_percent=float(F(100,17)),candidate_value_pairs=dict(weight_offline=weight_candidates,activation_online=activation),
        lifetime_bytes=dict(pseudo_bf16_weight=bf16,packed_plus_full_bf16_copy=metadata+bf16),
        tie_example=dict(inputs=[str(v) for v in x],fp4=[str(v) for v in base],
            squared_error_sum=dict(baseline=str(sse(base)),refine_lowest=str(sse(low)),refine_other_tied_position=str(sse(high)),encoder_decoder_position_mismatch=str(sse(mismatch))),
            scope='Hypothetical index choices only; does not execute or predict torch.topk.'),
        printed_scale_counterexample=dict(amax=7,printed_rtne_exponent=printed_rtne,printed_ceil_exponent=printed_ceil))


def verify():
    proof = read(DEST/'reading.json'); rows = read(ROOT/proof['sources_file'])
    assert len(rows) == len({r['id'] for r in rows}) == 19
    assert Counter(r['status_code'] for r in rows) == {200:19}
    for row in rows:
        path=ROOT/row['file']
        assert sha(path)==row['sha256'] and path.stat().st_size==row['bytes']
        assert row['reading_status']=='declared_scopes_read'
    assert len(proof['scopes'])==23 and len(proof['reused_scopes'])==1
    assert {s['source_id'] for s in proof['scopes']}=={r['id'] for r in rows}
    for scope in proof['scopes']+proof['reused_scopes']:
        path=ROOT/scope['file']; assert sha(path)==scope['sha256']
        mode=scope['mode']
        if mode=='full_text':continue
        if mode=='lines':
            text=''.join(path.read_text().splitlines(keepends=True)[scope['first_line']-1:scope['last_line']])
        elif mode=='html_selector':
            nodes=BeautifulSoup(path.read_text(),'html.parser').select(scope['selector']); assert len(nodes)==1
            text=nodes[0].get_text(' ',strip=True)+'\n'; assert text==scope['selected_text']
        elif mode=='heading_siblings':
            h=BeautifulSoup(path.read_text(),'html.parser').find(id=scope['heading_id']); out=[h.get_text(' ',strip=True)]
            for node in h.next_siblings:
                if getattr(node,'name',None) in scope['stop_headings']:break
                if getattr(node,'name',None):out.append(node.get_text(' ',strip=True))
            text='\n'.join(out)+'\n'; assert text==scope['selected_text']
        elif mode=='json_ld_fields':
            soup=BeautifulSoup(path.read_text(),'html.parser')
            raw=next(d for n in soup.find_all('script',type='application/ld+json') if (d:=json.loads(n.string or n.get_text())).get('@type')==scope['schema_type'])
            assert {k:raw[k] for k in scope['fields']}==scope['values'];continue
        else:
            raw=read(path)
            if mode=='json_fields':assert {k:raw[k] for k in scope['fields']}==scope['values']
            elif mode=='commit_identity':assert dict(sha=raw['sha'],date=raw['commit']['committer']['date'],message=raw['commit']['message'])==scope['values']
            elif mode=='tree_paths':assert not raw['truncated'] and raw['sha']==scope['sha'] and [r['path'] for r in raw['tree']]==scope['paths']
            else:raise AssertionError(mode)
            continue
        assert digest(text)==scope['selected_sha256']
    paper=read(ROOT/'references/proceedings/ASPLOS/2026/m2xfp-reading.json')
    pdf=ROOT/paper['pdf_file']; assert sha(pdf)==paper['pdf_sha256']
    assert sha(ROOT/paper['archive_text_file'])==paper['archive_text_sha256']
    pages=subprocess.check_output(['pdftotext','-raw',str(pdf),'-'],text=True).split('\f')
    assert sum(bool(p.strip()) for p in pages)==17
    assert [p['physical_page'] for p in paper['selected_text_pages']]==list(range(2,14))
    for page in paper['selected_text_pages']:assert digest(pages[page['physical_page']-1])==page['sha256']
    assert [p['physical_page'] for p in paper['viewed_pages']]==list(range(8,14))
    for page in paper['viewed_pages']:assert page['actually_viewed'] and sha(ROOT/page['file'])==page['sha256']
    for obj in (paper,proof):assert not obj['downloaded_code_executed'] and not obj['hardware_experiments_run']
    return dict(status='passed',verified_at=datetime.now(timezone.utc).isoformat(),paper_text_pages=12,viewed_paper_images=6,
        source_responses=19,successful_responses=19,declared_source_scopes=23,reused_scopes=1,arithmetic=arithmetic(),
        scope='Declared source integrity and independent arithmetic; not full publication, kernel integration, model-quality or hardware validation.')


if __name__=='__main__':
    result=verify()
    for name,data in [('metadata-quantization-audit.json',result),('metadata-quantization-arithmetic.json',result['arithmetic'])]:
        (Path(__file__).parent/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(result,ensure_ascii=False,indent=2))
