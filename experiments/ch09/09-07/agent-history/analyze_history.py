"""Reconstruct complete-output consistency and actual native cache operations."""
import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import re
import statistics


def main(args):
    root=args.run;prepared=json.loads((root/'prepared.json').read_text())
    completed=json.loads((root/'completion.json').read_text());rows=[];checks=0;groups=[]
    for result in completed:
        run=root/f'r{result["rep"]}-{result["condition"]}'
        raw=[json.loads(x) for x in (run/'requests.jsonl').read_text().splitlines()]
        assert len(raw)==result['requests']==12;checks+=1
        events=defaultdict(list);scheduled=defaultdict(int);peak_blocks=defaultdict(int)
        for index in range(2):
            for p in (run/f'engine{index}').glob('adapter-*.jsonl'):
                for line in p.read_text().splitlines():
                    e=json.loads(line);events[e['request_id']].append(e)
            for line in (run/f'engine{index}'/'blocks.jsonl').read_text().splitlines():
                e=json.loads(line)
                if e['event']=='schedule':
                    for rid,n in e['scheduled_tokens'].items():scheduled[rid]+=n
                for request in e['requests']:
                    peak_blocks[request['id']]=max(peak_blocks[request['id']],sum(len(group) for group in request['blocks']))
        for record in raw:
            source=prepared['requests'][record['turn']];prompt=source['prompt_token_ids']
            assert record['engine']==record['turn']%2;checks+=1
            candidates={key for key in set(events)|set(scheduled) if re.fullmatch(re.escape(record['id'])+r'(?:-[0-9a-f]{8})?',key)}
            assert len(candidates)==1;checks+=1;rid=candidates.pop();native=events[rid]
            try:action=json.loads(record['text']);valid_json=True
            except json.JSONDecodeError:action=None;valid_json=False
            ops={};stored_decode=0
            token_hashes={hashlib.sha256(json.dumps(prompt+record['output_ids'][:i]).encode()).hexdigest():len(prompt)+i
                          for i in range(len(record['output_ids'])+1)}
            for kind in ['store','retrieve']:
                submitted=[e for e in native if e['kind']==kind+'_submit' and e['submitted']]
                finished=[e for e in native if e['kind']==kind+'_complete']
                for e in submitted:
                    assert e['token_ids_sha256'] in token_hashes;checks+=1
                    assert 0<=e['start']<e['end']<=token_hashes[e['token_ids_sha256']];checks+=1
                    assert e['end']<=len(prompt)+len(record['output_ids'])-1;checks+=1
                    if kind=='store':stored_decode+=max(0,e['end']-max(e['start'],len(prompt)))
                ops[kind]=dict(submissions=len(submitted),completions=len(finished),
                    all_completions_successful=bool(finished) and all(e['success'] for e in finished),
                    ranges=[[e['start'],e['end'],e['skip_first_n_tokens']] for e in submitted])
            full_work=len(prompt)+len(record['output_ids'])-1
            if result['condition']=='recompute':assert scheduled[rid]==full_work;checks+=1
            stream=[e for e in record['events'] if e[1]>0];assert stream;checks+=1
            next_common=None
            if record['turn']+1<len(prepared['requests']):
                following=prepared['requests'][record['turn']+1]['prompt_token_ids']
                consumed=prompt+record['output_ids'][:-1]
                next_common=0
                for left,right in zip(consumed,following):
                    if left!=right:break
                    next_common+=1
            rows.append(dict(rep=result['rep'],condition=result['condition'],turn=record['turn'],id=record['id'],
                engine=record['engine'],native_id=rid,input_tokens=len(prompt),output_tokens=len(record['output_ids']),
                normal_stop=record['finish_reason']=='stop',valid_json=valid_json,
                original_action_equal=action==source['original_action'],
                original_ids_equal=record['output_ids']==source['original_output_ids'],
                output_ids=record['output_ids'],observed_ttft_s=stream[0][0]-record['start_s'],
                request_wall_s=record['end_s']-record['start_s'],scheduled_tokens=scheduled[rid],
                skipped_scheduled_tokens=full_work-scheduled[rid],peak_assigned_blocks=peak_blocks[rid],
                lookup_tokens=[e['matched_tokens'] for e in native if e['kind']=='lookup'],
                stored_decode_tokens=stored_decode,next_history_common_tokens=next_common,
                next_history_preserves_full_prompt=next_common>=len(prompt) if next_common is not None else None,
                operations=ops))
        groups.append(result)
    references={(r['rep'],r['turn']):r for r in rows if r['condition']=='recompute'}
    for row in rows:row['reference_ids_equal']=row['output_ids']==references[row['rep'],row['turn']]['output_ids']
    summary=[]
    for rep in range(prepared['repetitions']):
        for condition in prepared['conditions']:
            subset=[r for r in rows if r['rep']==rep and r['condition']==condition]
            complete=next(x for x in groups if x['rep']==rep and x['condition']==condition)
            summary.append(dict(rep=rep,condition=condition,requests=len(subset),
                normal_stop=sum(r['normal_stop'] for r in subset),reference_ids_equal=sum(r['reference_ids_equal'] for r in subset),
                original_ids_equal=sum(r['original_ids_equal'] for r in subset),
                ttft_median_ms=statistics.median(r['observed_ttft_s'] for r in subset)*1000,
                replay_wall_s=complete['replay_wall_s'],scheduled_tokens=sum(r['scheduled_tokens'] for r in subset),
                skipped_scheduled_tokens=sum(r['skipped_scheduled_tokens'] for r in subset),
                stored_decode_tokens=sum(r['stored_decode_tokens'] for r in subset),
                retrieve_submissions=sum(r['operations']['retrieve']['submissions'] for r in subset)))
    out=dict(checks=checks,rows=rows,summary=summary,source_task_succeeded=False,
             scope='Full generation for frozen failed Agent history; tools are not rerun and new outputs do not determine later inputs.')
    args.out.write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps({'checks':checks,'requests':len(rows),'normal_stop':sum(r['normal_stop'] for r in rows),
                      'reference_ids_equal':sum(r['reference_ids_equal'] for r in rows),'summary':summary}))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--run',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    main(p.parse_args())
