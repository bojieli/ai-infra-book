#!/usr/bin/env python3
"""Verify selected RLBoost sources and teaching budgets, without importing them."""
from datetime import datetime, timezone
from fractions import Fraction as F
from itertools import product
from pathlib import Path
import json

from bs4 import BeautifulSoup
from verify_reward_scheduling import digest, field, read

ROOT = Path(__file__).resolve().parents[2]
DIRECTORY = ROOT / 'references/framework-history/2026-09-09/rlboost-recovery'


def sources():
    manifest = read(DIRECTORY / 'sources.json')
    proof = read(DIRECTORY / 'reading.json')
    assert len(manifest) == proof['responses'] == 21
    by_id = {item['id']: item for item in manifest}
    assert len(by_id) == 21 and len(proof['scopes']) == 18
    for item in manifest:
        raw = (ROOT / item['file']).read_bytes()
        assert item['status_code'] == 200
        assert len(raw) == item['bytes'] and digest(raw) == item['sha256']
    for scope in proof['scopes']:
        assert scope['file'] == by_id[scope['id']]['file']
        raw = (ROOT / scope['file']).read_bytes()
        assert digest(raw) == scope['sha256'] == by_id[scope['id']]['sha256']
        kind = scope['kind']
        if kind == 'line_ranges':
            lines = raw.decode().splitlines(keepends=True)
            for span in scope['ranges']:
                assert 1 <= span['start'] <= span['end'] <= len(lines)
                assert digest(''.join(lines[span['start'] - 1:span['end']]).encode()) == span['sha256']
        elif kind == 'json_fields':
            data = json.loads(raw)
            assert all(field(data, key) == value for key, value in scope['values'].items())
            if 'gitlinks' in scope:
                assert [entry for entry in data['tree'] if entry['type'] == 'commit'] == scope['gitlinks']
        elif kind == 'html_selectors':
            soup = BeautifulSoup(raw, 'html.parser')
            for selection in scope['selectors']:
                node = soup.select_one(selection['selector'])
                assert digest(node.get_text(' ', strip=True).encode()) == selection['text_sha256']
        else:
            assert kind == 'full_file'
    selected = {item['file'] for item in proof['scopes']}
    assert set(proof['downloaded_not_read']) == {item['file'] for item in manifest} - selected
    for item in proof['reused_sources']:
        assert digest((ROOT / item['file']).read_bytes()) == item['sha256']
    paper = read(ROOT / 'references/proceedings/NSDI/2026/rlboost-reading.json')
    assert digest((ROOT / paper['pdf']['file']).read_bytes()) == paper['pdf']['sha256']
    catalog = read(ROOT / 'references/proceedings/NSDI/2026/manifest.json')
    entry = next(item for item in catalog['entries'] if item.get('id') == 'nsdi26-wu-yongji')
    assert entry['selected_reading'] == paper['reading']
    assert paper['reading']['individual_physical_pages'] == [9, 10, 11, 12, 13, 17, 18]
    for view in paper['images']:
        assert view['actually_viewed'] and digest((ROOT / view['file']).read_bytes()) == view['sha256']
    assert not proof['downloaded_code_executed'] and not proof['hardware_experiments_run']
    return dict(successful_responses=21, selected_scopes=18, downloaded_not_read=3,
                paper_pages=7, paper_images=4, page_text_comparison='Checked by verify_archive.py')


def arithmetic():
    # Decimal GB/Gbps. These are full weights per receiving instance, regardless of TP=2.
    weight = 30_000_000_000
    receiver = F(50_000_000_000, 8)
    sender = F(200_000_000_000, 8)
    assert weight / receiver == F(24, 5)
    assert max(weight / receiver, 6 * weight / sender) == F(36, 5)
    for count in range(1, 21):
        bound = max(weight / receiver, count * weight / sender)
        assert sender * bound >= count * weight and receiver * bound >= weight
    rate_base, rate_spot = F(8379, 100), F(532, 100)
    multiplier = (rate_base + 6 * rate_spot) / rate_base
    assert multiplier == F(29, 21)
    assert multiplier / F(6, 5) > 1 and multiplier / F(8, 5) < 1
    # Check the quoted appendix price construction independently of rounded cost inputs.
    assert (F(10162, 100) + F(6596, 100)) / 2 == rate_base
    assert (F(2378, 100) / 4 + F(675, 100) + F(2024, 100) / 4 + F(176, 100) * 2) / 4 == F(851, 160)
    assert F(8000, 80) - 2 - 1 == 97
    assert F(4000 - 1000, 80) == F(75, 2)
    for pair in product([0, 10, 1000, 4000, 8000], repeat=2):
        retained = 2 * min(pair)
        assert retained <= sum(pair)
        assert sum(value - min(pair) for value in pair) == sum(pair) - retained
    config = read(DIRECTORY / 'qwen3-14b-config.json')
    assert [config[key] for key in ['num_hidden_layers', 'num_attention_heads', 'num_key_value_heads', 'head_dim']] == [40, 40, 8, 128]
    per_token = 2 * config['num_hidden_layers'] * config['num_key_value_heads'] * config['head_dim'] * 2
    assert per_token == 163840 and F(per_token * 8192, 2**30) == F(5, 4)
    assert F(48, config['num_hidden_layers']) == F(6, 5)
    return dict(single_receiver_seconds=4.8, all_six_receivers_lower_bound_seconds=7.2,
                break_even_throughput_multiplier=float(multiplier),
                cost_ratio_at_1_2x=float(multiplier / F(6, 5)),
                cost_ratio_at_1_6x=float(multiplier / F(8, 5)),
                migration_saved_seconds=97, batch_trimming_redo_seconds=37.5,
                receiver_counts_checked=20, batch_length_pairs_checked=25,
                qwen3_14b_kv_bytes_per_token=per_token, qwen3_14b_8k_kv_gib=1.25,
                scope='Conditional arithmetic; no workload, quality, cloud-price or implementation benchmark')


if __name__ == '__main__':
    report = dict(status='passed', recorded_at=datetime.now(timezone.utc).isoformat(),
                  sources=sources(), arithmetic=arithmetic(),
                  downloaded_code_executed=False, hardware_experiments_run=False)
    (ROOT / 'research/2026-infra-survey/rlboost-recovery-audit.json').write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(report, ensure_ascii=False, indent=2))
