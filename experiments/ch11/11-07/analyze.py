"""Offline use/terminal-state ledger; no billing or quota conversion."""
import collections, hashlib, json, sys
from pathlib import Path
B=Path(__file__).absolute().parent
out=Path(sys.argv[1]) if len(sys.argv)>1 else B/'results'
out.mkdir(parents=True,exist_ok=True)
index=json.loads((B/'records/index.json').read_text())
rows=[];seen=set();terminal_seen=set();checks=0
for src in index['sources']:
    data=(B/'records'/src['excerpt']).read_bytes()
    assert hashlib.sha256(data).hexdigest()==src['excerpt_sha256'];checks+=1
    lines=data.splitlines(keepends=True)
    assert len(lines)==len(src['selected_lines']);checks+=1
    for line,ref in zip(lines,src['selected_lines']):
        assert len(line)==ref['bytes'] and hashlib.sha256(line).hexdigest()==ref['sha256'];checks+=1
    events=[json.loads(l) for l in lines]
    thread=[e['thread_id'] for e in events if e['type']=='thread.started']
    terminal=[e for e in events if e['type']=='turn.completed']
    assert len(thread)==len(terminal)==1;checks+=1
    key=(thread[0],src['source'])
    assert key not in seen;seen.add(key);checks+=1
    terminal_identity=(thread[0],json.dumps(terminal[0],sort_keys=True))
    assert terminal_identity not in terminal_seen;terminal_seen.add(terminal_identity);checks+=1
    usage=terminal[0]['usage']
    assert all(type(x) is int and x>=0 for x in usage.values());checks+=1
    assert usage['cached_input_tokens']<=usage['input_tokens'];checks+=1
    final=[e for e in events if e.get('item',{}).get('type')=='agent_message']
    rows.append(dict(source=src['source'],thread_id=thread[0],worker=src['source'].split('/')[0],
                     terminal_event='turn.completed',reported_usage=usage,final_message_present=bool(final),
                     accepted_task_count=None,monthly_coverage=None,elapsed_seconds=None,
                     billed_amount=None,product_quota_consumed=None,model_and_plan=None))
totals=dict(collections.Counter())
for r in rows:
    for k,v in r['reported_usage'].items():totals[k]=totals.get(k,0)+v
report=dict(scope='observed terminal turns, not invoices or quality-qualified monthly tasks',
            logs=len(rows),worker_directories=len({r['worker'] for r in rows}),distinct_thread_ids=len({r['thread_id'] for r in rows}),
            raw_usage_field_sums=totals,rows=rows,checks=checks,
            caveats=['Fields are reported separately; do not add cached tokens to input tokens or reasoning tokens to output tokens.',
                     'No inference of API billing, subscription quotas, model/plan identity, monthly coverage or quality acceptance.',
                     'Available retained logs only; absent or quota-blocked attempts are not counted as zero.',
                     'Different workers/resumed turns are not matched subscription/API/relay trials.',
                     'Repeated thread IDs occur; field sums are arithmetic over records, not proof of disjoint billed intervals.',
                     'Calculation and public pricing snapshots belong to separate owner.'])
(out/'analysis.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k not in ['rows','caveats']}))
