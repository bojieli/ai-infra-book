#!/usr/bin/env python3
"""Offline, standard-library inspection of sealed records; never runs their code.

Run anywhere: python3 /path/to/experiments/ch11/11-10/analyze.py
Outputs stay next to this file. Adjacent evidence is REQUIRED, not bundled.
"""
import ast
import hashlib
import json
import math
import os
from pathlib import Path
import resource
import statistics
import sys
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
LOCK_SHA256 = '215ea32e91452be112605db18bacdbc53cf3fa89ddae4733a16ef16a917727a9'
BASE = 'experiments/ch11/'
CHECKS = {}
RECORDS = []
SOURCES = {}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def check(group, condition, context):
    row = CHECKS.setdefault(group, {'passed': 0, 'failed': []})
    if not condition:
        row['failed'].append(str(context))
        raise ValueError(f'{group}: {context}')
    row['passed'] += 1


def read(path):
    check('locked_reads', path in SOURCES, path)
    data = (ROOT / path).read_bytes()
    check('source_hashes', digest(data) == SOURCES[path]['sha256'], path)
    return data.decode('utf-8')


def js(path):
    return json.loads(read(path))


def lines(path):
    return [json.loads(line) for line in read(path).splitlines() if line.strip()]


def seq(values, context):
    check('finite_ordered_times', all(isinstance(v, (int, float)) and math.isfinite(v)
                                    for v in values), context)
    check('finite_ordered_times', all(a <= b for a, b in zip(values, values[1:])), context)


def record(group, path, locator, **values):
    row = dict(group=group, source=path, source_sha256=SOURCES[path]['sha256'],
               locator=locator, **values)
    RECORDS.append(row)
    return row


def static_strings(path):
    # Parse literals only: no import, eval, exec, runpy, or workload execution.
    tree = ast.parse(read(path))
    return {node.targets[0].id: node.value.value for node in tree.body
            if isinstance(node, ast.Assign) and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str)}


def source_versions(base, environment):
    hashes = environment.get('source_hashes', {})
    if 'source_sha256' in environment:
        hashes = {**hashes, 'run.py': environment['source_sha256']}
    for name, sha in hashes.items():
        check('recorded_source_versions', SOURCES[base + name]['sha256'] == sha, base + name)


def quality(validation, context):
    q = json.loads(validation['stdout'])
    check('saved_quality_consistency', validation['returncode'] == 0, context)
    check('saved_quality_consistency', len(q['cases']) == 6, context)
    for c in q['cases']:
        expected_pass = ('actual' in c and c['actual'] == c['expected'] and c.get('unchanged') is True)
        check('saved_quality_consistency', c['passed'] == expected_pass, context)
    check('saved_quality_consistency', q['passed'] == all(c['passed'] for c in q['cases']), context)
    return dict(passed=q['passed'], cases=6, cases_passed=sum(c['passed'] for c in q['cases']))


def output_events(row, context, primary=False):
    events = row['output_events'] if primary else row['events']
    key = 't_s' if primary else 'time_s'
    start = row['model_start_s'] if primary else row['start_s']
    end = row['model_end_s']
    ids = row['output_token_ids'] if primary else row['output_ids']
    seq([start] + [e[key] for e in events] + [end], context)
    seq([0] + [e['token_count'] for e in events], context)
    check('token_accounting', bool(events) and events[-1]['token_count'] == len(ids), context)
    m = row.get('engine_metrics')
    if m is None:
        check('explicit_missing_engine_metrics', not primary, context)
        return dict(engine_queue_s=None, controller_first_output_s=events[0][key]-start)
    check('token_accounting', m['num_generation_tokens'] == len(ids) and not m['is_corrupted'], context)
    # These are engine monotonic timestamps. Never subtract arrival_time (epoch)
    # or compare the primary loop-relative timestamps to this clock origin.
    seq([m[k] for k in ['queued_ts', 'scheduled_ts', 'first_token_ts', 'last_token_ts']], context)
    return dict(engine_queue_s=m['scheduled_ts'] - m['queued_ts'],
                controller_first_output_s=events[0][key] - start)


