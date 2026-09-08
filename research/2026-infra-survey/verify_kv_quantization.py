"""Check archived reading ranges and independently recalculate format budgets."""
from pathlib import Path
from bs4 import BeautifulSoup
import hashlib
import json
import math
import re

ROOT = Path(__file__).resolve().parents[2]
DEST = ROOT / 'references/framework-history/2026-09-08/kv-quantization'


def verify():
    sources = json.loads((DEST / 'sources.json').read_text())
    by = {s['id']: s for s in sources}
    assert len(by) == len(sources) == 30
    for s in sources:
        data = (ROOT / s['file']).read_bytes()
        assert len(data) == s['bytes'] and hashlib.sha256(data).hexdigest() == s['sha256']
    proof = json.loads((DEST / 'reading-proof.json').read_text())
    assert len(proof['sources']) == 14 and not proof['downloaded_code_executed']
    for p in proof['sources']:
        source = by[p['source_id']]
        assert p['source_sha256'] == source['sha256']
        original = (ROOT / source['file']).read_text()
        if p['kind'] == 'lines':
            lines = original.splitlines(keepends=True)
            assert all(0 < a <= b <= len(lines) for a, b in p['ranges'])
            expected = ''.join(''.join(lines[a-1:b]) for a, b in p['ranges'])
        elif p['kind'] == 'html_main_chars':
            soup = BeautifulSoup(original, 'html.parser')
            main = (soup.select_one('main') or soup).get_text('\n', strip=True) + '\n'
            assert main.encode() == (ROOT / source['derived_text']['file']).read_bytes()
            a, b = p['range']
            expected = main[a:b]
        else:
            assert p['kind'] == 'json_body_chars'
            body = json.loads(original)['body']
            expected = ''.join(body[a:b] for a, b in p['ranges'])
        data = (ROOT / p['selected']['file']).read_bytes()
        assert data == expected.encode() and len(data) == p['selected']['bytes']
        assert hashlib.sha256(data).hexdigest() == p['selected']['sha256']

    a = json.loads((ROOT / 'research/2026-infra-survey/arithmetic.json').read_text())['kv_format_teaching']
    cfg = json.loads((ROOT / a['config']).read_text())
    layers, heads, dim = cfg['num_hidden_layers'], cfg['num_key_value_heads'], cfg['head_dim']
    # Count each K/V vector row and complete format blocks, independently of total-bit algebra.
    rows = 2 * layers * heads * a['context'] * a['requests']
    assert dim % 32 == 0 and rows * dim == a['values']
    ggml = (DEST / 'ollama-096-blocks.txt').read_text()
    assert re.search(r'#define QK4_0 32\s+typedef struct\s*\{\s*ggml_half d;', ggml)
    assert re.search(r'#define QK8_0 32\s+typedef struct\s*\{\s*ggml_half d;', ggml)
    assert a['bf16_mib'] == rows * dim * 2 / 2**20 == 1152
    assert a['fp8_payload_mib'] == rows * dim / 2**20 == 576
    assert a['q8_0_mib'] == rows * (dim // 32) * (32 + 2) / 2**20 == 612
    assert a['q4_0_mib'] == rows * (dim // 32) * (16 + 2) / 2**20 == 324
    assert a['block16_fp4_mib'] == rows * (dim // 16) * (8 + 1) / 2**20 == 324
    assert a['static_per_head_kv_fp32_scales_bytes'] == 2 * layers * heads * 4 == 2304
    assert a['nvfp4_global_kv_scales_bytes'] == 2 * layers * 4 == 288
    assert a['shared_per_layer_fp8_workspace_mib'] == rows // layers * dim / 2**20 == 16
    assert math.isclose(a['oaken_ideal_density_bits'], 4 + 8 * .1)
    assert math.isclose(a['oaken_ideal_density_mib'], a['bf16_mib'] * 4.8 / 16)
    fit = a['blog_rounded_fit']
    cross = fit['crossover_tokens']
    # At the claimed intersection both historical fitted lines agree.
    assert math.isclose(fit['bf16_intercept_ms'] + cross * fit['bf16_slope_ms_per_token'],
                        fit['fp8_intercept_ms'] + cross * fit['fp8_slope_ms_per_token'])
    return dict(source_responses=30, failed_responses=4, selected_text_records=14,
                arithmetic='passed', scope='Source text integrity and independent teaching arithmetic; no model execution.')


if __name__ == '__main__':
    print(json.dumps(verify(), ensure_ascii=False, indent=2))
