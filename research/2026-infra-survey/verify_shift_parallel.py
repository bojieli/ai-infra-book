#!/usr/bin/env python3
"""Check selected primary evidence and independent Qwen3 arithmetic invariants."""
from datetime import datetime, timezone
from fractions import Fraction as F
from pathlib import Path
import hashlib
import json
import math
import subprocess
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[2]
VENUE = ROOT/'references/proceedings/ASPLOS/2026'
FRAME = ROOT/'references/framework-history/2026-09-08/shift-parallelism'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify():
    r = json.loads((VENUE/'shift-reading.json').read_text())
    assert r['physical_pages'] == list(range(1,13))
    assert sha(ROOT/r['pdf_file']) == r['pdf_sha256']
    joined = ''
    for page in r['page_texts']:
        path = ROOT/page['file']; assert sha(path) == page['sha256']
        fresh = subprocess.check_output(['pdftotext','-layout','-f',str(page['page']),
            '-l',str(page['page']),str(ROOT/r['pdf_file']),'-'],text=True,stderr=subprocess.PIPE)
        assert fresh == path.read_text(); joined += fresh
    assert joined == (ROOT/r['text_file']).read_text()
    assert sha(ROOT/r['text_file']) == r['text_sha256']
    for page in r['viewed_pages']:
        assert page['actually_viewed'] and sha(ROOT/page['file']) == page['sha256']
    assert not r['downloaded_code_executed'] and not r['hardware_experiments_run']
    sources = json.loads((FRAME/'sources.json').read_text())
    scope = json.loads((FRAME/'readings.json').read_text())['sources']
    by_id = {s['id']:s for s in sources}
    assert len(by_id) == len(sources) == 22
    assert len(scope) == 21 and sum(s['status_code']!=200 for s in sources) == 1
    for s in sources:
        path = ROOT/s['file']; assert sha(path) == s['sha256'] and path.stat().st_size == s['bytes']
        assert s['read_scope'] and s['reading_status'] != 'downloaded_not_read'
    for s in scope:
        path = ROOT/s['file']; assert sha(path) == s['file_sha256']
        if 'line_ranges_inclusive' in s:
            lines = path.read_text().splitlines(keepends=True)
            t = ''.join(''.join(lines[a-1:b]) for a,b in s['line_ranges_inclusive'])
            assert t == (ROOT/s['text_file']).read_text()
            assert sha(ROOT/s['text_file']) == s['text_sha256']
        if s['kind']=='selected_html_block':
            soup = BeautifulSoup(path.read_text(),'html.parser')
            assert soup.select(s['selector'])[s['index']].get_text('\n',strip=True) == (ROOT/s['text_file']).read_text()
            assert soup.select_one(s['date_selector']).get_text(strip=True) == s['publication_date']
    tree = json.loads((FRAME/'tree.json').read_text())
    head = json.loads((FRAME/'head.json').read_text())['sha']
    assert tree['sha']==head and not tree['truncated']
    blobs = {x['path']:x['sha'] for x in tree['tree'] if x['type']=='blob'}
    for s in sources:
        marker = '/'+head+'/'
        if marker in s['url']:
            path = s['url'].split(marker,1)[1];data = (ROOT/s['file']).read_bytes()
            assert hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest() == blobs[path]
    releases = json.loads((FRAME/'releases.json').read_text())
    assert next(x for x in releases if x['tag_name']=='v0.0.7')['published_at']=='2025-05-29T23:36:55Z'
    assert 'shift_parallel_threshold: int = 512' in (FRAME/'v007-args.py').read_text()
    assert 'shift_parallel_threshold: int = 512' in (FRAME/'args.py').read_text()
    assert 'default threshold is 256' in (FRAME/'shift-guide.rst').read_text()
    assert 'VLLM_PATCH_VERSION = "0.26.0"' in (FRAME/'utils.py').read_text()
    assert 'raise RuntimeError(' in (FRAME/'plugin.py').read_text()

    a = json.loads((Path(__file__).parent/'shift-parallel-arithmetic.json').read_text())
    c = json.loads((ROOT/a['config_file']).read_text()); assert sha(ROOT/a['config_file']) == a['config_sha256']
    assert (c['hidden_size'],c['num_hidden_layers'],c['num_attention_heads'],c['num_key_value_heads'],c['head_dim'],c['intermediate_size']) == (4096,36,32,8,128,12288)
    cap = a['capacity'];mib = 2**20
    assert cap['layer_matrix_bytes'] == {'qkv':48*mib,'o':32*mib,'ffn':288*mib}
    assert cap['dual_weight_per_gpu_per_layer_bytes'] == 276*mib
    assert cap['extra_weight_per_gpu_all_layers_bytes'] == 3312*mib
    assert cap['kv_per_gpu_one_8192_token_sequence_bytes'] == 288*mib
    assert F(cap['extra_weight_per_gpu_all_layers_bytes'],cap['kv_per_gpu_one_8192_token_sequence_bytes']) == F(23,2)
    # Enumerate ownership by independently splitting each TP half across the two SP ranks.
    owner = {}
    for tp_rank in range(2):
        for sp_rank in range(2):
            physical = sp_rank*2+tp_rank
            owner[physical] = list(range(tp_rank*4+sp_rank*2,tp_rank*4+sp_rank*2+2))
    assert sorted(h for heads in owner.values() for h in heads) == list(range(8))
    assert sum(owner[p['rank']] != p['naive_sorted_tp_heads'] for p in a['kv_ownership']) == 2
    for p in a['kv_ownership']:
        assert owner[p['rank']] == p['base_kv_heads'] == p['shift_kv_heads']
    # A two-token batch: enumerate remote halves of the QKV and output buffers.
    qkv_remote = (16+2*4)*128*2//2
    out_remote = (2*8*128*2)//2
    assert qkv_remote==3072 and out_remote==2048
    assert a['communication']['mixed_qkv_alltoall']*2==qkv_remote
    assert a['communication']['mixed_output_alltoall']*2==out_remote
    assert a['communication']['mixed_total']==10752 and a['communication']['full_tp_two_allreduces']==24576
    # Separate oracle: local weight-bound floor, compute slope, then serialized communication.
    def estimate(n, mixed, whole):
        nn = n+(n%2) if mixed else n
        compute_us = F(nn*96468992,500*10**6)
        memory_us = F((184 if mixed else 92)*mib,2*10**6)
        comm_us = F(8 if mixed else 4)+F(nn*(10752 if mixed else 24576),100000)
        layer = max(compute_us,memory_us)+comm_us
        end = F(2)+F(4096*nn,100000) if mixed else F(0)
        return layer*36+end if whole else layer
    for row in a['rows']:
        n = row['n']
        for name,mixed in [('full_tp',False),('mixed',True)]:
            assert math.isclose(float(estimate(n,mixed,False)),row[name]['subchain_budget_us'],rel_tol=1e-12)
            assert math.isclose(float(estimate(n,mixed,True)),row[name]['all_layers_matrix_communication_budget_us'],rel_tol=1e-12)
    first_layer = next(n for n in range(1,8193) if estimate(n,True,False)<estimate(n,False,False))
    first_whole = next(n for n in range(1,8193) if estimate(n,True,True)<estimate(n,False,True))
    assert first_layer==a['first_mixed_win_scheduled_tokens']==304
    assert first_whole==a['first_all_layers_matrix_communication_win_scheduled_tokens']==305
    assert not a['hardware_experiments_run']
    return dict(verified_at=datetime.now(timezone.utc).isoformat(),status='passed',selected_pages=12,
        viewed_pages=4,framework_responses=22,declared_successful_source_scopes=21,
        calculation='passed: capacity, rank ownership, remote payloads and serial teaching budget',
        framework_or_hardware_executed=False,scope='Declared source scopes and teaching arithmetic; not a runtime validation.')


if __name__=='__main__':
    report=verify()
    (Path(__file__).parent/'shift-parallel-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(report,ensure_ascii=False,indent=2))
