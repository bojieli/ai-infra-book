#!/usr/bin/env python3
"""Check fixed source identity and independent RoPE/resource arithmetic."""
from datetime import datetime, timezone
from fractions import Fraction as F
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'references/framework-history/2026-09-09/nonlinear-resources'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def calculate():
    cfg = json.loads((ROOT / 'references/outline-checks/2026-09-07/scaling-history/qwen3-8b-config.json').read_text())
    # Fixed-position rotation is linear in its input. Exact rational coefficients
    # avoid confusing this algebraic check with a floating-point quality test.
    c, s = F(3, 5), F(4, 5)
    def rotate(v):
        x, y = v
        return (c*x-s*y, s*x+c*y)
    x, y = (F(2), F(-3)), (F(5), F(7))
    a, b = F(2), F(-4)
    assert rotate(tuple(a*u+b*v for u, v in zip(x, y))) == tuple(
        a*u+b*v for u, v in zip(rotate(x), rotate(y)))
    assert sum(v*v for v in rotate(x)) == sum(v*v for v in x)

    q_heads, k_heads, dim = cfg['num_attention_heads'], cfg['num_key_value_heads'], cfg['head_dim']
    pairs = q_elements = k_elements = flops = 0
    # Enumerate independent coordinate pairs, not an invocation of framework code.
    for head_count, kind in [(q_heads, 'q'), (k_heads, 'k')]:
        for _ in range(head_count):
            for first in range(0, dim, 2):
                assert first+1 < dim
                pairs += 1
                flops += 4+2
                if kind == 'q':
                    q_elements += 2
                else:
                    k_elements += 2
    tokens, width = 1024, 2
    traffic_per_token = (q_elements+k_elements) * width * 2
    table = tokens * (dim//2) * 2 * width
    assert (pairs, q_elements, k_elements, flops) == (2560, 4096, 1024, 15360)
    assert traffic_per_token == 20*1024 and tokens*traffic_per_token == 20*2**20
    assert table == 256*1024
    assert cfg['hidden_size'] * width == 8*1024
    assert 2*cfg['intermediate_size'] * width == 48*1024
    return dict(q_heads=q_heads, k_heads=k_heads, head_dim=dim,
                rotation_pairs_per_token=pairs, rotation_flops_per_token=flops,
                main_tensor_bytes_per_token=traffic_per_token,
                tokens=tokens, main_tensor_mib=tokens*traffic_per_token/2**20,
                assumed_single_bf16_table_kib=table/1024,
                rmsnorm_input_row_kib=cfg['hidden_size']*width/1024,
                swiglu_input_row_kib=2*cfg['intermediate_size']*width/1024,
                fixed_position_linearity='checked with exact rational arithmetic',
                scope='One layer, full Q/K rotation, BF16; V not rotated. Main tensor interface lower bound excludes coefficient/index traffic, conversions and fusion. Table is one 1024-position teaching instance, not actual engine residency or measured HBM traffic.')


def verify():
    records = json.loads((SOURCE / 'sources.json').read_text())
    reading = json.loads((SOURCE / 'reading.json').read_text())
    assert len(records) == 1 and records[0]['status_code'] == 200
    assert len(reading['reused_inputs']) == 3 and len(reading['scopes']) == 4
    all_records = records+reading['reused_inputs']
    byid = {r['id']: r for r in all_records}
    assert len(byid) == len(all_records)
    for r in all_records:
        data = (ROOT / r['file']).read_bytes()
        assert len(data) == r['bytes'] and sha(data) == r['sha256']
        if 'git_blob' in r:
            obj = json.loads((ROOT / r['tree_file']).read_text())
            assert not obj['truncated'] and obj['sha'] == r['commit']
            entry = next(e for e in obj['tree'] if e['path'] == r['repo_path'])
            assert entry['sha'] == r['git_blob'] == hashlib.sha1(
                b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
    for scope in reading['scopes']:
        r = byid[scope['source_id']]
        assert (r['file'], r['sha256']) == (scope['file'], scope['sha256'])
        data = (ROOT / r['file']).read_bytes()
        if scope['mode'] == 'lines':
            lo, hi = scope['first_line'], scope['last_line']
            lines = data.splitlines(keepends=True)
            assert 1 <= lo <= hi <= len(lines)
            assert sha(b''.join(lines[lo-1:hi])) == scope['selected_sha256']
            continue
        obj = json.loads(data)
        if scope['mode'] == 'tree_entries':
            assert not obj['truncated'] and obj['sha'] == scope['commit']
            assert all(e in obj['tree'] for e in scope['entries'])
        elif scope['mode'] == 'commit_identity':
            assert scope['values'] == dict(sha=obj['sha'], date=obj['commit']['committer']['date'])
        elif scope['mode'] == 'json_fields':
            assert all(obj[k] == v for k, v in scope['values'].items())
        else:
            raise AssertionError(scope['mode'])
    report = dict(verified_at=datetime.now(timezone.utc).isoformat(), status='passed',
                  framework_responses=1, reused_inputs=3, read_scopes=4,
                  arithmetic=calculate(), downloaded_code_executed=False,
                  hardware_experiments_run=False,
                  scope='Declared source identity/ranges and independent arithmetic. PICACHU pages/figures and new abstracts are checked by the public-paper verifier; no full framework integration claim.')
    (ROOT / 'research/2026-infra-survey/nonlinear-resources-audit.json').write_text(
        json.dumps(report, ensure_ascii=False, indent=2)+'\n')
    return report


if __name__ == '__main__':
    print(json.dumps(verify(), ensure_ascii=False))
