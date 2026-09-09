"""Reconstruct quality, token equivalence, native transfer and scheduler evidence."""
import argparse
from collections import defaultdict
import json
import re
from pathlib import Path

parser=argparse.ArgumentParser();parser.add_argument('run',type=Path)
parser.add_argument('--out',type=Path,required=True);args=parser.parse_args()
assert not args.out.exists()
root=args.run;prepared=json.loads((root/'prepared.json').read_text())
records=[json.loads(x) for x in (root/'requests.jsonl').read_text().splitlines()]
completion=json.loads((root/'completion.json').read_text())
assert len(records)==completion['requests']==len(prepared['cases'])*3
assert len({x['id'] for x in records})==len(records)
cases={x['id']:x for x in prepared['cases']}
references={r['case_id']:r for r in records if r['path']=='baseline'}
events=defaultdict(list);scheduled=defaultdict(int)
for name in ['baseline','producer','consumer']:
    for path in (root/name).glob('adapter-*.jsonl'):
        for line in path.read_text().splitlines():
            e=json.loads(line);events[e['request_id']].append(e)
    for line in (root/name/'blocks.jsonl').read_text().splitlines():
        e=json.loads(line)
        if e['event']=='schedule':
            for rid,n in e['scheduled_tokens'].items():scheduled[rid]+=n
rows=[]
for r in records:
    candidates={key for key in set(events)|set(scheduled) if re.fullmatch(re.escape(r['id'])+r'(?:-[0-9a-f]{8})?',key)}
    assert len(candidates)==1, (r['id'],candidates)
    native_id=candidates.pop()
    native=events[native_id]
    operations={}
    for kind in ['store','retrieve']:
        starts=[e for e in native if e['kind']==kind+'_submit' and e['submitted']]
        ends=[e for e in native if e['kind']==kind+'_complete']
        operations[kind]=dict(submissions=len(starts),completions=len(ends),
            all_reported_completions_successful=bool(ends) and all(e['success'] for e in ends),
            token_ranges=[[e['start'],e['end'],e['skip_first_n_tokens']] for e in starts])
    actual_quality=r['finish_reason']=='stop' and r['text'].strip()==cases[r['case_id']]['expected']
    assert actual_quality==r['quality_pass']
    stream=[e for e in r['events'] if e[1]>0]
    rows.append(dict(id=r['id'],case_id=r['case_id'],path=r['path'],
                     input_tokens=cases[r['case_id']]['input_tokens'],
                     output_tokens=len(r['output_ids']),quality_pass=actual_quality,
                     token_ids_equal_reference=r['output_ids']==references[r['case_id']]['output_ids'],
                     wall_s=r['end_s']-r['start_s'],
                     observed_ttft_s=stream[0][0]-r['start_s'] if stream else None,
                     native_request_id=native_id,scheduled_tokens=scheduled.get(native_id),
                     lookup_matched_tokens=[e['matched_tokens'] for e in native if e['kind']=='lookup'],
                     operations=operations))
result=dict(scope=prepared['scope'],smoke=prepared['smoke'],requests=len(rows),
            quality_pass=sum(r['quality_pass'] for r in rows),
            output_token_equal_reference=sum(r['token_ids_equal_reference'] for r in rows),
            rows=rows,
            limits=['Observation hooks perturb timing; no physical traffic measurement.',
                    'TTFT is application stream observation, not pure prefill kernel time.',
                    'A successful daemon lookup alone does not prove transfer completion.',
                    'Two engines share one GPU; no cross-host performance claim.'])
args.out.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:result[k] for k in ['smoke','requests','quality_pass','output_token_equal_reference']}))