def primary():
    b = BASE + '11-01/'
    env = js(b + 'results/environment.json')
    source_versions(b, env)
    fixed = static_strings(b + 'run.py')
    for key, filename in [('SPEC', 'SPEC.txt'), ('CHECKER', 'test_intervals.py')]:
        check('primary_fixture_identity', fixed[key] == read(b + 'results/workspace/' + filename), key)
    rows = lines(b + 'results/rounds.jsonl')
    final = js(b + 'results/final.json')
    baseline = quality(js(b + 'results/baseline.json'), 'primary baseline')
    final_q = quality(final['validation'], 'primary final')
    code = fixed['INITIAL']
    messages = list(rows[0]['messages'])
    check('primary_fixture_identity', messages[1]['content'] == fixed['SPEC'] +
          '\nInspect the implementation, fix it, and validate it.', 'initial user prompt')
    check('primary_task_coverage', len(rows) == 12, 'all recorded turns')
    derived = []
    previous = 0
    for i, r in enumerate(rows):
        context = f'primary turn {i}'
        check('primary_conversation', r['turn'] == i and r['messages'] == messages, context)
        seq([previous, r['model_start_s'], r['model_end_s'], r['tool_start_s'], r['tool_end_s'], final['elapsed_s']], context)
        previous = r['tool_end_s']
        check('primary_action_identity', json.loads(r['output_text']) == r['action'], context)
        a = r['action']
        if a['tool'] == 'write_file':
            code = a['content']
            check('primary_action_identity', r['tool_result']['sha256'] == digest(code.encode())
                  and r['tool_result']['written_bytes'] == len(code.encode()), context)
        elif a['tool'] == 'read_file':
            check('primary_action_identity', r['tool_result']['content'] == code, context)
        q = quality(r['tool_result'], context) if a['tool'] == 'run_tests' else None
        check('primary_file_chain', digest(code.encode()) == r['file_sha256'], context)
        for key in ['model_parent_cpu_s', 'tool_parent_cpu_s', 'tool_child_cpu_s']:
            check('nonnegative_cpu', math.isfinite(r[key]) and r[key] >= 0, context + key)
        measured = output_events(r, context, primary=True)
        check('token_accounting', 0 <= r['cached_tokens'] <= len(r['prompt_token_ids']), context)
        derived.append(record('primary_agent_turn', b + 'results/rounds.jsonl', f'line:{i+1}',
            turn=i, action=a['tool'], model_start_s=r['model_start_s'], model_end_s=r['model_end_s'],
            model_wall_s=r['model_end_s'] - r['model_start_s'],
            tool_start_s=r['tool_start_s'], tool_end_s=r['tool_end_s'],
            tool_wall_s=r['tool_end_s'] - r['tool_start_s'],
            model_controller_cpu_s=r['model_parent_cpu_s'], tool_controller_cpu_s=r['tool_parent_cpu_s'],
            tool_reaped_child_cpu_s=r['tool_child_cpu_s'], quality=q,
            input_tokens=len(r['prompt_token_ids']), output_tokens=len(r['output_token_ids']),
            cached_tokens=r['cached_tokens'], file_sha256=r['file_sha256'], **measured))
        messages += [dict(role='assistant', content=r['output_text']),
                     dict(role='user', content='Tool result: ' + json.dumps(r['tool_result']))]
    check('primary_file_chain', code == final['final_code'] == read(b + 'results/workspace/intervals.py'), 'final')
    check('primary_task_coverage', final['agent_finished'] == any(r['action']['tool'] == 'finish' for r in rows), 'finish action')
    raw_samples = js(b + 'results/resource-samples.json')
    samples = raw_samples['samples']
    seq([s['t_s'] for s in samples], 'controller samples')
    seq([s['cpu_user_s'] + s['cpu_system_s'] for s in samples], 'controller cumulative CPU')
    phases = {}
    for name in sorted({s['phase'] for s in samples}):
        vals = [s['rss_kib'] / 1024 for s in samples if s['phase'] == name]
        check('rss_samples', all(v > 0 for v in vals), name)
        phases[name] = dict(count=len(vals), min_mib=min(vals), max_mib=max(vals))
    totals = {key: sum(r[key] for r in derived) for key in [
        'model_wall_s', 'tool_wall_s', 'model_controller_cpu_s', 'tool_controller_cpu_s',
        'tool_reaped_child_cpu_s', 'engine_queue_s', 'input_tokens', 'output_tokens', 'cached_tokens']}
    gaps = [b['t_s'] - a['t_s'] for a, b in zip(samples, samples[1:])]
    return dict(environment=env, task_count=1, turns=len(rows),
        initial_code_sha256=digest(fixed['INITIAL'].encode()), spec_sha256=digest(fixed['SPEC'].encode()),
        checker_sha256=digest(fixed['CHECKER'].encode()), baseline_quality=baseline, final_quality=final_q,
        agent_finished=final['agent_finished'], verified_usable_s=None,
        loop_wall_s=final['elapsed_s'], **totals,
        model_wall_fraction=totals['model_wall_s'] / final['elapsed_s'],
        model_controller_cpu_per_wall=totals['model_controller_cpu_s'] / totals['model_wall_s'],
        unassigned_loop_wall_s=final['elapsed_s'] - totals['model_wall_s'] - totals['tool_wall_s'],
        engine_queue_max_s=max(r['engine_queue_s'] for r in derived),
        rss_scope=raw_samples['scope'], sampled_peak_rss_mib=max(s['rss_kib'] for s in samples) / 1024,
        sample_count=len(samples), sample_gap_median_s=statistics.median(gaps),
        sample_gap_max_s=max(gaps), rss_by_phase=phases,
        gpu_utilization=None, gpu_memory_peak=None, network_congestion=None,
        api_quota=None, actual_currency_cost=None, service_target_s=None, slo_achieved=None)


