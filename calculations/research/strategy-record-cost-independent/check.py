"""Independent archived-protocol and exhaustive subset truth review."""
import hashlib
import importlib.util
import itertools
import json
import math
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
SOURCE = ROOT / 'calculations/research/strategy-record-cost'
spec = importlib.util.spec_from_file_location('strategy_candidate', SOURCE/'strategy_record_cost.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
result = module.calculate()
checks = []
locks = json.loads((SOURCE/'sources.lock.json').read_text())
for row in locks:
    data = (ROOT/row['file']).read_bytes()
    assert len(data)==row['bytes'] and hashlib.sha256(data).hexdigest()==row['sha256']
checks.append('18 locked originals verified')
all_attempts = all_groups = truncations = 0
for batch in result['batches']:
    paths = {x['kind']:ROOT/x['file'] for x in locks if x['batch']==batch['batch']}
    tasks = json.loads(paths['results/tasks.json'].read_text())
    truths = {}
    for task in tasks['tasks']:
        # Exhaustive inclusion masks, independent of candidate dynamic program.
        truths[task['id']] = sum(sum(value for value,include in zip(task['values'],mask) if include)==task['target']
                                for mask in itertools.product((0,1),repeat=len(task['values'])))
        assert truths[task['id']]==tasks['answers'][task['id']]
    raw=[json.loads(line) for line in paths['results/raw.jsonl'].read_text().splitlines()]
    assert len(raw)==24
    for record,group in zip(raw,batch['groups']):
        task = next(t for t in tasks['tasks'] if t['id']==record['task'])
        expected_attempts=1 if record['policy']=='adaptive' and len(task['values'])<=8 else 2
        assert len(record['candidates'])==expected_attempts
        assert record['selection_start']<=record['selected_at']<=record['scored_at']
        parsed=[]
        for attempt,candidate in zip(record['candidates'],group['candidates']):
            text=attempt['text']
            if not batch['batch'].startswith('no-thinking'):
                text=text.partition('</think>')[2] if '</think>' in text else ''
            try:value=json.loads(text)
            except (ValueError,TypeError):value=None
            value=value['count'] if isinstance(value,dict) and list(value)==['count'] and type(value['count']) is int else None
            parsed.append(value)
            assert candidate['parsed_value']==value
            assert candidate['input_tokens']==len(attempt['input_ids'])
            assert candidate['returned_output_ids']==len(attempt['output_ids'])
            assert candidate['task_correct']==(value==truths[record['task']])
            assert attempt['events'][-1]['tokens']==len(attempt['output_ids'])
            all_attempts+=1;truncations+=attempt['finish_reason']=='length'
        counts=Counter(value for value in parsed if value is not None)
        selected=min((i for i,v in enumerate(parsed) if counts and v is not None and counts[v]==max(counts.values())),default=None)
        assert group['selected_candidate_index']==selected
        if record['policy']=='parallel':
            assert max(a['start'] for a in record['candidates'])<min(a['end'] for a in record['candidates'])
        elif len(record['candidates'])==2:
            assert record['candidates'][0]['validation_end']<=record['candidates'][1]['start']
        assert group['group_wall_seconds']==record['scored_at']-record['start']
        all_groups+=1
    for strategy in batch['strategies']:
        selected=[r for r in raw if r['policy']==strategy['strategy']]
        inputs=sum(len(a['input_ids']) for r in selected for a in r['candidates'])
        outputs=sum(len(a['output_ids']) for r in selected for a in r['candidates'])
        assert strategy['input_tokens']==inputs and strategy['returned_output_ids']==outputs
        assert strategy['failed_group_output_ids']==outputs
        assert strategy['successes']==0
        for key in ('output_ids_per_success','group_wall_seconds_per_success','fee','gpu_seconds','actual_kv_peak_bytes'):
            assert strategy[key] is None
        wall=sum(r['scored_at']-r['start'] for r in selected)
        assert strategy['group_wall_seconds_sum']==wall
        if strategy['strategy']=='parallel':
            assert strategy['client_request_seconds_sum']>wall
    checks.append(batch['batch']+': brute-force truths, every strict parse/selection/candidate/schedule/cost')
assert (all_attempts,all_groups,truncations)==(132,72,88)
for values,winner in [([None,4,3,3,4],1),([8,9,9],1),([None,None],None),([2,1],0)]:
    assert module.selected_index(values)==winner
checks.append('synthetic valid-majority/tie cases supplement all-invalid archive')
(HERE/'results.json').write_text(json.dumps(dict(module_sha256=hashlib.sha256((SOURCE/'strategy_record_cost.py').read_bytes()).hexdigest(),checks=checks,attempts=all_attempts,groups=all_groups,truncations=truncations),indent=2)+'\n')
print('PASS 132 attempts,72 groups,88 truncations; independent exhaustive truths and protocol/cost checks')
