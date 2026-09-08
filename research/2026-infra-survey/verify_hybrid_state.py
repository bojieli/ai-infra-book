"""Check selected source spans and independent K3 state/frontier arithmetic."""
from pathlib import Path
from bs4 import BeautifulSoup
import hashlib
import json

ROOT = Path(__file__).resolve().parents[2]
DEST = ROOT / 'references/framework-history/2026-09-08/hybrid-state'


def verify():
    sources = json.loads((DEST / 'sources.json').read_text())
    by = {s['id']: s for s in sources}
    assert len(by) == len(sources) == 18
    proof = json.loads((DEST / 'reading-proof.json').read_text())
    for r in proof['reused_sources']:
        s = next(s for s in json.loads((ROOT / r['manifest']).read_text())
                 if s['id'] == r['source_id'])
        assert s['sha256'] == r['source_sha256']
        by[s['id']] = s
    for s in by.values():
        data = (ROOT / s['file']).read_bytes()
        assert len(data) == s['bytes']
        assert hashlib.sha256(data).hexdigest() == s['sha256']
    assert len(proof['sources']) == 21 and not proof['downloaded_code_executed']
    for p in proof['sources']:
        s = by[p['source_id']]
        assert p['source_sha256'] == s['sha256']
        raw = (ROOT / s['file']).read_text()
        if p['kind'] == 'lines':
            rows = raw.splitlines(keepends=True)
            assert all(0 < a <= b <= len(rows) for a, b in p['ranges'])
            expected = ''.join(''.join(rows[a-1:b]) for a, b in p['ranges'])
        elif p['kind'] == 'html_chars':
            body = BeautifulSoup(raw, 'html.parser').select_one(p['selector']).get_text('\n', strip=True)
            assert all(0 <= a < b <= len(body) for a, b in p['ranges'])
            expected = ''.join(body[a:b] for a, b in p['ranges'])
        elif p['kind'] == 'json_fields':
            j = json.loads(raw)
            if 'json_parent' in p:
                j = j[p['json_parent']]
            expected = json.dumps({k: j[k] for k in p['fields']}, ensure_ascii=False, indent=2) + '\n'
        else:
            assert p['kind'] == 'reused_text'
            data = (ROOT / p['text']['file']).read_bytes()
            assert len(data) == p['text']['bytes']
            assert hashlib.sha256(data).hexdigest() == p['text']['sha256']
            # The saved earlier extraction is the actual article text, not navigation.
            soup = BeautifulSoup(raw, 'html.parser')
            assert soup.select_one('article').get_text('\n', strip=True).strip() == data.decode().strip()
            expected = data.decode()
        data = (ROOT / p['selected']['file']).read_bytes()
        assert data == expected.encode() and len(data) == p['selected']['bytes']
        assert hashlib.sha256(data).hexdigest() == p['selected']['sha256']

    a = json.loads((ROOT / 'research/2026-infra-survey/arithmetic.json').read_text())['hybrid_state_teaching']
    cfg = json.loads((ROOT / a['config']).read_text())['text_config']
    lc = cfg['linear_attn_config']
    linear, full = set(lc['kda_layers']), set(lc['full_attn_layers'])
    assert linear.isdisjoint(full) and linear | full == set(range(1, cfg['num_hidden_layers']+1))
    assert len(linear) == 69 and len(full) == 24
    assert lc['num_heads'] % a['attention_tp'] == 0
    # Enumerate each layer/head payload, separately from the closed-form saved calculation.
    rank_heads = lc['num_heads'] // a['attention_tp']
    matrix_rank = sum(lc['head_dim']**2 * a['recurrent_bytes']
                      for layer in linear for head in range(rank_heads))
    conv_rank = sum((lc['short_conv_kernel_size']-1)*lc['head_dim']*a['conv_bytes']
                    for layer in linear for head in range(rank_heads) for qkv in range(3))
    assert matrix_rank*a['attention_tp'] == a['logical_matrix_bytes'] == 434110464
    assert conv_rank*a['attention_tp'] == a['logical_conv_bytes'] == 15261696
    checkpoint = matrix_rank + conv_rank
    assert checkpoint == a['checkpoint_bytes_per_rank'] == 56171520
    assert checkpoint*a['attention_tp'] == a['logical_checkpoint_bytes'] == 449372160
    mla_token = sum((cfg['kv_lora_rank']+cfg['qk_rope_head_dim'])*a['mla_bytes'] for layer in full)
    assert mla_token == a['mla_bytes_per_token_per_rank'] == 27648
    assert mla_token*a['context'] == a['mla_history_bytes_per_rank'] == 226492416
    assert mla_token*a['context']*a['attention_tp'] == a['mla_history_bytes_deployment']
    for row in a['retention']:
        materialized = list(range(row['interval_tokens'], a['context']+1, row['interval_tokens']))
        assert len(materialized) == row['checkpoints']
        assert sum(checkpoint for _ in materialized) == row['bytes_per_rank']
    f = a['frontier']
    full_available = set(range(0, f['matched_tokens']+1, f['hash_tokens']))
    recurrent = set(f['retained_boundaries']) | {0}
    restored = max(full_available & recurrent)
    assert restored == f['restored_tokens']
    assert f['matched_tokens']-restored == f['recomputed_tokens'] == 2560
    assert f['matched_tokens'] % f['physical_block_tokens'] != 0
    # Finer identity alone changes neither the materialized state nor the restore point.
    assert max(set(range(f['matched_tokens']+1)) & recurrent) == restored
    assert max(full_available & (recurrent | {f['matched_tokens']})) == f['restored_after_materializing']
    dates = a['pr_merge_dates']
    for n, date in dates.items():
        j = json.loads((DEST / f'vllm-pr-{n}.json').read_text())
        assert j['merged_at'][:10] == date
    return dict(source_responses=18, reused_sources=3, selected_text_records=21,
                arithmetic='passed', scope='Selected source integrity, K3 payload and common-boundary teaching arithmetic; no model execution.')


if __name__ == '__main__':
    print(json.dumps(verify(), ensure_ascii=False, indent=2))
