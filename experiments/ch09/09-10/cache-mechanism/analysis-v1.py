import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent


def main():
    read = lambda p: json.loads(p.read_text())
    sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    results = ROOT / 'results'
    plan = read(results / 'plan.json')
    resume = read(results / 'resume-info.json')
    assert plan['source_sha256']['run.py'] == sha(ROOT / 'initial-run.py')
    for f, expected in resume['new_source_sha256'].items():
        assert sha(ROOT / f) == expected
        if f != 'run.py':
            assert plan['source_sha256'][f] == expected
    assert read(results / 'execution.json') == {'status': 'completed', 'groups': 12}
    config = read(ROOT / 'config.json')
    reference = read(ROOT / 'reference.json')
    assert len(plan['order']) == 12
    summaries = []
    count = 0
    for c in plan['order']:
        p = results / f"{c['trial']}-{c['entry']}-{c['count']}"
        done = read(p / 'execution.json')
        coordinator = read(p / 'coordinator.json')
        assert done == {'status': 'completed', 'entry': c['entry'], 'count': c['count']}
        assert coordinator['exit_code'] == 0 and not coordinator['timed_out']
        actual = read(p / 'server-info.json')
        assert all(actual[k] == v for k, v in config.items()), (p, 'actual config mismatch')
        logs = '\n'.join((p / f).read_text(errors='replace') for f in ['worker.log', 'server.log'] if (p / f).exists())
        pool_sizes = [int(x) for x in re.findall(r'max_total_num_tokens=(\d+)', logs)]
        assert pool_sizes and set(pool_sizes) == {4096}, (p, pool_sizes)
        prep = read(p / 'cache-preparation.json')
        assert prep['files_verified'] == 65 and prep['source_manifest_sha256'] == sha(ROOT / 'cache-manifest.json')
        rows = read(p / 'requests.json')
        assert len(rows) == c['count'] and sorted(r['index'] for r in rows) == list(range(c['count']))
        for r in rows:
            assert r['output_ids'] == reference['output_ids'] and r['response']['text'] == reference['text']
            assert r['passed'] and r['sent_s'] <= r['end_s']
        count += len(rows)
        first = min(rows, key=lambda r: r['end_s'])
        sent = min(rows, key=lambda r: r['sent_s'])
        events = [json.loads(l) for l in (p / 'storage.jsonl').read_text().splitlines()]
        gets = [x for x in events if x['method'] == 'get' and x['success']]
        ordered = sorted(rows, key=lambda r: r['end_s'])
        summaries.append({**c, 'first_sent_index': sent['index'], 'first_completed_index': first['index'],
            'first_cached_tokens': first['response']['meta_info'].get('cached_tokens'),
            'first_cached_details': first['response']['meta_info'].get('cached_tokens_details'),
            'requests_in_completion_order': [{'index': r['index'], 'cached_tokens': r['response']['meta_info'].get('cached_tokens'),
                 'details': r['response']['meta_info'].get('cached_tokens_details')} for r in ordered],
            'get_count': len(gets), 'unique_get_keys': len({x['key'] for x in gets}),
            'get_file_bytes_sum': sum(x['bytes'] for x in gets), 'actual_pool_tokens': pool_sizes[0]})
    assert count == 54
    report = {'groups': summaries, 'exact_output_checks': count, 'status': 'completed',
              'performance_comparison': 'not claimed: shared GPU with existing 49GiB service',
              'causal_scope': 'Observed API/storage behavior only; native and HTTP lifecycle differ.'}
    (ROOT / 'summary.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