def process_observations():
    b = BASE + '11-01/process-resources/'
    source_versions(b, js(b + 'results/environment.json'))
    order = js(b + 'results/order.json')
    result = []
    digests = set()
    for index, case in enumerate(order):
        p = b + f'results/case{index}.json'
        r = js(p)
        check('process_case_coverage', all(r[k] == v for k, v in case.items()), p)
        check('process_case_coverage', len(r['launch']) == len(r['completed']) == 4, p)
        cpus = []
        for launch in r['launch']:
            c = r['completed'][str(launch['pid'])]
            w = json.loads(c['stdout'])
            seq([r['start'], launch['at'], w['start'], w['ready'], w['end'], c['reaped'], r['end']], p)
            check('process_outputs', c['returncode'] == 0 and w['pid'] == launch['pid']
                  and w['memory_check'] == 16384 and 0 <= w['cpu_work'] <= w['cpu_total'], p)
            if r['mode'] == 'cpu':
                digests.add(w['digest'])
            else:
                check('process_outputs', w['digest'] is None, p)
            cpus.append(w['cpu_total'])
        seq([s['at'] for s in r['samples']], p)
        rss = [sum(w['rss'] for w in s['processes']) for s in r['samples']]
        check('rss_samples', all(v >= 0 for v in rss), p)
        result.append(record('separate_process_case', p, '$', trial=r['trial'], mode=r['mode'],
            arrival=r['arrival'], wall_s=r['end']-r['start'], child_cpu_s=sum(cpus),
            sampled_sum_peak_rss_mib=max(rss)/1024**2, processes=4,
            quality_scope='stored page-touch count and digest agreement; no new CPU reference run'))
    check('process_digest_agreement', len(digests) == 1 and len(next(iter(digests))) == 64, '24 CPU workers')
    return result


