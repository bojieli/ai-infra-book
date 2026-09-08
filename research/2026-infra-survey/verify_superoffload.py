#!/usr/bin/env python3
"""Check selected primary evidence and the teaching comparison without running upstream code."""
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import math
import re
import subprocess
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[2]
VENUE = ROOT / 'references/proceedings/ASPLOS/2026'
FRAME = ROOT / 'references/framework-history/2026-09-08/training-superchip'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify():
    record = json.loads((VENUE / 'superoffload-reading.json').read_text())
    assert record['physical_pages'] == list(range(3, 13)) + [16]
    assert sha(ROOT / record['pdf_file']) == record['pdf_sha256']
    assert [p['page'] for p in record['page_texts']] == record['physical_pages']
    joined = ''
    for page in record['page_texts']:
        path = ROOT / page['file']
        fresh = subprocess.check_output(['pdftotext', '-layout', '-f', str(page['page']),
                  '-l', str(page['page']), str(ROOT / record['pdf_file']), '-'], text=True)
        assert fresh == path.read_text() and sha(path) == page['sha256']
        joined += fresh
    assert joined == (ROOT / record['text_file']).read_text()
    assert sha(ROOT / record['text_file']) == record['text_sha256']
    for page in record['viewed_pages']:
        assert page['actually_viewed'] and page['physical_page'] in record['physical_pages']
        assert sha(ROOT / page['file']) == page['sha256']
    assert not record['downloaded_code_executed'] and not record['hardware_experiments_run']

    sources = json.loads((FRAME / 'sources.json').read_text())
    scopes = json.loads((FRAME / 'readings.json').read_text())
    assert len(sources) == 7 and len(scopes['sources']) == 5
    for source in sources:
        path = ROOT / source['file']
        assert sha(path) == source['sha256'] and path.stat().st_size == source['bytes']
        assert source['status_code'] == 200 and source['read_scope']
        if source['id'] in ('deepspeed-v0180-commit', 'examples-head'):
            continue
        if 'raw.githubusercontent.com' in source['url']:
            commit = 'deepspeed-v0180-commit' if source['id'] == 'superoffload-config-v0180' else 'examples-head'
            assert '/' + json.loads((FRAME / (commit + '.json')).read_text())['sha'] + '/' in source['url']
    for scope in scopes['sources']:
        path = ROOT / scope['file']
        assert sha(path) == scope['file_sha256']
        text = path.read_text()
        if scope['kind'] == 'html_article':
            text = BeautifulSoup(text, 'html.parser').select_one(scope['selector']).get_text('\n', strip=True) + '\n'
        else:
            assert len(text.splitlines()) == scope['line_count']
        assert text == (ROOT / scope['text_file']).read_text()
        assert sha(ROOT / scope['text_file']) == scope['text_sha256']
    assert not scopes['downloaded_code_executed'] and not scopes['hardware_experiments_run']
    script = (FRAME / 'finetune_qwen3-14b_1gpu.sh').read_text()
    # Parse only the two literal JSON templates. Never execute the downloaded shell.
    templates = re.findall(r'<< EOF\n(.*?)\nEOF', script, re.S)
    configs = [json.loads(t.replace('$BATCH_SIZE', '4')) for t in templates]
    assert len(configs) == 2 and all(c['zero_optimization']['stage'] == 3 for c in configs)
    a, b = [c['zero_optimization']['offload_optimizer'] for c in configs]
    assert a['ratio'] == 0.90 and 'ratio' not in b
    assert a['pin_memory'] and b['pin_memory'] and '--bind_cores_to_rank' not in script
    config_text = (FRAME / 'offload-config-v0180.py').read_text()
    assert 'ratio: float = Field(1.0,' in config_text and 'super_offload: bool = False' in config_text
    assert 'deepspeed>=0.17.0' in (FRAME / 'requirements.txt').read_text()

    result = json.loads(Path(__file__).with_name('superoffload-arithmetic.json').read_text())
    q = json.loads((ROOT / result['config_file']).read_text())
    assert sha(ROOT / result['config_file']) == result['config_sha256']
    n = q['hidden_size'] * q['intermediate_size']
    assert n == 50331648 and result['matrix'] == [12288, 4096]
    assert result['low_bytes'] == 96*2**20 and result['high_bytes'] == 192*2**20
    assert result['cast_read_write_bytes'] == 288*2**20
    # A conversion reads one low-precision tensor and writes one high-precision tensor.
    cpu_s = (96+192)*2**20 / result['effective_cpu_cast_Bps']
    gpu_s = (96+192)*2**20 / result['effective_gpu_cast_Bps']
    for row in result['cases']:
        link = row['effective_link_Bps']
        expected_cpu = cpu_s + 96*2**20/link
        expected_gpu = gpu_s + 192*2**20/link
        assert math.isclose(row['cpu_cast_path_ms'], expected_cpu*1000)
        assert math.isclose(row['gpu_cast_path_ms'], expected_gpu*1000)
        assert (row['faster'] == 'cpu_cast') == (expected_cpu < expected_gpu)
    crossing = result['link_crossover_Bps']
    assert math.isclose(cpu_s+96*2**20/crossing, gpu_s+192*2**20/crossing)
    assert result['cases'][0]['faster'] != result['cases'][1]['faster']
    # The common GPU input is excluded; host and GPU staging cannot be pooled.
    cap = result['incremental_capacity']
    assert cap == dict(cpu_cast_host_bytes=288*2**20, gpu_cast_host_bytes=192*2**20,
                       cpu_cast_gpu_bytes=0, gpu_cast_gpu_bytes=192*2**20)
    assert cap['gpu_cast_gpu_bytes'] > 64*2**20
    outline = (ROOT / 'outlines/10-训练系统.md').read_text()
    assert record['adoption']['subsections'] == ['10.1.2']
    assert 'case-studies/training-offload-and-casting.md' in outline
    return dict(status='passed', verified_at=datetime.now(timezone.utc).isoformat(),
                selected_physical_pages=len(record['physical_pages']), viewed_pages=len(record['viewed_pages']),
                framework_responses=len(sources), framework_content_scopes=len(scopes['sources']),
                arithmetic='passed', upstream_code_executed=False, hardware_experiments_run=False)


if __name__ == '__main__':
    report = verify()
    Path(__file__).with_name('superoffload-audit.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2))
