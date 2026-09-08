#!/usr/bin/env python3
"""Check declared source scopes and independent examples; execute no upstream code."""
from datetime import datetime, timezone
from fractions import Fraction as F
from pathlib import Path
import hashlib
import json
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'references/framework-history/2026-09-09/lora-admission'
INTERVIEWS = ROOT / 'references/interviews/2026-09-09/eighth-pass'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def check_file(row):
    data = (ROOT / row['file']).read_bytes()
    assert len(data) == row['bytes'] and sha(data) == row['sha256'], row['file']
    return data


def calculate():
    cfg = json.loads((ROOT / 'references/outline-checks/2026-09-07/scaling-history/qwen3-8b-config.json').read_text())
    hidden, layers, head_dim = cfg['hidden_size'], cfg['num_hidden_layers'], cfg['head_dim']
    q_out = cfg['num_attention_heads'] * head_dim
    v_out = cfg['num_key_value_heads'] * head_dim
    rank, element_bytes = 16, 2
    adapter = layers * rank * (hidden + q_out + hidden + v_out) * element_bytes
    kv_per_token = layers * 2 * v_out * element_bytes
    assert adapter == 15335424 and kv_per_token == 147456
    assert adapter / 2**20 == 14.625
    assert 100 * 8192 * kv_per_token / 2**30 == 112.5
    load_lower_bound_ms = F(adapter * 1000, 12 * 2**30)
    assert load_lower_bound_ms < 4

    # Count allocated token positions, not runtime or executed instruction count.
    groups = []
    for counts in [[20], [17, 1, 1, 1]]:
        allocated = sum(((n + 15) // 16) * 16 for n in counts)
        groups.append(dict(tokens_by_adapter=counts, blocks=allocated // 16,
                           positions=allocated, fill=float(F(sum(counts), allocated))))
    assert [x['blocks'] for x in groups] == [2, 5]
    assert [x['fill'] for x in groups] == [0.625, 0.25]

    # Independent dependency schedule. One serial copy lane, one compute lane;
    # no interference and enough GPU slots for all four adapters.
    load_ends = [4 * (i + 1) for i in range(4)]
    costs = {1: 16, 3: 20, 4: 22}
    plans = {}
    for name, batches in [('load_all', [[0, 1, 2, 3]]),
                          ('ready_first', [[0], [1, 2, 3]])]:
        compute_end = compute_work = 0
        completions = [None] * 4
        starts = [None] * 4
        timeline = []
        for batch in batches:
            start = max(compute_end, max(load_ends[i] for i in batch))
            duration = costs[len(batch)]
            compute_end = start + duration
            compute_work += duration
            timeline.append(dict(requests=batch, compute_ms=[start, compute_end]))
            for i in batch:
                starts[i] = start
                completions[i] = compute_end
        plans[name] = dict(completion_ms=completions,
                           mean_ms=sum(completions) / 4, maximum_ms=max(completions),
                           start_ms=starts, mean_wait_before_prefill_ms=sum(starts) / 4,
                           compute_work_ms=compute_work, timeline=timeline)
    assert plans['load_all']['completion_ms'] == [38] * 4
    assert plans['ready_first']['completion_ms'] == [20, 40, 40, 40]
    assert plans['ready_first']['mean_ms'] < plans['load_all']['mean_ms']
    assert plans['ready_first']['maximum_ms'] > plans['load_all']['maximum_ms']
    assert plans['load_all']['mean_wait_before_prefill_ms'] == plans['ready_first']['mean_wait_before_prefill_ms'] == 16
    assert [plans[k]['compute_work_ms'] for k in ['load_all', 'ready_first']] == [22, 36]
    return dict(adapter_bytes=adapter, adapter_mib=adapter / 2**20,
                hundred_adapters_gib=100 * adapter / 2**30,
                kv_bytes_per_token=kv_per_token, hundred_8192_token_requests_kv_gib=112.5,
                gpu_slots=8, pinned_slots=6, other_slots=8-6,
                assumed_copy_GiBps=12, copy_only_lower_bound_ms=float(load_lower_bound_ms),
                adapter_groups=groups, load_ends_ms=load_ends, schedules=plans,
                scope='Teaching inputs, not performance measurements. Prefill completion proxy, not full TTFT or P99; logical padding positions do not predict speedup.')


def verify_interviews():
    records = json.loads((INTERVIEWS / 'sources.json').read_text())
    proof = json.loads((INTERVIEWS / 'reading-proof.json').read_text())
    assert len(records) == len(proof['records']) == 3
    byid = {row['id']: row for row in records}
    for row in records:
        assert row['status_code'] == 200
        check_file(row)
    for scope in proof['records']:
        soup = BeautifulSoup(check_file(byid[scope['source_id']]), 'html.parser')
        assert scope['interview_date'] is None and not scope['new_primary_interview_sample']
        if scope['mode'] == 'restricted_main_state':
            raw = next(s.get_text() for s in soup.find_all('script')
                       if s.get_text().startswith('window.__INITIAL_STATE__='))
            obj = json.JSONDecoder().raw_decode(raw.split('=', 1)[1])[0]
            assert obj['prefetchData']['2']['ssrCommonData']['contentData'] == scope['observed_value']
        elif scope['mode'] == 'article_text':
            assert scope['selector'] == 'h1.find_parent(article)'
            article = soup.find('h1').find_parent('article')
            derived = (article.get_text('\n', strip=True) + '\n').encode()
            assert derived == (ROOT / scope['text_file']).read_bytes()
            assert len(derived) == scope['text_bytes'] and sha(derived) == scope['text_sha256']
            assert scope['displayed_date'] in derived.decode()
            external = [a['href'] for a in article.select('a[href]')
                        if a['href'].startswith(('https://', 'http://'))]
            assert external == scope['original_post_links'] == []
        else:
            raise AssertionError(scope['mode'])
    assert proof['new_numbered_questions'] == proof['new_primary_interview_samples'] == 0
    return dict(responses=3, article_texts_read=2, author_only_responses=1,
                new_primary_interview_samples=0, new_numbered_questions=0)


def verify():
    records = json.loads((SOURCE / 'sources.json').read_text())
    reading = json.loads((SOURCE / 'reading.json').read_text())
    assert len(records) == 19 and all(x['status_code'] == 200 for x in records)
    assert len(reading['derived_files']) == 1 and len(reading['reused_inputs']) == 14
    assert len(reading['scopes']) == 37
    all_records = records + reading['derived_files'] + reading['reused_inputs']
    byid = {x['id']: x for x in all_records}
    assert len(byid) == len(all_records)
    for row in all_records:
        data = check_file(row)
        if 'git_blob' in row:
            tree = json.loads((ROOT / row['tree_file']).read_text())
            assert not tree['truncated'] and tree['sha'] == row['commit']
            entry = next(x for x in tree['tree'] if x['path'] == row['repo_path'])
            blob = hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
            assert blob == row['git_blob'] == entry['sha']
        if 'selector' in row:
            assert row['selector'] == 'article, otherwise main'
            soup = BeautifulSoup(check_file(byid[row['source_id']]), 'html.parser')
            article = soup.find('article') or soup.find('main')
            assert data == (article.get_text('\n', strip=True) + '\n').encode()
    for scope in reading['scopes']:
        row = byid[scope['source_id']]
        assert (row['file'], row['sha256']) == (scope['file'], scope['sha256'])
        data = check_file(row)
        mode = scope['mode']
        if mode == 'lines':
            lo, hi = scope['first_line'], scope['last_line']
            lines = data.splitlines(keepends=True)
            assert 1 <= lo <= hi <= len(lines)
            assert sha(b''.join(lines[lo-1:hi])) == scope['selected_sha256']
            continue
        obj = json.loads(data)
        if mode == 'json_pr_body':
            assert all(obj[k] == v for k, v in scope['values'].items())
            assert sha(obj['body'].encode()) == scope['body_sha256']
            assert not scope['linked_images_read'] and not scope['comments_read']
        elif mode == 'history_identities':
            for entry in scope['entries']:
                item = obj[entry['index']]
                assert (item['sha'], item['commit']['committer']['date'], item['commit']['message'].splitlines()[0]) == (entry['sha'], entry['date'], entry['subject'])
        elif mode == 'commit_identity':
            assert scope['values'] == dict(sha=obj['sha'], date=obj['commit']['committer']['date'])
        elif mode == 'tree_entries':
            assert not obj['truncated'] and obj['sha'] == scope['commit']
            assert all(x in obj['tree'] for x in scope['entries'])
        elif mode == 'json_fields':
            assert all(obj[k] == v for k, v in scope['values'].items())
        else:
            raise AssertionError(mode)
    report = dict(verified_at=datetime.now(timezone.utc).isoformat(), status='passed',
                  framework_responses=19, derived_files=1, reused_inputs=14, read_scopes=37,
                  arithmetic=calculate(), interviews=verify_interviews(),
                  new_paper_readings=0, downloaded_code_executed=False,
                  hardware_experiments_run=False,
                  scope='Declared source identity/ranges, HTML extraction and independent arithmetic; not full framework/model integration or interview attribution.')
    (ROOT / 'research/2026-infra-survey/lora-admission-audit.json').write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    return report


if __name__ == '__main__':
    print(json.dumps(verify(), ensure_ascii=False))