def timeout_and_batch():
    b = BASE + '11-05/'
    p = b + 'results/run-v1/raw.json'
    r = js(p)
    source_versions(b, r)
    result = []
    for i, row in enumerate(r['records']):
        seq([row['wait_start_s'], row['feedback_s'], row.get('release_observed_s', row['feedback_s'])], p)
        if 'result' in row:
            w = row['result']
            check('timeout_output_identity', w['digest'] == r['reference']['digest']
                  and w['iterations'] == r['reference']['iterations'], f'row {i}')
            seq([w['start_s'], w['end_s']], p)
        if row['mode'] == 'thread-wait-timeout':
            check('timeout_release_boundary', row['timed_out'] and row['worker_running_at_feedback']
                  and row['feedback_s'] < row['result']['end_s'] <= row['release_observed_s'], p)
        elif row['mode'] == 'process-terminate-and-reap':
            check('timeout_release_boundary', row['returncode'] == -15 and row['timed_out'], p)
        result.append(record('separate_timeout', p, f'records[{i}]', trial=row['trial'], mode=row['mode'],
            feedback_wait_s=row['feedback_s']-row['wait_start_s'],
            feedback_to_release_s=(row['release_observed_s']-row['feedback_s']) if 'release_observed_s' in row else None))
    b += 'batch-scheduling/'
    execution = js(b + 'results/execution.json')
    source_versions(b, execution)
    refs = js(b + 'results/references.json')
    batch_results = []
    p = b + 'results/raw.jsonl'
    batches = lines(p)
    check('batch_coverage', len(batches) == 9, p)
    for i, row in enumerate(batches):
        tasks = row['tasks']
        check('batch_coverage', len(tasks) == 6 and {t['id'] for t in tasks} == {t['id'] for t in execution['task_spec']}, p)
        edges = []
        for t in tasks:
            w = t['result']
            spec = next(s for s in execution['task_spec'] if s['id'] == t['id'])
            check('batch_matched_work', all(t[k] == v for k,v in spec.items())
                  and w['iterations'] == t['iterations'], t['id'])
            seq([row['start_s']+t['arrival_s'], t['dispatch_s'], w['compile_start_s'], w['compile_end_s'],
                 w['work_start_s'], w['work_end_s'], t['feedback_s'], t['release_s'], row['end_s']], t['id'])
            check('batch_output_identity', t['exit_code'] == 0 and w['digest'] == refs[str(t['iterations'])]['digest'], t['id'])
            edges.extend([(t['dispatch_s'], 1), (t['release_s'], -1)])
        active = 0
        for _, delta in sorted(edges):
            active += delta
            check('batch_slot_occupancy', 0 <= active <= 2, p)
        batch_results.append(record('separate_batch', p, f'line:{i+1}', trial=row['trial'], policy=row['policy'],
            a_feedback_s=max(t['feedback_s'] for t in tasks if t['batch']=='A')-row['start_s'],
            b_feedback_s=max(t['feedback_s'] for t in tasks if t['batch']=='B')-row['start_s'],
            all_release_s=max(t['release_s'] for t in tasks)-row['start_s'],
            cpu_work_s=sum(t['result']['cpu_s'] for t in tasks),
            task_queue_s=[dict(id=t['id'], seconds=t['dispatch_s']-row['start_s']-t['arrival_s']) for t in tasks]))
    return dict(timeout=result, batch=batch_results)


