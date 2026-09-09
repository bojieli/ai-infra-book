"""Validate the same-layout MoE teaching case, not a serving implementation."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'research/2026-infra-survey/parallel-moe-ownership'


def verify():
    raw = subprocess.check_output([sys.executable, str(BASE / 'check.py'), '--root', str(ROOT)])
    assert raw == (BASE / 'results.json').read_bytes()
    data = json.loads(raw)
    for meta in data['sources'].values():
        content = (ROOT / meta['file']).read_bytes()
        assert len(content) == meta['bytes']
        assert hashlib.sha256(content).hexdigest() == meta['sha256']
    snapshots = json.loads((BASE / 'inputs/provenance.json').read_text())
    for meta in snapshots['files']:
        content = (ROOT / meta['archived_file']).read_bytes()
        assert len(content) == meta['bytes']
        assert hashlib.sha256(content).hexdigest() == meta['sha256']
    # Independently sum the recorded directed edges across the declared cut.
    cuts = []
    for phase in data['phases']:
        edges = phase['collective_messages']
        assert len(edges) == 80
        forward = sum(e['bytes'] for e in edges if e['source'] < 4 <= e['destination'])
        backward = sum(e['bytes'] for e in edges if e['destination'] < 4 <= e['source'])
        assert forward == backward == phase['cross_server_each_direction_per_layer_bytes']
        assert forward + backward == phase['cross_server_send_per_layer_bytes']
        assert all(row['network_input_dispatch_send_bytes'] == 0 for row in phase['ranks'])
        cuts.append(forward + backward)
    assert cuts == [768 * 2**20, 96 * 2**10]
    assert data['weights']['per_rank_weight_bytes'] == 64821419008
    assert data['phases'][0]['ranks'][0]['end_kv_bytes'] == 788529152
    assert data['phases'][1]['ranks'][0]['end_kv_bytes'] == 788625408
    assert all(data['checks'].values())
    result = {
        'status': 'passed',
        'scope': 'One declared DP1/TP2/EP4 teaching layout; exact integer ownership and directed-edge accounting, not framework defaults, timing or floating-point equivalence.',
        'recomputed_output_byte_equal': True,
        'self_contained_archived_inputs': True,
        'cross_server_send_per_layer_bytes': cuts,
        'phases': 2,
        'recorded_messages_per_phase': 80,
        'downloaded_code_executed': False,
        'gpu_tests_run': False,
    }
    (BASE / 'validation.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    return result


if __name__ == '__main__':
    print(json.dumps(verify(), ensure_ascii=False))
