"""Replay a retrospective design review from copied raw experimental records."""
import hashlib
import json
import re
from pathlib import Path

BASE = Path(__file__).resolve().parent

def unique(pairs):
    obj = {}
    for key, value in pairs:
        if key in obj:
            raise ValueError('duplicate JSON key')
        obj[key] = value
    return obj

for binding in json.loads((BASE / 'source-bindings.json').read_text())['files']:
    data = (BASE / binding['copy']).read_bytes()
    assert len(data) == binding['bytes']
    assert hashlib.sha256(data).hexdigest() == binding['sha256']

reports = []
input_hashes = set()
for name in ['bf16', 'fp8', 'fp8_qbf16']:
    root = BASE / 'source' / name
    env = json.loads((root / 'environment.json').read_text())
    input_hash = hashlib.sha256((root / 'inputs.json').read_bytes()).hexdigest()
    input_hashes.add(input_hash)
    assert env['input_sha256'] == input_hash
    tasks = {t['id']: t for t in json.loads((root / 'inputs.json').read_text())['tasks']}
    assert len(tasks) == 8
    for task in tasks.values():
        facts = dict(re.findall(r'^(k\d{4}) = (\d{6})$', task['messages'][1]['content'], re.M))
        assert len(facts) == task['rows']
        assert all(facts[k] == v for k, v in task['expected'].items())
    rows = [json.loads(line) for line in (root / 'requests.jsonl').read_text().splitlines()]
    assert len({row['id'] for row in rows}) == len(rows)
    batches = [json.loads(line) for line in (root / 'batches.jsonl').read_text().splitlines()]
    scored = []
    for batch in batches:
        if batch['trial'] == 'warm' or batch['mode'] != 'natural':
            continue
        group = [row for row in rows if row['id'].startswith(batch['id'] + '-')]
        assert len(group) == 4 and len({r['task_id'] for r in group}) == 4
        for row in group:
            try:
                answer = json.loads(row['text'], object_pairs_hook=unique)
            except (ValueError, TypeError):
                answer = None
            correct = answer == tasks[row['task_id']]['expected'] and row['finish_reason'] == 'stop'
            scored.append(dict(id=row['id'], task_id=row['task_id'], correct=correct,
                               finish=row['finish_reason'], elapsed_s=row['end_s'] - row['start_s'],
                               rows=batch['rows'], concurrency=batch['concurrency']))
    assert len(scored) == 32
    snap = json.loads((root / 'kv-snapshots.json').read_text())['after_calibration'][0]
    reports.append(dict(candidate=name, observed_natural_requests=32, distinct_tasks=8,
                        correct=sum(r['correct'] for r in scored),
                        failed_request_ids=[r['id'] for r in scored if not r['correct']],
                        all_quality_gate_passed=all(r['correct'] for r in scored),
                        unique_kv_storage_bytes=snap['unique_kv_storage_bytes'],
                        records=scored, production_capacity=None, monetary_cost=None,
                        corrected_answer_completion_time=None))
assert len(input_hashes) == 1
by_name = {r['candidate']: r for r in reports}
sets = {name: set(r['failed_request_ids']) for name, r in by_name.items()}
result = dict(scope='Historical evidence review, not a preregistered experiment or deployment benchmark',
              candidates=reports, baseline_and_qcontrol_failure_sets_equal=sets['bf16'] == sets['fp8_qbf16'],
              proceed_to_validation=['bf16', 'fp8_qbf16'],
              approved_for_deployment=[r['candidate'] for r in reports if r['all_quality_gate_passed']],
              calculations_scope='No capacity, traffic, price or critical-path model implemented; C72 remains separate')
(BASE / 'review-results.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({r['candidate']: {'correct': r['correct'], 'quality_gate': r['all_quality_gate_passed']} for r in reports}))