def prewarm():
    b = BASE + '11-06/'
    env = js(b + 'results/environment.json')
    source_versions(b, env)
    fixture = js(b + 'fixture.json')
    origin = 'experiments/ch03/03-04/'
    check('prewarm_origin_identity', fixture['source_sha256'] == SOURCES[origin+'run.py']['sha256']
          and fixture['trace_sha256'] == SOURCES[origin+'results/rounds.jsonl']['sha256'], '03-04 origin')
    source_rows = lines(origin+'results/rounds.jsonl')
    check('prewarm_origin_identity', fixture['trace_sha256'] != SOURCES[BASE+'11-01/results/rounds.jsonl']['sha256'],
          'different trajectory from primary')
    for r, f in zip(source_rows, fixture['rounds']):
        check('prewarm_origin_identity', all(r[k] == v for k, v in f.items()), str(f['turn']))
    check('prewarm_coverage', len(source_rows) == len(fixture['rounds']) == 12, 'source turns')
    results = []
    paths = sorted(p for p in SOURCES if p.startswith(b+'results/') and p.endswith('/raw.json'))
    check('prewarm_coverage', len(paths) == 12 and js(b+'results/completion.json')['completed'], '12 cases')
    for p in paths:
        r = js(p)
        seq([r['origin_ns'], r['work_done_ns'], r['end_ns']], p)
        check('prewarm_coverage', len(r['rows']) == 12, p)
        for i, (row, f) in enumerate(zip(r['rows'], fixture['rounds'])):
            check('prewarm_tool_identity', row['turn'] == i and row['response']['reply'] == f['tool_result']
                  and row['file_sha256'] == f['file_sha256'], p+str(i))
            check('prewarm_tool_identity', row['gap_s'] == f['model_end_s']-f['model_start_s'], p+str(i))
            seq([row['gap_start_ns'], row['call_ns'], row['send_ns'], row['response']['start_ns'],
                 row['response']['end_ns'], row['received_ns']], p+str(i))
        work = p.rsplit('/',1)[0]+'/workspace/'
        check('prewarm_tool_identity', SOURCES[work+'intervals.py']['sha256'] == r['rows'][-1]['file_sha256']
              and read(work+'SPEC.txt') == fixture['fixture']['SPEC']
              and read(work+'test_intervals.py') == fixture['fixture']['CHECKER'], p)
        launches = {e['pid']: e for e in r['events'] if e['event'] == 'launch'}
        ready = {e['pid']: e for e in r['events'] if e['event'] == 'ready'}
        destroyed = {e['pid']: e for e in r['events'] if e['event'] == 'destroy'}
        check('prewarm_process_lifecycle', launches.keys() == ready.keys() == destroyed.keys(), p)
        for pid in launches:
            seq([launches[pid]['t_ns'], ready[pid]['t_ns'], destroyed[pid]['t_ns'], destroyed[pid]['end_ns']], p)
            check('prewarm_process_lifecycle', destroyed[pid]['returncode'] == 0, p)
        used = {row['worker_pid'] for row in r['rows']}
        unused = launches.keys() - used
        sums = [sum(w['rss_bytes'] for w in s['workers']) for s in r['samples']]
        mids = [(s['start_ns']+s['end_ns'])/2e9 for s in r['samples']]
        seq(mids, p)
        residency = sum((b-a)*(x+y)/2 for a,b,x,y in zip(mids,mids[1:],sums,sums[1:])) / 1024**3
        results.append(record('separate_prewarm_replay', p, '$', trial=r['trial'], policy=r['policy'],
            work_done_s=(r['work_done_ns']-r['origin_ns'])/1e9,
            recorded_gap_to_call_s=sum((x['call_ns']-x['gap_start_ns'])/1e9 for x in r['rows']),
            historical_model_gap_s=sum(x['gap_s'] for x in r['rows']),
            tool_call_s=sum((x['received_ns']-x['call_ns'])/1e9 for x in r['rows']),
            sampled_sum_peak_rss_mib=max(sums)/1024**2, sampled_residency_gib_s=residency,
            unused_ready_s=sum((destroyed[pid]['t_ns']-ready[pid]['t_ns'])/1e9 for pid in unused),
            unused_workers=len(unused), prediction_hits=sum(x['prediction_hit'] is True for x in r['rows']),
            quality=quality(r['rows'][-1]['response']['reply'], p),
            real_model_executed=False, matched_to_primary=False))
    return results


def model_quality():
    results = []
    for sub in ['11-08', '11-08/wide-budget', '11-09/repair-continuation', '11-09/model-candidate']:
        b = BASE + sub + '/'
        env = js(b+'results/environment.json')
        source_versions(b, env)
        p = b+'results/raw.jsonl'
        rows = lines(p)
        independent_path = b+'results/'+('independent.json' if 'repair' in sub else 'independent-checks.json')
        independent = {}
        independent_code_hashes = {}
        if independent_path in SOURCES:
            ind = js(independent_path)
            if isinstance(ind, dict):
                source_versions(b, ind)
            for row in (ind['records'] if isinstance(ind, dict) else ind):
                q = json.loads(row['stdout'])
                check('independent_saved_quality', row['returncode'] == 0 and q['passed'] + len(q['failures']) == q['cases'], independent_path)
                check('independent_saved_quality', q['passed'] == q['value_and_input_passed'] - q['additional_alias_failures'], independent_path)
                key = row.get('request_id', row.get('case_index'))
                independent[key] = {k:v for k,v in q.items() if k != 'failures'}
                if 'code_sha256' in row:
                    independent_code_hashes[key] = row['code_sha256']
        for i, r in enumerate(rows):
            key = r.get('request_id', r.get('case_index'))
            seq([r['start_s'], r['model_end_s'], r['done_s']], p+str(i))
            measured = output_events(r, p+str(i))
            check('model_request_controls', r['cached_tokens'] == 0, p+str(i))
            check('model_request_controls', r['finish_reason'] in ['stop', 'length'] and
                  (r['finish_reason'] != 'length' or len(r['output_ids']) == r['budget']), p+str(i))
            q = quality(r['result']['validation'], p+str(i)) if 'validation' in r['result'] else None
            check('model_quality_status', r['result']['passed'] == (q['passed'] if q else False), p)
            work = b+'results/'+(r['request_id'] if 'request_id' in r else f"case{r['case_index']}")+'/'
            if 'write' in r['result']:
                check('model_code_identity', SOURCES[work+'intervals.py']['sha256'] == r['result']['write']['sha256'], work)
                if key in independent_code_hashes:
                    check('independent_code_identity', independent_code_hashes[key] == SOURCES[work+'intervals.py']['sha256'], work)
            check('model_common_fixture', read(work+'SPEC.txt') == read(BASE+'11-01/results/workspace/SPEC.txt')
                  and read(work+'test_intervals.py') == read(BASE+'11-01/results/workspace/test_intervals.py'), work)
            results.append(record('separate_model_request', p, f'line:{i+1}', experiment=sub,
                request_key=key, trial=r['trial'], stage=r.get('stage'), budget=r.get('budget', 1000),
                thinking=r.get('thinking', False), model_snapshot=env['config']['model'].split('/')[-1],
                input_tokens=len(r['input_ids']), output_tokens=len(r['output_ids']),
                finish_reason=r['finish_reason'], model_wall_s=r['model_end_s']-r['start_s'],
                model_plus_original_validation_s=r['done_s']-r['start_s'], quality=q,
                independent_quality=independent.get(key), verified_usable_s=None, actual_currency_cost=None,
                matched_to_primary=False, **measured))
    return results


