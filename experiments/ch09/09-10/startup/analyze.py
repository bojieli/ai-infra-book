"""Offline gates for a completed startup run; compilation review remains explicit."""
import argparse
import hashlib
import json
from pathlib import Path
import statistics

ROOT = Path(__file__).resolve().parent


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--results', type=Path, default=ROOT / 'results')
    a = ap.parse_args()
    read = lambda p: json.loads(p.read_text())
    terminal = read(a.results / 'execution.json')
    assert terminal == {'status': 'completed', 'scored_groups': 6, 'warmup_groups': 2}
    plan = read(a.results / 'plan.json')
    for name, expected in plan['source_hashes'].items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == expected
    reference = read(ROOT / 'reference.json')
    rows = []
    checked = {'formal': 0, 'warmup': 0}
    for trial, policy in plan['order']:
        p = a.results / f'{trial}-{policy}'
        e, requests = read(p / 'execution.json'), read(p / 'requests.json')
        assert e['status'] == 'completed' and e['request_count'] == 8 and e['exit_code'] is not None
        assert sorted(r['index'] for r in requests) == list(range(8))
        assert all(r['passed'] and r['output_ids'] == reference['output_ids'] for r in requests)
        assert all(r['response'].get('text') == reference['text'] for r in requests)
        assert e['warmup'] == trial.startswith('warmup')
        checked['warmup' if e['warmup'] else 'formal'] += len(requests)
        assert all(r['planned_s'] <= r['arrived_s'] <= r['sent_s'] <= r['end_s'] for r in requests)
        assert all(r['sent_s'] >= e['ready_s'] for r in requests)
        assert e['first_complete_s'] == min(r['end_s'] for r in requests)
        assert e['all_complete_s'] == max(r['end_s'] for r in requests)
        assert e['launch_s'] < e['ready_s'] <= e['first_complete_s'] <= e['all_complete_s'] <= e['reaped_s']
        # Heuristic extraction for human JIT review, not proof that no compilation occurred.
        mentions = [line for line in (p / 'server.log').read_text(errors='replace').splitlines()
                    if 'server_args=ServerArgs' not in line
                    and any(word in line.lower() for word in ['compil', 'jit', 'building'])]
        first_send = min(requests, key=lambda r: r['sent_s'])
        first_complete = min(requests, key=lambda r: r['end_s'])
        compact = lambda r: {'index': r['index'], 'sent_s': r['sent_s'], 'end_s': r['end_s'],
                             'cached_tokens': r['response']['meta_info'].get('cached_tokens'),
                             'cached_tokens_details': r['response']['meta_info'].get('cached_tokens_details')}
        storage_events = [json.loads(line) for line in (p / 'storage.jsonl').read_text().splitlines()]
        row = {'trial': trial, 'policy': policy, 'warmup': e['warmup'],
               'ready_after_launch_s': e['ready_s'] - e['launch_s'],
               'first_complete_after_launch_s': e['first_complete_s'] - e['launch_s'],
               'drained_after_launch_s': e['all_complete_s'] - e['launch_s'],
               'drained_after_ready_s': e['all_complete_s'] - e['ready_s'],
               'max_arrival_lateness_s': max(r['arrived_s'] - r['planned_s'] for r in requests),
               'cache_details': [r['response']['meta_info'].get('cached_tokens_details') for r in requests],
               'first_sent_request': compact(first_send), 'first_completed_request': compact(first_complete),
               'successful_storage_get_count': sum(x['method'] == 'get' and x['success'] for x in storage_events),
               'successful_storage_get_file_bytes': sum(x['bytes'] for x in storage_events if x['method'] == 'get' and x['success']),
               'unique_successful_get_keys': len({x['key'] for x in storage_events if x['method'] == 'get' and x['success']}),
               'jit_log_mentions_for_review': mentions}
        rows.append(row)
    assert checked == {'formal': 48, 'warmup': 16}
    report = {'rows': rows, 'formal_output_checks': checked['formal'], 'warmup_output_checks': checked['warmup'],
              'jit_equivalence_review': 'pending_manual_review',
              'speedup_claim_allowed': False,
              'timing_scope': 'Client startup backlog including health gate; not pre-ready engine queue.'}
    (ROOT / 'summary.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'output_checks': 64, 'jit_equivalence_review': 'pending_manual_review'}))


if __name__ == '__main__':
    main()