def collectors():
    faults = []
    b = BASE+'11-09/collector-faults/'
    for p in sorted(p for p in SOURCES if p.startswith(b+'results/') and p.endswith('/record.json')):
        r = js(p)
        work = {w['event_id']: w for w in r['work']}
        unique = {k: json.loads(v) for k,v in r['unique_events']}
        check('collector_task_identity', len(work) == 6 and len({w['task_id'] for w in work.values()}) == 5, p)
        check('collector_task_identity', all(unique[k] == work[k] for k in unique), p)
        check('collector_task_identity', all(a['status'] == 200 for a in r['accepted']), p)
        committed = [d for d in r['deliveries'] if d[2]]
        check('collector_task_identity', r['before_probe'] == sum(work[k]['attempt_id'] == 0 for k in unique), p)
        check('collector_task_identity', {d[0] for d in committed} == unique.keys(), p)
        check('collector_task_identity', all(json.loads(d[3]) == work[d[0]] for d in r['deliveries']), p)
        faults.append(record('separate_collector_fault', p, '$', trial=r['trial'], condition=r['name'],
            tool_attempts=len(work), tool_cpu_s=sum(w['cpu_s'] for w in work.values()),
            restored_before_probe=r['before_probe'], unique_records=len(unique),
            delivery_attempts=len(r['deliveries']), duplicate_commits=len(committed)-len(unique)))
    drains = []
    b = BASE+'11-09/collector-drain/'
    for p in sorted(p for p in SOURCES if p.startswith(b+'results/') and p.endswith('/execution.json')):
        folder = p.rsplit('/',1)[0]+'/'
        r = js(p)
        source = lines(folder+'source.jsonl')
        backend = lines(folder+'backend.jsonl')
        src = {s['event']['event_id']:s for s in source}
        commits = {}
        for row in backend:
            seq([row['start_s'], row['commit_start_s'], row['end_s']], p)
            if row['success']:
                for e in row['events']:
                    check('collector_payload_and_time', src[e['event_id']]['event'] == e, p)
                    check('collector_payload_and_time', src[e['event_id']]['dispatch_s'] <= row['end_s'], p)
                    commits.setdefault(e['event_id'], row['end_s'])
        check('collector_coverage', len(src) == len(commits) == 120 and src.keys() == commits.keys(), p)
        check('collector_coverage', r['exit_code'] == 0, p)
        for s in source:
            seq([s['planned_s'], s['dispatch_s'], s['ack_s']], p)
            check('collector_receive_ack', s['ack']['status'] == 200, p)
        pending = sum(t > r['production_end_s'] for t in commits.values())
        drains.append(record('separate_collector_drain', p, '$', trial=r['trial'], injected_delay_s=r['delay_s'],
            committed_events=len(commits), pending_at_production_end=pending,
            drain_after_production_end_s=max(commits.values())-r['production_end_s'],
            first_all_120_committed_after_restore_s=max(commits.values())-r['restore_s'],
            max_dispatch_lateness_s=max(s['dispatch_s']-s['planned_s'] for s in source),
            scope='dispatch-minus-commit unfinished work; not internal queue depth or API quota'))
    return dict(faults=faults, drains=drains)


def main():
    global SOURCES
    begin = time.monotonic()
    for key in ['OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS']:
        os.environ[key] = '1'
    # Darwin rejects this AS limit (also documented in 11-06). Bound pinned
    # input/output sizes and verify measured RSS there; do not claim a hard cap.
    if sys.platform != 'darwin':
        resource.setrlimit(resource.RLIMIT_AS, (2*1024**3, 2*1024**3))
    resource.setrlimit(resource.RLIMIT_FSIZE, (8*1024**2, 8*1024**2))
    raw = (HERE/'sources.lock.json').read_bytes()
    check('source_lock_identity', digest(raw) == LOCK_SHA256, 'sources.lock.json')
    SOURCES = json.loads(raw)['files']
    check('offline_resource_budget', sum(e['bytes'] for e in SOURCES.values()) <= 16*1024**2,
          'bounded source bytes <=16MiB')
    for path, entry in SOURCES.items():
        check('source_paths', not Path(path).is_absolute() and '..' not in Path(path).parts, path)
        data = (ROOT/path).read_bytes()
        check('source_hashes', len(data) == entry['bytes'] and digest(data) == entry['sha256'], path)
    for p in SOURCES:
        if p.endswith('/manifest.json'):
            manifest = js(p)
            items = manifest['files']
            if isinstance(items, list):
                items = {item['path']: item for item in items}
            for name, item in items.items():
                path = p.rsplit('/',1)[0]+'/'+name
                if path in SOURCES:
                    check('original_seal_agreement', SOURCES[path]['sha256'] == item['sha256'], path)
    inventory = next(x for x in js('experiments/inventory.json') if x['id']=='11-10')
    summary = dict(schema_version=1, status='offline_evidence_complete_pending_main_agent_review',
        original_requirement=inventory['requirements'], original_experiment_status=inventory['status'],
        expansion_implemented=False, original_requirement_fully_validated=False,
        primary=primary(), separate_process=process_observations(),
        separate_cpu_scheduling=timeout_and_batch(), separate_prewarm=prewarm(),
        separate_model_requests=model_quality(), separate_collectors=collectors(),
        calculation_reference=dict(path='calculations/results/retry-paths-book.json',
            sha256=SOURCES['calculations/results/retry-paths-book.json']['sha256'],
            role='Existing hypothetical teaching inputs/results; linked only, never recomputed or copied.',
            measured_price=False, real_budget=None),
        missing=['matched resource interventions on the primary full Agent workload',
                 'quality-passing full Agent completion', 'declared service deadline and success target',
                 'provider prices / measured total cost', 'GPU utilization, memory peak, and scheduling contention',
                 'full process-tree memory / pressure / swap', 'API quotas, throttles and ingress queues',
                 'cold start and prewarm comparison for the primary Agent', 'representative arrivals and replications'])
    for path, entry in SOURCES.items():
        check('sources_unchanged_after_analysis', digest((ROOT/path).read_bytes()) == entry['sha256'], path)
    usage = resource.getrusage(resource.RUSAGE_SELF)
    rss_bytes = usage.ru_maxrss if sys.platform == 'darwin' else usage.ru_maxrss*1024
    check('offline_resource_budget', rss_bytes <= 2*1024**3, 'peak RSS <=2GiB')
    checks = dict(schema_version=1, status='passed', groups=CHECKS,
        runtime=dict(python=sys.version.split()[0], platform=sys.platform, single_threaded=True,
                     hard_address_space_cap_applied=sys.platform != 'darwin',
                     child_processes_created=0, peak_rss_bytes=rss_bytes,
                     process_cpu_s=usage.ru_utime+usage.ru_stime, wall_s=time.monotonic()-begin),
        limitations=['No saved model or tool program was executed; quality checks inspect saved outputs only.',
                     'Source SHA checks prove byte identity, not correctness of the original instrumentation.',
                     'Process digest agreement uses stored outputs; no workload reference is recomputed.',
                     'Collector records inspected offline; this is not a complete SQLite/durability audit.',
                     'CPU seconds and wall seconds are different quantities; their difference is not measured wait time.'])
    decision = dict(schema_version=1, status='verification_plan_only',
        recommendation='First instrument the model-service path and establish quality-passing completion; then test GPU service capacity only if the matched workload shows pressure.',
        expansion_implemented=False, procurement_quantity=None, measured_expansion_gain=None,
        service_deadline_s=None, success_within_deadline_target=None, actual_budget=None,
        resources=[
            dict(resource='CPU', evidence='summary.json#/primary/model_controller_cpu_s',
                 finding='Controller is lightly consuming CPU during model request intervals; full CPU saturation/queues unmeasured.',
                 action='Measure tool queue, process-tree CPU and throttling before a one-core intervention.'),
            dict(resource='GPU', evidence='summary.json#/primary/model_wall_s',
                 finding='Model requests dominate this one failed attempt; no GPU saturation metric.',
                 action='Instrument service/queue/quality before a matched capacity intervention.'),
            dict(resource='memory', evidence='summary.json#/primary/rss_by_phase',
                 finding='Controller residency observed; full process tree and memory pressure unknown.',
                 action='Collect full scope memory/pressure before raising memory limit.'),
            dict(resource='API', evidence='summary.json#/primary/engine_queue_s',
                 finding='Local AsyncLLMEngine queue timestamps are available; external quota is not used or measured.',
                 action='Increasing an unused external API quota cannot affect this unchanged local call path.'),
            dict(resource='prewarm_pool', evidence='summary.json#/separate_prewarm',
                 finding='Separate 03-04 tool replay shows startup/residency tradeoffs; not matched to the primary trace.',
                 action='Test a small pool under the frozen full Agent workload and record unused residency.')],
        next_round=dict(protocol='README.md', implemented=False, randomization_seed=1110,
            feasibility_pairs=3, initial_formal_pairs_per_arm_and_block=30,
            primary_quality='all original six checks pass; independent checks separately reported',
            required_preregistration=['L', 'P', 'delta', 'B', 'resource allocations', 'arrival trace', 'cold/warm protocol'],
            acceptance='Quality and L/P, preregistered paired effect confidence interval and delta, cleanup/residency constraints, then owner-verified real cost within B; no successful denominator means no procurement conclusion.'),
        calculation_reference=summary['calculation_reference'])
    outputs = {'summary.json':summary, 'records.json':dict(schema_version=1, records=RECORDS),
               'decision.json':decision, 'checks.json':checks}
    encoded = {name:(json.dumps(obj, ensure_ascii=False, indent=2, allow_nan=False)+'\n').encode()
               for name,obj in outputs.items()}
    existing = sum(p.stat().st_size for p in HERE.rglob('*') if p.is_file() and p.name not in encoded)
    if existing+sum(map(len,encoded.values())) > 30*1024**2:
        raise ValueError('Output directory would exceed 30MiB')
    for name,data in encoded.items():
        (HERE/name).write_bytes(data)
    files = {p.relative_to(HERE).as_posix():dict(bytes=p.stat().st_size, sha256=digest(p.read_bytes()))
             for p in sorted(HERE.rglob('*')) if p.is_file() and p.name != 'manifest.json'}
    status = ROOT/'experiments/parallel-workers/pooldecision/status.md'
    manifest = dict(schema_version=1, files=files, self_excluded=True,
                    sources_lock_sha256=LOCK_SHA256,
                    external_status=dict(path=status.relative_to(ROOT).as_posix(),
                                         sha256=digest(status.read_bytes())),
                    scope='All deliverables in 11-10, excluding this manifest; sources are referenced, never copied.')
    (HERE/'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps(dict(status='passed', records=len(RECORDS), sources=len(SOURCES),
                         checks=sum(g['passed'] for g in CHECKS.values()), peak_rss_bytes=rss_bytes)))


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        # Do not overwrite a previous valid result on a failed source or data check.
        print(f'OFFLINE CHECK FAILED; outputs not refreshed: {exc}', file=sys.stderr)
        raise SystemExit(1)
